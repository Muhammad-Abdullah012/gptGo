import { captureScreenshot, focusActiveTab, performAction, sendMessageToActiveTab, waitForActiveTabToLoad } from "@/lib/backgroundHelpers";
import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { state } from "@/store/store.svelte";
import { delay } from "@/lib/delay";

export const startTask = async () => {
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