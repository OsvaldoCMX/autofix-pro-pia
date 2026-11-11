# ADR-017 — Interfaz web para el personal del taller y el cliente, servida por la misma API

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 09/11/2026 (revisión del PIA, Fase 13) |
| Trazabilidad | Revisión del 09/11/2026 · todas las User Stories · CA-037, CA-038 (consulta pública) · ADR-008, ADR-011, ADR-012 · `interfaz-web.md` |

## Contexto

En la revisión del 09/11/2026 el profesor evaluó el sistema como un usuario del taller, no en Swagger: busca errores de captura y mensajes que entienda alguien que no sabe de computadoras. Hasta la v3.0 las «pantallas» de los criterios se representaban con sus endpoints y la demostración usaba Swagger UI (`decisiones-tecnicas.md` §4), que no es una herramienta para el personal del taller. El equipo son dos estudiantes sin experiencia en frameworks de JavaScript; la API se despliega como un solo Web Service gratuito de Render (ADR-011) y se protege con un token por empleado (ADR-012).

## Alternativas consideradas

- **SPA con React o Vue:** componentes y ecosistema, pero agrega Node, npm y un paso de compilación (en el Dockerfile o en otro despliegue) que el equipo no domina.
- **Páginas generadas en el servidor (plantillas Jinja2):** poco JavaScript, pero mezcla la presentación con las rutas de la API y cada formulario necesitaría su propia ruta HTML además de la JSON.
- **Sitio estático en otro servicio:** separa la página, pero agrega otra URL, otro despliegue y la configuración de CORS.
- **HTML, CSS y JavaScript sin framework (módulos ES) servidos por el mismo FastAPI** (elegida).

## Decisión

La página vive en `src/api/web/` (capa de presentación; `src/` conserva sus cuatro paquetes y el Dockerfile no cambia) y FastAPI la sirve en `/` sin cambiar `/docs`, `/openapi.json`, `/health` ni `/api/*`. Navegación con `#` en la dirección para que recargar no dé 404. La página **solo habla con la API** (nunca con Supabase). El inicio de sesión pide la **clave de acceso** del empleado, que es el mismo token Bearer de ADR-012; se guarda en `sessionStorage` (se borra al cerrar la pestaña) y la nueva ruta `GET /api/sesion` devuelve el nombre y el puesto (401 sin clave o con una clave inválida; 403 con la de Sistema, que no es un empleado). Los errores se muestran con el `detalle` de la API tal cual: si un mensaje no se entiende, se corrige en el dominio o en `api/errores.py`. Las validaciones de la página solo ayudan; las reglas siguen en el dominio y la página no decide reglas del negocio (por ejemplo, no decide si una cotización va al Gerente). El dinero se maneja como texto o centavos, nunca con sumas de números decimales de JavaScript. Las rutas P2 que responden 501 no aparecen. Las pantallas, los botones por estado y los mensajes están en `docs/interfaz-web.md`; la revisión es manual (Fase 18), porque pytest prueba la API.

## Consecuencias

- (+) Una sola URL y un solo despliegue; sin CORS.
- (+) Sin Node, sin npm ni compilación: el Dockerfile y el CI no cambian.
- (+) La API sigue siendo la autoridad de las reglas; Swagger sigue disponible para la parte técnica.
- (−) Más JavaScript escrito a mano; se mitiga con un módulo por puesto y un solo `api.js` para todas las llamadas y los errores.
- (−) La clave queda en el navegador del empleado mientras la pestaña está abierta; aceptable con datos ficticios y ya documentado como limitación en ADR-012.
- (−) La página no tiene pruebas automatizadas; se revisa con la lista de la Fase 18 (`docs/evidencias/revision-interfaz.md`).
