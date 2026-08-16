# Recomendador de candidatos

Sistema que recibe CVs en PDF y una descripción de puesto, y devuelve un ranking
de candidatos ordenado por **afinidad semántica** — no por coincidencia de
palabras clave. Un CV que dice *"diseño de pipelines ETL"* puntúa alto frente a
una oferta que pide *"data engineering"* aunque no compartan ni una palabra.

Todo corre en local: el modelo de embeddings, la base de datos y el cálculo de
similitud. Sin APIs de pago ni servicios cloud.

---

## Resultado de ejemplo

Dieciocho candidatos frente a cuatro ofertas. Dieciséis son perfiles ficticios
generados para la demo y sí están en el repositorio; los otros dos son CVs reales
con datos personales y **quedan excluidos por `.gitignore`** — por eso aparecen
aquí como `CV1` y `Evaristo CV`. Todos rondan los 2.500-3.500 caracteres, la
longitud de un CV real de verdad.

Los cinco primeros de cada oferta, sin tocar nada entre ejecuciones:

| # | Oferta backend Python | | Oferta data scientist NLP | |
|---|---|---|---|---|
| 1 | **Ana Ruiz** — Backend Python | `0.7856` | **Marc Soler** — Data Scientist | `0.7035` |
| 2 | David Ortega — DevOps/SRE | `0.6221` | Nadia Belkacem — ML Engineer | `0.6988` |
| 3 | Nadia Belkacem — ML Engineer | `0.6190` | Elena Cortés — Data Eng. junior | `0.6410` |
| 4 | Kwame Osei — Data Engineer | `0.6136` | Sofía Marchetti — Product Designer | `0.6344` |
| 5 | CV1 | `0.5912` | Hugo Delgado — Analista BI | `0.6265` |

| # | Oferta frontend React | | Oferta data engineer *(en inglés)* | |
|---|---|---|---|---|
| 1 | **Lucía Fernández** — Frontend | `0.7676` | **Kwame Osei** — Data Engineer | `0.7579` |
| 2 | Sofía Marchetti — Product Designer | `0.7049` | Evaristo CV | `0.7429` |
| 3 | CV1 | `0.6835` | Elena Cortés — Data Eng. junior | `0.7038` |
| 4 | Ana Ruiz — Backend Python | `0.6732` | CV1 | `0.6911` |
| 5 | Nadia Belkacem — ML Engineer | `0.6316` | Priya Raghunathan — Cloud | `0.5718` |

Cuatro lecturas de estas tablas:

**Acierta el primero en las cuatro ofertas**, y con margen: el ganador saca entre
`0.015` y `0.16` al segundo. El segundo puesto también es defendible en todas —
un product designer detrás de una frontend, un ML engineer detrás de un data
scientist, una data engineer junior detrás del sénior.

**Distingue familias que se solapan.** El conjunto incluye a propósito data
engineer, data analyst, data scientist y ML engineer, que comparten vocabulario.
Aun así, la oferta de NLP pone arriba al data scientist y al ML engineer, y la de
plataforma de datos al data engineer y a la junior del mismo campo. No está
agrupando por "temática de datos", está separando dentro de ella.

**El cruce de idiomas funciona.** La cuarta oferta está en inglés y los CVs en
español compiten de tú a tú: el ganador es un CV en inglés, pero el segundo y el
tercero están en español.

**Dice por qué encaja, no solo cuánto.** Cada CV se guarda además troceado en
fragmentos, y el sistema señala cuál de ellos es el más afín a la oferta. El
ranking muestra ese extracto junto al primer candidato, así que se puede
comprobar el resultado en dos segundos en lugar de creerse el número. El
fragmento no interviene en la puntuación — ver más abajo por qué.

**Y el punto débil, que se deja a la vista.** Frente a la oferta de backend, la
técnica de RRHH queda 14ª de 18, por delante de un desarrollador full stack
(13º). Un perfil no técnico no debería adelantar a un programador. La causa está
explicada abajo: promediar fragmentos empuja todo documento largo hacia el centro
del espacio semántico, y en la zona media de la tabla las diferencias se
comprimen hasta volverse ruido. El primer puesto es fiable; el puesto once no lo
es. El otro control negativo, el contable, sí queda último en las cuatro.

---

## Cómo funciona

```
CV.pdf ──► extract_text.py ──► embed_and_store.py ──► MySQL
           (pdfplumber)        (sentence-transformers)  (texto + vector JSON)
                                                            │
oferta ──► embed_and_store.py ──► match.py ────────────────►┤
           (mismo modelo)         (coseno con numpy)         │
                                          │                  │
                                          ▼                  ▼
                                      ranking            tabla matches
```

Cada texto —CV u oferta— se convierte en un vector de 384 dimensiones que
representa su *significado*. Comparar dos textos es entonces medir el ángulo
entre sus vectores:

```python
similitud = dot(a, b) / (norm(a) * norm(b))
```

