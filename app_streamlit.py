"""Paso 7 (vitrina): interfaz visual del recomendador para la demo del portfolio.

Esta capa existe para que el proyecto se pueda ENSENAR sin abrir una terminal.
No decide nada: habla con api.py por HTTP, igual que hacen los flujos de n8n.
Es decir, es un tercer consumidor del mismo pipeline (terminal, n8n, y esto),
lo cual es justamente la demostracion de que la logica esta bien separada.

Sobre el diseno: el tema base vive en .streamlit/config.toml y aqui solo se
anade lo que el tema no alcanza. Los selectores CSS se limitan a atributos
[data-testid] y [data-baseweb], que Streamlit mantiene estables entre versiones;
las clases con hash (.st-emotion-cache-xxxx) cambian en cada release y usarlas
seria firmar que la interfaz se rompa en la proxima actualizacion.

Arranque (con api.py ya corriendo en el puerto 8000):
    .venv\\Scripts\\python.exe -m streamlit run app_streamlit.py
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")

API = os.getenv("API_URL", "http://127.0.0.1:8000")
OFERTAS_DIR = RAIZ / os.getenv("OFERTAS_DIR", "ofertas")
MODELO = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

st.set_page_config(
    page_title="Ranking de candidatos",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --ink-900:#10141B; --ink-800:#171C26; --ink-700:#1E2532;
  --line:#242C3A; --line-soft:#1B2230;
  --paper:#E8E6E1; --muted:#8A93A3; --faint:#5D6675;
  --brass:#C9A227; --brass-dim:#8A7220;
}

/* Columna de documento: un informe se lee mejor medido que a todo lo ancho.
   El padding superior NO se puede apretar mas: la barra de herramientas de
   Streamlit es fija y flota sobre el contenido, asi que un valor por debajo de
   su altura mete la primera linea debajo de ella y la recorta. */
.stMainBlockContainer { max-width: 1120px; padding-top: 5rem; }

/* --- Cabecera ------------------------------------------------------- */
.encabezado { border-bottom: 1px solid var(--line); padding-bottom: 1.4rem; margin-bottom: .4rem; }
.cintillo {
  font-family: 'IBM Plex Mono', monospace; font-size: .68rem; letter-spacing: .18em;
  text-transform: uppercase; color: var(--brass); margin-bottom: .7rem;
}
.cintillo span { color: var(--faint); }
.encabezado h1 {
  font-family: 'Source Serif 4', Georgia, serif; font-weight: 400;
  font-size: clamp(2rem, 4.2vw, 3.1rem); line-height: 1.04;
  letter-spacing: -.015em; color: var(--paper); margin: 0 0 .55rem;
}
.encabezado h1 em { font-style: italic; color: var(--brass); }
.entradilla { color: var(--muted); font-size: .95rem; max-width: 54ch; margin: 0; }

/* --- Candidato principal: el unico momento con volumen ---------------- */
.principal {
  display: grid; grid-template-columns: 168px 1fr; gap: 2rem; align-items: center;
  background: var(--ink-800); border: 1px solid var(--line);
  border-left: 2px solid var(--brass); padding: 1.7rem 1.9rem; margin: 1.6rem 0 2.4rem;
}
.principal .rotulo {
  font-family:'IBM Plex Mono',monospace; font-size:.66rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--brass); margin-bottom:.5rem;
}
.principal .nombre {
  font-family:'Source Serif 4',Georgia,serif; font-size:1.85rem; font-weight:400;
  color:var(--paper); line-height:1.1; margin-bottom:1.1rem;
}
.cifras { display:flex; gap:2.6rem; flex-wrap:wrap; }
.cifra .clave {
  font-family:'IBM Plex Mono',monospace; font-size:.63rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--faint); display:block; margin-bottom:.28rem;
}
.cifra .valor {
  font-family:'IBM Plex Mono',monospace; font-size:1.5rem; font-weight:500;
  color:var(--paper); font-variant-numeric: tabular-nums;
}
.cifra .valor.acento { color: var(--brass); }
.archivo { font-family:'IBM Plex Mono',monospace; font-size:.72rem; color:var(--faint); margin-top:1rem; }

/* Cita del trozo de CV que motiva la puntuacion. Es lo que permite comprobar
   el ranking en vez de creerselo, asi que va junto al primer puesto. */
.porque { margin-top:1.1rem; padding-left:.9rem; border-left:1px solid var(--brass-dim); }
.porque .clave {
  font-family:'IBM Plex Mono',monospace; font-size:.63rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--faint); display:block; margin-bottom:.35rem;
}
.porque p {
  margin:0; color:var(--muted); font-size:.84rem; line-height:1.55;
  font-style:italic;
}

/* --- Libro mayor: el resto de la clasificacion ------------------------ */
.rotulo-seccion {
  font-family:'IBM Plex Mono',monospace; font-size:.66rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--faint);
  padding-bottom:.6rem; border-bottom:1px solid var(--line); margin-bottom:.2rem;
}
.fila {
  display:grid; grid-template-columns:2.6rem minmax(0,1fr) 42% 4.7rem;
  gap:1rem; align-items:center; padding:.72rem 0;
  border-bottom:1px solid var(--line-soft);
}
.fila:hover { background: rgba(201,162,39,.035); }
.fila .orden {
  font-family:'IBM Plex Mono',monospace; font-size:.78rem; color:var(--faint);
  font-variant-numeric: tabular-nums;
}
.fila .quien { color:var(--paper); font-size:.94rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
/* La regla capilar mide el score en escala absoluta 0-1, sin normalizar al
   maximo de la lista: normalizar exageraria diferencias pequenas y haria
   parecer decisivo lo que no lo es. */
.regla { position:relative; height:1px; background:#1F2634; }
.regla i {
  position:absolute; left:0; top:0; height:1px; display:block;
  background:var(--brass); opacity:.75;
}
.regla i::after {
  content:''; position:absolute; right:0; top:-3px; width:1px; height:7px;
  background:var(--brass); opacity:1;
}
.fila .marca {
  font-family:'IBM Plex Mono',monospace; font-size:.86rem; color:var(--muted);
  text-align:right; font-variant-numeric: tabular-nums;
}

.nota {
  color:var(--faint); font-size:.79rem; line-height:1.6; max-width:70ch;
  border-top:1px solid var(--line); padding-top:1rem; margin-top:1.8rem;
}
.nota b { color:var(--muted); font-weight:500; }

/* --- Barra lateral: ficha de procedencia, no panel de metricas -------- */
[data-testid="stSidebar"] { border-right:1px solid var(--line); }
.ficha { border-top:1px solid var(--line); padding-top:.7rem; margin-top:.3rem; }
.ficha .par { display:flex; justify-content:space-between; gap:1rem; padding:.42rem 0; font-size:.8rem; }
.ficha .par dt { color:var(--faint); }
.ficha .par dd {
  margin:0; color:var(--paper); font-family:'IBM Plex Mono',monospace;
  font-variant-numeric:tabular-nums;
}
.estado { display:flex; align-items:center; gap:.5rem; font-size:.78rem; color:var(--muted); margin-bottom:.9rem; }
.punto { width:6px; height:6px; border-radius:50%; background:var(--brass); box-shadow:0 0 0 3px rgba(201,162,39,.14); }
.punto.frio { background:#B4472F; box-shadow:0 0 0 3px rgba(180,71,47,.14); }

/* --- Pestanas -------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] { gap:2rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
  font-size:.82rem; letter-spacing:.03em; color:var(--faint);
  padding:.55rem 0; background:transparent;
}
.stTabs [aria-selected="true"] { color:var(--paper); }

/* La accion principal va perfilada, no maciza: un bloque de laton a todo lo
   ancho le robaba el protagonismo al diagrama del angulo, que es el unico
   elemento que debe pesar en esta pagina. */
[data-testid="stBaseButton-primary"], button[kind="primary"] {
  background: transparent; border: 1px solid var(--brass);
  color: var(--brass); font-weight: 500; letter-spacing: .02em;
  transition: background .15s ease, color .15s ease;
}
[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover {
  background: var(--brass); color: var(--ink-900); border-color: var(--brass);
}
[data-testid="stBaseButton-primary"]:focus-visible, button[kind="primary"]:focus-visible {
  outline: 2px solid var(--brass); outline-offset: 2px;
}

[data-testid="stTextArea"] textarea { font-size:.86rem; line-height:1.55; }
[data-testid="stExpander"] summary { font-size:.88rem; }
[data-testid="stMetricValue"] { font-family:'IBM Plex Mono',monospace; font-size:1.35rem; }
[data-testid="stMetricLabel"] {
  font-family:'IBM Plex Mono',monospace; font-size:.63rem;
  letter-spacing:.13em; text-transform:uppercase; color:var(--faint);
}

@media (max-width: 760px) {
  .principal { grid-template-columns:1fr; gap:1.2rem; }
  .fila { grid-template-columns:2.2rem minmax(0,1fr) 4.5rem; }
  .fila .regla { display:none; }
}
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def detalle_candidato(candidato_id: int) -> dict:
    """Datos de un candidato, incluido el texto extraido de su PDF.

    Cacheado porque Streamlit reejecuta el script entero en cada interaccion y
    el cuerpo de un expander se ejecuta este abierto o cerrado. Sin cache, cada
    clic en cualquier parte de la pagina relanzaria una peticion por candidato.
    """
    return requests.get(f"{API}/candidatos/{candidato_id}", timeout=30).json()


@st.cache_data(show_spinner=False)
def pdf_candidato(candidato_id: int) -> bytes:
    """Bytes del PDF original. Cacheado por el mismo motivo, y aqui pesa mas:
    son cientos de kilobytes por candidato en cada reejecucion del script."""
    return requests.get(f"{API}/candidatos/{candidato_id}/pdf", timeout=60).content


def consultar_salud() -> dict | None:
    """Pregunta a la API si ella, MySQL y el modelo estan vivos.

    Se hace al principio y no en cada accion porque el fallo tipico de esta demo
    no es intermitente: o el stack esta levantado o no lo esta. Detectarlo una
    vez y decirlo claro ahorra mucho mas tiempo que un error a mitad de uso.
    """
    try:
        return requests.get(f"{API}/salud", timeout=5).json()
    except requests.RequestException:
        return None


def grados(score: float) -> float:
    """Convierte la similitud en el angulo que realmente representa.

    El coseno de un angulo ES la metrica del proyecto, asi que arccos devuelve
    el angulo entre el vector de la oferta y el del CV. Se acota a [-1, 1]
    porque el redondeo en coma flotante puede sacar un 1.0000000002 que haria
    reventar acos con un ValueError.
    """
    return math.degrees(math.acos(max(-1.0, min(1.0, score))))


def arco(score: float, lado: int = 168) -> str:
    """Dibuja el angulo entre los dos vectores como un diagrama real.

    Es el unico elemento con peso visual de la pagina, y se gana el sitio
    porque no es decoracion: los dos rayos son la oferta y el CV, y el arco
    entre ellos es literalmente lo que mide la similitud coseno. Un angulo
    pequeno es un candidato afin.
    """
    ox, oy, largo, radio = 22, lado - 30, lado - 52, 40
    theta = math.radians(grados(score))
    fx, fy = ox + largo * math.cos(theta), oy - largo * math.sin(theta)
    ax, ay = ox + radio * math.cos(theta), oy - radio * math.sin(theta)

    return f"""
