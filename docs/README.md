# Documentación — AutoFix Pro (PIA)

**Componentes de Lógica de Negocio · FIME UANL · Profesor: Miguel Ángel Gómez Marroquín**
**Equipo 6:** Jesus Eduardo Moreno Osoria (2136063) · Osvaldo Salvador Cárdenas Mejorado (2141553)
**Versión de la documentación:** 3.1 (09/11/2026, después de la revisión del profesor)

Esta carpeta es la fuente única del análisis y la arquitectura del PIA. Todo está en Markdown para que se lea en GitHub y se pueda comparar entre versiones.

| Carpeta / archivo | Contenido |
|---|---|
| [BRD.md](BRD.md) | Business Requirements Document v3.1 (16 necesidades, 12 restricciones de proceso, criterios de éxito). |
| [user-stories.md](user-stories.md) | 27 User Stories y 66 criterios de aceptación en Gherkin, con trazabilidad necesidad → US → CA → BPMN. |
| [gherkin/](gherkin/README.md) | Los mismos 66 criterios como escenarios Gherkin formales (`# language: es`) en 8 archivos `.feature`. |
| [glosario.md](glosario.md) | Lenguaje ubicuo, los 25 estados del sistema y su nombre en el código. |
| [bpmn/](bpmn/README.md) | BPMN v3 vigente (PDF) y la v2 como historial, con la lista de cambios. |
| [architecture/](architecture/README.md) | Modelo de dominio, modelo de datos, decisiones técnicas, patrones, SOLID, 18 ADR y diagramas UML. |
| [api/](api/README.md) | Contrato de la API REST (51 rutas, roles, códigos y ejemplos; solo `GET /api/sesion` sigue «Planeado» hasta la Fase 15). |
| [trazabilidad/](trazabilidad/matriz-trazabilidad.md) | Matriz BRD → regla → componente → prueba (Markdown y Excel). |
| [datos-profesor/](datos-profesor/README.md) | Cómo se cargan los datos del profesor, diferencias D-01 a D-07, anomalías y oráculos de los 120 casos y 20 transiciones. |
| [registro-de-cambios.md](registro-de-cambios.md) | Hallazgos H-PIA-01 a H-PIA-29 y conteos U3 → PIA → v3.1. |
| [interfaz-web.md](interfaz-web.md) | *(v3.1)* Pantallas de la página web por puesto: qué ve cada usuario, sus botones por estado, la ruta que llama y los criterios que cubre. |
| [auditoria-errores-de-usuario.md](auditoria-errores-de-usuario.md) | *(v3.1)* Auditoría «¿y si me equivoco?» (AU-01 a AU-39) con las decisiones del equipo. |
| [plan-de-implementacion.md](plan-de-implementacion.md) | Las 21 fases (0 a 20): de la preparación del repositorio a la entrega del 06/11/2026 y, después de la revisión, la interfaz web y las correcciones, con lo que construye cada una, sus pruebas y su estado de avance. |

## Conteos clave

Fuera de `docs/`: `database/` (esquema y datos iniciales para Supabase y Docker) y `scripts/` (generadores de la documentación y del SQL).

16 necesidades · 27 User Stories · 66 criterios · 35 reglas de negocio · 8 Specifications · 4 máquinas de estados (25 estados) · 31 Domain Events · 12 servicios de aplicación · 12 consultas · 51 rutas de API (1 planeada: `GET /api/sesion`, Fase 15) · 18 ADR · 19 tablas.

Lo aprobado en la Fase 13 (revisión del 09/11/2026) se construyó en la Fase 14 (10/11/2026); solo `GET /api/sesion` sigue marcada «Planeado» porque se construye en la Fase 15.
