# ADR-012 — Seguridad con token sencillo por empleado y rol

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | RN-01, RN-14 · BRD §2 Roles y permisos, §5 Fuera del alcance (sin cuentas de clientes) · CA-013, CA-021, CA-030, CA-037 |

## Contexto

Cada actor del taller tiene acciones distintas (Asesor, Técnico, Gerente, Compras, Caja) y el BRD excluye cuentas para clientes y responsables de flotilla. La consulta de estado del cliente es pública (US-021). Es un proyecto académico con datos ficticios.

## Alternativas consideradas

- **Sin seguridad:** no demuestra los roles y cualquiera cambiaría estados en producción.
- **OAuth2/JWT con usuarios y contraseñas:** más completo, pero agrega registro, hashes y expiración que el BRD no pide.
- **Token Bearer fijo por empleado de demostración** (elegida).

## Decisión

Los seis empleados de demostración (EMP-001 Asesor, EMP-002 y EMP-003 Técnicos, EMP-004 Gerente, EMP-005 Compras, EMP-006 Caja) vienen en `database/02_datos_iniciales.sql`; además existe un usuario técnico «Sistema» que no es empleado. Sus tokens vienen de variables de entorno (`TOKEN_ASESOR`, …, `TOKEN_SISTEMA`). La dependencia `requiere_rol(*roles)` lee `Authorization: Bearer <token>`, lo compara con `secrets.compare_digest` y entrega el `Empleado`: 401 si falta o es inválido, 403 si su rol no puede usar la ruta. Rutas públicas: `/health`, `/docs`, `/openapi.json` y `/api/consulta-de-estado`.

## Consecuencias

- (+) Se demuestra la regla «cada ruta exige un rol» (RN-01, RN-14) con pruebas de 401/403.
- (+) Swagger permite probar con el botón *Authorize*.
- (−) Los tokens no expiran; se cambian modificando la variable. Es una limitación documentada para un entorno de demostración.
- (−) Nunca se suben tokens reales: `.env.example` solo tiene marcadores.

**Actualización v3.1 (09/11/2026).** La página web (`/` y sus archivos, ADR-017) también es pública: pide la clave de acceso del empleado, que es este mismo token, y la manda a la API como `Authorization: Bearer`. La ruta `GET /api/sesion` devuelve el nombre y el puesto del empleado de la clave.
