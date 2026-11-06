"""El mismo caso de uso en memoria y en base de datos debe dejar exactamente lo mismo (ADR-004).

Cada prueba ejecuta un flujo en los dos talleres, con el mismo reloj, y compara lo que responden
sus lectores, sus alertas y su bitácora. Si un servicio olvidara llamar a `guardar`, o el mapeo
perdiera un dato, las dos versiones dejarían de coincidir.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TypeVar

import pytest
from sqlalchemy import Engine, select

from application.comandos import (
    AjustarCotizacion,
    AsignarTrabajos,
    CancelarOrden,
    EntregarSinReparacion,
    PresentarCotizacion,
    ReactivarOrden,
    RefaccionPropuesta,
    RegistrarAvisoAlCliente,
    RegistrarEntrega,
    RegistrarLlegadaDeRefaccion,
    RegistrarRecontacto,
    RegistrarSalida,
    ReportarFallaAdicional,
    RevisarCotizacion,
    TrabajoPropuesto,
)
from application.consultas.vistas import ExpedienteDeOrdenVista
from application.manejadores.alertas import ManejadoresDeAlertas
from application.unidad_de_trabajo import RegistroDeBitacora
from domain.clientes.cliente import TipoCliente
from domain.compartido.valores import NumeroOrden, Placas
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import EstadoOrden
from infrastructure.base_de_datos.tablas import eventos
from infrastructure.eventos.publicador_en_proceso import PublicadorEnProceso
from tests.integration.apoyo_base import TallerEnBase
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    EMPLEADOS,
    GERENTE,
    OTRO_TECNICO,
    TECNICO,
    Taller,
    asignada,
    autorizada,
    con_adicional,
    cotizada,
    decidir,
    en_diagnostico,
    en_espera,
    en_reparacion,
    pagada,
    pausada,
    poner_hora,
    por_cobrar,
    recibida,
)

R = TypeVar("R")

LUNES_5 = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)  # mediodía en Monterrey
VIERNES_9 = LUNES_5 + timedelta(days=4)
_DESDE_SIEMPRE = datetime(2000, 1, 1, tzinfo=UTC)
_HASTA_SIEMPRE = datetime(2100, 1, 1, tzinfo=UTC)


def _con_alertas_reales(taller: Taller, publicador: PublicadorEnProceso) -> Taller:
    for tipo, manejador in ManejadoresDeAlertas(taller.uow).suscripciones().items():
        publicador.suscribir(tipo, manejador)
    return taller


def _bitacora_en_base(motor: Engine) -> list[RegistroDeBitacora]:
    with motor.connect() as conexion:
        filas = conexion.execute(select(eventos).order_by(eventos.c.id)).mappings().all()
    return [
        RegistroDeBitacora(
            fila["tipo"], fila["agregado"], fila["id_agregado"], fila["datos"], fila["ocurrido_en"]
        )
        for fila in filas
    ]


@dataclass
class Pareja:
    memoria: Taller
    base: TallerEnBase

    def en_ambas(self, flujo: Callable[[Taller], R]) -> R:
        """Ejecuta el flujo en los dos talleres y exige el mismo resultado y el mismo estado."""
        en_memoria = flujo(self.memoria)
        en_base = flujo(self.base)
        assert en_base == en_memoria
        self.exigir_que_coincidan()
        return en_base

    def exigir_que_coincidan(self) -> None:
        memoria, base = self.memoria.lector(), self.base.lector()
        resumenes = base.ordenes(None)
        assert resumenes == memoria.ordenes(None)
        for resumen in resumenes:
            numero = NumeroOrden(resumen.numero_orden)
            assert base.expediente(numero) == memoria.expediente(numero)
        assert base.clientes(None, None) == memoria.clientes(None, None)
        assert base.solicitudes_pendientes() == memoria.solicitudes_pendientes()
        assert (
            base.cotizaciones_pendientes_de_aprobacion()
            == memoria.cotizaciones_pendientes_de_aprobacion()
        )
        assert (
            base.ordenes_con_solicitudes_pendientes()
            == memoria.ordenes_con_solicitudes_pendientes()
        )
        assert (
            base.cotizaciones_presentadas_sin_decision()
            == memoria.cotizaciones_presentadas_sin_decision()
        )
        assert base.total_de_pagos_entre(
            _DESDE_SIEMPRE, _HASTA_SIEMPRE
        ) == memoria.total_de_pagos_entre(_DESDE_SIEMPRE, _HASTA_SIEMPRE)
        for empleado in EMPLEADOS:
            identificador, rol = empleado.id_empleado, empleado.rol
            assert base.alertas_de(identificador, rol) == memoria.alertas_de(identificador, rol)
            assert base.panel_del_tecnico(identificador) == memoria.panel_del_tecnico(identificador)
        assert _bitacora_en_base(self.base.motor) == self.memoria.datos.bitacora

    def expediente(self, numero: str) -> ExpedienteDeOrdenVista:
        return self.base.lector().expediente(NumeroOrden(numero))


@pytest.fixture
def pareja(motor: Engine) -> Pareja:
    publicador_de_memoria, publicador_de_base = PublicadorEnProceso(), PublicadorEnProceso()
    return Pareja(
        _con_alertas_reales(Taller(publicador_de_memoria), publicador_de_memoria),
        _con_alertas_reales(TallerEnBase(motor, publicador_de_base), publicador_de_base),
    )


# ------------------------------------------------------------------ flujos completos
def test_flujo_orden_particular_completa(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero = pagada(taller)
        taller.entrega.entregar(RegistrarEntrega(numero))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.estado == "Cerrada"
    assert (expediente.pago_monto, expediente.pago_forma) == ("3000.00", "Tarjeta")
    assert expediente.total_autorizado == "3000.00"
    assert [trabajo.estado for trabajo in expediente.trabajos] == ["Completado", "Completado"]
    assert expediente.fecha_entrega == AHORA


def test_flujo_orden_de_flotilla_con_credito(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero = por_cobrar(taller)
        taller.entrega.entregar(RegistrarEntrega(numero))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.estado == "Cerrada"
    assert expediente.credito_monto == "3000.00"
    assert expediente.credito_fecha_vencimiento == date(2026, 10, 20)
    assert expediente.pago_monto is None
    assert expediente.cotizaciones[0].autorizante == "Ana Torres"


# ------------------------------------------------------------------ criterios y reglas
def test_ca_012_rechazo_total_queda_guardado(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, id_cotizacion = cotizada(taller)
        decidir(taller, id_cotizacion, ())
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.estado == "Cotizada"
    assert expediente.rechazo_total is True
    assert expediente.cotizaciones[0].estado == "Rechazada"
    assert expediente.trabajos == ()


def test_rn_18_entrega_sin_reparacion_tras_rechazo(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, id_cotizacion = cotizada(taller)
        decidir(taller, id_cotizacion, ())
        taller.entrega.entregar_sin_reparacion(EntregarSinReparacion(numero))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.estado == "Cerrada sin Reparación"
    assert expediente.pago_monto is None


def test_rn_05_ajuste_reemplaza_lineas_y_refacciones(pareja: Pareja) -> None:
    ajuste = (
        TrabajoPropuesto(
            1,
            "Frenos",
            Decimal("100.00"),
            (RefaccionPropuesta("Balatas", 2, Decimal("50.00")),),
        ),
    )

    def flujo(taller: Taller) -> str:
        numero, id_cotizacion = cotizada(taller, importes=("9000.00", "9000.00"))
        taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, False, "Bajar el costo"))
        taller.cotizacion.ajustar(AjustarCotizacion(id_cotizacion, ajuste))
        return numero

    cotizacion = pareja.expediente(pareja.en_ambas(flujo)).cotizaciones[0]

    assert cotizacion.estado == "Pendiente de Autorización del Cliente"
    assert cotizacion.observaciones_del_gerente == "Bajar el costo"
    assert cotizacion.total == "200.00"
    assert [linea.descripcion for linea in cotizacion.lineas] == ["Frenos"]
    assert [r.descripcion for r in cotizacion.lineas[0].refacciones] == ["Balatas"]


def test_rn_04_cotizacion_aprobada_por_el_gerente_guarda_su_fecha(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, id_cotizacion = cotizada(taller, importes=("20000.00",))
        pendientes = taller.lector().cotizaciones_pendientes_de_aprobacion()
        assert [(c.id_cotizacion, c.version, c.total) for c in pendientes] == [
            (id_cotizacion, "v.1", "20000.00")
        ]
        taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, True))
        return numero

    cotizacion = pareja.expediente(pareja.en_ambas(flujo)).cotizaciones[0]

    assert cotizacion.estado == "Pendiente de Autorización del Cliente"
    assert cotizacion.fecha_aprobacion_gerencial == AHORA


def test_ca_016_adicional_es_la_siguiente_version(pareja: Pareja) -> None:
    numero, _ = pareja.en_ambas(con_adicional)

    expediente = pareja.expediente(numero)

    assert [(c.version, c.tipo) for c in expediente.cotizaciones] == [
        ("v.1", "Inicial"),
        ("v.2", "Adicional"),
    ]
    assert expediente.cotizaciones[1].total == "1200.00"


def test_ca_017_adicional_autorizada_agrega_trabajos(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, id_adicional = con_adicional(taller)
        decidir(taller, id_adicional, (1,))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert [(t.id, t.importe, t.estado) for t in expediente.trabajos[2:]] == [
        (3, "500.00", "Pendiente"),
        (4, "700.00", "No Autorizado"),
    ]
    alertas = pareja.base.lector().alertas_de(TECNICO, RolDeEmpleado.TECNICO)
    assert "CotizacionAutorizada" in [alerta.tipo for alerta in alertas]


def test_ca_022_al_llegar_la_refaccion_regresa_a_su_estado(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[str, str]:
        sin_iniciar = en_espera(taller)
        iniciada = en_espera(taller, iniciada=True)
        for numero in (sin_iniciar, iniciada):
            taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))
        return sin_iniciar, iniciada

    sin_iniciar, iniciada = pareja.en_ambas(flujo)

    assert pareja.expediente(sin_iniciar).estado == "Autorizada"
    assert pareja.expediente(iniciada).estado == "En Reparación"
    solicitud = pareja.expediente(sin_iniciar).solicitudes[0]
    assert (solicitud.estado, solicitud.fecha_llegada) == ("Disponible", AHORA)


def test_ca_024_al_llegar_la_refaccion_se_descarta_la_nota_sin_firmar(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero = en_espera(taller)
        taller.retiro.registrar_salida(RegistrarSalida(numero))
        taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.nota_fecha_salida is None
    assert expediente.nota_firmada is False


def test_ca_025_reactivada_va_al_final_de_la_fila(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[str, str]:
        retirada = pausada(taller)
        en_el_taller = asignada(taller)
        poner_hora(taller.reloj, AHORA + timedelta(days=2))
        taller.retiro.reactivar(ReactivarOrden(retirada))
        return retirada, en_el_taller

    retirada, en_el_taller = pareja.en_ambas(flujo)

    panel = pareja.base.lector().panel_del_tecnico(TECNICO)
    assert [vista.numero_orden for vista in panel] == [en_el_taller, retirada]
    assert pareja.expediente(retirada).estado == "En Espera de Refacción"
    assert pareja.expediente(retirada).nota_firmada is True


def test_ca_034_falla_adicional_queda_guardada(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero = en_reparacion(taller)
        taller.diagnostico.reportar_falla_adicional(
            ReportarFallaAdicional(numero, TECNICO, "Fuga de aceite")
        )
        return numero

    falla = pareja.expediente(pareja.en_ambas(flujo)).fallas_adicionales[0]

    assert (falla.id, falla.descripcion, falla.tecnico) == (1, "Fuga de aceite", TECNICO)
    assert falla.reportada_en == AHORA


def test_ca_044_cancelacion_queda_guardada(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero = recibida(taller)
        taller.cancelacion.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))
        return numero

    expediente = pareja.expediente(pareja.en_ambas(flujo))

    assert expediente.estado == "Cancelada"
    assert expediente.cancelacion_motivo == "El cliente desistió"


# ------------------------------------------------------------------ lector
def test_ca_013_panel_del_tecnico_por_fila_de_trabajo(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[str, str]:
        poner_hora(taller.reloj, AHORA + timedelta(hours=1))
        reciente = en_diagnostico(taller)
        poner_hora(taller.reloj, AHORA)
        antigua = asignada(taller)
        return antigua, reciente

    antigua, reciente = pareja.en_ambas(flujo)

    panel = pareja.base.lector().panel_del_tecnico(TECNICO)
    assert [vista.numero_orden for vista in panel] == [antigua, reciente]
    assert [vista.diagnostico_asignado for vista in panel] == [False, True]
    assert [trabajo.id for trabajo in panel[0].trabajos] == [1, 2]


def test_ca_036_panel_muestra_solo_trabajos_del_tecnico(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, _ = autorizada(taller, lineas=(1,))
        taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), OTRO_TECNICO))
        return numero

    numero = pareja.en_ambas(flujo)

    lector = pareja.base.lector()
    assert lector.panel_del_tecnico(TECNICO) == []
    panel = lector.panel_del_tecnico(OTRO_TECNICO)
    assert [(vista.numero_orden, [t.id for t in vista.trabajos]) for vista in panel] == [
        (numero, [1])
    ]


def test_rn_20_consulta_exige_folio_y_placas(pareja: Pareja) -> None:
    numero = pareja.en_ambas(recibida)
    placas = Placas("ABC001")

    for lector in (pareja.memoria.lector(), pareja.base.lector()):
        vista = lector.estado_de_orden(NumeroOrden(numero), placas)
        assert (vista.numero_orden, vista.estado) == (numero, "Recibida")
        assert lector.estado_de_orden(NumeroOrden(numero), Placas("OTRA1")) is None
        assert lector.estado_de_orden(NumeroOrden("OS-9999"), placas) is None


def test_rn_21_ingresos_suman_contado_sin_credito(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> None:
        pagada(taller)
        por_cobrar(taller)

    pareja.en_ambas(flujo)

    una_hora = timedelta(hours=1)
    for lector in (pareja.memoria.lector(), pareja.base.lector()):
        assert lector.total_de_pagos_entre(AHORA - una_hora, AHORA + una_hora) == Decimal("3000.00")
        assert lector.total_de_pagos_entre(AHORA, AHORA + una_hora) == Decimal("3000.00")
        assert lector.total_de_pagos_entre(AHORA - una_hora, AHORA) == 0


def test_lector_filtra_clientes_y_ordenes(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[str, str]:
        return recibida(taller), en_diagnostico(taller, flotilla=True)

    particular, flotilla = pareja.en_ambas(flujo)

    for lector in (pareja.memoria.lector(), pareja.base.lector()):
        assert [c.nombre for c in lector.clientes(TipoCliente.FLOTILLA, "NORTE")] == [
            "Transportes Norte SA"
        ]
        assert lector.clientes(TipoCliente.FLOTILLA, "Otra") == []
        assert len(lector.clientes(TipoCliente.PARTICULAR, None)) == 1
        assert [o.numero_orden for o in lector.ordenes(EstadoOrden.RECIBIDA)] == [particular]
        assert [o.numero_orden for o in lector.ordenes(EstadoOrden.EN_DIAGNOSTICO)] == [flotilla]
        assert lector.vehiculo_por_placas(Placas("ABC001")).cliente.nombre == "Luis Peña"
        assert lector.vehiculo_por_placas(Placas("NOEXISTE")) is None
        assert lector.expediente(NumeroOrden("OS-9999")) is None
        assert lector.cotizacion("COT-9999") is None


def test_lector_devuelve_la_cotizacion_con_sus_lineas(pareja: Pareja) -> None:
    _, id_cotizacion = pareja.en_ambas(cotizada)

    en_base = pareja.base.lector().cotizacion(id_cotizacion)

    assert en_base == pareja.memoria.lector().cotizacion(id_cotizacion)
    assert en_base.total == "3000.00"
    assert [linea.subtotal for linea in en_base.lineas] == ["1000.00", "2000.00"]


# ------------------------------------------------------------------ plazos y alertas
def _revisar_en(taller: Taller, fecha: datetime) -> tuple[int, int]:
    poner_hora(taller.reloj, fecha)
    resultado = taller.revision.revisar()
    return resultado.alertas_de_refaccion, resultado.alertas_de_recontacto


def _presentada(taller: Taller) -> str:
    _, id_cotizacion = cotizada(taller)
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    return id_cotizacion


def test_ca_023_revision_alerta_refaccion_retrasada_una_vez(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[tuple[int, int], tuple[int, int]]:
        poner_hora(taller.reloj, LUNES_5)
        en_espera(taller)
        return _revisar_en(taller, VIERNES_9), _revisar_en(taller, VIERNES_9)

    assert pareja.en_ambas(flujo) == ((1, 0), (0, 0))


def test_rn_11_aviso_al_cliente_detiene_la_alerta(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> tuple[int, int]:
        poner_hora(taller.reloj, LUNES_5)
        numero = en_espera(taller)
        taller.refacciones.registrar_aviso_al_cliente(RegistrarAvisoAlCliente(numero, 1))
        return _revisar_en(taller, VIERNES_9)

    assert pareja.en_ambas(flujo) == (0, 0)
    assert pareja.expediente("OS-0001").solicitudes[0].fecha_aviso_al_cliente == LUNES_5


def test_ca_040_revision_alerta_cotizacion_sin_respuesta_por_periodo(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> list[tuple[int, int]]:
        id_cotizacion = _presentada(taller)
        tras_49_horas = AHORA + timedelta(hours=49)
        resultados = [_revisar_en(taller, tras_49_horas), _revisar_en(taller, tras_49_horas)]
        taller.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))
        resultados.append(_revisar_en(taller, tras_49_horas + timedelta(hours=49)))
        return resultados

    assert pareja.en_ambas(flujo) == [(0, 1), (0, 0), (0, 1)]


def test_rn_11_revision_conserva_alertas_de_refaccion_y_de_cotizacion(pareja: Pareja) -> None:
    """Si el lector corriera dentro de la transacción, en SQLite se perderían las de refacción."""

    def flujo(taller: Taller) -> tuple[int, int]:
        poner_hora(taller.reloj, LUNES_5)
        en_espera(taller)
        _presentada(taller)
        return _revisar_en(taller, VIERNES_9)

    assert pareja.en_ambas(flujo) == (1, 1)

    tipos = [a.tipo for a in pareja.base.lector().alertas_de(ASESOR, RolDeEmpleado.ASESOR)]
    assert "RefaccionRetrasada" in tipos
    assert "CotizacionSinRespuesta" in tipos


def test_alertas_y_bitacora_iguales_en_memoria_y_base(pareja: Pareja) -> None:
    def flujo(taller: Taller) -> str:
        numero, id_cotizacion = cotizada(taller, importes=("20000.00",))
        taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, True))
        return numero

    pareja.en_ambas(flujo)

    gerentes = pareja.base.lector().alertas_de(GERENTE, RolDeEmpleado.GERENTE)
    assert [alerta.tipo for alerta in gerentes] == ["AprobacionGerencialRequerida"]
    assert gerentes[0].destinatario_rol is RolDeEmpleado.GERENTE
    assert "CotizacionAprobadaPorGerente" in [
        registro.tipo for registro in _bitacora_en_base(pareja.base.motor)
    ]
