# Documentación — AutoFix Pro (PIA)

**Componentes de Lógica de Negocio · FIME UANL · Profesor: Miguel Ángel Gómez Marroquín**
**Equipo 6:** Jesus Eduardo Moreno Osoria (2136063) · Osvaldo Salvador Cárdenas Mejorado (2141553)
**Versión de la documentación:** 3.0 (04/11/2026)

Esta carpeta es la fuente única del análisis y la arquitectura del PIA. Todo está en Markdown para que se lea en GitHub y se pueda comparar entre versiones.

| Carpeta / archivo | Contenido |
|---|---|
| [BRD.md](BRD.md) | Business Requirements Document v3.0 (15 necesidades, 10 restricciones de proceso, criterios de éxito). |
| [user-stories.md](user-stories.md) | 25 User Stories y 46 criterios de aceptación en Gherkin, con trazabilidad necesidad → US → CA → BPMN. |
| [gherkin/](gherkin/README.md) | Los mismos 46 criterios como escenarios Gherkin formales (`# language: es`) en 8 archivos `.feature`. |
| [glosario.md](glosario.md) | Lenguaje ubicuo, los 25 estados del sistema y su nombre en el código. |
| [bpmn/](bpmn/README.md) | BPMN v3 vigente (PDF) y la v2 como historial, con la lista de cambios. |
| [architecture/](architecture/README.md) | Modelo de dominio, modelo de datos, decisiones técnicas, patrones, SOLID, 16 ADR y diagramas UML. |
| [api/](api/README.md) | Contrato planeado de la API REST (43 rutas, roles, códigos y ejemplos). |
| [trazabilidad/](trazabilidad/matriz-trazabilidad.md) | Matriz BRD → regla → componente → prueba (Markdown y Excel). |
| [datos-profesor/](datos-profesor/README.md) | Cómo se cargan los datos del profesor, diferencias D-01 a D-07, anomalías y oráculos de los 120 casos y 20 transiciones. |
| [registro-de-cambios.md](registro-de-cambios.md) | Hallazgos H-PIA-01 a H-PIA-15 y conteos U3 → PIA. |
| [plan-de-implementacion.md](plan-de-implementacion.md) | Las 12 fases de la implementación (de la preparación del repositorio al README técnico), con lo que construye cada una, sus pruebas y su estado de avance. |

## Conteos clave

Fuera de `docs/`: `database/` (esquema y datos iniciales para Supabase y Docker) y `scripts/` (generadores de la documentación y del SQL).

15 necesidades · 25 User Stories · 46 criterios · 24 reglas de negocio · 8 Specifications · 4 máquinas de estados (25 estados) · 26 Domain Events · 12 servicios de aplicación · 11 consultas · 43 rutas de API · 16 ADR · 18 tablas.
