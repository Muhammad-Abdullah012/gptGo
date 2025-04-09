import { KEY_TO_CODE } from "@/constants/browserActions";
import { delay } from "./delay";

export const setInputValue = async (value: string) => {
  const activeElement = document.activeElement;
  if (
    activeElement instanceof HTMLInputElement ||
    activeElement instanceof HTMLTextAreaElement
  ) {
    activeElement.value = value;
    activeElement.dispatchEvent(new Event("input", { bubbles: true }));
    const enterEvent = new KeyboardEvent('keydown', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      which: 13,
      bubbles: true,
      cancelable: true
    });
    activeElement.dispatchEvent(enterEvent);
  } else {
    console.error("No active input or textarea element to set value");
  }
};

export const simulateKeyPress = async (key: string) => {
  // Ensure document has focus
  if (!document.hasFocus()) {
    window.focus();
    document.body.focus();
    await delay(50);
  }

  // Create both keydown and keyup events
  const keyDownEvent = new KeyboardEvent("keydown", {
    key,
    code: KEY_TO_CODE[key] ?? `Key${key.toUpperCase()}`,
    bubbles: true,
    cancelable: true,
  });

  const keyUpEvent = new KeyboardEvent("keyup", {
    key,
    code: KEY_TO_CODE[key] ?? `Key${key.toUpperCase()}`,
    bubbles: true,
    cancelable: true,
  });

  // Dispatch events with short delay between them
  document.dispatchEvent(keyDownEvent);
  await delay(50);
  document.dispatchEvent(keyUpEvent);
};
