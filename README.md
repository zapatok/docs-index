# docs-index

Buscador de la biblioteca de prevención de riesgos laborales (normativa chilena).

168 documentos oficiales, 6.867 páginas, 13.300 fragmentos cortados por artículo y página.
Búsqueda léxica en español sobre Postgres (`tsvector`, parser `spanish`).

`config.js` lleva una cadena de conexión con rol **solo lectura** (`SELECT` + función `buscar()`);
no puede escribir ni borrar.
