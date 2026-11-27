# Miura — sitio oficial

Sitio público estático de Miura y Miura Panel. Se publica en GitHub Pages desde el artefacto de GitHub Actions, con el dominio `miura.srtgateway.ovh`; ningún servidor VPS sirve sus páginas.

## Desarrollo local

Requiere Python 3 y Node.js/npm para las pruebas de navegador.

```sh
python3 scripts/build.py --output dist
python3 scripts/check.py dist
npm ci
npx playwright install chromium
npm run test:e2e
python3 -m http.server 8000 --directory dist
```

El build obtiene la versión, instalador y SHA-256 desde el manifiesto canónico `https://juanramonvf.github.io/miura-panel/updates/stable.json`. Rechaza versiones no estables, URLs fuera del release oficial o versión/hash inválidos. No se mantiene un número de versión manual en este repositorio.

## Contenido y rutas

- `/`: portada Miura; el catálogo `src/apps.json` incluye solo aplicaciones existentes.
- `/panel/`: funciones verificables, capturas del Panel real en modo demo, descarga estable y hash.
- `/help/`, `/news/`: ayuda pública y novedades/versiones.
- `help.html`, `ayuda.html`, `news.html`, `novedades.html` y `changelog.html`: aliases de compatibilidad que conservan el fragmento de URL.
- `README.txt`: resumen de terminal migrado, con instalador y SHA obtenidos del manifest en cada build.
- `CNAME`: dominio GitHub Pages. No sustituye la configuración de Pages ni modifica DNS.

Las capturas se toman del Panel real en modo de demostración, con datos ficticios y sin información de servidores. No deben sustituirse por mockups ni datos de producción.

## Pruebas y publicación

La workflow `.github/workflows/pages.yml` valida cada pull request y despliega únicamente `main` a GitHub Pages. También reconstruye y publica a diario para refrescar la versión estable desde el manifiesto aunque no haya cambios del sitio. Las Actions de terceros están fijadas a SHA completos; el workflow limita permisos por job y no usa secretos del repositorio.

Las pruebas Python verifican contenido, rutas locales, HTTPS/hosts permitidos, aliases, CNAME, producto único y pins de Actions. `npm audit` bloquea vulnerabilidades altas; Playwright Chromium comprueba navegación, descarga/hash y ausencia de desbordamiento horizontal en escritorio y móvil.

## Añadir una aplicación real

Añade una entrada en `src/apps.json` solo cuando exista el producto y su repositorio oficial. Incluye rutas y documentación verificables; no registres productos planificados o ficticios.
