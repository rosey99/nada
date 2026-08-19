//var conv = new showdown.Converter({ metadata: true });

class ChatApp {
  constructor() {
    // Configuration - Update these URLs to match your FastAPI server
    this.API_BASE_URL = "{{API_BASE_URL}}";

    //this.conv = new showdown.Converter({ metadata: true });
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
    //
    this.messagesContainer = document.getElementById("chatMessages");
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.typingIndicator = document.getElementById("typingIndicator");
    this.statusIndicator = document.getElementById("statusIndicator");
    this.clearHistoryBtn = document.getElementById("clearHistoryBtn");
    this.historyIndicator = document.getElementById("historyIndicator");
    this.themeSelector = document.getElementById("themeSelector");

    this.initializeEventListeners();
    this.updateHistoryIndicator();
    this.loadTheme();
  }

  initializeEventListeners() {
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.clearHistoryBtn.addEventListener("click", () => this.clearHistory());
    this.themeSelector.addEventListener("change", (e) =>
      this.changeTheme(e.target.value),
    );
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        // TODO remove this and allow multi-line strings
        //  needs tab/focus to send button instead?
        this.sendMessage();
      }
    });
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
  // A little helper ripped-off from da web
  truncateToLength(inputString, maxLength) {
    return inputString.length > maxLength
      ? inputString.substring(0, maxLength - 5) + ". . ."
      : inputString;
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;
    var startTime, endTime;
    // Add user message to chat UI
    this.addMessage(message, "user");
    this.messageInput.value = "";
    this.setInputEnabled(true);
    this.showTypingIndicator();
    startTime = new Date();
    try {
      const response = await this.callAgentAPI(message);
      endTime = new Date();
      let elapsedTime = endTime - startTime;
      this.hideTypingIndicator();
      this.addMessage(response.response, "assistant");
      this.addUsageData(response.usage, elapsedTime);
      //console.log("Got response: " + JSON.stringify(response));
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
  // Added by yours truly
  async getProviders() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/providers`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          //auth: "{{DEPENDS}}",
        },
      });
      console.log("adding providers");
      this.addProviderList(await response.text());
    } catch (error) {
      //this.hideTypingIndicator();
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    } finally {
      //this.setInputEnabled(true);
      //console.log("adding providers");
      //this.addProviderList(response.body);
    }
  }
  async getProvidersJSON() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/providers_json`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          //auth: "{{DEPENDS}}",
        },
      });
      console.log("adding providers json");
      let provObj = await response.json();
      this.providerData = provObj;
      this.addProvidersOptions(provObj);
    } catch (error) {
      //this.hideTypingIndicator();
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    } finally {
      //this.setInputEnabled(true);
      //console.log("adding providers");
      //this.addProviderList(response.body);
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
        const response = await fetch(
          `${this.API_BASE_URL}/agent/models_update`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              //auth: "{{DEPENDS}}",
            },
            body: JSON.stringify({
              provider_name: this.providerSelector.value,
              model_id: this.modelSelector.value,
            }),
          },
        );
        console.log("updating model");
        let provObj = await response.json();
        this.providerData = provObj;
        this.addProvidersOptions(provObj);
      } catch (error) {
        //this.hideTypingIndicator();
        this.addErrorMessage("Sorry, I encountered an error: " + error.message);
      } finally {
        //this.setInputEnabled(true);
        //console.log("adding providers");
        //this.addProviderList(response.body);
      }
    }
  }

  // TODO fix this up with an abstract select.clear/select.add
  addProvidersOptions(providers_obj) {
    if (this.providerSelector.options.length > 0) {
      Array.from(this.providerSelector.options).forEach((opt) => {
        this.providerSelector.remove(opt);
      });
    }
    for (var i = 0; i < providers_obj.length; i++) {
      const providerOpt = document.createElement("option");
      //providerDiv.className = "status-message";
      providerOpt.text = providers_obj[i].name;
      providerOpt.value = providers_obj[i].name;
      if (providers_obj[i].is_active) {
        //console.log("Found active provider: " + providerOpt.value);
        providerOpt.selected = true;
      }
      this.providerSelector.add(providerOpt);
      if (providerOpt.selected === true) {
        //console.log("Selected Provider: " + providers_obj[i].name);
        if (this.modelSelector.options.length > 0) {
          Array.from(this.modelSelector.options).forEach((opt) => {
            this.modelSelector.remove(opt);
          });
        }
        var is_selected = new Array();
        var is_loaded = new Array();
        for (var n = 0; n < providers_obj[i].models.length; n++) {
          const modelOpt = document.createElement("option");

          modelOpt.text = this.truncateToLength(
            providers_obj[i].models[n].id,
            45,
          );
          modelOpt.value = providers_obj[i].models[n].id;
          if (providers_obj[i].models[n].selected) {
            console.log("Found selected model: " + modelOpt.value);
            //modelOpt.selected = true;
            is_selected.push(modelOpt);
          }
          if (providers_obj[i].models[n].model_status === "loaded") {
            console.log("Found loaded model: " + modelOpt.value);
            //modelOpt.selected = true;
            is_loaded.push(modelOpt);
          }
          this.modelSelector.add(modelOpt);
        }
        //console.log("Providertop: " + providers_obj[i].name + " " + i);
        if (is_selected.length === 0) {
          // We have no selected model
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
        //console.log("Providerbotom: " + providers_obj[i].name + " " + i);
        var model_id = this.modelSelector.value;
        var provderName = this.providerSelector.value;
        //console.log("Provider: " + providers_obj[i].name);
        //console.log("Providersel: " + provderName);
        //console.log("Model: " + model_id);

        for (var ii = 0; ii < providers_obj[i].models.length; ii++) {
          //console.log("Model2: " + providers_obj[i].models[ii].id);
          //console.log("Provider2: " + providers_obj[i].name);
          if (providers_obj[i].models[ii].id === model_id) {
            //console.log("Model3: " + providers_obj[i].models[ii].id);
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

    //this.scrollToBottom();
  }

  addUsageData(usage_obj, elapsed_time) {
    var content = "";
    Object.keys(usage_obj).forEach((key) => {
      content += `<p>${key}: ${usage_obj[key]}</p>`;
    });
    content += `<p>Elapsed time: ${(elapsed_time /= 1000)} seconds.`;
    //const usageDiv = document.createElement("div");
    //usageDiv.className = "metrics-message";
    this.metricsContainer.innerHTML = content;
    //this.metricsContainer.appendChild(usageDiv);
    //this.scrollToBottom();
  }
  addProviderList(content) {
    const providerDiv = document.createElement("div");
    providerDiv.className = "status-message";
    providerDiv.innerHTML = content;
    this.providersList.appendChild(providerDiv);
    //this.scrollToBottom();
  }
  async callAgentAPI(message) {
    const response = await fetch(`${this.API_BASE_URL}/agent/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        //auth: "{{DEPENDS}}",
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
    messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(content)}
            </div>
        `;
    this.messagesContainer.appendChild(messageDiv);
    this.scrollToBottom();
  }

  addErrorMessage(content) {
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.textContent = content;
    this.messagesContainer.appendChild(errorDiv);
    this.scrollToBottom();
  }

  formatMessage(content) {
    // Basic formatting - convert line breaks and make links clickable
    //const html = this.conv(content);
    const html = marked.parse(content);
    return html;
    //return content
    //  .replace(/\n/g, "<br>")
    //  .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
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
      this.messagesContainer.appendChild(initialMessage.cloneNode(true));
    }

    // Update history indicator
    this.updateHistoryIndicator();

    // Show confirmation
    this.addMessage(
      "✨ Conversation history cleared! Starting fresh.",
      "assistant",
    );
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
