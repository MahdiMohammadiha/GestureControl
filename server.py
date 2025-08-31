import asyncio
import websockets
import cv2
import numpy as np
import ssl
from settings import CERT_FILE, KEY_FILE

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)


async def handler(websocket):
    print("New client connected!")

    try:
        async for message in websocket:
            # The message from client comes in binary (jpeg bytes) format.
            if isinstance(message, (bytes, bytearray)):
                # Convert bytes to numpy array
                nparr = np.frombuffer(message, np.uint8)

                # Convert to image with OpenCV
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    cv2.imshow("Camera Stream", frame)

                    # Close by pressing the q key.
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            else:
                print("Got non-binary message:", message)

    except websockets.ConnectionClosed:
        print("Client disconnected")
    finally:
        cv2.destroyAllWindows()


async def main():
    start_server = await websockets.serve(handler, "0.0.0.0", 12345, ssl=ssl_context)
    print("WSS server started on port 12345")
    await start_server.wait_closed()  # keep running


if __name__ == "__main__":
    asyncio.run(main())
