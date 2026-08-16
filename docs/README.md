# Capturas del README

Las tres están hechas y en uso:

| Archivo | Qué muestra |
|---|---|
| `streamlit_ranking.png` | La vitrina con la oferta `data_engineer`, elegida porque es la que enseña el filtro de requisitos trabajando |
| `n8n_flujo_a.png` | Flujo A — alta de candidato |
| `n8n_flujo_b.png` | Flujo B — ranking |

Todas se generan con Playwright, sin tocar el ratón. Si hay que rehacerlas, esto
es lo que costó averiguar:

## Streamlit

- **`clip` no baja del viewport salvo `full_page=True`.** Sin eso el ranking sale
  cortado a media tabla aunque el recorte pida más alto.
- **Playwright deja el cursor sobre el botón** tras hacer clic, así que fotografía
  la fila en estado *hover*. Hay que apartar el ratón antes de capturar.
- **Cuidado con quién gana.** La ficha del primer puesto cita un fragmento de su
  CV, así que si ganara `CV1` o `Evaristo CV` la imagen publicaría texto de un CV
  real con su correo y su teléfono. El script comprueba el nombre del líder y
  avisa si es uno de los dos.

## n8n

- **El editor exige cuenta**, aunque los webhooks funcionen sin ella. Si se pierde
  la contraseña, `npx n8n user-management:reset` borra el propietario y deja pasar
  por la pantalla de alta otra vez. **Los flujos se conservan**, pero conviene
  respaldar `~/.n8n/database.sqlite` antes; los JSON de `n8n/` son el otro
  respaldo.
- **El alta y el inicio de sesión se parecen** —ambos piden correo y contraseña—
  y hay que distinguirlos: el alta trae además los campos de nombre y un botón
  *Next*, el inicio de sesión solo *Sign in*.
- **Recortar el lienzo por detección de contenido exige un umbral por debajo de
  158.** Ese es el gris de los puntos del fondo, que cubren toda la superficie:
  con un umbral más alto se cuentan como contenido y el recorte sale del tamaño
  original. Los nodos son 43 o más oscuros.
- **Al medir el área hay que ignorar los bordes.** n8n flota botones oscuros
  arriba, a la derecha y abajo a la izquierda, y estiran la caja hasta el ancho
  completo.
- **Publicar un flujo no registra su webhook hasta reiniciar n8n.** Si un webhook
  da 404, es esto el 90% de las veces.
