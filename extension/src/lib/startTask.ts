import { captureScreenshot, focusActiveTab, getCurrentTabHtml, getCurrentTabUrl, performAction, sendMessageToActiveTab, waitForActiveTabToLoad } from "@/lib/backgroundHelpers";
import { BROWSER_ACTIONS } from "@/constants/browserActions";
import { state } from "@/store/store.svelte";
import { delay } from "@/lib/delay";
import { closeSocket, connectSocket, sendMessage } from "./socket";

export const startTask = async () => {
    try {
        console.log("******* startTask function called *******");
        await focusActiveTab();
        await waitForActiveTabToLoad();
        // Scroll to top to ensure vimium controls are visible
        // await sendMessageToActiveTab({
        //     action: BROWSER_ACTIONS.PRESS_KEY,
        //     payload: { key: "Escape" },
        // });
        // await sendMessageToActiveTab({
        //     action: BROWSER_ACTIONS.PRESS_KEY,
        //     payload: { key: "f" },
        // });

        await delay(1000); // Wait for vimium controls to appear
        const screenshot = await captureScreenshot();

        // Add retry logic for API calls
        const MAX_RETRIES = 3;
        let retries = 0;

        const currentUrl = await getCurrentTabUrl();
        // const currentPageHtml = await getCurrentTabHtml();

        // await connectSocket((data) => {
        //     console.log("[WS] Update:", data);
        //     // Support stop message
        //     if (data?.javascript?.done) {
        //         console.log("[WS] Task complete");
        //         closeSocket()
        //         return;
        //     }

        //     if (data?.type === "run_js") {
        //         sendMessageToActiveTab({
        //             action: BROWSER_ACTIONS.RUN_CODE,
        //             payload: data?.javascript,
        //         }).then(() => {
        //             sendMessage({
        //                 type: "dom_update",
        //                 query: state.prompt,
        //                 image: screenshot,
        //                 url: currentUrl,
        //                 html: currentPageHtml.html,
        //                 // previous_actions: state.previousActions.slice(-3),
        //             });
        //         });
        //     }

        // });

        // sendMessage({
        //     type: "start",
        //     query: state.prompt,
        //     image: screenshot,
        //     url: currentUrl,
        //     html: currentPageHtml.html,
        //     // previous_actions: state.previousActions.slice(-3),
        // });
        const fetchWithRetry = async () => {
            try {
                const currentPageHtml = await getCurrentTabHtml();

                console.log("request body  => ", JSON.stringify({
                    prompt: state.prompt,
                    // image: screenshot,
                    current_url: currentUrl,
                    current_page_html: currentPageHtml.html,
                    previous_actions: state.previousActions.slice(-3), // Track action history
                }));


                const response = await fetch("http://localhost:8000/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        prompt: state.prompt,
                        image: screenshot,
                        currentUrl,
                        currentPageHtml: currentPageHtml.html,
                        previousActions: state.previousActions.slice(-3), // Track action history
                    }),
                });

                if (!response.ok)
                    throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            } catch (error) {
                if (retries++ < MAX_RETRIES) {
                    await delay(4000 * retries);
                    console.log("Retrying fetch... due to error => ", error);
                    return fetchWithRetry();
                }
                throw error;
            }
        };
        await delay(1000);
        const data = await fetchWithRetry();
        console.log("response => ", data);
        await sendMessageToActiveTab({
            action: BROWSER_ACTIONS.RUN_CODE,
            payload: data,
        })


        // // const taskCompleted = await performAction(data.generated_text);
        // let taskCompleted = false;
        // // Store action history
        state.previousActions = [
            ...(state.previousActions || []),
            data.generated_text,
        ].slice(-5); // Keep last 5 actions
        console.log("data.done => ", data?.generated_text?.done)
        if (!data?.generated_text?.estimated_completion) {
            await waitForActiveTabToLoad();
            await delay(1000);
            await startTask();

        }
    } catch (error) {
        console.error("Task failed:", error);
        if (error instanceof Error)
            console.error("error stack => ", error.stack)
        // Implement error recovery logic here
    }
}