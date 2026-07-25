/**
 * Modern AI Chat Application
 * A clean, modern chat interface for AI agent interactions
 */

class ChatApp {
  constructor() {
    // Conversation history
    this.conversationHistory = [];

    // Theme state (default to dark)
    this.currentTheme = "dark";

    // DOM elements
    this.providerData = null;
    this.providerSelector = document.getElementById("providersSelect");
    this.modelSelector = document.getElementById("modelSelect");
    this.metricsContainer = document.getElementById("queryMetrics");
    this.providersList = document.getElementById("providersList");
    this.outputSpan = document.getElementById("outputSpan");
    this.inputSpan = document.getElementById("inputSpan");
    this.messagesContainer = document.getElementById("chatMessages");
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.typingIndicator = document.getElementById("typingIndicator");
    this.statusIndicator = document.getElementById("statusIndicator");
    this.clearHistoryBtn = document.getElementById("clearHistoryBtn");
    this.deleteGroupBtn = document.getElementById("deleteGroupBtn");
    this.deleteDropdownContent = document.getElementById("deleteDropdownContent");
    this.historyIndicator = document.getElementById("historyIndicator");
    this.themeSelector = document.getElementById("themeSelector");

    this.initializeEventListeners();
    this.updateHistoryIndicator();
    this.loadTheme();
  }

