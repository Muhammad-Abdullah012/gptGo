import { IAction } from "@/interfaces";

export const state = $state({
    prompt: "",
    previousActions: [] as IAction[],
    lastScreenshotTime: 0,
    isProcessing: false
  });