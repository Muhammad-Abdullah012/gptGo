export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
  // Function to capture the active tab's screenshot
  async function captureScreenshot(): Promise<string> {
    return browser.tabs.captureVisibleTab();
  }

  // Listen for messages from the popup
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "captureScreenshot") {
      captureScreenshot()
        .then((screenshot) => {
          sendResponse({ screenshot });
        })
        .catch(console.error);
      return true;
    }
  });
});
