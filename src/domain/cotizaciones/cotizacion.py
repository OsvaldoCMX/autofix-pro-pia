"""Aggregate Cotización (raíz: Cotizacion).

Invariantes que protege:
- Tiene al menos un trabajo y su total es la suma de sus líneas (RN-23).
- La inicial es v.1; las adicionales son v.2 en adelante (RN-24).
- No se presenta al cliente mientras espera al Gerente (RN-06).
- El rechazo del Gerente exige observaciones y la ajustada no regresa a revisión (RN-05).
- La decisión se registra una sola vez y sobre líneas existentes (RN-22).
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from domain.compartido.errores import (
    CotizacionSinTrabajos,
    OperacionDeCotizacionNoPermitida,
    ValorInvalido,
)
from domain.compartido.especificacion import Especificacion
from domain.compartido.eventos import RaizDeAgregado
from domain.compartido.valores import Dinero, NumeroOrden, texto_requerido
from domain.cotizaciones import eventos as ev
from domain.cotizaciones.especificaciones import RequiereAprobacionGerencial
from domain.cotizaciones.estados import MAQUINA_DE_COTIZACION, EstadoCotizacion
from domain.cotizaciones.linea_de_cotizacion import DecisionDeLinea, LineaDeCotizacion
from domain.cotizaciones.valores import (
    Autorizante,
    DecisionDelCliente,
    Recontacto,
    TipoCotizacion,
    TrabajoDecidido,
    VersionCotizacion,
)

_E = EstadoCotizacion


class Cotizacion(RaizDeAgregado):
    def __init__(
        self,
        id_cotizacion: str,
        numero_orden: NumeroOrden,
        tipo: TipoCotizacion,
        version: VersionCotizacion,
        lineas: Iterable[LineaDeCotizacion],
        generada_en: datetime,
    ) -> None:
        super().__init__()
        self._validar_version(tipo, version)
        self.id = id_cotizacion
        self.numero_orden = numero_orden
        self.tipo = tipo
        self.version = version
        self._lineas = self._indexar_lineas(lineas)
        self.estado = _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
        self.generada_en = generada_en
        self.fecha_aprobacion_gerencial: datetime | None = None
        self.observaciones_del_gerente: str | None = None
        self.fecha_presentacion: datetime | None = None
        self.decision: DecisionDelCliente | None = None
        self._recontactos: list[Recontacto] = []

    @classmethod
    def generar(
        cls,
        id_cotizacion: str,
        numero_orden: NumeroOrden,
        tipo: TipoCotizacion,
        version: VersionCotizacion,
        lineas: Iterable[LineaDeCotizacion],
        fecha: datetime,
        politica: Especificacion[Cotizacion] | None = None,
    ) -> Cotizacion:
        cotizacion = cls(id_cotizacion, numero_orden, tipo, version, lineas, fecha)
        cotizacion._registrar(
            ev.CotizacionGenerada(fecha, *cotizacion._claves(), str(version), cotizacion._total())
        )
        if (politica or RequiereAprobacionGerencial()).es_satisfecha_por(cotizacion):
            cotizacion.estado = _E.PENDIENTE_DE_APROBACION_GERENCIAL
            cotizacion._registrar(
                ev.AprobacionGerencialRequerida(fecha, *cotizacion._claves(), cotizacion._total())
            )
        return cotizacion

    @property
    def lineas(self) -> tuple[LineaDeCotizacion, ...]:
        return tuple(self._lineas[numero] for numero in sorted(self._lineas))

    @property
    def total(self) -> Dinero:
        total = Dinero.cero()
        for linea in self._lineas.values():
            total = total + linea.subtotal
        return total

    @property
    def recontactos(self) -> tuple[Recontacto, ...]:
        return tuple(self._recontactos)

    @property
    def ultimo_contacto(self) -> datetime | None:
        """Fecha desde la que corren las 48 horas: el último recontacto o la presentación."""
        if self._recontactos:
            return max(recontacto.registrado_en for recontacto in self._recontactos)
        return self.fecha_presentacion

    def aprobar_por_gerente(self, fecha: datetime) -> None:
        self._exigir_estado(_E.PENDIENTE_DE_APROBACION_GERENCIAL, "aprobar")
        self._cambiar_estado(_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE)
        self.fecha_aprobacion_gerencial = fecha
        self._registrar(ev.CotizacionAprobadaPorGerente(fecha, *self._claves()))

    def rechazar_por_gerente(self, observaciones: str, fecha: datetime) -> None:
        self._exigir_estado(_E.PENDIENTE_DE_APROBACION_GERENCIAL, "rechazar")
        limpias = texto_requerido(
            observaciones, "El Gerente debe capturar sus observaciones al rechazar una cotización."
        )
        self._cambiar_estado(_E.REQUIERE_AJUSTE)
        self.observaciones_del_gerente = limpias
        self._registrar(ev.CotizacionRechazadaPorGerente(fecha, *self._claves(), limpias))

    def ajustar(self, lineas: Iterable[LineaDeCotizacion], fecha: datetime) -> None:
        """La versión ajustada sigue las indicaciones del Gerente y no regresa a revisión."""
        self._exigir_estado(_E.REQUIERE_AJUSTE, "ajustar")
        self._lineas = self._indexar_lineas(lineas)
        self._cambiar_estado(_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE)
        self._registrar(ev.CotizacionAjustada(fecha, *self._claves(), self._total()))

    def marcar_presentada(self, fecha: datetime) -> None:
        """Inicia el plazo de 48 horas; una segunda presentación no lo reinicia."""
        self._exigir_estado(_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, "presentar")
        if self.fecha_presentacion is not None:
            raise OperacionDeCotizacionNoPermitida(
                f"La cotización {self.version} ya fue presentada; "
                "para volver a contactar al cliente registre un recontacto."
            )
        self.fecha_presentacion = fecha
        self._registrar(ev.CotizacionPresentada(fecha, *self._claves()))

    def registrar_recontacto(self, asesor: str, fecha: datetime) -> None:
        self._exigir_estado(_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, "registrar un recontacto de")
        if self.fecha_presentacion is None:
            raise OperacionDeCotizacionNoPermitida(
                f"La cotización {self.version} todavía no se presenta al cliente."
            )
        recontacto = Recontacto(asesor, fecha)
        self._recontactos.append(recontacto)
        self._registrar(ev.RecontactoRegistrado(fecha, *self._claves(), recontacto.asesor))

    def registrar_decision(
        self, lineas_autorizadas: Iterable[int], autorizante: Autorizante, fecha: datetime
    ) -> DecisionDelCliente:
        """Total, parcial o rechazo. `VerificadorDeAutorizante` comprueba E2 antes de llamarlo."""
        self._exigir_estado(_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, "registrar la decisión de")
        autorizadas = set(lineas_autorizadas)
        desconocidas = autorizadas - set(self._lineas)
        if desconocidas:
            raise ValorInvalido(f"La cotización no tiene los trabajos: {sorted(desconocidas)}.")

        for linea in self.lineas:
            linea.decision = (
                DecisionDeLinea.AUTORIZADA
                if linea.numero in autorizadas
                else DecisionDeLinea.NO_AUTORIZADO
            )
        self._cambiar_estado(self._estado_de_la_decision(autorizadas))
        self.decision = self._armar_decision(autorizante, fecha)
        self._registrar(self._evento_de_decision(autorizante, fecha))
        return self.decision

    def _estado_de_la_decision(self, autorizadas: set[int]) -> EstadoCotizacion:
        if not autorizadas:
            return _E.RECHAZADA
        if autorizadas >= set(self._lineas):
            return _E.AUTORIZADA
        return _E.AUTORIZADA_PARCIALMENTE

    def _armar_decision(self, autorizante: Autorizante, fecha: datetime) -> DecisionDelCliente:
        return DecisionDelCliente(
            id_cotizacion=self.id,
            autorizados=self._trabajos_con(DecisionDeLinea.AUTORIZADA),
            no_autorizados=self._trabajos_con(DecisionDeLinea.NO_AUTORIZADO),
            autorizante=autorizante,
            registrada_en=fecha,
            tipo_cotizacion=self.tipo,
        )

    def _trabajos_con(self, decision: DecisionDeLinea) -> tuple[TrabajoDecidido, ...]:
        return tuple(
            TrabajoDecidido(linea.numero, linea.descripcion, linea.subtotal)
            for linea in self.lineas
            if linea.decision is decision
        )

    def _evento_de_decision(
        self, autorizante: Autorizante, fecha: datetime
    ) -> ev.CotizacionAutorizada | ev.CotizacionRechazadaPorCliente:
        es_adicional = self.tipo is TipoCotizacion.ADICIONAL
        if self.estado is _E.RECHAZADA:
            return ev.CotizacionRechazadaPorCliente(
                fecha, *self._claves(), es_adicional, autorizante.nombre
            )
        parcial = self.estado is _E.AUTORIZADA_PARCIALMENTE
        return ev.CotizacionAutorizada(
            fecha, *self._claves(), parcial, es_adicional, autorizante.nombre
        )

    def _exigir_estado(self, esperado: EstadoCotizacion, accion: str) -> None:
        if self.estado is not esperado:
            raise OperacionDeCotizacionNoPermitida(
                f"No se puede {accion} la cotización {self.version} porque está en "
                f"«{self.estado.value}»; debe estar en «{esperado.value}»."
            )

    def _cambiar_estado(self, nuevo: EstadoCotizacion) -> None:
        MAQUINA_DE_COTIZACION.validar(self.estado, nuevo)
        self.estado = nuevo

    def _claves(self) -> tuple[str, str]:
        return self.id, str(self.numero_orden)

    def _total(self) -> str:
        return str(self.total.monto)

    @staticmethod
    def _validar_version(tipo: TipoCotizacion, version: VersionCotizacion) -> None:
        if tipo is TipoCotizacion.INICIAL and version.numero != 1:
            raise ValorInvalido("La cotización inicial siempre es la versión 1.")
        if tipo is TipoCotizacion.ADICIONAL and version.numero < 2:
            raise ValorInvalido("Una cotización adicional es la versión 2 o posterior.")

    @staticmethod
    def _indexar_lineas(lineas: Iterable[LineaDeCotizacion]) -> dict[int, LineaDeCotizacion]:
        indice: dict[int, LineaDeCotizacion] = {}
        for linea in lineas:
            if linea.numero in indice:
                raise ValorInvalido(f"El trabajo {linea.numero} está repetido en la cotización.")
            indice[linea.numero] = linea
        if not indice:
            raise CotizacionSinTrabajos("Una cotización debe incluir al menos un trabajo.")
        return indice
