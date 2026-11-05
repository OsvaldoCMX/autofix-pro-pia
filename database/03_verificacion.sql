-- AutoFix Pro · Verificación de la carga (ejecutar después de 01 y 02). Cada fila muestra lo obtenido y lo esperado.
SELECT 'empleados' AS tabla, COUNT(*) AS obtenido, 6 AS esperado FROM empleados
UNION ALL SELECT 'clientes', COUNT(*), 40 FROM clientes
UNION ALL SELECT 'vehiculos', COUNT(*), 60 FROM vehiculos
UNION ALL SELECT 'ordenes «Recibida»', COUNT(*), 60 FROM ordenes WHERE estado = 'Recibida'
UNION ALL SELECT 'catalogo_servicios', COUNT(*), 20 FROM catalogo_servicios
UNION ALL SELECT 'servicios inhabilitados', COUNT(*), 1 FROM catalogo_servicios WHERE NOT habilitado
UNION ALL SELECT 'servicios_solicitados', COUNT(*), 117 FROM servicios_solicitados
UNION ALL SELECT 'órdenes sin detalle', COUNT(*), 2 FROM ordenes o WHERE NOT EXISTS (SELECT 1 FROM servicios_solicitados s WHERE s.numero_orden = o.numero)
UNION ALL SELECT 'no autorizadas', COUNT(*), 7 FROM referencia_operaciones_profesor WHERE NOT autorizado
UNION ALL SELECT 'secuencias', COUNT(*), 3 FROM secuencias;

-- Total de referencia de todas las operaciones (precio × cantidad): debe dar 305758.00
SELECT SUM(c.precio_mxn * s.cantidad) AS total_referencia FROM servicios_solicitados s JOIN catalogo_servicios c USING (recurso_id);

-- Operación con mayor total: debe ser AUT-O008 con 12887.00
SELECT s.numero_orden, SUM(c.precio_mxn * s.cantidad) AS total FROM servicios_solicitados s JOIN catalogo_servicios c USING (recurso_id)
GROUP BY s.numero_orden ORDER BY total DESC LIMIT 1;
