import { BROWSER_ACTIONS, KEY_TO_CODE } from "@/constants/browserActions";
import { IAction } from "@/interfaces";
import { delay } from "@/lib/delay";
import { state } from "@/store/store.svelte";

export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
  // Function to capture the active tab's screenshot
  async function captureScreenshot(): Promise<string> {
    return browser.tabs.captureVisibleTab();
  }

  async function performAction(action: IAction) {
    console.log("action => ", JSON.stringify(action));
    if (action.navigate) {
      await browser.tabs.update({ url: action.navigate });
    }
    if (action.click) {
      console.log("key to code => ", KEY_TO_CODE[action.click]);
      if (KEY_TO_CODE[action.click]) {
        await sendMessageToActiveTab({
          action: BROWSER_ACTIONS.PRESS_KEY,
          payload: { key: KEY_TO_CODE[action.click] },
        });
      } else {
        for (const key of action.click.split("")) {
          await sendMessageToActiveTab({
            action: BROWSER_ACTIONS.PRESS_KEY,
            payload: { key },
          });
        }
      }
    }
    if (action.type) {
      // Focus input field before typing
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.TYPE,
        payload: { text: action.type },
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

  async function waitForActiveTabToLoad(timeoutMs: number = 10000): Promise<void> {
    const [tab] = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (!tab) {
      throw new Error("No active tab found");
    }

    if (tab.status === "complete") {
      return;
    }

    // Create a promise that resolves when the tab finishes loading
    const loadingPromise = new Promise<void>((resolve, reject) => {
      const listener = (tabId: number, changeInfo: any) => {
        if (tabId === tab.id && changeInfo.status === "complete") {
          cleanup();
          resolve();
        }
      };

      const errorListener = (closedTabId: number) => {
        if (closedTabId === tab.id) {
          cleanup();
          reject(new Error("Tab closed before loading completed"));
        }
      };

      const cleanup = () => {
        browser.tabs.onUpdated.removeListener(listener);
        browser.tabs.onRemoved.removeListener(errorListener);
      };

      // Add listeners
      browser.tabs.onUpdated.addListener(listener);
      browser.tabs.onRemoved.addListener(errorListener);

      browser.tabs.get(tab.id!)
        .then((currentTab) => {
          if (currentTab.status === "complete") {
            cleanup();
            resolve();
          }
        })
        .catch(() => { /* Tab was closed, handled by errorListener */ });
    });

    // Add a timeout mechanism
    const timeoutPromise = new Promise<void>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Timeout: Tab did not complete loading within ${timeoutMs}ms`));
      }, timeoutMs);
    });

    await Promise.race([loadingPromise, timeoutPromise]);
  }
  // background.ts (Update startTask)
  async function startTask() {
    try {
      console.log("******* startTask function called *******");
      await focusActiveTab();
      await waitForActiveTabToLoad();
      // Scroll to top to ensure vimium controls are visible
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: { key: "Escape" },
      });
      await sendMessageToActiveTab({
        action: BROWSER_ACTIONS.PRESS_KEY,
        payload: { key: "f" },
      });

      await delay(1000); // Wait for vimium controls to appear
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
        await waitForActiveTabToLoad();
        await delay(1000);
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

    if (!tab?.id) {
      throw new Error('No active tab found');
    }

    console.log("tab => ", tab.id, ", tab status => ", tab.status, ", payload => ", JSON.stringify(payload));
    if (tab.status !== "complete") {
      await waitForActiveTabToLoad();
      console.log("tab status changed to complete");
    }
    try {
      await delay(1000);
      await browser.tabs.sendMessage(tab.id, payload);
    } catch (error) {
      console.error('Failed to send message to tab:', error);
      throw new Error('Message sending failed - content script might not be loaded');
    }
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
