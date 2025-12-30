chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scan_video") {
        captureAndProcess();
        sendResponse({ status: "started" });
    }
});

async function captureAndProcess() {
    const video = document.querySelector("video");
    
    if (!video) {
        alert("No video found on this page!");
        return;
    }

    // 1. Capture the Frame
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64 string
    const dataURL = canvas.toDataURL("image/jpeg");

    // 2. Remove old boxes
    document.querySelectorAll(".magic-ocr-box").forEach(e => e.remove());

    // 3. Send to Server
    try {
        const response = await fetch("http://127.0.0.1:5001/ocr", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: dataURL })
        });

        const result = await response.json();
        
        if (result.success) {
            drawOverlay(video, result.data);
        } else {
            console.error("Server error:", result.error);
        }
    } catch (err) {
        alert("Is your Python server running? Failed to connect.");
        console.error(err);
    }
}

function drawOverlay(video, textData) {
    // Get the video's actual size on screen vs original size
    const rect = video.getBoundingClientRect();
    const scaleX = rect.width / video.videoWidth;
    const scaleY = rect.height / video.videoHeight;

    // Create a container for our text boxes
    const container = document.createElement("div");
    container.className = "magic-ocr-box"; 
    container.style.position = "absolute";
    container.style.left = rect.left + window.scrollX + "px";
    container.style.top = rect.top + window.scrollY + "px";
    container.style.width = rect.width + "px";
    container.style.height = rect.height + "px";
    container.style.pointerEvents = "none"; 
    container.style.zIndex = "9999"; 
    
    document.body.appendChild(container);

    textData.forEach(item => {
        const box = document.createElement("div");
        box.innerText = item.text;
        
        // Add a class for styling
        box.className = "magic-text-box"; 

        // Position matches the text exactly
        box.style.left = (item.box.x * scaleX) + "px";
        box.style.top = (item.box.y * scaleY) + "px";
        box.style.width = (item.box.width * scaleX) + "px";
        box.style.height = (item.box.height * scaleY) + "px";
        box.style.fontSize = (item.box.height * scaleY * 0.85) + "px"
        box.dataset.text = item.text; 
        container.appendChild(box);
    });
}
