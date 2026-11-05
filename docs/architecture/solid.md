# Revisión SOLID — AutoFix Pro (U3 → PIA)

La revisión de la Unidad 3 encontró siete hallazgos y los corrigió en el diseño. En el PIA se revisaron de nuevo con el diseño ampliado (API, base de datos, Specifications, máquinas de estados y eventos) y se agregaron cinco hallazgos nuevos (S-08 a S-12).

## 1. Hallazgos de la Unidad 3 (vigentes)

| ID | Principio | Hallazgo / evidencia | Impacto | Cambio o confirmación | Estado en el PIA |
|---|---|---|---|---|---|
| S-01 | S | La regla de $15,000 podía quedar en `ServicioDeCotizacion`. | El servicio decidiría el negocio y tendría dos razones para cambiar. | Se movió al dominio; el servicio solo la pasa a `Cotizacion.generar`. | Se mantiene; ahora es la Specification `RequiereAprobacionGerencial` (ADR-005, ADR-006). |
| S-02 | S | `OrdenDeServicio` corría el riesgo de crecer con un condicional por cada estado. | Clase extensa y difícil de mantener. | Las transiciones viven en una tabla; la orden solo valida. | Se generaliza a `MaquinaDeEstados` para los 4 objetos con estado (ADR-007). |
| S-03 | S | Un único «ServicioDeOrdenes» para todos los casos de uso. | Mezclaría actores distintos. | Un servicio por caso de uso y actor. | De 5 a 12 servicios (ADR-003). |
| S-04 | O | Otra política no debe editar `Cotizacion`. | Cada política nueva sería otro `if`. | Política inyectada. | Se mantiene con Specifications. |
| S-05 | L | Repositorios en memoria y en base de datos deben comportarse igual. | Cambiar de implementación rompería los servicios. | Contrato en la interfaz (`obtener()` lanza el error del negocio). | Comprobado en la U5 con pruebas de contrato; se repiten contra PostgreSQL. |
| S-06 | I | Compras, el Gerente y el cliente solo leen. | Quedarían expuestos a `agregar()` y `guardar()`. | `LectorDeOrdenes` solo de lectura. | Se amplía con las vistas nuevas (panel del técnico, ingresos del día, alertas). |
| S-07 | D | La aplicación necesita fecha y hora, alertas y PDF. | Quedaría amarrada a detalles técnicos. | Puertos `Reloj`, `PublicadorDeEventos`, `GeneradorDeDocumentos`. | Se mantiene; FastAPI y SQLAlchemy solo aparecen en `api/` e `infrastructure/`. |

## 2. Hallazgos nuevos del PIA

| ID | Principio | Hallazgo / evidencia | Riesgo | Decisión |
|---|---|---|---|---|
| S-08 | S | Las rutas de FastAPI podrían validar reglas o abrir transacciones directamente. | La lógica quedaría repartida entre HTTP y dominio. | Las rutas solo traducen HTTP ↔ Command/Query y llaman a un servicio; las reglas siguen en el dominio (ADR-008). |
| S-09 | O | Las notificaciones de CA-007, CA-015, CA-022, CA-032… podrían programarse dentro de cada servicio. | Cada aviso nuevo editaría un caso de uso. | Domain Events + manejadores: un aviso nuevo es un manejador nuevo (ADR-016). |
| S-10 | O | Las reglas compuestas (entrega, cancelación, inicio de trabajo, alertas) escritas como `if` anidados. | Cambiar una condición obliga a editar el método del Aggregate. | Specifications combinables (ADR-006). |
| S-11 | I | Las rutas necesitan saber «quién es el empleado», no todo el módulo de seguridad. | Las rutas dependerían de cómo se guardan los tokens. | Dependencia `requiere_rol(*roles)` que solo entrega el `Empleado` (ADR-012). |
| S-12 | D | La API podría crear repositorios o el motor de base de datos dentro de cada ruta. | Imposible probar la API con otra base o en memoria. | Composition Root en `api/dependencias.py`; las pruebas sustituyen dependencias con `app.dependency_overrides` (ADR-008, ADR-010). |

## 3. Cómo se verifica

- Prueba de arquitectura (como en la U5): `domain` no importa `fastapi`, `sqlalchemy`, `pydantic` ni otras capas; `application` no importa `api` ni `infrastructure`.
- Pruebas de contrato memoria vs. base de datos (S-05).
- Cada Specification y cada manejador tiene pruebas propias (S-09, S-10).
