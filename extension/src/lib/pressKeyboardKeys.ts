import { KEY_TO_CODE } from "@/constants/browserActions";
import { delay } from "./delay";

// content.ts (Update pressKey function)
export const pressKey = async (key: string) => {
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
  await new Promise((resolve) => setTimeout(resolve, 50));
  document.dispatchEvent(keyUpEvent);
};
