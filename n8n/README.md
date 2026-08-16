# Paso 6 — Orquestación con n8n

Tres piezas, en este orden de arranque:

```
n8n (flujos visuales)  ->  api.py (traductor HTTP->Python)  ->  scripts + MySQL
   :5678                      :8000                              :3306
```

## Arrancar

```powershell
# 1. MySQL
docker compose up -d

# 2. La capa HTTP (déjala abierta: carga el modelo una vez al arrancar)
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000

# 3. n8n (en otra terminal)
npx -y n8n
```

Comprobación rápida de que la base está viva antes de tocar n8n:

```powershell
curl.exe http://127.0.0.1:8000/salud
# {"estado":"ok","candidatos_indexados":8,"dimension_embedding":384}
```

## Los dos flujos

**Flujo A — alta de candidato.** `POST /webhook/candidato` con un PDF en el campo
de formulario `archivo`. Extrae el texto, calcula el embedding y lo guarda.

```bash
curl -X POST http://127.0.0.1:5678/webhook/candidato -F "archivo=@cv.pdf"
# {"ok":true,"id":85,"nombre":"...","archivo":"cv.pdf","caracteres":726,"dimension":384}
```

**Flujo B — ranking.** `POST /webhook/match` con el texto de la oferta.

```bash
curl -X POST http://127.0.0.1:5678/webhook/match \
  -H "Content-Type: application/json" \
  -d '{"texto":"Desarrollador backend con Python y MySQL...","top":3}'
# [{"titulo":"...","total_candidatos":3,"ranking":[{"posicion":1,"candidato":"Ana Ruiz Backend","score":0.7383}, ...]}]
```

Campos aceptados por el Flujo B: `texto` (obligatorio), `titulo`, `top`,
`guardar` (a `false` para probar sin escribir en la base de datos).

## Importar los flujos en una instalación limpia

```powershell
npx -y n8n import:workflow --input="n8n\flujo_a_alta_candidato.json"
npx -y n8n import:workflow --input="n8n\flujo_b_ranking.json"
npx -y n8n list:workflow                       # copia los IDs
npx -y n8n publish:workflow --id=<ID>          # uno por flujo
```

Los webhooks **no quedan registrados hasta reiniciar n8n** tras publicar; el
propio comando lo avisa. Si un webhook devuelve 404, es casi siempre esto.

## Decisiones de este paso

**n8n con `npx` y no en Docker.** En un contenedor, `localhost` es el propio
contenedor, no la máquina: n8n no alcanzaría ni a la API ni a MySQL sin
configurar redes. Ejecutándolo nativo, las tres piezas comparten `127.0.0.1`.

**Una capa HTTP intermedia en vez de que n8n ejecute los scripts.** Los nodos
HTTP llaman a `api.py`, que importa las funciones ya probadas en el paso 5 sin
reimplementar nada. Borrando `api.py` y `n8n/`, el pipeline sigue funcionando
por línea de comandos: esa es la prueba de que la separación es real.

**La API es un servicio permanente, no un script por petición.** Cargar el
modelo de embeddings tarda varios segundos; como proceso encendido se paga una
sola vez al arrancar.

**Sin autenticación.** Corre en local y no se expone a internet. En un despliegue
real iría un token por cabecera — es una decisión consciente, no un olvido.
