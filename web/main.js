const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const startBtn = document.getElementById("startBtn");

let socket;

startBtn.addEventListener("click", async () => {
    // اتصال WebSocket به متغیر سراسری
    socket = new WebSocket("wss://10.38.148.72:12345");

    socket.onopen = () => {
        console.log("Connected to WebSocket server ✅");
        startCamera();
    };

    socket.onclose = () => {
        console.log("Disconnected ❌");
    };

    socket.onerror = (err) => {
        console.error("WebSocket error:", err);
    };

    startBtn.disabled = true;
});

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth / 2;
            canvas.height = video.videoHeight / 2;
            startStreaming();
        };
    } catch (err) {
        console.error("Error accessing camera:", err);
        alert("دوربین پیدا نشد یا دسترسی داده نشده!");
    }
}

function startStreaming() {
    setInterval(() => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.save();

        // آینه افقی
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.restore();

        canvas.toBlob((blob) => {
            if (blob && socket && socket.readyState === WebSocket.OPEN) {
                blob.arrayBuffer().then((buffer) => {
                    socket.send(buffer);
                });
            }
        }, "image/jpeg", 0.5);
    }, 100);
}
