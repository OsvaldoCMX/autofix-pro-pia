# Patrones aplicados — AutoFix Pro (PIA)

Cada patrón se eligió por un problema concreto del caso, no por usarlo. La columna «Evidencia» indica dónde se ve en el código planeado (estructura de `decisiones-tecnicas.md` §2) y qué criterio lo justifica.

| Patrón | Capa | Problema del caso que resuelve | Evidencia (clase / archivo) | CA / RN | ADR |
|---|---|---|---|---|---|
| **Domain Model** | domain | Reglas que dependen del estado y cruzan orden, cotización y cliente. | `OrdenDeServicio`, `Cotizacion`, `Cliente`, `Vehiculo`, `Empleado` | CA-005, CA-010, CA-042 | ADR-001 |
| **Aggregate / Aggregate Root** | domain | Mantener invariantes en una sola transacción (p. ej. «En Espera de Refacción» mientras haya solicitudes). | Raíces con entidades internas (`Trabajo`, `SolicitudDeCompra`, `LineaDeCotizacion`) | CA-019, CA-022 | ADR-002 |
| **Entity** | domain | Objetos con identidad que cambian de estado. | `Trabajo`, `SolicitudDeCompra`, `FallaAdicional`, `LineaDeCotizacion` | CA-014, CA-019 | ADR-002 |
| **Value Object** | domain | Datos que se definen por su valor y validan su propia regla. | `Dinero` (Decimal, nunca negativo), `Placas`, `VIN`, `NumeroOrden`, `Diagnostico`, `Pago`, `CargoACredito`, `Cancelacion` | CA-026, CA-037, RN-23 | ADR-001 |
| **Specification** | domain | Reglas compuestas legibles y reutilizables (AND/OR/NOT). | `Especificacion` y E1–E8 en `*/especificaciones.py` | CA-007, CA-029, CA-041 a CA-046 | ADR-006 |
| **State Machine (tabla)** | domain | 25 estados en 4 objetos con transiciones permitidas explícitas. | `MaquinaDeEstados` y `estados.py` de cada módulo | RN-22, todas las transiciones | ADR-007 |
| **Policy / Strategy** | domain | La regla de $15,000 puede cambiar de monto o de alcance. | `RequiereAprobacionGerencial` inyectada en `Cotizacion.generar` | CA-007, CA-016 | ADR-005 |
| **Domain Service** | domain | Reglas que no pertenecen a un solo Aggregate. | `VerificadorDeAutorizante` (Cliente + Autorizante), `CalendarioHabil` | CA-029, CA-021 | ADR-001 |
| **Domain Events / Observer** | domain → application | Avisar a otros empleados sin acoplar los casos de uso. | Eventos en `*/eventos.py`; `PublicadorEnProceso` + `manejadores/alertas.py` | CA-007, CA-015, CA-022, CA-032 | ADR-016 |
| **Repository** | domain (interfaz) / infrastructure | Guardar y recuperar Aggregates sin conocer el gestor. | `RepositorioDeOrdenes` … ; `infrastructure/base_de_datos/repositorios.py`, `memoria/` | CE-01, CE-06 | ADR-004 |
| **Unit of Work** | application / infrastructure | Confirmar juntos los cambios de dos Aggregates y publicar eventos solo después. | `UnidadDeTrabajo` (abstracta), `UnidadDeTrabajoSqlAlchemy` | CA-005, CA-010 | ADR-002, ADR-016 |
| **Service Layer (Application Service)** | application | Coordinar cada caso de uso sin absorber reglas. | 12 `ServicioDe…` | todos | ADR-003 |
| **Command / Query (CQRS básico)** | application | Separar escrituras de consultas que cruzan órdenes. | `comandos.py`, `consultas/`, `LectorDeOrdenes`, vistas | CA-013, CA-021, CA-030, CA-031, CA-037 | ADR-003 |
| **DTO** | application / api | No exponer los Aggregates hacia afuera. | `resultados.py`, vistas de consultas, esquemas Pydantic | CA-038 | ADR-003, ADR-008 |
| **Ports and Adapters (Hexagonal)** | application ↔ infrastructure | Reloj, publicador, PDF y almacenamiento intercambiables (y simulables en pruebas). | `puertos.py`: `Reloj`, `PublicadorDeEventos`, `GeneradorDeDocumentos`; adaptadores en `infrastructure/` | CA-005, CA-023 | ADR-004, ADR-014 |
| **Data Mapper** | infrastructure | El dominio no hereda del ORM. | Tablas de SQLAlchemy Core (`tablas.py`) y traducción explícita fila ↔ objeto del dominio (`mapeo.py`, como en la U5) | — | ADR-009 |
| **Composition Root / Dependency Injection** | api | Un solo lugar decide qué implementación se usa (memoria, base de datos, PDF falso…). | `api/dependencias.py` con `Depends` de FastAPI | — | ADR-008 |
| **Adapter (carga de datos)** | scripts / tests | Convertir los CSV del profesor al modelo propio sin cambiar requisitos. | `scripts/db/generar_datos_iniciales.py` → `database/02_datos_iniciales.sql`; arnés `tests/datos_profesor/` | H-PIA-03 | ADR-013 |

## Patrones considerados y descartados

| Patrón | Por qué no |
|---|---|
| Transaction Script para la escritura | Repetiría las validaciones de estado en cada caso de uso (ADR-001). |
| Patrón State con una clase por estado | 25 clases para reglas de tipo «desde X solo a Y»; la tabla es más clara (ADR-007). |
| CQRS con base de lectura separada / Event Sourcing | Excesivo para el volumen de un taller (ADR-003). |
| Active Record | Mezclaría el dominio con el ORM (ADR-004). |
| Broker de mensajes | Las alertas son internas y en el mismo proceso (ADR-016). |
