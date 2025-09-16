import asyncio
import websockets
import cv2
import numpy as np
import ssl
import uuid
from settings import CERT_FILE, KEY_FILE

MAX_CLIENTS = 3
TIMEOUT = 30  # seconds

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

connected_clients = {}  # websocket -> client_id
latest_frames = {}      # client_id -> frame (numpy array)


async def handler(websocket):
    global connected_clients, latest_frames

    if len(connected_clients) >= MAX_CLIENTS:
        print("Max clients reached, rejecting new client.")
        await websocket.close()
        return

    client_id = str(uuid.uuid4())[:8]
    connected_clients[websocket] = client_id
    print(f"New client connected! ID={client_id}, Total clients: {len(connected_clients)}")

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
            except asyncio.TimeoutError:
                print(f"Client {client_id} timed out. Closing connection.")
                await websocket.close()
                break

            if isinstance(message, (bytes, bytearray)):
                nparr = np.frombuffer(message, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None:
                    latest_frames[client_id] = frame
            else:
                print(f"Client {client_id} sent non-binary message:", message)

    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        connected_clients.pop(websocket, None)
        latest_frames.pop(client_id, None)
        print(f"Client {client_id} removed. Total clients: {len(connected_clients)}")


async def start_server():
    start_server = await websockets.serve(
        handler,
        "0.0.0.0",
        12345,
        ssl=ssl_context,
    )
    print("WSS server started on port 12345")
    await start_server.wait_closed()
