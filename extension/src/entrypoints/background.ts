export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
  // Function to capture the active tab's screenshot
  async function captureScreenshot(): Promise<string> {
    return browser.tabs.captureVisibleTab();
  }

  // Listen for messages from the popup
  browser.runtime.onMessage.addListener(
    async (message, sender, sendResponse) => {
      if (message.action === "captureScreenshot") {
        try {
          const screenshot = await captureScreenshot();
          sendResponse({ success: true, screenshot });
        } catch (error) {
          sendResponse({ success: false, error });
        }
      }
    }
  );
});