  initializeEventListeners() {
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.clearHistoryBtn.addEventListener("click", () => this.clearHistory());
    this.deleteGroupBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleDeleteDropdown();
    });
    // Close dropdown when clicking outside
    document.addEventListener("click", () => this.closeDeleteDropdown());
    this.themeSelector.addEventListener("change", (e) =>
      this.changeTheme(e.target.value),
    );
    // this.messageInput.addEventListener("keypress", (e) => {
    //   if (e.key === "Enter") {
    //     this.sendMessage();
    //   }
    // });
    this.modelSelector.addEventListener("change", () =>
      this.updateModel(this.modelSelector),
    );
    this.providerSelector.addEventListener("change", () =>
      this.updateModel(this.providerSelector),
    );
  }

  changeTheme(theme) {
    this.currentTheme = theme;
    document.body.className = theme;
    this.themeSelector.value = theme;
    this.saveTheme();
  }

  saveTheme() {
    // Store theme preference in memory (since localStorage isn't available)
    window.currentTheme = this.currentTheme;
  }

  loadTheme() {
    // Load theme from memory if available, otherwise use dark as default
    if (window.currentTheme) {
      this.currentTheme = window.currentTheme;
    } else {
      this.currentTheme = "dark";
    }
    document.body.className = this.currentTheme;
    this.themeSelector.value = this.currentTheme;
  }

  // Helper to truncate long text
  truncateToLength(inputString, maxLength) {
    return inputString.length > maxLength
      ? inputString.substring(0, maxLength - 5) + "..."
      : inputString;
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;

    // Add user message to chat UI
    this.addMessage(message, "user");
    this.messageInput.value = "";
    this.setInputEnabled(true);
    this.showTypingIndicator();

    const startTime = new Date();
    try {
      const response = await this.callAgentAPI(message);
      const endTime = new Date();
      const elapsedTime = endTime - startTime;

      this.hideTypingIndicator();
      this.addMessage(response.response, "assistant");
      this.addUsageData(response.usage, elapsedTime);
      // Update conversation history from server response
      if (response.history) {
        this.conversationHistory = response.history;
        this.updateHistoryIndicator();
      }
    } catch (error) {
      this.hideTypingIndicator();
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    } finally {
      this.setInputEnabled(true);
      this.messageInput.focus();
    }
  }

  async getProviders() {
    try {
      const response = await fetch("/providers", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Adding providers");
      this.addProviderList(await response.text());
    } catch (error) {
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    }
  }

  async getProvidersJSON() {
    try {
      const response = await fetch("/providers_json", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Adding providers JSON");
      let provObj = await response.json();
      this.providerData = provObj;
      this.addProvidersOptions(provObj);
    } catch (error) {
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    }
  }

  async updateModel(elem) {
    if (elem === this.providerSelector) {
      console.log("Provider changed");
      let provName = this.providerSelector.value;
      for (var i = 0; i < this.providerData.length; i++) {
        if (this.providerData[i].name != provName) {
          this.providerData[i].is_active = false;
        } else {
          this.providerData[i].is_active = true;
        }
      }
      this.addProvidersOptions(this.providerData);
    }

    if (this.modelSelector.value) {
      try {
        const response = await fetch("/agent/models_update", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            provider_name: this.providerSelector.value,
            model_id: this.modelSelector.value,
          }),
        });
        console.log("Updating model");
        let provObj = await response.json();
        this.providerData = provObj;
        this.addProvidersOptions(provObj);
      } catch (error) {
        this.addErrorMessage("Sorry, I encountered an error: " + error.message);
      }
    }
  }

  addProvidersOptions(providers_obj) {
    // Clear existing provider options
    if (this.providerSelector.options.length > 0) {
      Array.from(this.providerSelector.options).forEach((opt) => {
        this.providerSelector.remove(opt);
      });
    }

    for (var i = 0; i < providers_obj.length; i++) {
      const providerOpt = document.createElement("option");
      providerOpt.text = providers_obj[i].name;
      providerOpt.value = providers_obj[i].name;
      if (providers_obj[i].is_active) {
        providerOpt.selected = true;
      }
      this.providerSelector.add(providerOpt);

      if (providerOpt.selected === true) {
        // Clear existing model options
        if (this.modelSelector.options.length > 0) {
          Array.from(this.modelSelector.options).forEach((opt) => {
            this.modelSelector.remove(opt);
          });
        }

        var is_selected = [];
        var is_loaded = [];

        for (var n = 0; n < providers_obj[i].models.length; n++) {
          const modelOpt = document.createElement("option");

          modelOpt.text = this.truncateToLength(
            providers_obj[i].models[n].id,
            45,
          );
          modelOpt.value = providers_obj[i].models[n].id;

          if (providers_obj[i].models[n].selected) {
            is_selected.push(modelOpt);
          }
          if (providers_obj[i].models[n].model_status === "loaded") {
            is_loaded.push(modelOpt);
          }
          this.modelSelector.add(modelOpt);
        }

        // Select loaded model if no selected model exists
        if (is_selected.length === 0) {
          for (var j = 0; j < is_loaded.length; j++) {
            is_loaded[j].selected = true;
            console.log("Selecting loaded model: " + is_loaded[j].value);
          }
        } else {
          for (var j = 0; j < is_selected.length; j++) {
            is_selected[j].selected = true;
            console.log(
              "Selecting pre-selected model: " + is_selected[j].value,
            );
          }
        }

        // Update input/output spans
        for (var ii = 0; ii < providers_obj[i].models.length; ii++) {
          if (providers_obj[i].models[ii].id === this.modelSelector.value) {
            let inputs = Array.from(
              providers_obj[i].models[ii].architecture.input_modalities,
            );
            let outputs = Array.from(
              providers_obj[i].models[ii].architecture.output_modalities,
            );
            this.inputSpan.innerHTML = inputs.join(", ");
            this.outputSpan.innerHTML = outputs.join(", ");
          }
        }
      }
    }
  }

  addUsageData(usage_obj, elapsed_time) {
    var content = "";
    Object.keys(usage_obj).forEach((key) => {
      if (key === "details") {
        Object.keys(usage_obj[key]).forEach((detail_key) => {
          content += `<p>${detail_key}: ${usage_obj[key][detail_key]}</p>`;
        });
      } else {
        content += `<p>${key}: ${usage_obj[key]}</p>`;
      }
    });
    content += `<p>Elapsed time: ${(elapsed_time / 1000).toFixed(2)} seconds.</p>`;
    this.metricsContainer.innerHTML = content;
  }

  addProviderList(content) {
    const providerDiv = document.createElement("div");
    providerDiv.className = "status-message";
    providerDiv.innerHTML = content;
    this.providersList.appendChild(providerDiv);
  }

  async callAgentAPI(message) {
    const response = await fetch("/agent/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: message,
        history: this.conversationHistory,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  addMessage(content, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    const msgIndex = this.conversationHistory.length;
    messageDiv.setAttribute("data-message-index", msgIndex);
    messageDiv.innerHTML = `
      <button class="message-delete-btn" title="Delete this message" onclick="app.deleteMessage(${msgIndex}, event)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
      <div class="message-content">
        ${this.formatMessage(content)}
      </div>
    `;
    this.messagesContainer.appendChild(messageDiv);
    this.scrollToBottom();
  }

  addErrorMessage(content) {
    const msgIndex = this.conversationHistory.length;
    const errorDiv = document.createElement("div");
    errorDiv.className = "message error-message";
    errorDiv.setAttribute("data-message-index", msgIndex);
    errorDiv.innerHTML = `
      <button class="message-delete-btn" title="Delete this message" onclick="app.deleteMessage(${msgIndex}, event)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
      <div class="message-content">
        ${content}
      </div>
    `;
    this.messagesContainer.appendChild(errorDiv);
    this.scrollToBottom();
  }

  formatMessage(content) {
    // Use marked.js for markdown parsing
    return marked.parse(content);
  }

  showTypingIndicator() {
    this.typingIndicator.style.display = "block";
    this.scrollToBottom();
  }

  hideTypingIndicator() {
    this.typingIndicator.style.display = "none";
  }

  setInputEnabled(enabled) {
    this.messageInput.disabled = !enabled;
    this.sendButton.disabled = !enabled;
  }

  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  clearHistory() {
    // Clear conversation history
    this.conversationHistory = [];

    // Clear chat messages (keep initial greeting)
    const initialMessage =
      this.messagesContainer.querySelector(".message.assistant");
    this.messagesContainer.innerHTML = "";
    if (initialMessage) {
      const cloned = initialMessage.cloneNode(true);
      // Reset the data-message-index on the cloned element
      cloned.setAttribute("data-message-index", "0");
      const deleteBtn = cloned.querySelector(".message-delete-btn");
      if (deleteBtn) {
        deleteBtn.setAttribute("onclick", "app.deleteMessage(0, event)");
      }
      this.messagesContainer.appendChild(cloned);
    }

    // Update history indicator
    this.updateHistoryIndicator();

    // Show confirmation
    this.addMessage(
      "✨ Conversation history cleared! Starting fresh.",
      "assistant",
    );
  }

  // --- Delete Group Dropdown ---
  toggleDeleteDropdown() {
    this.deleteDropdownContent.classList.toggle("show");
  }

  closeDeleteDropdown() {
    this.deleteDropdownContent.classList.remove("show");
  }

  // --- Delete Single Message ---
  async deleteMessage(index, event) {
    if (event) {
      event.stopPropagation();
    }
    if (index < 0 || index >= this.conversationHistory.length) return;

    // Find and animate the message element
    const messageEl = this.messagesContainer.querySelector(
      `[data-message-index="${index}"]`,
    );
    if (messageEl) {
      messageEl.classList.add("deleting");
      await new Promise((resolve) => setTimeout(resolve, 300));
      messageEl.remove();
    }

    // Remove from history
    this.conversationHistory.splice(index, 1);
    this.updateMessageIndices();
    this.updateHistoryIndicator();

    // Sync with server
    try {
      await fetch("/agent/history", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ indices: [index] }),
      });
    } catch (error) {
      console.error("Failed to sync deletion with server:", error);
    }
  }

  // --- Delete Messages by Role ---
  async deleteMessagesByRole(role) {
    this.closeDeleteDropdown();

    // Find indices of messages with the given role (reverse order)
    const indicesToDelete = [];
    for (let i = this.conversationHistory.length - 1; i >= 0; i--) {
      if (this.conversationHistory[i].role === role) {
        indicesToDelete.push(i);
      }
    }

    if (indicesToDelete.length === 0) return;

    // Animate and remove each message
    for (const idx of indicesToDelete) {
      const messageEl = this.messagesContainer.querySelector(
        `[data-message-index="${idx}"]`,
      );
      if (messageEl) {
        messageEl.classList.add("deleting");
        await new Promise((resolve) => setTimeout(resolve, 100));
        messageEl.remove();
      }
    }

    // Filter history to remove messages with that role
    this.conversationHistory = this.conversationHistory.filter(
      (msg) => msg.role !== role,
    );
    this.updateMessageIndices();
    this.updateHistoryIndicator();

    // Sync with server
    try {
      await fetch("/agent/history", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
    } catch (error) {
      console.error("Failed to sync deletion with server:", error);
    }

    const roleLabel = role === "user" ? "your" : "AI response";
    this.addMessage(
      `✨ Deleted all ${roleLabel}.`,
      "assistant",
    );
  }

  // --- Delete Last N Messages (pairs) ---
  async deleteLastMessages(n) {
    this.closeDeleteDropdown();

    if (n <= 0) return;

    const totalToDelete = n * 2; // user + assistant pairs
    if (totalToDelete >= this.conversationHistory.length) {
      // If deleting more than half the history, just clear all
      this.clearHistory();
      return;
    }

    const startIdx = this.conversationHistory.length - totalToDelete;
    const indicesToDelete = [];
    for (let i = startIdx; i < this.conversationHistory.length; i++) {
      indicesToDelete.push(i);
    }

    // Animate and remove each message (reverse order for smooth animation)
    for (let i = indicesToDelete.length - 1; i >= 0; i--) {
      const idx = indicesToDelete[i];
      const messageEl = this.messagesContainer.querySelector(
        `[data-message-index="${idx}"]`,
      );
      if (messageEl) {
        messageEl.classList.add("deleting");
        await new Promise((resolve) => setTimeout(resolve, 80));
        messageEl.remove();
      }
    }

    // Truncate history
    this.conversationHistory = this.conversationHistory.slice(0, startIdx);
    this.updateMessageIndices();
    this.updateHistoryIndicator();

    // Sync with server
    try {
      await fetch("/agent/history", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ last_n: n }),
      });
    } catch (error) {
      console.error("Failed to sync deletion with server:", error);
    }

    this.addMessage(
      `✨ Deleted last ${n} conversation(s).`,
      "assistant",
    );
  }

  // --- Update data-message-index attributes after deletion ---
  updateMessageIndices() {
    const messages = this.messagesContainer.querySelectorAll(".message");
    messages.forEach((msg, i) => {
      msg.setAttribute("data-message-index", i);
      // Update the delete button's onclick
      const deleteBtn = msg.querySelector(".message-delete-btn");
      if (deleteBtn) {
        deleteBtn.setAttribute("onclick", `app.deleteMessage(${i}, event)`);
      }
    });
  }

  updateHistoryIndicator() {
    const messageCount = this.conversationHistory.length;
    this.historyIndicator.textContent = `History: ${messageCount} messages`;
  }
}

// Initialize the chat app when the page loads
document.addEventListener("DOMContentLoaded", () => {
  const app = new ChatApp();
  app.getProviders();
  app.getProvidersJSON();
});