<svg viewBox="0 0 {lado} {lado}" width="{lado}" height="{lado}" aria-hidden="true">
  <line x1="{ox}" y1="{oy}" x2="{ox + largo}" y2="{oy}"
        stroke="#3A4354" stroke-width="1"/>
  <line x1="{ox}" y1="{oy}" x2="{fx:.1f}" y2="{fy:.1f}"
        stroke="#C9A227" stroke-width="1.5"/>
  <path d="M {ox + radio} {oy} A {radio} {radio} 0 0 0 {ax:.1f} {ay:.1f}"
        fill="none" stroke="#C9A227" stroke-width="1" opacity=".55"/>
  <circle cx="{ox}" cy="{oy}" r="2" fill="#C9A227"/>
  <text x="{ox + radio + 8}" y="{oy - 12}" fill="#8A93A3"
        font-family="IBM Plex Mono, monospace" font-size="11">{grados(score):.1f}&#176;</text>
</svg>"""


# Encabezado de seccion de un CV: dos o mas mayusculas seguidas como palabra
# suelta (PERFIL, EXPERIENCIA, TECNOLOGÍAS, PROFILE...).
_CABECERA = re.compile(r"\b[A-ZÁÉÍÓÚÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ]{2,})*\b")


def citar(extracto: str, limite: int = 320) -> str:
    """Prepara el fragmento ganador para mostrarlo como justificacion.

    El primer fragmento de un CV arrastra siempre la cabecera del documento
    (nombre, telefono, correo), que no explica nada y ademas saca datos de
    contacto a pantalla. Si dentro del arranque hay un titulo de seccion, la cita
    empieza ahi: asi se lee 'PERFIL Ingeniera de software...' en vez de un numero
    de telefono, y de paso se ve DE QUE SECCION viene lo que encajo.

    El recorte es solo de presentacion. La API sigue devolviendo el fragmento
    intacto, que es el que de verdad se comparo.
    """
    texto = " ".join((extracto or "").split())
    if not texto:
        return ""

    encontrada = _CABECERA.search(texto[:220])
    if encontrada and encontrada.start() > 0:
        texto = texto[encontrada.start():]

    if len(texto) > limite:
        texto = texto[:limite].rsplit(" ", 1)[0] + "..."
    return texto


def escapar(texto: str) -> str:
    """Escapa el texto que se inyecta como HTML.

    Los nombres salen de nombres de fichero subidos por quien sea; sin esto,
    un CV llamado '<img onerror=...>.pdf' se ejecutaria al pintar el ranking.
    """
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# --------------------------------------------------------------------------
salud = consultar_salud()

st.markdown(
    f"""
