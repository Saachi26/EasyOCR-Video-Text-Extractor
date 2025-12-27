document.getElementById("scanBtn").addEventListener("click", async () => {
    const status = document.getElementById("status");
    status.innerText = "Scanning...";

    // Get the current active tab
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Send a message to the content script running on the page
    chrome.tabs.sendMessage(tab.id, { action: "scan_video" }, (response) => {
        if (chrome.runtime.lastError) {
            status.innerText = "Error: Refresh page";
        } else {
            status.innerText = "Done!";
        }
    });
});