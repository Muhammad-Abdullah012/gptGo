export const getCleanedHTML = (body: string): string => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(body, 'text/html');
    const clonedBody = doc.body;

    // Tags to remove
    const junkTags = ['path', "line"];

    junkTags.forEach(tag => {
        const elements = clonedBody.querySelectorAll(tag);
        elements.forEach(el => el.remove());
    });

    // Remove inline styles and event handlers
    const allElements = clonedBody.querySelectorAll('*');
    allElements.forEach(el => {
        el.removeAttribute('style');
        el.removeAttribute("class");
        el.removeAttribute("src");
        Array.from(el.attributes).forEach(attr => {
            if (attr.name.startsWith('on')) el.removeAttribute(attr.name);
        });
    });

    return clonedBody.innerHTML;
}

/**
 * Returns the HTML of all elements currently visible in the viewport.
 * @returns A string of concatenated outerHTML of visible elements.
 */
export const getVisibleClickableHTML = (): string => {
    const clickableSelectors = [
        'a[href]',
        'button',
        'input',
        'input[type="button"]',
        'input[type="submit"]',
        'div[role="button"]',
        '[onclick]',
        '[role="link"]',
        '[role="button"]'
    ];

    const elements = Array.from(document.querySelectorAll<HTMLElement>(clickableSelectors.join(',')));

    const isVisible = (el: HTMLElement): boolean => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return (
            rect.width > 0 &&
            rect.height > 0 &&
            rect.bottom > 0 &&
            rect.right > 0 &&
            rect.top < window.innerHeight &&
            rect.left < window.innerWidth &&
            style.visibility !== 'hidden' &&
            style.display !== 'none'
        );
    };

    const visibleElements = elements.filter(isVisible);

    const isVisibleOrPartiallyVisible = (el: HTMLElement): boolean => {
        const style = window.getComputedStyle(el);
        return style.visibility !== 'hidden' && style.display !== 'none';
    };

    const dialogs = Array.from(document.querySelectorAll<HTMLElement>('[role="dialog"]'))
        .filter(isVisibleOrPartiallyVisible);

    const wrapper = document.createElement('div');
    visibleElements.forEach(el => wrapper.appendChild(el.cloneNode(true)));

    dialogs.forEach(dialog => wrapper.appendChild(dialog.cloneNode(true)));

    return wrapper.innerHTML;
};