<div class="encabezado">
  <div class="cintillo">Afinidad sem&aacute;ntica <span>&middot;</span> Motor local</div>
  <h1>Ranking de <em>candidatos</em></h1>
  <p class="entradilla">Compara cada CV con la descripci&oacute;n del puesto por
significado, no por coincidencia de palabras. El orden lo decide el
&aacute;ngulo entre sus vectores.</p>
</div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    if salud is None:
        st.markdown(
            '<div class="estado"><span class="punto frio"></span>'
            "Sin conexi&oacute;n con la API</div>",
            unsafe_allow_html=True,
        )
        st.caption("Arranca el servicio y recarga la página:")
        st.code(
            ".venv\\Scripts\\python.exe -m uvicorn api:app "
            "--host 127.0.0.1 --port 8000",
            language="powershell",
        )
        st.caption(f"Destino: {API}")
    else:
        st.markdown(
            '<div class="estado"><span class="punto"></span>Servicios activos</div>'
            '<dl class="ficha">'
            f'<div class="par"><dt>Perfiles</dt><dd>{salud["candidatos_indexados"]}</dd></div>'
            f'<div class="par"><dt>Dimensiones</dt><dd>{salud["dimension_embedding"]}</dd></div>'
            '<div class="par"><dt>Similitud</dt><dd>coseno</dd></div>'
            "</dl>",
            unsafe_allow_html=True,
        )
        st.caption("Procedencia")
        st.markdown(
            f'<div class="archivo">{escapar(MODELO)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Modelo, base de datos y cálculo corren en esta máquina. "
            "Sin APIs externas."
        )

