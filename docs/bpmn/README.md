# BPMN — AutoFix Pro

| Archivo | Qué es |
|---|---|
| `BPMN_AutoFix_Pro_v3.pdf` | **BPMN vigente (PIA)**. Es el PDF exportado de Lucidchart en la v2 con los cambios de la v3 aplicados directamente sobre el archivo, con los mismos estilos, tipografías y colores. |
| `BPMN_AutoFix_Pro_v2.pdf` | Versión de la Unidad 2/3 (historial). |

> El archivo de Lucidchart no se actualizó (el plan de pago terminó). Si en el futuro se vuelve a editar en Lucidchart, hay que repetir ahí los cambios de la tabla de abajo.

## 1. Qué modela el BPMN

**Diagrama 1 (proceso principal).** Pool *AutoFix Pro* con los carriles Asesor de Servicio, Gerente de Taller, Técnico, Compras y Caja; los pools externos *Cliente / Conductor* y *Responsable de Flotilla* se comunican solo por flujos de mensaje. Fases:

1. Recepción y registro
2. Diagnóstico y cotización (aprobación gerencial si la cotización inicial supera $15,000 MXN)
3. Autorización (temporizador no interruptor de 48 h para recontactar; rechazo total → entrega sin reparación)
4. Gestión de refacciones (temporizador no interruptor de 3 días hábiles)
5. Reparación y ampliación (cotización adicional v.n)
6. Cierre, pago y entrega (pago de contado o cargo a crédito según el tipo de cliente)

**Diagrama 2 (casos especiales).**
- **Caso especial 1: retiro anticipado del vehículo** con Nota de Responsabilidad (CA-024, CA-025).
- **Caso especial 2: el cliente desiste antes de la cotización** *(nuevo en v3)*: evento de inicio de mensaje «Cliente desiste del servicio» → compuerta «¿La orden ya tiene cotización?» → **No:** «Registrar cancelación con motivo» (objeto de datos «Orden de Servicio [Cancelada]» y anotación con la regla) → «Devolver vehículo al cliente» (mensaje «Vehículo») → fin «Orden cancelada sin cobro». **Sí:** fin «Continúa con el rechazo total (Fase 3)» (CA-044, CA-045).

Cada fase está ligada a sus criterios de aceptación en `../user-stories.md` (sección 4) y en la matriz `../trazabilidad/matriz-trazabilidad.md` (columna «BPMN»).

## 2. Cambios aplicados en la v3

| # | Dónde | Cambio | Motivo |
|---|---|---|---|
| 1 | Título del Diagrama 2 | «AutoFix Pro - BPMN (Casos especiales: retiro anticipado y cancelación antes de la cotización)». Los encabezados de fase dicen ahora «Caso especial 1…» y «Caso especial 2…». | H-PIA-01 |
| 2 | Diagrama 2 | Nuevo **caso especial 2** debajo del caso 1, con el mismo pool, carril y estilos. | H-PIA-01 (US-025, CA-044, CA-045) |
| 3 | Diagrama 2, caso 2 | Anotación: «Regla: solo se cancela si la orden está «Recibida» o «En Diagnóstico». Se guardan fecha, hora y motivo; sin cobro.» | BRD restricción 10 |
| 4 | Diagrama 1, Fase 6, carril Caja | «Registrar cargo a crédito (15 días)» → **«Registrar cargo a crédito»**; mensaje «Cargo a crédito (15 días)» → **«Aviso de cargo a crédito»**. | H-PIA-02 |
| 5 | Diagrama 1, Fase 6 | Nueva anotación asociada al fin «Vehículo entregado, orden cerrada»: «Si es flotilla, al entregar se registra la fecha de vencimiento del crédito: entrega + 15 días naturales.» | H-PIA-02 (CA-041) |
| 6 | Diagrama 2, caso 1 | Objeto de datos «Orden de Servicio [Pausada por Retiro de Vehículo]» (nombre completo del Glosario). | Lenguaje ubicuo |
| 7 | Diagrama 2, caso 1 | La anotación de «Reactivar orden y formarla al final» agrega: «Al reactivarse vuelve a «En Espera de Refacción» si falta alguna pieza; si ya están todas, a «Autorizada» (ningún trabajo iniciado) o a «En Reparación».» | H-PIA-07 (CA-025) |
| 8 | Recuadro «Notas del modelo» | Nueva viñeta: «La cancelación solo procede antes de la cotización; si ya existe, se registra el rechazo total y el vehículo se entrega sin reparación (Diagrama 2, caso 2).» | H-PIA-01 |

El flujo principal (6 fases) no cambió.

## 3. Correspondencia de los objetos de datos con los estados

Los objetos de datos usan exactamente los estados del Glosario: «Orden de Servicio [Recibida]» (Fase 1), «[Lista para Entrega]» (Fase 5), «[Cerrada]» (Fase 6), «[Pausada por Retiro de Vehículo]» (caso 1) y «[Cancelada]» (caso 2). El rechazo total termina en el evento «Orden cerrada sin reparación» (Fase 3), que corresponde al estado «Cerrada sin Reparación». La máquina de estados completa está en `../architecture/diagramas/estados-orden.png`.
