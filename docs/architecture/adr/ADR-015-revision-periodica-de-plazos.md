# ADR-015 — Revisión periódica de plazos con un endpoint y un workflow programado

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | N-05, N-14 · US-012, US-023 · CA-023, CA-040 · RN-11, RN-12 · BPMN temporizadores no interruptores |

## Contexto

CA-023 pide una revisión diaria de las refacciones con más de 3 días hábiles y CA-040 una revisión de las cotizaciones con más de 48 horas sin respuesta. El servicio gratuito de Render se duerme sin tráfico, así que un temporizador dentro de la aplicación no correría.

## Alternativas consideradas

- **Planificador dentro de la app (APScheduler):** no corre mientras el servicio está dormido.
- **Cron Job de Render:** es de pago.
- **Endpoint idempotente + workflow programado de GitHub Actions** (elegida).

## Decisión

`POST /api/revisiones/plazos` (solo `TOKEN_SISTEMA`) ejecuta `ServicioDeRevisionDePlazos`, que evalúa E7 `RequiereAlertaDeRefaccion` y E8 `RequiereRecontacto` con el reloj actual y crea alertas solo si no existe ya una alerta abierta para la misma solicitud o el mismo periodo de la cotización (idempotente). `.github/workflows/revision-de-plazos.yml` lo llama cada 6 horas (`cron: '0 */6 * * *'`) y también se puede lanzar a mano (`workflow_dispatch`). En las pruebas se usa un reloj falso.

## Consecuencias

- (+) Cumple «revisión diaria» aunque el servicio duerma (la llamada lo despierta).
- (+) Se puede demostrar en vivo desde Swagger.
- (+) Como la revisión consulta la base, también evita que Supabase pause el proyecto por inactividad.
- (−) GitHub puede retrasar los workflows programados y los desactiva tras 60 días sin actividad en el repositorio.
