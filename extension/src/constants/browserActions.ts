export const BROWSER_ACTIONS = {
  PRESS_KEY: "PRESS_KEY",
  TYPE: "TYPE",
  START_TASK: "START_TASK",
  NEXT: "NEXT",
  CONTENT_SCRIPT_READY: "CONTENT_SCRIPT_READY",
  PING: "PING",
  GET_HTML: "GET_HTML",
  RUN_CODE: "RUN_CODE"
};

export const KEY_TO_CODE: { [key: string]: string } = {
  Escape: "Escape",
  Enter: "Enter",
  Tab: "Tab",
  ArrowUp: "ArrowUp",
  ArrowDown: "ArrowDown",
  ArrowLeft: "ArrowLeft",
  ArrowRight: "ArrowRight",
};
