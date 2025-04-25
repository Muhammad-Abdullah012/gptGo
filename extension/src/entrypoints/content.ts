import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { getCleanedHTML, getVisibleClickableHTML } from "@/lib/getHtml";
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
      if (message.action === BROWSER_ACTIONS.GET_HTML) {
        sendResponse({ html: getCleanedHTML(getVisibleClickableHTML()) });
      }
      if (message.action === BROWSER_ACTIONS.RUN_CODE) {
        console.log("running code")
        const payload = message.payload;
        const jsCode = payload?.generated_text?.javascript_code;
        const scroll = payload?.generated_text?.scroll;

        if (scroll) {
          window.scrollBy(0, 500);
        }

        if (jsCode) {
          try {
            const fn = new Function(jsCode);
            fn();
          } catch (err) {
            console.error("Error executing JS code:", err);
          }
        }

      }
    });
  },
});
