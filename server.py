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


async def handler(websocket):
    global connected_clients

    # Limit the number of clients
    if len(connected_clients) >= MAX_CLIENTS:
        print("Max clients reached, rejecting new client.")
        await websocket.close()
        return

    # Assign a unique ID
    client_id = str(uuid.uuid4())[:8]  # First 8 characters of UUID
    connected_clients[websocket] = client_id
    window_name = f"Camera Stream {client_id}"

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
                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            else:
                print(f"Client {client_id} sent non-binary message:", message)

    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        connected_clients.pop(websocket, None)
        cv2.destroyWindow(window_name)
        print(f"Client {client_id} removed. Total clients: {len(connected_clients)}")


async def main():
    start_server = await websockets.serve(handler, "0.0.0.0", 12345, ssl=ssl_context)
    print("WSS server started on port 12345")
    await start_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
