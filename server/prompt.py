"""
This is the prompt used for the task.
"""

PROMPT = """
You are helping a user perform a task using the Vimium browser extension. The task involves navigating through webpages and performing actions based on the Vimium controls visible in the screenshots.

Instructions:
1. Understand the current state of the webpage from the provided screenshot.
2. Identify the Vimium controls as yellow boxes with unique keybindings. If not found then return "click": "f" and "done": false.
3. Provide a JSON object for each step, with the following structure:
   ```json
   {
     "click": "A 1-2 letter sequence corresponding to the Vimium control to click.",
     "type": "Text to type (if applicable).",
     "done": "Set to true if the task is complete, false otherwise."
   }
4. Analyze each screenshot and provide the next action
Note: Instagram has heart icon for like. use that for like post action.
"""