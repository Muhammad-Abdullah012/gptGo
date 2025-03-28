import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { IAction } from "@/interfaces";
import { delay } from "@/lib/delay";
import { pressKey } from "@/lib/pressKeyboardKeys";
import { state } from "@/store/store.svelte";

export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
  // Function to capture the active tab's screenshot
  async function captureScreenshot(): Promise<string> {
    return browser.tabs.captureVisibleTab();
  }

  async function performAction(action: IAction) {
    console.log("action => ", JSON.stringify(action));
    if (action.done) {
      return true;
    }
    if (action.navigate) {
      await browser.tabs.update({ url: action.navigate });
    }
    if (action.click) {
      for (const key of action.click.split("")) {
        await sendMessageToActiveTab({
          action: BROWSER_ACTIONS.PRESS_KEY,
          payload: { key },
        });
        await delay(100);
      }
    }
    if (action.type) {
      // Focus input field before typing
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: { key: "Escape" }, // Exit any vimium modes
      });
      await delay(200);

      for (const key of action.type.split("")) {
        await sendMessageToActiveTab({
          action: BROWSER_ACTIONS.PRESS_KEY,
          payload: { key },
        });
        await delay(50);
      }

      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: { key: "Enter" },
      });
    }
    return action.done || false;
  }

  async function focusActiveTab() {
    const [tab] = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (tab.id && tab.windowId) {
      await browser.windows.update(tab.windowId, { focused: true });
      await browser.tabs.update(tab.id, { active: true });
    }
  }
  // background.ts (Update startTask)
  async function startTask() {
    try {
      await focusActiveTab();
      await delay(1000); // Wait for vimium controls to appear

      // Scroll to top to ensure vimium controls are visible
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: { key: "gg" },
      });

      await delay(500);
      const screenshot = await captureScreenshot();

      // Add retry logic for API calls
      const MAX_RETRIES = 3;
      let retries = 0;

      const fetchWithRetry = async () => {
        try {
          const response = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              prompt: state.prompt,
              image: screenshot,
              previousActions: state.previousActions.slice(-3), // Track action history
            }),
          });

          if (!response.ok)
            throw new Error(`HTTP error! Status: ${response.status}`);
          return response.json();
        } catch (error) {
          if (retries++ < MAX_RETRIES) {
            await delay(2000 * retries);
            return fetchWithRetry();
          }
          throw error;
        }
      };

      const data = await fetchWithRetry();
      const taskCompleted = await performAction(data.generated_text);

      // Store action history
      state.previousActions = [
        ...(state.previousActions || []),
        data.generated_text,
      ].slice(-5); // Keep last 5 actions

      if (!taskCompleted) {
        // Wait for page stability
        await delay(3000);
        await startTask();
      }
    } catch (error) {
      console.error("Task failed:", error);
      // Implement error recovery logic here
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
