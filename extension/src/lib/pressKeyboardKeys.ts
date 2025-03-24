export const pressKey = (key: string) => {
  const event = new KeyboardEvent("keydown", {
    key,
    code: `Key${key.toUpperCase()}`,
    location: 0,
    repeat: false,
    isComposing: false,
    bubbles: true,
    cancelable: true,
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    metaKey: false,
  });
  document.dispatchEvent(event);
};