if salud is None:
    st.stop()


evaluar, indice, incorporar = st.tabs(
    ["Evaluar puesto", "Índice de perfiles", "Añadir perfil"]
)

# --------------------------------------------------------------------------
with evaluar:
    ejemplos = sorted(OFERTAS_DIR.glob("*.txt")) if OFERTAS_DIR.is_dir() else []
    opciones = ["Redactar puesto"] + [p.stem for p in ejemplos]

    eleccion = st.selectbox("Puesto", opciones)
    texto_inicial = ""
    if eleccion != "Redactar puesto":
        texto_inicial = (OFERTAS_DIR / f"{eleccion}.txt").read_text(encoding="utf-8")

    texto = st.text_area(
        "Descripción del puesto",
        value=texto_inicial,
        height=200,
        placeholder="Pega aquí la descripción del puesto...",
    )

    # 'bottom' alinea por la base en vez de por arriba: el number_input lleva
    # etiqueta encima y el boton no, asi que alinear por arriba los descuadra
    # justo por la altura de esa etiqueta.
    izquierda, derecha = st.columns([3, 1], vertical_alignment="bottom")
    with izquierda:
        lanzar = st.button("Evaluar candidatos", type="primary",
                           use_container_width=True)
    with derecha:
        top = st.number_input("Perfiles a mostrar", min_value=1, max_value=50, value=8)

    if lanzar:
        if not texto.strip():
            st.error("El puesto está vacío. Escribe o elige una descripción.")
        else:
            titulo = eleccion if eleccion != "Redactar puesto" else "Puesto sin título"
            with st.spinner("Comparando vectores..."):
                respuesta = requests.post(
                    f"{API}/match",
                    json={"texto": texto, "titulo": titulo, "top": int(top)},
                    timeout=120,
                )

            if respuesta.status_code != 200:
                st.error(respuesta.json().get("detail", respuesta.text))
            else:
                ranking = respuesta.json()["ranking"]
                lider, resto = ranking[0], ranking[1:]

                cita = citar(lider.get("extracto", ""))
                porque = (
                    f'<div class="porque"><span class="clave">Por qu&eacute; encaja'
                    f'</span><p>&laquo;{escapar(cita)}&raquo;</p></div>'
                    if cita else ""
                )

                st.markdown(
                    f"""
<div class="principal">
  <div>{arco(lider["score"])}</div>
  <div>
    <div class="rotulo">Mejor alineamiento</div>
    <div class="nombre">{escapar(lider["candidato"])}</div>
    <div class="cifras">
      <div class="cifra"><span class="clave">Afinidad</span>
        <span class="valor acento">{lider["score"]:.4f}</span></div>
      <div class="cifra"><span class="clave">&Aacute;ngulo</span>
        <span class="valor">{grados(lider["score"]):.1f}&#176;</span></div>
      <div class="cifra"><span class="clave">Posici&oacute;n</span>
        <span class="valor">01</span></div>
    </div>
    {porque}
  </div>
</div>""",
                    unsafe_allow_html=True,
                )

                if resto:
                    filas = "".join(
                        f'<div class="fila">'
                        f'<span class="orden">{f["posicion"]:02d}</span>'
                        f'<span class="quien">{escapar(f["candidato"])}</span>'
                        f'<span class="regla"><i style="width:{max(f["score"],0)*100:.1f}%"></i></span>'
                        f'<span class="marca">{f["score"]:.4f}</span>'
                        f"</div>"
                        for f in resto
                    )
                    st.markdown(
                        f'<div class="rotulo-seccion">Resto de la clasificaci&oacute;n</div>'
                        f"{filas}",
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    "<p class='nota'>La afinidad es el coseno del ángulo entre el "
                    "vector del puesto y el de cada CV. Mide <b>dirección, no "
                    "magnitud</b>: por eso un CV de tres páginas no gana a uno de "
                    "una sola por ser más largo. Lo que informa es el orden "
                    "relativo, no la cifra absoluta.</p>",
                    unsafe_allow_html=True,
                )

