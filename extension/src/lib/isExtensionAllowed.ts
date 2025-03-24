export const checkIfExtensionIsAllowed = async () => {
  try {
    const [tab] = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });

    // Check if the tab URL is accessible by extensions
    return !(
      !tab.url ||
      tab.url.startsWith("chrome://") ||
      tab.url.startsWith("about:")
    );
  } catch (error) {
    return false;
  }
};
