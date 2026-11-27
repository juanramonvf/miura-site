#!/usr/bin/env python3
"""Build the static Miura website from the canonical Panel stable feed."""

import argparse
import html
import json
import re
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


FEED = "https://juanramonvf.github.io/miura-panel/updates/stable.json"
INSTALLER_RE = re.compile(
    r"https://github\.com/juanramonvf/miura-panel/releases/download/v"
    r"(?P<version>\d+\.\d+\.\d+)/"
    r"install-spanish-empire-panel-v(?P=version)\.sh"
)
SHA256_RE = re.compile(r"[a-fA-F0-9]{64}")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
ROOT = Path(__file__).resolve().parents[1]


def load_manifest():
    request = urllib.request.Request(FEED, headers={"User-Agent": "miura-site-build/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        manifest = json.load(response)
    if not isinstance(manifest, dict):
        raise SystemExit("stable manifest inválido: se esperaba un objeto JSON")
    version = manifest.get("version")
    installer = manifest.get("installer")
    sha256 = manifest.get("sha256")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise SystemExit("stable manifest inválido: versión estable incorrecta")
    match = INSTALLER_RE.fullmatch(installer) if isinstance(installer, str) else None
    if not match or match.group("version") != version:
        raise SystemExit("stable manifest inválido: instalador fuera del canal oficial o versión discordante")
    parsed = urlsplit(installer)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.query or parsed.fragment:
        raise SystemExit("stable manifest inválido: URL del instalador no permitida")
    if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
        raise SystemExit("stable manifest inválido: SHA-256 incorrecto")
    return {"version": version, "installer": installer, "sha256": sha256.lower()}


def read_apps():
    apps = json.loads((ROOT / "src/apps.json").read_text(encoding="utf-8"))
    if not isinstance(apps, list) or not apps:
        raise SystemExit("src/apps.json debe contener al menos una aplicación existente")
    for app in apps:
        if not isinstance(app, dict) or not all(isinstance(app.get(key), str) and app[key].strip()
                                                for key in ("name", "href", "github", "description")):
            raise SystemExit("registro de aplicación inválido")
        if not app["href"].startswith("/") or app["href"].startswith("//"):
            raise SystemExit("la ruta de una aplicación debe ser local")
        if not app["github"].startswith("https://github.com/juanramonvf/"):
            raise SystemExit("la URL de GitHub debe ser del espacio oficial de Miura")
    return apps


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body):
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#101114">
  <meta name="description" content="Miura: software autoalojado para administrar sistemas propios con control y transparencia.">
  <title>{esc(title)}</title>
  <style>
    :root{{color-scheme:dark;--bg:#101114;--card:#181a1f;--line:#303239;--text:#f2f1ed;--muted:#afb1b8;--gold:#d7b96f;--gold-light:#f0d995;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}}
    *{{box-sizing:border-box}}body{{margin:0;line-height:1.65;background:radial-gradient(ellipse at 70% 0%,#25221a 0,transparent 35rem),var(--bg)}}
    a{{color:var(--gold-light);text-underline-offset:3px}}a:hover{{color:#fff}}a:focus-visible{{outline:3px solid var(--gold);outline-offset:4px;border-radius:3px}}
    .skip{{position:absolute;left:-9999px}}.skip:focus{{left:1rem;top:1rem;z-index:10;background:var(--bg);padding:.7rem}}
    header,footer{{max-width:1120px;margin:auto;padding:24px;display:flex;align-items:center;justify-content:space-between;gap:1.5rem}}
    .brand{{font-weight:850;letter-spacing:.28em;color:var(--gold);text-decoration:none}}nav{{display:flex;flex-wrap:wrap;gap:1.2rem}}nav a{{color:#d5d2c9;text-decoration:none;font-size:.95rem}}
    main{{max-width:1120px;margin:auto;padding:48px 24px 96px}}.hero{{max-width:800px;padding:48px 0 72px}}.eyebrow{{font-size:.75rem;letter-spacing:.18em;color:var(--gold);text-transform:uppercase}}
    h1{{font-size:clamp(2.8rem,8vw,5.8rem);line-height:1.02;letter-spacing:-.045em;margin:.35em 0 .25em}}h2{{font-size:clamp(1.5rem,4vw,2.2rem);line-height:1.2}}h3{{font-size:1.15rem}}em{{font-style:normal;color:var(--gold-light)}}p{{max-width:760px;color:var(--muted)}}
    .button{{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:11px 18px;border:1px solid #8d7843;border-radius:7px;text-decoration:none;margin:12px 10px 0 0;font-weight:650}}.button.primary{{background:#b29450;color:#15130d;border-color:#b29450}}.button:hover{{background:#272319;color:#fff}}
    .section{{padding:24px 0 36px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:18px}}.card{{background:linear-gradient(145deg,#1b1d22,#15171b);border:1px solid var(--line);border-radius:12px;padding:24px;margin:16px 0}}.card p{{margin-bottom:.25rem}}
    .feature-list{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,225px),1fr));gap:10px;padding:0;list-style:none}}.feature-list li{{padding:13px 15px;background:#17191d;border-left:2px solid #75633b;color:#d8d6d0}}
    figure{{margin:20px 0;background:#15171b;border:1px solid var(--line);border-radius:10px;padding:10px}}figure img{{display:block;width:100%;height:auto;border-radius:6px}}figcaption{{padding:10px 6px 2px;color:var(--muted);font-size:.9rem}}
    .hash{{display:block;overflow-wrap:anywhere;border:1px solid #33343a;border-radius:7px;padding:12px;background:#101114;color:#e6d49c;font: .86rem/1.6 ui-monospace,SFMono-Regular,Consolas,monospace}}
    details{{margin:.8rem 0;padding:14px 17px;border:1px solid var(--line);border-radius:8px;background:#15171b}}summary{{cursor:pointer;color:#e4d6aa;font-weight:650}}code{{overflow-wrap:anywhere;color:var(--gold-light)}}footer{{border-top:1px solid #292b30;color:#92959d;font-size:.9rem}}
    @media(max-width:650px){{header{{align-items:flex-start;flex-direction:column;gap:.8rem}}nav{{gap:.6rem 1rem}}main{{padding:22px 18px 64px}}.hero{{padding:38px 0 52px}}.card{{padding:19px}}footer{{align-items:flex-start;flex-direction:column}}}}
    @media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important;animation:none!important;transition:none!important}}}}
  </style>
</head>
<body><a class="skip" href="#contenido">Saltar al contenido</a>{body}</body>
</html>
'''


def header(active=""):
    links = (("/panel/", "Miura Panel"), ("/help/", "Ayuda"), ("/news/", "Novedades"))
    nav = "".join(f'<a href="{href}"{(" aria-current=\"page\"" if active == href else "")}>{label}</a>' for href, label in links)
    return f'<header><a class="brand" href="/" aria-label="Miura, inicio">MIURA</a><nav aria-label="Navegación principal">{nav}<a href="https://github.com/juanramonvf">GitHub</a></nav></header>'


def home(apps):
    cards = "".join(
        f'<article class="card app-card"><span class="eyebrow">Aplicación</span><h3>{esc(app["name"])}</h3>'
        f'<p>{esc(app["description"])}</p><a class="button" href="{esc(app["href"])}">Descubrir Miura Panel</a></article>'
        for app in apps
    )
    return f'''{header()}<main id="contenido">
      <section class="hero"><span class="eyebrow">Software autoalojado</span><h1>Tu infraestructura.<br><em>A tu manera.</em></h1>
        <p>Miura desarrolla herramientas prácticas para administrar sistemas propios con control local, límites claros y transparencia.</p>
        <a class="button primary" href="/panel/">Conoce Miura Panel</a><a class="button" href="https://github.com/juanramonvf">Explorar en GitHub</a>
      </section><section class="section" aria-labelledby="apps-title"><span class="eyebrow">Aplicaciones</span><h2 id="apps-title">Herramientas Miura</h2><div class="grid">{cards}</div></section>
      </main><footer><span>© Miura</span><a href="https://github.com/juanramonvf">GitHub oficial</a></footer>'''


def panel(manifest):
    version, installer, digest = (esc(manifest[key]) for key in ("version", "installer", "sha256"))
    return f'''{header("/panel/")}<main id="contenido">
      <section class="hero"><span class="eyebrow">Miura / Aplicaciones</span><h1>Miura Panel</h1>
        <p>Un panel web autoalojado para consultar el estado de servidores Debian, Ubuntu y derivados compatibles. Reúne métricas del sistema, avisos, APT, Docker y funciones administrativas protegidas.</p>
        <a class="button primary" href="{installer}" rel="noopener">Descargar versión estable · v{version}</a>
        <a class="button" href="https://github.com/juanramonvf/miura-panel">Código y soporte en GitHub</a>
      </section>
      <section class="section"><span class="eyebrow">Qué incluye</span><h2>Visibilidad con límites explícitos</h2>
        <ul class="feature-list"><li>CPU, memoria, temperatura, red y discos</li><li>Avisos de APT, servicios y Docker</li><li>Vista HTTP de solo lectura</li><li>Administración por HTTPS autenticado</li><li>Gestión de varios paneles</li><li>Conexiones SSH con huellas verificadas</li><li>Acciones Docker compatibles y acotadas</li><li>Copias de seguridad y rollback del panel</li></ul>
      </section>
      <section class="section"><span class="eyebrow">Instalación</span><h2>Instala la versión estable</h2>
        <p>Descarga el instalador desde el release oficial y verifica el SHA-256 antes de ejecutarlo. Requiere un sistema compatible con Debian/Ubuntu, systemd y privilegios sudo; Docker y VPN son opcionales.</p>
        <a class="button" href="{installer}" rel="noopener">Descargar instalador v{version}</a>
        <p>SHA-256 del instalador:</p><code class="hash">{digest}</code>
        <p><a href="/help/">Guía completa de instalación y ayuda</a> · <a href="https://github.com/juanramonvf/miura-panel/releases">Historial de versiones</a></p>
      </section>
      <section class="section"><span class="eyebrow">Interfaz</span><h2>Una vista del panel</h2>
        <p>Capturas del programa real ejecutado en modo de demostración. Las métricas y nombres son datos sintéticos incluidos por Miura Panel; no representan un servidor real.</p>
        <figure><img src="/assets/screenshots/panel-desktop.png" alt="Miura Panel en navegador de escritorio, con datos de demostración" loading="lazy"><figcaption>Vista de escritorio · modo de demostración · datos sintéticos.</figcaption></figure>
        <figure><img src="/assets/screenshots/panel-tablet.png" alt="Miura Panel en una ventana de tableta, con datos de demostración" loading="lazy"><figcaption>Vista compacta · modo de demostración · datos sintéticos.</figcaption></figure>
      </section>
      </main><footer><span>Versión estable publicada: v{version}</span><a href="/news/">Novedades</a></footer>'''


def help_page():
    return f'''{header("/help/")}<main id="contenido"><span class="eyebrow">Documentación pública</span><h1>Ayuda y manual</h1>
      <p>Guía migrada de la documentación pública de Miura Panel. Las opciones pueden variar por distribución, permisos y versión; comprueba siempre el estado que muestra tu instalación.</p>
      <section class="card" id="instalacion"><h2>Instalación por primera vez</h2><p>Miura Panel funciona en Debian, Ubuntu y derivados compatibles con apt-get y systemd; está diseñado para AMD64 y ARM64. Conéctate por SSH al servidor con una cuenta sudo, descarga el instalador estable desde la <a href="/panel/">página de Miura Panel</a> y verifica el SHA-256 publicado antes de ejecutarlo. El asistente muestra un resumen; revisa las opciones de nombre, red y puerto antes de confirmar.</p><p>Docker y VPN son opcionales y no se instalan por su cuenta. En una VM o VPS pueden no estar disponibles las lecturas SMART o las temperaturas de algunos dispositivos. Si la instalación ya existe, comprueba las copias de seguridad antes de actualizar.</p></section>
      <section class="card" id="actualizaciones"><h2>Comprobar, actualizar y revertir</h2><p>Cuando exista una versión nueva, el panel HTTPS autenticado puede mostrar «Nueva versión · Actualizar». Confirma solo después de revisar la acción. La cabecera indica fases verificables (preparación, instalación, reinicio y finalización); el proceso continúa en el servidor aunque cierres la pestaña. La vista HTTP es de solo lectura.</p><p>Por SSH puedes consultar con <code>sudo miura-panel-update --check</code> y actualizar con <code>sudo miura-panel-update</code>. El actualizador consulta el manifiesto HTTPS, valida el SHA-256 del instalador y conserva una copia previa. Si una operación falla, consulta el resultado antes de repetirla y utiliza la ruta de rollback documentada por el instalador.</p></section>
      <section class="card" id="desinstalacion"><h2>Desinstalar</h2><p>En el servidor que quieres retirar, ejecuta <code>sudo miura-panel-uninstall</code>. El desinstalador detiene y elimina los componentes administrados del panel; no pretende borrar Docker, VPN ni otras aplicaciones. Revisa su resumen y las copias conservadas antes de tomar decisiones adicionales. Si se usaba gestión remota desde otro panel, revisa y revoca las autorizaciones SSH correspondientes.</p></section>
      <section class="card" id="servidores"><h2>Panel y varios servidores</h2><p>La vista general reúne contenedores, servicios, actualizaciones APT y avisos; CPU, memoria, temperatura, red, discos y SMART según disponibilidad. HTTP (puerto 8766 por defecto) permite consultar. Para modificar configuración o iniciar actualizaciones usa el acceso HTTPS autenticado (8767 por defecto), si se ha configurado. Los puertos pueden cambiar durante la instalación.</p><p>El rol de servidor principal es opcional: no crea una VPN ni concede permisos por sí solo. Si guardas varios paneles, el selector cambia de equipo; algunos favoritos se guardan en el servidor de origen.</p></section>
      <section class="card" id="ssh"><h2>Autorizar SSH de forma segura</h2><p>En el principal, genera o consulta la clave pública y utiliza la autorización preparada por el panel en el destino. Para cada servidor, consulta la huella y compárala con la huella obtenida localmente en ese equipo antes de autorizar. Mantén la clave privada en el principal, no habilites root por SSH y no desactives la comprobación de huellas.</p><p>Al quitar un destino de la lista no se revoca automáticamente una clave que ya se instaló allí. Revoca en el servidor las autorizaciones que ya no necesites.</p></section>
      <section class="card" id="docker"><h2>Docker local y remoto</h2><p>Miura Panel puede mostrar contenedores activos y detenidos. La actualización local se limita a proyectos Compose verificables cuando el actualizador está habilitado. La autorización Docker remota es independiente del acceso SSH y debe concederse en cada destino solo cuando corresponda. Las acciones se restringen a operaciones compatibles; stacks de Portainer que el panel no puede verificar permanecen protegidos.</p><p>En «Docker SSH», el panel diferencia destinos autorizados, no autorizados, sin Docker o no disponibles. El permiso puede revocarse en el destino con <code>sudo miura-panel-fleet docker-disable</code>. No concedas permisos Docker indiscriminados ni actualices contenedores solo porque aparezca una versión nueva.</p></section>
      <section class="card" id="https"><h2>Cuenta y acceso HTTPS</h2><p>Activa la cuenta y configura HTTPS desde la consola del servidor con <code>sudo miura-panel-admin-setup</code>. Puede utilizarse un certificado local, Let's Encrypt con un dominio compatible o uno propio. Cambiar un favorito para que use https:// no habilita el servicio. El acceso administrativo está pensado para redes privadas o de confianza; no expongas el panel directamente a Internet sin proteger la red.</p><p>La cuenta usa un correo como identificador. La caducidad de sesión controla cuánto dura la sesión; cerrar todas las sesiones también te desconectará.</p></section>
      <section class="card" id="recuperacion"><h2>Recuperación de cuenta y correo</h2><p>La recuperación SMTP es opcional y se configura en la interfaz administrativa. Si no está disponible, recupera el acceso localmente por SSH con <code>sudo miura-panel-admin-setup --recover</code>. Los enlaces de recuperación son temporales y de un solo uso.</p><p>Protege los archivos de configuración y copias de seguridad. No compartas credenciales, claves, tokens o datos privados del servidor al solicitar ayuda.</p></section>
      <section class="card" id="filtros"><h2>Filtros y avisos</h2><p>La vista de Docker permite buscar contenedores y filtrar todos, actualizables, protegidos o detenidos. El estado de versión puede consultarse desde la cabecera; desde Configuración se puede comprobar el panel actual o equipos autorizados sin instalar una actualización.</p></section>
      <section class="card" id="problemas"><h2>Si algo no funciona</h2><ul><li>HTTP funciona y HTTPS no: comprueba que la administración HTTPS se haya configurado y que el puerto sea accesible desde tu red.</li><li>Un servidor no aparece: revisa su URL, puerto y conexión. El puerto SSH es independiente del puerto web.</li><li>Docker SSH no está autorizado: verifica el permiso en ese destino; no es el mismo permiso que la vinculación SSH.</li><li>Un stack no puede actualizarse: puede tratarse de una protección deliberada para proyectos no verificables.</li><li>Una actualización falla: conserva el resultado, revisa la copia previa y no repitas la operación a ciegas.</li></ul></section>
      <section class="card" id="ayuda"><h2>Ayuda e incidencias</h2><p>Consulta el <a href="/README.txt">resumen de texto para terminal</a>, el <a href="https://github.com/juanramonvf/miura-panel#readme">README del proyecto</a>, los <a href="https://github.com/juanramonvf/miura-panel/releases">releases y sus notas</a> o abre un <a href="https://github.com/juanramonvf/miura-panel/issues">issue en GitHub</a>. Antes de compartir registros, elimina direcciones IP, nombres de host, correos y cualquier credencial.</p></section>
      </main><footer><a href="/panel/">Miura Panel</a><a href="/news/">Novedades</a></footer>'''


def news(manifest):
    version = esc(manifest["version"])
    return f'''{header("/news/")}<main id="contenido"><span class="eyebrow">Miura Panel</span><h1>Novedades</h1>
      <section class="card"><h2>Versión estable actual: v{version}</h2><p>Esta versión se obtiene automáticamente del manifiesto estable oficial de Miura Panel durante la compilación del sitio.</p><a class="button primary" href="{esc(manifest["installer"])}">Descargar instalador estable</a><a class="button" href="https://github.com/juanramonvf/miura-panel/releases">Ver notas y versiones</a></section>
      </main><footer><a href="/panel/">Miura Panel</a><a href="/help/">Ayuda</a></footer>'''


def readme_text(manifest):
    return f'''MIURA PANEL — AYUDA OFICIAL
============================

MANUAL VISUAL:
https://miura.srtgateway.ovh/help/

VERSIÓN ESTABLE: {manifest["version"]}
INSTALADOR: {manifest["installer"]}
SHA-256: {manifest["sha256"]}

INSTALAR (por SSH, con una cuenta sudo)
1. Descarga el instalador desde la página oficial anterior.
2. Comprueba que su SHA-256 coincide con el publicado.
3. Revisa el resumen del asistente antes de confirmar.

ACCESO WEB
- Invitado, solo lectura: HTTP, puerto 8766 por defecto.
- Administración: HTTPS, puerto 8767 por defecto, si se configuró.
- IP y puertos pueden variar según la instalación.

COMPROBAR Y ACTUALIZAR POR SSH
sudo miura-panel-update --check
sudo miura-panel-update

DESINSTALAR
sudo miura-panel-uninstall

CONFIGURAR ACCESO ADMINISTRATIVO HTTPS
sudo miura-panel-admin-setup

RECUPERAR LA CUENTA LOCALMENTE
sudo miura-panel-admin-setup --recover

AYUDA Y NOVEDADES
https://miura.srtgateway.ovh/help/
https://miura.srtgateway.ovh/news/
https://github.com/juanramonvf/miura-panel/releases

No expongas la administración a Internet sin proteger la red. No compartas
contraseñas, tokens, claves privadas, direcciones o registros con datos privados.
'''


def alias_page(target):
    return page("Contenido trasladado · Miura", f'''<main id="contenido"><h1>Contenido trasladado</h1>
      <p>Esta dirección antigua continúa disponible. Si no se abre automáticamente, usa el enlace.</p>
      <p><a href="{target}">Abrir {target}</a></p>
      <script>location.replace({json.dumps(target)} + location.search + location.hash)</script></main>''')


def write_page(output, route, title, body):
    folder = output if route == "/" else output / route.strip("/")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(page(title, body), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    manifest = load_manifest()
    apps = read_apps()
    write_page(output, "/", "Miura · Software autoalojado", home(apps))
    write_page(output, "/panel/", "Miura Panel · Supervisión de servidores", panel(manifest))
    write_page(output, "/help/", "Ayuda y manual · Miura Panel", help_page())
    write_page(output, "/news/", "Novedades · Miura Panel", news(manifest))
    for alias, target in (("help.html", "/help/"), ("ayuda.html", "/help/"),
                          ("news.html", "/news/"), ("novedades.html", "/news/"),
                          ("changelog.html", "/news/")):
        (output / alias).write_text(alias_page(target), encoding="utf-8")
    (output / "README.txt").write_text(readme_text(manifest), encoding="utf-8")
    (output / "CNAME").write_text("miura.srtgateway.ovh\n", encoding="ascii")
    assets = ROOT / "assets"
    if assets.is_dir():
        shutil.copytree(assets, output / "assets")


if __name__ == "__main__":
    main()
