# Escenarios Gherkin — AutoFix Pro

Cada archivo agrupa las User Stories de un área del proceso. Cada **Escenario** es un criterio de aceptación con el mismo texto que `../user-stories.md` y lleva las etiquetas `@US-xxx` y `@CA-xxx`.

Los archivos usan `# language: es`, por lo que las palabras clave están en español (`Característica`, `Escenario`, `Dado`, `Cuando`, `Entonces`, `Y`). Se pueden ejecutar con `pytest-bdd` o `behave`, o servir como especificación para las pruebas `test_ca_0XX_…` (ver `../architecture/decisiones-tecnicas.md`).

| Archivo | Característica | User Stories | Escenarios |
|---|---|---|---|
| `01_recepcion.feature` | Recepción y registro del vehículo | US-001, US-002, US-003, US-016 | 6 |
| `02_diagnostico.feature` | Asignación y diagnóstico | US-020, US-019, US-007 | 6 |
| `03_cotizacion.feature` | Cotización y aprobación gerencial | US-004, US-005, US-023 | 6 |
| `04_autorizacion.feature` | Autorización del cliente y cotizaciones adicionales | US-006, US-009 | 6 |
| `05_reparacion_y_refacciones.feature` | Reparación, refacciones y retiro anticipado | US-008, US-010, US-011, US-012, US-013 | 10 |
| `06_caja_y_entrega.feature` | Caja y entrega del vehículo | US-014, US-015, US-022, US-024 | 6 |
| `07_consultas.feature` | Consultas del gerente y del cliente | US-017, US-018, US-021 | 4 |
| `08_cancelacion.feature` | Cancelación de la orden | US-025 | 2 |
| **Total** | 8 características | 25 | **46** |

La etiqueta `@v3` marca los escenarios que se agregaron o precisaron en el PIA.