# --------------------------------------------------------------------------
with indice:
    listado = requests.get(f"{API}/candidatos", timeout=30).json()

    if listado["total"] == 0:
        st.info("No hay perfiles indexados. Añade uno desde la pestaña 'Añadir perfil'.")
    else:
        st.markdown(
            f'<div class="rotulo-seccion">{listado["total"]} perfiles en el '
            "&iacute;ndice</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "El PDF y el texto extraído, uno al lado del otro: es la forma rápida "
            "de detectar una extracción defectuosa antes de culpar al ranking."
        )

        for candidato in listado["candidatos"]:
            with st.expander(f"{candidato['nombre']}  ·  {candidato['archivo']}"):
                detalle = detalle_candidato(candidato["id"])

                izq, centro, der = st.columns(3)
                izq.metric("Caracteres", f"{detalle['caracteres']:,}".replace(",", "."))
                centro.metric("ID", detalle["id"])
                der.metric("Indexado", "Sí" if detalle["indexado"] else "No")

                columna_pdf, columna_texto = st.columns(2)

                with columna_pdf:
                    st.caption("PDF original")
                    if not detalle["pdf_disponible"]:
                        st.warning(
                            "El PDF ya no está en la carpeta de CVs. El texto "
                            "extraído sigue en la base de datos."
                        )
                    else:
                        pdf_bytes = pdf_candidato(candidato["id"])
                        st.pdf(pdf_bytes, height=430)
                        st.download_button(
                            "Descargar PDF",
                            data=pdf_bytes,
                            file_name=detalle["archivo"],
                            mime="application/pdf",
                            key=f"descargar_{candidato['id']}",
                        )

                with columna_texto:
                    st.caption("Texto extraído")
                    st.text_area(
                        "Texto extraído",
                        value=detalle["texto"],
                        height=430,
                        label_visibility="collapsed",
                        key=f"texto_{candidato['id']}",
                    )

# --------------------------------------------------------------------------
with incorporar:
    st.markdown(
        '<div class="rotulo-seccion">Alta de candidato</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Sube un CV en PDF. Se extrae el texto, se calcula su vector y queda "
        "disponible para el ranking al instante. Subir el mismo archivo otra vez "
        "actualiza al candidato en vez de duplicarlo."
    )

    pdf = st.file_uploader("CV en PDF", type=["pdf"])

    if pdf is not None and st.button("Añadir al índice", type="primary"):
        with st.spinner("Extrayendo texto y calculando el vector..."):
            respuesta = requests.post(
                f"{API}/candidatos",
                files={"archivo": (pdf.name, pdf.getvalue(), "application/pdf")},
                timeout=120,
            )

        if respuesta.status_code != 200:
            st.error(respuesta.json().get("detail", respuesta.text))
        else:
            datos = respuesta.json()
            # Resubir un CV cambia su texto y su PDF, asi que la version
            # cacheada en la pestana del indice dejaria de ser cierta.
            detalle_candidato.clear()
            pdf_candidato.clear()
            st.success(f"{datos['nombre']} añadido al índice.")

            izq, centro, der = st.columns(3)
            izq.metric("Caracteres", f"{datos['caracteres']:,}".replace(",", "."))
            centro.metric("Dimensiones", datos["dimension"])
            der.metric("ID", datos["id"])
