# ADR-003 — Service Layer por caso de uso y CQRS básico

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 10/2026 (Unidad 3); actualizada en el PIA |
| Trazabilidad | N-02 a N-05, N-08 a N-11, N-13 a N-15 · US-005, US-007, US-011, US-017, US-018, US-021 · CA-007, CA-013, CA-021, CA-030, CA-031, CA-037, CA-038 |

## Contexto

Los casos de uso tienen actores distintos (Asesor, Técnico, Gerente, Compras, Caja). Los paneles de Compras, del técnico, del Gerente y la consulta del cliente (US-007, US-011, US-017, US-018, US-021) solo leen y cruzan varias órdenes. La Service Layer debe coordinar sin absorber reglas.

## Alternativas consideradas

- **Un único ServicioDeOrdenes:** menos archivos, pero mezcla actores y crece sin control.
- **Reglas en los servicios** (Transaction Script disfrazado): contradice ADR-001.
- **CQRS completo con base de lectura separada:** excesivo para el volumen de un taller.

## Decisión

Un Application Service por grupo de casos de uso de un mismo actor: `ServicioDeRecepcion`, `ServicioDeCancelacion`, `ServicioDeDiagnostico`, `ServicioDeCotizacion`, `ServicioDeAprobacionGerencial`, `ServicioDeAutorizacion`, `ServicioDeReparacion`, `ServicioDeRefacciones`, `ServicioDeRetiro`, `ServicioDeCaja`, `ServicioDeEntrega` y `ServicioDeRevisionDePlazos` (12). Cada método recibe un Command y devuelve un resultado (DTO). Las consultas usan Queries con su manejador y la interfaz `LectorDeOrdenes`, y devuelven vistas propias: `ConsultarEstadoDeOrden`, `BuscarVehiculoPorPlacas`, `BuscarClientes`, `ConsultarPanelDelTecnico`, `ListarSolicitudesPendientes`, `ListarCotizacionesPendientesDeAprobacion`, `ConsultarCotizacion`, `ConsultarExpedienteDeOrden`, `ListarOrdenes`, `ConsultarIngresosDelDia` y `ListarAlertas`. Mismo almacenamiento para lectura y escritura.

## Consecuencias

- (+) Cada servicio tiene una sola razón para cambiar (SOLID-S).
- (+) Las vistas no exponen los Aggregates; la consulta del cliente no revela datos si el folio y las placas no coinciden (CA-038).
- (+) Las rutas de la API solo traducen HTTP ↔ Command/Query (ADR-008).
- (−) Más clases pequeñas.

**Actualización PIA.** Se agregaron los servicios y consultas que la U3 dejó como trabajo posterior (recepción, diagnóstico, reparación, retiro, caja, cancelación, consultas del Gerente y revisión de plazos).
