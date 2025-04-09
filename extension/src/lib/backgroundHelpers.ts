import { BROWSER_ACTIONS, KEY_TO_CODE } from "@/constants/browserActions";
import { IAction } from "@/interfaces";
import { delay } from "./delay";

export const captureScreenshot = async (): Promise<string> => {
    return browser.tabs.captureVisibleTab();
}

export const focusActiveTab = async () => {
    const [tab] = await browser.tabs.query({
        active: true,
        currentWindow: true,
    });
    if (tab.id && tab.windowId) {
        await browser.windows.update(tab.windowId, { focused: true });
        await browser.tabs.update(tab.id, { active: true });
    }
}

export const waitForActiveTabToLoad = async (timeoutMs: number = 10000): Promise<void> => {
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

export const sendMessageToActiveTab = async (payload: object) => {
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



export const performAction = async (action: IAction) => {
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