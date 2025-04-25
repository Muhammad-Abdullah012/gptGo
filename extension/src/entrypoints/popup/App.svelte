<script lang="ts">
  import { onMount } from "svelte";
  import { BROWSER_ACTIONS } from "@/constants/browserActions";
  import { checkIfExtensionIsAllowed } from "@/lib/isExtensionAllowed";

  // State variables
  let userInput = ""; // Stores the user's input
  let isLoading = false; // Indicates if the API request is in progress
  let message = ""; // Feedback message for the user
  let isExtensionAllowed = false;

  onMount(() => {
    checkIfExtensionIsAllowed()
      .then((allowed) => {
        isExtensionAllowed = allowed;
      })
      .catch((error) => {
        console.error("Error checking if extension is allowed:", error);
      });
  });
  // Function to handle form submission
  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!userInput.trim()) {
      message = "Input cannot be empty.";
      return;
    }

    isLoading = true;
    message = ""; // Clear previous messages
    console.log("isExtensionAllowed => ", isExtensionAllowed);
    if (!isExtensionAllowed) {
      browser.tabs.update({ url: "https://www.google.com" });
      isExtensionAllowed = true;
    }

    if (isExtensionAllowed) {
      browser.runtime
        .sendMessage({
          action: BROWSER_ACTIONS.START_TASK,
          payload: { prompt: userInput },
        })
        .catch((error) => {
          console.error("Error sending message to background script:", error);
          message = "Error sending message to background script.";
        })
        .finally(() => {
          isLoading = false;
        });
      window.close();
    }
    // const interval = setInterval(handleNextClick, 2000);

    // userInput = ""; // Clear the input field
  }

  async function handleNextClick() {
    console.log("running next click");
    browser.runtime
      .sendMessage({
        action: BROWSER_ACTIONS.NEXT,
      })
      .catch((error) => {
        console.error("Error sending message to background script:", error);
        message = "Error sending message to background script.";
      })
      .finally(() => {
        isLoading = false;
      });
  }
</script>

<main>
  <div class="card">
    <h2 class="card-title">Enter your task</h2>
    <form onsubmit={handleSubmit}>
      <input
        type="text"
        bind:value={userInput}
        placeholder="Enter your input here"
        class="input-field"
      />
      <button type="submit" disabled={isLoading} class="submit-button">
        {isLoading ? "Sending..." : "Submit"}
      </button>
      <button type="button" onclick={handleNextClick} class="submit-button">
        Next
      </button>
    </form>
    {#if message}
      <p class="message">{message}</p>
    {/if}
  </div>
</main>

<style>
  /* General Reset */
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  /* Main Container */
  main {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f9f9f9;
    color: #333;
    padding: 1em;
    border-radius: 8px;
    max-width: 400px;
    margin: auto;
    box-shadow:
      0 4px 6px rgba(0, 0, 0, 0.1),
      0 1px 3px rgba(0, 0, 0, 0.06);
  }

  /* Header */
  .header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 1em;
  }

  .header h1 {
    font-size: 1.5em;
    font-weight: 600;
    margin-top: 0.5em;
    color: #54bc4a;
  }

  /* Logos */
  .logo {
    height: 4em;
    margin: 0.5em;
    transition: transform 0.3s ease-in-out;
  }

  .logo:hover {
    transform: scale(1.1);
  }

  .logo.svelte:hover {
    filter: drop-shadow(0 0 1em #ff3e00aa);
  }

  /* Card */
  .card {
    background: white;
    padding: 1.5em;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-top: 1em;
  }

  .card-title {
    font-size: 1.2em;
    font-weight: 600;
    margin-bottom: 1em;
    color: #444;
  }

  /* Input Field */
  .input-field {
    width: 100%;
    padding: 0.75em;
    margin-bottom: 1em;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1em;
    transition: border-color 0.3s ease;
  }

  .input-field:focus {
    border-color: #54bc4a;
    outline: none;
  }

  /* Submit Button */
  .submit-button {
    width: 100%;
    padding: 0.75em;
    background-color: #54bc4a;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s ease;
    margin-bottom: 10px;
  }

  .submit-button:hover:not(:disabled) {
    background-color: #46a33d;
  }

  .submit-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }

  /* Message */
  .message {
    margin-top: 1em;
    font-size: 0.9em;
    text-align: center;
    color: #555;
  }

  .message.success {
    color: #28a745;
  }

  .message.error {
    color: #dc3545;
  }

  /* Footer */
  .footer {
    margin-top: 1em;
    text-align: center;
    font-size: 0.85em;
    color: #888;
  }
</style>
