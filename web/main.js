const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const toggleVideo = document.getElementById("toggleVideo");
const toggleStream = document.getElementById("toggleStream");
const wakeLockToggle = document.getElementById("wakeLockToggle");
const closeConnection = document.getElementById("closeConnection");


let socket;
let streaming = true;
let wakeLock = null;

// Web socket connection as soon as the page loads
window.addEventListener("load", () => {
    const loc = window.location;
    const wsProtocol = loc.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${loc.hostname}:12345`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("Connected to WebSocket server ✅", wsUrl);
        startCamera();
    };

    socket.onclose = () => {
        console.log("Disconnected ❌");
    };

    socket.onerror = (err) => {
        console.error("WebSocket error:", err);
    };
});

// Video display control
toggleVideo.addEventListener("change", () => {
    canvas.style.display = toggleVideo.checked ? "block" : "none";
});

// Data stream control
toggleStream.addEventListener("change", () => {
    streaming = toggleStream.checked;
});

// Control the screen stay on
wakeLockToggle.addEventListener("change", async () => {
    try {
        if (wakeLockToggle.checked) {
            wakeLock = await navigator.wakeLock.request("screen");
            console.log("Screen will stay awake ✅");
        } else if (wakeLock) {
            await wakeLock.release();
            wakeLock = null;
            console.log("Screen lock released ❌");
        }
    } catch (err) {
        console.error("Wake Lock error:", err);
        alert("Wake Lock API not supported on this device/browser.");
        wakeLockToggle.checked = false;
    }
});

closeConnection.addEventListener("change", () => {
    if (closeConnection.checked && socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
        console.log("WebSocket connection closed ❌");
    }
});

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            const FIXED_WIDTH = 1280;
            const FIXED_HEIGHT = 720;

            canvas.width = FIXED_WIDTH;
            canvas.height = FIXED_HEIGHT;

            startStreaming();
        };



    } catch (err) {
        console.error("Error accessing camera:", err);
        alert("دوربین پیدا نشد یا دسترسی داده نشده!");
    }
}

function startStreaming() {
    setInterval(() => {
        // Temporary canvas to send to WebSocket
        const sendCanvas = document.createElement("canvas");
        sendCanvas.width = canvas.width;
        sendCanvas.height = canvas.height;
        const sendCtx = sendCanvas.getContext("2d");

        if (streaming) {
            // Real webcam image with mirror
            sendCtx.save();
            sendCtx.translate(sendCanvas.width, 0);
            sendCtx.scale(-1, 1);
            sendCtx.drawImage(video, 0, 0, sendCanvas.width, sendCanvas.height);
            sendCtx.restore();
        } else {
            // black screen
            sendCtx.fillStyle = "black";
            sendCtx.fillRect(0, 0, sendCanvas.width, sendCanvas.height);
        }

        // Display on main canvas only if Show Video is on
        if (toggleVideo.checked) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            ctx.restore();
        }

        // Send to WebSocket
        sendCanvas.toBlob((blob) => {
            if (blob && socket && socket.readyState === WebSocket.OPEN) {
                blob.arrayBuffer().then((buffer) => {
                    socket.send(buffer);
                });
            }
        }, "image/jpeg", 0.5);

    }, 100);
}

