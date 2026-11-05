# ADR-014 — PDF generados al vuelo y fotos guardadas en la base de datos

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | N-01, N-02, N-11, N-12 · CA-002, CA-005, CA-024, CA-027 · BRD Restricciones técnicas |

## Contexto

El BRD pide almacenar digitalmente fotos y documentos (cotización, Nota de Responsabilidad, recibo interno; CA-002, CA-005, CA-024, CA-027). En Render el disco es efímero y un servicio de almacenamiento externo requiere credenciales.

## Alternativas consideradas

- **Guardar archivos en el disco del servidor:** se pierden en cada reinicio de Render.
- **Almacenamiento en la nube (S3 o similar):** correcto para producción real, pero agrega cuentas y secretos.
- **PDF generados al pedirlos y fotos en la base** (elegida).

## Decisión

Los PDF se generan al momento a partir de los datos guardados (fpdf2, detrás del puerto `GeneradorDeDocumentos`); como los datos ya no cambian después de la acción correspondiente (cotización guardada, nota firmada, pago registrado), el PDF siempre es el mismo. Las fotos se guardan en la tabla `fotos_de_danos` (`BYTEA`, JPEG o PNG, máximo 5 MB). Es alcance **P2**: si no se termina, las rutas responden 501 y la matriz lo indica.

## Consecuencias

- (+) Nada se pierde al reiniciar el servicio y no hay secretos extra.
- (−) La base crece con las fotos; aceptable para el volumen de una demostración.