Se usa el coseno y no la distancia euclídea porque mide **dirección, no
magnitud**. Un CV de tres páginas genera un vector con más "energía" acumulada
que una oferta de diez líneas; con una métrica sensible al tamaño, los CVs largos
ganarían por ser largos y no por ser afines. Al dividir por las dos normas esa
diferencia desaparece y solo queda la pregunta relevante: *hacia dónde apunta
cada texto*.

### Las tres formas de usarlo

El mismo pipeline se consume desde tres sitios distintos, y ninguno reimplementa
lógica. Es la prueba de que la separación por capas es real:

```
terminal ──┐
n8n ───────┼──► api.py ──► extract_text / embed_and_store / match ──► MySQL
Streamlit ─┘
```

---

## Puesta en marcha

```powershell
# 1. Dependencias
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Base de datos (MySQL 8 en Docker, local)
copy .env.example .env
docker compose up -d

# 3. Pipeline en Python puro
.\.venv\Scripts\python.exe db_setup.py          # crea el esquema
.\.venv\Scripts\python.exe embed_and_store.py   # indexa los CVs de cvs/
.\.venv\Scripts\python.exe match.py backend_python_senior
```

Eso ya imprime un ranking. Las capas de arriba son opcionales:

```powershell
# Capa HTTP (necesaria para n8n y para Streamlit)
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000

# Vitrina visual (el tema y el bind a localhost salen de .streamlit/config.toml)
.\.venv\Scripts\python.exe -m streamlit run app_streamlit.py

# Orquestación
npx -y n8n
```

Detalles de n8n (importar flujos, publicar, webhooks): [`n8n/README.md`](n8n/README.md).

---

## Decisiones y por qué

**Embeddings locales, modelo multilingüe.** `paraphrase-multilingual-MiniLM-L12-v2`
con `sentence-transformers`. Se descartó `all-MiniLM-L6-v2`, que es mejor en
inglés puro, porque los CVs y ofertas mezclan español e inglés y el modelo
monolingüe no alinea bien los dos idiomas en el mismo espacio. Sin APIs externas
(OpenAI, Voyage, Cohere): el proyecto no depende de terceros ni de una tarjeta.

**MySQL y no una base vectorial.** Con dieciocho candidatos, un índice vectorial
no aporta nada: comparar dieciocho vectores de 384 dimensiones es instantáneo. El
embedding se guarda serializado en una columna `JSON` y la similitud se calcula
en Python. Es una decisión de escala, no de desconocimiento — con cientos de
miles de CVs la respuesta correcta sería pgvector o Qdrant, y el cambio afectaría
solo a `match.py`.

**El coseno escrito a mano.** Existe `sklearn.metrics.pairwise.cosine_similarity`
y habría sido una línea. Se escribió con numpy para que la fórmula esté a la
vista y se pueda explicar, que es el objetivo de este proyecto.

**Todo en local, sin cloud.** Decisión deliberada de alcance.

**n8n con `npx` y no en Docker.** Dentro de un contenedor, `localhost` es el
propio contenedor: n8n no alcanzaría ni a la API ni a MySQL sin configurar redes.
Nativo, las piezas comparten `127.0.0.1`.

**Una capa HTTP entre n8n y los scripts.** Los nodos de n8n llaman a `api.py`,
que importa las funciones ya probadas. Borrando `api.py` y `n8n/`, el pipeline
sigue funcionando por terminal exactamente igual.

**Sin autenticación.** Corre en local y no se expone a internet. En un despliegue
real llevaría un token por cabecera. Es una decisión consciente, no un olvido.

---

## Problemas reales que aparecieron

Los tres se detectaron midiendo, no leyendo código.

**El modelo truncaba el 85% de cada CV en silencio.** MiniLM tiene una ventana de
128 tokens y descarta lo que sobra sin lanzar ningún error. De un CV de tres
páginas solo se comparaban el nombre, el titular y el párrafo de perfil — prosa
genérica que se parece entre todos los candidatos — y quedaba fuera la sección de
tecnologías, que es justo la que distingue un backend de un frontend. El síntoma
medible fue el perfil de RRHH colándose en cuarta posición frente a una oferta de
backend.

*Solución:* `embed()` trocea el documento por frases en fragmentos que caben
enteros en la ventana, embebe cada uno, **normaliza antes de promediar** (sin eso
un fragmento de mayor magnitud arrastra la media por enérgico, no por
representativo) y devuelve el centroide.

*Contrapartida honesta:* promediar convierte el documento en su centroide
temático, así que un CV largo y transversal queda a media distancia de todo y
puntúa medio-alto frente a cualquier oferta. Se ve en las tablas: CV1, que es el
documento más largo del conjunto, aparece entre los seis primeros de las cuatro
ofertas pese a no ser el mejor para ninguna.

