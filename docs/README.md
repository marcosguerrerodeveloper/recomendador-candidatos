# Capturas para el README

Faltan tres imágenes. Requieren interacción con el navegador, así que hay que
hacerlas a mano. Con los tres servicios levantados:

| Archivo | Qué capturar |
|---|---|
| `n8n_flujo_a.png` | http://localhost:5678 → *Flujo A - Alta de candidato*, con los tres nodos visibles |
| `n8n_flujo_b.png` | http://localhost:5678 → *Flujo B - Ranking de candidatos* |
| `streamlit_ranking.png` | http://127.0.0.1:8501 → pestaña "Buscar candidatos" con un ranking ya calculado |

La primera vez que abras n8n te pedirá crear una cuenta de propietario (email y
contraseña). Es solo para el editor visual: los webhooks ya funcionan sin ella.

Cuando las tengas, descomenta el bloque de capturas al final del `README.md`
principal.

## Sugerencia para la de Streamlit

Elige `ejemplo_backend_python` en el desplegable y pulsa *Evaluar candidatos*: se
ve a Ana Ruiz Melgar arriba con su diagrama de ángulo y el perfil de RRHH abajo
del todo, que es la imagen que cuenta la historia de un vistazo.

**Cuidado si capturas la pestaña "Índice de perfiles".** Los nombres van con
seudónimo (`CV1`, `Evaristo CV`), pero el visor de PDF y el panel de texto
extraído muestran el documento entero, con su email y su teléfono. Para esa
captura, abre uno de los seis perfiles ficticios.
