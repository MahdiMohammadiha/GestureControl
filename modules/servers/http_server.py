from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from settings import CERT_FILE, KEY_FILE

app = FastAPI()

# Mount web directory for static files
app.mount("/", StaticFiles(directory="web", html=True), name="web")

# If you want, specifically give index.html.
@app.get("/")
async def index():
    return FileResponse("web/index.html")


async def start_http_server():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=10001,
        ssl_certfile=CERT_FILE,
        ssl_keyfile=KEY_FILE,
        reload=False,
    )
    server = uvicorn.Server(config)
    await server.serve()
