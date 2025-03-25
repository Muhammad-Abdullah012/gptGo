import { BROWSER_ACTIONS } from "@/constants/browserActions";

export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
  // Function to capture the active tab's screenshot
  async function captureScreenshot(): Promise<string> {
    return browser.tabs.captureVisibleTab();
  }

  async function startTask(prompt: string) {
    let taskCompleted = false;

    while (!taskCompleted) {
      const screenshot = await captureScreenshot();
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          image: screenshot,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Api response data => ", data);
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: {
          key: "f",
        },
      });
      taskCompleted = true;
    }
  }

  async function sendMessageToActiveTab(payload: object) {
    const [tab] = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });
    await browser.tabs.sendMessage(tab.id ?? 0, payload);
  }
  // Listen for messages from the popup
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("background.ts message received", JSON.stringify(message));
    if (message.action === BROWSER_ACTIONS.START_TASK) {
      startTask(message.payload.prompt)
        .then(() =>
          sendResponse({
            success: true,
            message: "Task completed successfully!",
          })
        )
        .catch((error) => {
          sendResponse({ success: false, message: error.message });
        });
      return true;
    }
  });
});
