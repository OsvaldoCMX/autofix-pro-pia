"""Pago de contado, recibo interno y cargo a crédito (US-014, US-015, US-022)."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, status

from api.dependencias import ContenedorDeLaApp
from api.errores import FuncionNoImplementada
from api.esquemas.caja import CargoRegistrado, DatosDeFormaDePago, DatosDePago, PagoRegistrado
from api.esquemas.comunes import errores
from api.seguridad import SOLO_CAJA
from application.comandos import CorregirFormaDePago, RegistrarCargoACredito, RegistrarPago
from application.resultados import ResultadoDeCargoACredito, ResultadoDePago

router = APIRouter(prefix="/api", tags=["Caja"], dependencies=[SOLO_CAJA])


@router.post(
    "/ordenes/{numero}/pago",
    response_model=PagoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el pago de contado de un cliente particular",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def registrar_pago(
    numero: str, datos: DatosDePago, contenedor: ContenedorDeLaApp
) -> ResultadoDePago:
    comando = RegistrarPago(numero, Decimal(datos.monto), datos.forma)
    return contenedor.caja().registrar_pago(comando)


@router.put(
    "/ordenes/{numero}/pago",
    response_model=PagoRegistrado,
    summary="Corregir la forma de pago mientras la orden está «Pagada»",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def corregir_forma_de_pago(
    numero: str, datos: DatosDeFormaDePago, contenedor: ContenedorDeLaApp
) -> ResultadoDePago:
    return contenedor.caja().corregir_forma_de_pago(CorregirFormaDePago(numero, datos.forma))


@router.get(
    "/ordenes/{numero}/recibo/pdf",
    summary="PDF del recibo interno (P2)",
    responses=errores(401, 403, 404, 409, 422, 501),
)
def pdf_de_recibo(numero: str) -> None:
    raise FuncionNoImplementada("El PDF del recibo interno todavía no está disponible.")


@router.post(
    "/ordenes/{numero}/cargo-a-credito",
    response_model=CargoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el cargo a crédito de una flotilla",
    responses=errores(401, 403, 404, 409, 422),
)
def registrar_cargo_a_credito(
    numero: str, contenedor: ContenedorDeLaApp
) -> ResultadoDeCargoACredito:
    return contenedor.caja().registrar_cargo_a_credito(RegistrarCargoACredito(numero))
