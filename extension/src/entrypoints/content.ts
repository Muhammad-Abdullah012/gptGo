import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { pressKey } from "@/lib/pressKeyboardKeys";

export default defineContentScript({
  matches: ["*://*.google.com/*"],
  main(ctx) {
    console.log("Hello content.");

    browser.runtime?.onMessage?.addListener((message, sender, sendResponse) => {
      console.log("content.ts:: message received", JSON.stringify(message));
      if (message.action === BROWSER_ACTIONS.PRESS_KEY) {
        pressKey(message.payload.key);
      }
    });

    // window.addEventListener("keydown", (event) => {
    //   console.log("Keydown event detected:", event);
    // });
  },
});
