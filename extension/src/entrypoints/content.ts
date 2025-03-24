import { pressKey } from "@/lib/pressKeyboardKeys";

export default defineContentScript({
  matches: ["*://*.google.com/*"],
  main(ctx) {
    console.log("Hello content.");
    
    browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
      console.log("message received", message);
      if (message.action === "PressKey") {
        pressKey("f");
      }
    });

    // window.addEventListener('keydown', (event) => {
    //   console.log('Keydown event detected:', event);
    // });
  },
});
