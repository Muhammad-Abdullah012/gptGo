import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { simulateKeyPress, setInputValue } from "@/lib/pressKeyboardKeys";

export default defineContentScript({
  matches: ["<all_urls>"],
  registration: "manifest",
  main(ctx) {
    console.log("Hello content.");

    browser.runtime?.onMessage?.addListener((message, sender, sendResponse) => {
      console.log("content.ts:: message received", JSON.stringify(message));
      if (message.action === BROWSER_ACTIONS.PRESS_KEY) {
        simulateKeyPress(message.payload.key);
      }
      if (message.action === BROWSER_ACTIONS.TYPE) {
        setInputValue(message.payload.text);
      }
      if (message.action = BROWSER_ACTIONS.GET_HTML) {
        sendResponse({ html: document.documentElement.outerHTML })
      }
    });
  },
});
