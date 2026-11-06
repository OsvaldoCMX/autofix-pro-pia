"""Unidad de Trabajo con base de datos: confirmar, revertir, bitácora y publicación (ADR-002, 016)."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy import Table, func, insert, select
from sqlalchemy.exc import IntegrityError, OperationalError

from application.comandos import CancelarOrden, RegistrarDecisionDelCliente
from application.puertos import PublicadorDeEventos
from application.servicios.servicio_de_cancelacion import ServicioDeCancelacion
from domain.compartido.errores import AutorizanteNoValido, ValorInvalido
from domain.compartido.valores import Dinero, NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import RolDeAutorizante, TipoCotizacion, VersionCotizacion
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from infrastructure.base_de_datos.repositorios import siguiente_folio
from infrastructure.base_de_datos.tablas import (
    clientes,
    cotizaciones,
    eventos,
    ordenes,
    trabajos,
)
from infrastructure.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.integration.apoyo_base import TallerEnBase
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    TECNICO,
    asignada,
    autorizada,
    cotizada,
    decidir,
    recibida,
)


def _contar(taller: TallerEnBase, tabla: Table) -> int:
    with taller.motor.connect() as conexion:
        return conexion.execute(select(func.count()).select_from(tabla)).scalar_one()


def _estado_de_orden(taller: TallerEnBase, numero: str) -> str:
    with taller.motor.connect() as conexion:
        return conexion.execute(
            select(ordenes.c.estado).where(ordenes.c.numero == numero)
        ).scalar_one()


def _orden_sin_cliente() -> OrdenDeServicio:
    return OrdenDeServicio(
        NumeroOrden("OS-0500"), "CLI-INEXISTENTE", False, Placas("XYZ1"), ASESOR, "Revisión", AHORA
    )


def test_confirmar_guarda_los_cambios(taller_en_base: TallerEnBase) -> None:
    recibida(taller_en_base)

    assert _contar(taller_en_base, ordenes) == 1
    assert _contar(taller_en_base, clientes) == 1


def test_sin_confirmar_no_guarda(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)

    with taller_en_base.uow() as uow:
        orden = uow.ordenes.obtener(NumeroOrden(numero))
        orden.asignar_tecnico_para_diagnostico(TECNICO, AHORA)
        uow.ordenes.guardar(orden)

    assert _estado_de_orden(taller_en_base, numero) == "Recibida"


def test_rn_22_error_revierte_los_dos_aggregates(taller_en_base: TallerEnBase) -> None:
    numero, id_cotizacion = cotizada(taller_en_base)

    with pytest.raises(ValorInvalido), taller_en_base.uow() as uow:
        cotizacion = uow.cotizaciones.obtener(id_cotizacion)
        cotizacion.marcar_presentada(AHORA)
        uow.cotizaciones.guardar(cotizacion)
        orden = uow.ordenes.obtener(NumeroOrden(numero))
        orden.rechazo_total = True
        uow.ordenes.guardar(orden)
        raise ValorInvalido("Falla a la mitad de la operación.")

    with taller_en_base.uow() as uow:
        assert uow.cotizaciones.obtener(id_cotizacion).fecha_presentacion is None
        assert uow.ordenes.obtener(NumeroOrden(numero)).rechazo_total is False


def test_ca_010_decision_guarda_cotizacion_orden_y_trabajos_juntos(
    taller_en_base: TallerEnBase,
) -> None:
    numero, id_cotizacion = cotizada(taller_en_base)

    decidir(taller_en_base, id_cotizacion, (1,))

    with taller_en_base.motor.connect() as conexion:
        estado = conexion.execute(
            select(cotizaciones.c.estado).where(cotizaciones.c.id == id_cotizacion)
        ).scalar_one()
    assert estado == "Autorizada Parcialmente"
    assert _estado_de_orden(taller_en_base, numero) == "Autorizada"
    assert _contar(taller_en_base, trabajos) == 2


def test_ca_010_autorizante_invalido_no_modifica_nada(taller_en_base: TallerEnBase) -> None:
    numero, id_cotizacion = cotizada(taller_en_base, flotilla=True)

    with pytest.raises(AutorizanteNoValido):
        taller_en_base.autorizacion.registrar_decision(
            RegistrarDecisionDelCliente(
                id_cotizacion, (1, 2), "Pedro, conductor", RolDeAutorizante.CLIENTE
            )
        )

    assert _estado_de_orden(taller_en_base, numero) == "Cotizada"
    assert _contar(taller_en_base, trabajos) == 0


def test_bitacora_se_guarda_en_la_misma_transaccion(taller_en_base: TallerEnBase) -> None:
    numero = asignada(taller_en_base)

    with taller_en_base.motor.connect() as conexion:
        fila = (
            conexion.execute(select(eventos).where(eventos.c.tipo == "TrabajosAsignados"))
            .mappings()
            .one()
        )

    assert (fila["agregado"], fila["id_agregado"]) == ("Orden", numero)
    assert fila["datos"] == {
        "numero_orden": numero,
        "ids_trabajos": [1, 2],
        "tecnico": TECNICO,
    }
    assert fila["ocurrido_en"] == AHORA
    assert fila["registrado_en"] is not None


def test_bitacora_se_revierte_si_no_se_confirma(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)
    antes = _contar(taller_en_base, eventos)

    with pytest.raises(ValorInvalido), taller_en_base.uow() as uow:
        orden = uow.ordenes.obtener(NumeroOrden(numero))
        orden.asignar_tecnico_para_diagnostico(TECNICO, AHORA)
        uow.ordenes.guardar(orden)
        raise ValorInvalido("Falla antes de confirmar.")

    assert _contar(taller_en_base, eventos) == antes


def test_eventos_se_publican_solo_al_confirmar(taller_en_base: TallerEnBase) -> None:
    """Cuando el publicador recibe el evento, el cambio ya se ve desde otra conexión."""
    numero = recibida(taller_en_base)
    visto: list[str] = []
    publicador = Mock(spec=PublicadorDeEventos)
    publicador.publicar.side_effect = lambda _eventos: visto.append(
        _estado_de_orden(taller_en_base, numero)
    )
    servicio = ServicioDeCancelacion(taller_en_base.uow(), taller_en_base.reloj, publicador)

    servicio.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    assert visto == ["Cancelada"]
    publicados = publicador.publicar.call_args.args[0]
    assert [type(evento).__name__ for evento in publicados] == ["OrdenCancelada"]

    uow = taller_en_base.uow()
    with uow:
        assert uow.eventos_confirmados() == []


def test_no_publica_si_falla_el_commit(taller_en_base: TallerEnBase) -> None:
    class UnidadQueFallaAlConfirmar(UnidadDeTrabajoSqlAlchemy):
        def _confirmar(self) -> None:
            raise OperationalError("COMMIT", {}, Exception("Se perdió la conexión."))

    numero = recibida(taller_en_base)
    publicador = Mock(spec=PublicadorDeEventos)
    uow = UnidadQueFallaAlConfirmar(taller_en_base.motor)
    servicio = ServicioDeCancelacion(uow, taller_en_base.reloj, publicador)

    with pytest.raises(OperationalError):
        servicio.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    publicador.publicar.assert_not_called()
    assert uow.eventos_confirmados() == []
    assert uow._conexion.closed
    assert _estado_de_orden(taller_en_base, numero) == "Recibida"


def test_la_conexion_se_cierra_al_confirmar_y_al_revertir(taller_en_base: TallerEnBase) -> None:
    al_confirmar = taller_en_base.uow()
    with al_confirmar as uow:
        uow.confirmar()
    sin_confirmar = taller_en_base.uow()
    with sin_confirmar:
        pass
    con_error = taller_en_base.uow()
    with pytest.raises(ValorInvalido), con_error:
        raise ValorInvalido("Falla.")

    assert al_confirmar._conexion.closed
    assert sin_confirmar._conexion.closed
    assert con_error._conexion.closed


def test_la_misma_unidad_se_puede_volver_a_usar(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)
    uow = taller_en_base.uow()

    for _ in range(2):
        with uow:
            assert uow.ordenes.obtener(NumeroOrden(numero)).numero == NumeroOrden(numero)
            uow.confirmar()


def test_leer_una_orden_sin_guardar_no_la_escribe(taller_en_base: TallerEnBase) -> None:
    """Un manejador de alertas lee la orden: no debe regresarla a un estado viejo."""
    numero = recibida(taller_en_base)

    with taller_en_base.uow() as uow:
        uow.ordenes.obtener(NumeroOrden(numero)).motivo_de_ingreso = "Cambio sin guardar"
        uow.confirmar()

    with taller_en_base.uow() as uow:
        assert uow.ordenes.obtener(NumeroOrden(numero)).motivo_de_ingreso == "Ruido al frenar"


def test_rn_23_la_base_rechaza_importe_negativo(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)

    with pytest.raises(IntegrityError), taller_en_base.motor.begin() as conexion:
        conexion.execute(
            insert(trabajos).values(
                numero_orden=numero, id=1, descripcion="Negativo", importe=-1, estado="Pendiente"
            )
        )


def test_rn_22_la_base_rechaza_un_estado_fuera_del_glosario(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)

    with pytest.raises(IntegrityError), taller_en_base.motor.begin() as conexion:
        conexion.execute(ordenes.update().where(ordenes.c.numero == numero).values(estado="Otro"))


def test_la_base_rechaza_orden_sin_cliente(taller_en_base: TallerEnBase) -> None:
    with pytest.raises(IntegrityError), taller_en_base.uow() as uow:
        uow.ordenes.agregar(_orden_sin_cliente())

    assert _contar(taller_en_base, ordenes) == 0


def test_folio_inexistente_se_rechaza(taller_en_base: TallerEnBase) -> None:
    with taller_en_base.motor.begin() as conexion:
        with pytest.raises(LookupError, match="no_existe"):
            siguiente_folio(conexion, "no_existe")
        assert siguiente_folio(conexion, "recibo") == 1
        assert siguiente_folio(conexion, "recibo") == 2


def test_recibo_numero_no_se_borra_al_guardar(taller_en_base: TallerEnBase) -> None:
    """El recibo es de la Fase 10: mientras tanto, guardar la orden no toca esa columna."""
    numero = recibida(taller_en_base)
    with taller_en_base.motor.begin() as conexion:
        conexion.execute(
            ordenes.update().where(ordenes.c.numero == numero).values(recibo_numero="REC-0001")
        )

    with taller_en_base.uow() as uow:
        uow.ordenes.guardar(uow.ordenes.obtener(NumeroOrden(numero)))
        uow.confirmar()

    with taller_en_base.motor.connect() as conexion:
        recibo = conexion.execute(
            select(ordenes.c.recibo_numero).where(ordenes.c.numero == numero)
        ).scalar_one()
    assert recibo == "REC-0001"


# ------------------------------------------------------------------ solo PostgreSQL
@pytest.fixture
def en_postgresql(taller_en_base: TallerEnBase) -> TallerEnBase:
    if taller_en_base.motor.dialect.name != "postgresql":
        pytest.skip("SQLite no tiene bloqueos de fila.")
    return taller_en_base


def _esta_bloqueada(taller: TallerEnBase, consulta: object) -> bool:
    """Intenta tomar el bloqueo sin esperar: si otra transacción lo tiene, falla al momento."""
    with taller.motor.connect() as conexion:
        try:
            conexion.execute(consulta.with_for_update(nowait=True))
        except OperationalError:
            return True
    return False


def test_obtener_bloquea_la_fila_de_la_orden(en_postgresql: TallerEnBase) -> None:
    numero = recibida(en_postgresql)
    consulta = select(ordenes.c.numero).where(ordenes.c.numero == numero)

    with en_postgresql.uow() as uow:
        uow.ordenes.obtener(NumeroOrden(numero))
        assert _esta_bloqueada(en_postgresql, consulta)
        assert en_postgresql.lector().expediente(NumeroOrden(numero)) is not None

    assert not _esta_bloqueada(en_postgresql, consulta)


def test_obtener_bloquea_la_fila_de_la_cotizacion(en_postgresql: TallerEnBase) -> None:
    _, id_cotizacion = autorizada(en_postgresql)
    consulta = select(cotizaciones.c.id).where(cotizaciones.c.id == id_cotizacion)

    with en_postgresql.uow() as uow:
        uow.cotizaciones.obtener(id_cotizacion)
        assert _esta_bloqueada(en_postgresql, consulta)

    assert not _esta_bloqueada(en_postgresql, consulta)


def test_el_lector_no_bloquea_la_orden(en_postgresql: TallerEnBase) -> None:
    numero = recibida(en_postgresql)
    consulta = select(ordenes.c.numero).where(ordenes.c.numero == numero)

    assert en_postgresql.lector().expediente(NumeroOrden(numero)) is not None
    assert not _esta_bloqueada(en_postgresql, consulta)


def test_cotizacion_de_una_orden_inexistente_se_rechaza(taller_en_base: TallerEnBase) -> None:
    cotizacion = Cotizacion.generar(
        "COT-1",
        NumeroOrden("OS-9999"),
        TipoCotizacion.INICIAL,
        VersionCotizacion(1),
        [LineaDeCotizacion(1, "Afinación", Dinero("100"))],
        AHORA,
    )

    with pytest.raises(IntegrityError), taller_en_base.uow() as uow:
        uow.cotizaciones.agregar(cotizacion)