**La solución evidente se probó y era peor.** Si promediar diluye al
especialista, lo lógico parece puntuar por el *mejor* fragmento: bastaría con que
una parte del CV respondiera a la oferta. Se implementó y se midió sobre las
cuatro ofertas y los dieciocho candidatos. Todas las variantes aciertan al
ganador, así que el criterio decisivo es dónde caen los dos controles negativos,
que deberían hundirse:

| agregación | posición media de los controles (de 18) |
|---|---|
| **promedio** | **16,62** |
| 70% promedio + 30% máximo | 16,12 |
| 50% + 50% | 15,75 |
| 30% + 70% | 15,25 |
| media del top-3 | 14,88 |
| media del top-2 | 14,75 |
| solo el máximo | 13,88 |

La relación es monótona: cuanto más peso al máximo, peor. El motivo es que el
máximo se queda con **un** fragmento, y todo CV tiene alguno genérico —el perfil
de apertura, los datos de disponibilidad— que puntúa tibio contra cualquier
oferta. Al promediar se premia que el documento entero vaya del tema. La
intuición era razonable y los datos la desmienten, así que el promedio se queda.

**Acentos partidos en dos glifos.** Uno de los CVs reales está generado con LaTeX
y no incrusta la letra acentuada, sino la base y el acento por separado. Al
extraer salía `Formacio´n Acade´mica`, `Espan˜a`, `Tecnolog´ıa`. Para el
tokenizador eso no son palabras en español, y se perdía el significado de
secciones enteras. `unicodedata.normalize("NFC")` no basta: son acentos
*espaciadores*, no combinantes, y hay que convertirlos primero. Además el acento
aparece unas veces delante y otras detrás de su letra, según la coordenada X con
la que el PDF dibujó cada glifo.

**Mojibake silencioso por stdin en Windows.** `sys.stdin` se abre con la
codificación del sistema (`cp1252`), así que una oferta en UTF-8 llegada por
tubería se decodificaba mal **sin lanzar ninguna excepción** y cambiaba el orden
del ranking. Importa porque es exactamente como n8n inyecta el texto. Se leen los
bytes crudos y se decodifican a mano.

---

## Limitaciones conocidas

- **Los CVs largos y transversales puntúan alto contra todo.** Explicado arriba.
- **La zona media del ranking no es fiable.** El primer puesto acierta en las
  cuatro ofertas y con margen, pero entre los puestos 8 y 15 las diferencias caen
  por debajo de `0.02` y el orden deja de significar nada: ahí es donde la
  técnica de RRHH adelanta a un desarrollador full stack. Al alargar los CVs de
  700 a 2.500 caracteres el primer puesto mejoró y la zona media empeoró, que es
  justo lo que predice el efecto centroide. Se descartaron dos explicaciones
  midiendo: no lo causa el texto genérico común a todos los CVs (al eliminarlo,
  el orden apenas se movió) y no lo arregla puntuar por el mejor fragmento (sale
  peor, ver la tabla de arriba).
- **El ranking mide afinidad temática, no idoneidad.** No distingue tres años de
  experiencia de diez, ni detecta que a un candidato le falta un requisito
  obligatorio. Un filtro duro previo (años, titulación, disponibilidad) sería el
  complemento natural.
- **Sin OCR.** Un CV escaneado como imagen no da texto; el sistema lo detecta y
  lo rechaza con un mensaje claro en vez de indexar un candidato vacío.
- **Streamlit no es desplegable tal cual en la nube.** La app consume la API
  local, que a su vez habla con MySQL local. En Streamlit Community Cloud no
  habría nada al otro lado. Desplegarlo exigiría exponer el stack o precalcular
  los datos de demo — y eso reabriría la decisión de "sin cloud".

---

## Estructura

```
extract_text.py       Paso 1 · PDF -> texto limpio (pdfplumber)
db_setup.py           Paso 2 · esquema MySQL y conexión reutilizable
embed_and_store.py    Paso 3 · texto -> vector de 384 dims -> MySQL
match.py              Paso 4 · coseno y ranking
api.py                Paso 6 · capa HTTP (FastAPI) que consumen n8n y Streamlit
app_streamlit.py      Paso 7 · vitrina visual
n8n/                  flujos exportados + guía de orquestación
cvs/                  CVs en PDF
ofertas/              descripciones de puesto en .txt
docs/                 capturas para este README
```

**Esquema de datos:** `candidatos` (clave única por archivo), `puestos` (clave
única por SHA-256 de la descripción) y `matches` (única por par candidato-puesto).
Las tres claves hacen el pipeline idempotente: reprocesar no duplica nada.

---

## Capturas

Pendientes: ver [`docs/README.md`](docs/README.md) para qué capturar y desde
dónde. Una vez estén en `docs/`, basta con descomentar este bloque:

<!--
| | |
|---|---|
| ![Flujo A en n8n](docs/n8n_flujo_a.png) | ![Flujo B en n8n](docs/n8n_flujo_b.png) |
| Flujo A — alta de candidato | Flujo B — ranking |

![Vitrina en Streamlit](docs/streamlit_ranking.png)
-->

