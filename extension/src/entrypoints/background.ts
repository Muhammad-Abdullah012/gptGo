import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { startTask } from "@/lib/startTask";
import { state } from "@/store/store.svelte";

export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });

  // Listen for messages from the popup
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("background.ts message received", JSON.stringify(message));
    if (message.action === BROWSER_ACTIONS.START_TASK) {
      if (message.payload.prompt) {
        state.prompt = message.payload.prompt;
      }
      if (state.isProcessing) {
        sendResponse({
          success: false,
          message: "Task already running",
        });
        return true;
      }

      state.isProcessing = true;
      startTask().finally(() => {
        state.isProcessing = false;
        state.previousActions = [];
      });

      sendResponse({
        success: true,
        message: "Task started!",
      });
      return true;
    }
  });
});
