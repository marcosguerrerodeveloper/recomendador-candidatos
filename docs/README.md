# Capturas para el README

Faltan **dos** imágenes, las de n8n. Requieren crear la cuenta de propietario del
editor visual (email y contraseña), así que hay que hacerlas a mano:

| Archivo | Qué capturar |
|---|---|
| `n8n_flujo_a.png` | http://localhost:5678 → *Flujo A - Alta de candidato*, con los tres nodos visibles |
| `n8n_flujo_b.png` | http://localhost:5678 → *Flujo B - Ranking de candidatos* |

`streamlit_ranking.png` ya está hecha, con la oferta `data_engineer` porque es la
que muestra el filtro de requisitos en acción.

## Dos cosas que hay que cuidar al capturar la vitrina

- **`clip` no baja del viewport salvo `full_page=True`.** Sin eso el ranking sale
  cortado a media tabla aunque el recorte pida más alto.
- **Playwright deja el cursor sobre el botón** tras hacer clic, así que fotografía
  la fila en estado *hover*. Hay que apartar el ratón antes de capturar.

La primera vez que abras n8n te pedirá crear una cuenta de propietario (email y
contraseña). Es solo para el editor visual: los webhooks ya funcionan sin ella.

Cuando las tengas, descomenta el bloque de capturas al final del `README.md`
principal.

## Sugerencia para la de Streamlit

Elige `backend_python_senior` en el desplegable y pulsa *Evaluar candidatos*: se
ve a Ana Ruiz Melgar arriba con su diagrama de ángulo y el perfil de RRHH abajo
del todo, que es la imagen que cuenta la historia de un vistazo.

**Cuidado si capturas la pestaña "Índice de perfiles".** Los nombres van con
seudónimo (`CV1`, `Evaristo CV`), pero el visor de PDF y el panel de texto
extraído muestran el documento entero, con su email y su teléfono. Para esa
captura, abre uno de los seis perfiles ficticios.
