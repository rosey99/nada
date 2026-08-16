/**
 * Modern AI Chat Application
 * A clean, modern chat interface for AI agent interactions
 */

class ChatApp {
  constructor() {
    // Conversation history
    this.conversationHistory = [];
    this.selectedHistory = [];
    this.selectedFiles = [];
    this.pendingContextObj = {};
    this.fileInput = document.getElementById("fileInput");
    this.attachButton = document.getElementById("attachButton");
    this.fileListing = document.getElementById("fileListing");
    // Theme state (default to minimal)
    this.currentTheme = "minimal";

    // DOM elements
    this.providerData = null;
    this.userContextData = null;
    this.userThreadsData = null;
    this.pendingThreadsData = null;
    this.selectedUserThread = null;
    this.providersContent = document.getElementById("providersContent");
    this.providerSelector = document.getElementById("providersSelect");
    this.modelSelector = document.getElementById("modelSelect");
    this.metricsContainer = document.getElementById("queryMetrics");
    this.providersList = document.getElementById("providersList");
    this.providerContent = document.getElementById("providersContent");
    this.outputSpan = document.getElementById("outputSpan");
    this.inputSpan = document.getElementById("inputSpan");
    this.messagesContainer = document.getElementById("chatMessages");
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.typingIndicator = document.getElementById("typingIndicator");
    this.statusIndicator = document.getElementById("statusIndicator");
    this.clearHistoryBtn = document.getElementById("clearHistoryBtn");
    this.historyIndicator = document.getElementById("historyIndicator");
    this.themeSelector = document.getElementById("themeSelector");
    this.toggleAll = document.getElementById("toggleAllMessages");
    this.contextSaveButton = document.getElementById("contextSaveButton");
    this.contextAddButton = document.getElementById("contextAddButton");
    this.newContextInput = document.getElementById("newContextIn");
    this.existingContextSel = document.getElementById("existingContext");
    this.newContextKey = document.getElementById("newContextKey");
    this.newContextVal = document.getElementById("newContextVal");
    this.newContextItemsDiv = document.getElementById("newContextItems");
    this.userContextDiv = document.getElementById("userContext");
    this.userThreadsDiv = document.getElementById("userThreads");

    this.initializeEventListeners();
    this.updateHistoryIndicator();
    this.loadTheme();
    // reset selector toggle
    this.toggleAll.checked = false;
  }

  initializeEventListeners() {
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.clearHistoryBtn.addEventListener("click", () => this.clearHistory());
    this.themeSelector.addEventListener("change", (e) =>
      this.changeTheme(e.target.value),
    );
    this.modelSelector.addEventListener("change", () =>
      this.updateModel(this.modelSelector),
    );
    this.providerSelector.addEventListener("change", () =>
      this.updateModel(this.providerSelector),
    );
    this.toggleAll.addEventListener("change", () =>
      this.toggleSelectAll(this.toggleAll),
    );
    this.attachButton.addEventListener("click", () => this.fileInput.click());
    this.fileInput.addEventListener("change", () => this.addFile());
    this.contextAddButton.addEventListener("click", () =>
      this.addPendingContext(),
    );
    this.contextSaveButton.addEventListener("click", () => this.saveContext());
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
      this.currentTheme = "minimal";
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

  // Add threads data
  addThreads() {
    const pendingDiv = this.userThreadsDiv;
    let userCont = this.userThreadsData;
    // clear
    Array.from(pendingDiv.children).forEach((elem) => {
      pendingDiv.removeChild(elem);
    });
    const newHead = document.createElement("h4");
    newHead.textContent = "Saved Threads";
    pendingDiv.appendChild(newHead);
    const newContextContent = document.createElement("div");
    for (let pendContext in userCont) {
      console.log("thread: " + pendContext);

      newContextContent.style.padding = "5px";
      const newTable = document.createElement("table");
      const newRow = document.createElement("tr");
      const newName = document.createElement("td");
      const newVal = document.createElement("td");
      const radioSel = document.createElement("input");
      radioSel.type = "radio";
      radioSel.name = "threadId";
      radioSel.value = pendContext;
      radioSel.addEventListener(
        "change",
        this.changeThread.bind(this, pendContext),
        false,
      );
      newName.appendChild(radioSel);
      newVal.textContent = userCont[pendContext].thread_name ?? "default";
      newVal.style.color = "blue";
      newRow.appendChild(newName);
      newRow.appendChild(newVal);
      newTable.appendChild(newRow);

      newContextContent.appendChild(newTable);
    }
    const addThreadButton = document.createElement("button");
    addThreadButton.textContent = "New Thread";
    addThreadButton.addEventListener(
      "click",
      this.createThread.bind(this),
      false,
    );
    newContextContent.appendChild(addThreadButton);
    pendingDiv.appendChild(newContextContent);
  }

  changeThread(thread_key) {
    let userCont = this.userThreadsData;
    let selectedThread = userCont[thread_key];
    if (selectedThread) {
      console.log("Selected thread: " + thread_key);
      this.selectedUserThread = thread_key;
      let newHistory = JSON.parse(selectedThread.messages);
      this.conversationHistory = newHistory;
      this.clearHistory(true);
      for (var i = 0; i < newHistory.length; i++) {
        let thisItem = newHistory[i];
        this.addMessage(thisItem.content, thisItem.role);
      }
      this.updateHistoryIndicator();
    }
  }

  addContext() {
    const pendingDiv = this.userContextDiv;
    let userCont = this.userContextData;
    // clear
    Array.from(pendingDiv.children).forEach((elem) => {
      pendingDiv.removeChild(elem);
    });
    const newHead = document.createElement("h4");
    newHead.textContent = "Saved Contexts";
    pendingDiv.appendChild(newHead);
    for (let pendContext in userCont) {
      console.log("context: " + pendContext);
      const newContextContent = document.createElement("div");
      newContextContent.style.padding = "5px";
      const newTable = document.createElement("table");
      const newCaption = document.createElement("caption");
      newCaption.textContent = pendContext;
      newCaption.style.textAlign = "left";
      newCaption.style.color = "blue";
      newTable.appendChild(newCaption);
      newTable.style.captionSide = "top";

      const headRow = document.createElement("tr");
      const newH1 = document.createElement("th");
      newH1.textContent = "Name";
      const newH2 = document.createElement("th");
      newH2.textContent = "Value";
      headRow.appendChild(newH1);
      headRow.appendChild(newH2);
      newTable.appendChild(headRow);
      for (let contName in userCont[pendContext]) {
        const newRow = document.createElement("tr");
        const newName = document.createElement("td");
        const newVal = document.createElement("td");
        newName.textContent = contName;
        newVal.textContent = userCont[pendContext][contName];
        newRow.appendChild(newName);
        newRow.appendChild(newVal);
        newTable.appendChild(newRow);
      }
      newContextContent.appendChild(newTable);
      pendingDiv.appendChild(newContextContent);
    }
  }

  addPendingContext() {
    const pendingDiv = this.newContextItemsDiv;
    let newKey = this.newContextInput.value;
    let selKey = this.existingContextSel.value;
    let thisKey = "";
    if (newKey) {
      thisKey = newKey;
    } else {
      if (selKey) {
        thisKey = selKey;
      }
    }
    console.log("adding context key: " + thisKey);
    let thisName = this.newContextKey.value;
    let thisValue = this.newContextVal.value;
    if (thisKey && thisName && thisValue) {
      let anObj = this.pendingContextObj[thisKey];
      if (anObj) {
        anObj[thisName] = thisValue;
      } else {
        this.pendingContextObj[thisKey] = { [thisName]: thisValue };
      }
      console.log("context: " + JSON.stringify(this.pendingContextObj));
      Array.from(pendingDiv.children).forEach((elem) => {
        pendingDiv.removeChild(elem);
      });
      for (let pendContext in this.pendingContextObj) {
        const newContextContent = document.createElement("div");
        const newTable = document.createElement("table");
        const newCaption = document.createElement("caption");
        newCaption.textContent = pendContext;
        newTable.appendChild(newCaption);
        newTable.style.captionSide = "top";
        for (let contName in this.pendingContextObj[pendContext]) {
          const newRow = document.createElement("tr");
          const newName = document.createElement("td");
          const newVal = document.createElement("td");
          newName.textContent = contName;
          newVal.textContent = this.pendingContextObj[pendContext][contName];
          newRow.appendChild(newName);
          newRow.appendChild(newVal);
          newTable.appendChild(newRow);
          newContextContent.appendChild(newTable);
          pendingDiv.appendChild(newContextContent);
        }
      }
    }
  }
  async createThread() {
    //var threadsObj = this.pendingThreadsData;
    //if (!threadsObj) return;
    const threadNameDia = document.createElement("dialog");
    const threadNameFrm = document.createElement("form");
    threadNameFrm.method = "dialog";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = "New Thread";
    const closeButton = document.createElement("button");
    closeButton.addEventListener("click", () => {
      threadNameDia.close();
    });
    threadNameFrm.appendChild(nameInput);
    threadNameFrm.appendChild(closeButton);
    threadNameDia.appendChild(threadNameFrm);
    document.body.appendChild(threadNameDia);
    threadNameDia.close();
    threadNameDia.showModal();
    let threadName = nameInput.value;
    console.log("Got dialog data: " + threadName);
    document.body.removeChild(threadNameDia);
    try {
      const response = await fetch("/api/v1/threads", {
        method: "PATCH",
        body: JSON.stringify({ [threadName]: [] }),
        headers: {
          "Content-Type": "application/json",
        },
      });
      let resObj = await response.json();
      const endTime = new Date();
      const elapsedTime = endTime - startTime;
      console.log(
        "Thread update took: " +
          elapsedTime +
          " with result " +
          JSON.stringify(resObj),
      );
    } catch (error) {
      this.hideTypingIndicator();
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    } finally {
      this.getThreadsJSON();
      this.addThreads();
      this.setInputEnabled(true);
      this.messageInput.focus();
    }
  }
  async saveContext() {
    var context = this.pendingContextObj;
    if (!context) return;
    const startTime = new Date();
    try {
      const response = await fetch("/api/v1/context", {
        method: "PATCH",
        body: JSON.stringify(context),
        headers: {
          "Content-Type": "application/json",
        },
      });
      let resObj = await response.json();
      const endTime = new Date();
      const elapsedTime = endTime - startTime;
      console.log(
        "Context update took: " +
          elapsedTime +
          " with result " +
          JSON.stringify(resObj),
      );
    } catch (error) {
      this.hideTypingIndicator();
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    } finally {
      this.getContextJSON();
      this.addContext();
      this.setInputEnabled(true);
      this.messageInput.focus();
    }
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
        Array.from(response.history).forEach((opt) => {
          Object.keys(opt).forEach((key) => {
            console.log(`${key}: ${opt[key]}`);
          });
        });
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

  async getProvidersJSON() {
    try {
      const response = await fetch("/api/v1/providers", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Adding providers JSON");
      let provObj = await response.json();
      this.providerData = provObj;
      this.addProvidersOptions(provObj);
      this.addProviderList(provObj);
    } catch (error) {
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    }
  }

  async getContextJSON() {
    try {
      const response = await fetch("/api/v1/context", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Adding context JSON");
      let provObj = await response.json();
      this.userContextData = provObj;
      this.addContext();
    } catch (error) {
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    }
  }

  async getThreadsJSON() {
    try {
      const response = await fetch("/api/v1/threads", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      console.log("Adding threads JSON");
      let provObj = await response.json();
      this.userThreadsData = provObj;
      this.addThreads();
    } catch (error) {
      this.addErrorMessage("Sorry, I encountered an error: " + error.message);
    }
  }

  async updateModel(elem) {
    if (elem === this.providerSelector) {
      console.log("Provider changed");
      let provID = this.providerSelector.value;
      for (let provKey in this.providerData) {
        if (provKey != provID) {
          this.providerData[provKey].is_active = false;
          console.log("Deactivating provider key: " + provID + " " + provKey);
        } else {
          this.providerData[provKey].is_active = true;
          console.log("Activating provider key: " + provID + " " + provKey);
        }
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

    for (let prov_key in providers_obj) {
      const providerOpt = document.createElement("option");
      providerOpt.text = providers_obj[prov_key].name;
      providerOpt.value = prov_key;
      if (providers_obj[prov_key].is_active) {
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

        for (let mod_key in providers_obj[prov_key].models) {
          const modelOpt = document.createElement("option");
          modelOpt.text = this.truncateToLength(
            providers_obj[prov_key].models[mod_key].id,
            45,
          );
          modelOpt.value = mod_key;

          if (providers_obj[prov_key].models[mod_key].selected) {
            is_selected.push(modelOpt);
          }
          if (
            providers_obj[prov_key].models[mod_key].model_status === "loaded"
          ) {
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
        for (let mod_key in providers_obj[prov_key].models) {
          if (
            providers_obj[prov_key].models[mod_key].id ===
            this.modelSelector.value
          ) {
            let inputs = Array.from(
              providers_obj[prov_key].models[mod_key].architecture
                .input_modalities,
            );
            let outputs = Array.from(
              providers_obj[prov_key].models[mod_key].architecture
                .output_modalities,
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

  addProviderList(provObj) {
    const providerDiv = this.providersContent;
    var content = "";
    for (var i = 0; i < provObj.length; i++) {
      console.log("Found provider J: " + provObj[i].name + " - " + i);
      let spanColor = "blue";
      if (provObj[i].status === "OFFLINE") {
        spanColor = "red";
      }
      content += `<p>${provObj[i].name} is <span style="color: ${spanColor};">${provObj[i].status}</span> with ${provObj[i].models.length} models</p>`;
    }
    providerDiv.innerHTML = content;
  }

  async callAgentAPI(message) {
    // inject modal call here

    let dataObj = {
      query: message,
      history: this.conversationHistory,
      provider_slug: this.providerSelector.value,
      model_id: this.modelSelector.value,
      thread_id: this.selectedUserThread ?? null,
    };

    const formData = new FormData();
    formData.append("agent_query", JSON.stringify(dataObj));

    for (let i = 0; i < this.selectedFiles.length; i++) {
      formData.append("files", this.selectedFiles[i]);
      console.log("Adding file: " + this.selectedFiles[i].name);
    }

    const response = await fetch("/agent/v1/query", {
      method: "POST",
      body: formData,
    });

    // TODO fix this with better error handling, free the UI
    if (!response.ok) {
      this.addErrorMessage(
        "Sorry, I encountered an error: " +
          response.status +
          " -> " +
          response.statusText,
      );
    }
    // reset files only when successful for now
    this.selectedFiles = [];
    this.updateFileList();
    // return response data
    return await response.json();
  }

  addMessage(content, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    messageDiv.innerHTML = `
      <input type="checkbox" style="margin: 1em;"></input>
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

  toggleSelectAll(checkboxAll) {
    const children = this.messagesContainer.children;
    for (let i = 0; i < children.length; i++) {
      let checkbox = children[i].children[0];
      if (checkbox !== "undefined" && checkbox.nodeName === "INPUT") {
        if (checkboxAll.checked) {
          checkbox.checked = true;
        } else {
          checkbox.checked = false;
        }
      }
    }
  }

  addFile(fileForm) {
    // get the file data and push it to an array
    const fileInput = this.fileInput;
    for (var i = 0; i < fileInput.files.length; i++) {
      this.selectedFiles.push(fileInput.files[i]);
      console.log(
        "Upload file: " +
          fileInput.files[i].name +
          " length: " +
          fileInput.files[i].size,
      );
    }
    this.updateFileList();
  }

  updateFileList() {
    const filesList = this.fileListing;
    const selFiles = this.selectedFiles;
    // Clear existing file attachments
    if (filesList.children.length > 0) {
      Array.from(filesList.children).forEach((para) => {
        filesList.removeChild(para);
      });
    }
    for (var i = 0; i < selFiles.length; i++) {
      let rem_button = document.createElement("button");
      rem_button.textContent = "X";
      rem_button.addEventListener(
        "click",
        this.removeFile.bind(this, i),
        false,
      );
      let file_item = document.createElement("p");
      file_item.textContent = `${selFiles[i].name} | ${selFiles[i].size} bytes `;
      rem_button.style.color = "red";
      file_item.appendChild(rem_button);
      filesList.appendChild(file_item);
    }
    console.log("Added files listings: " + filesList.children.length);
  }

  removeFile(index) {
    let thisIndex = Number(index);
    console.log("Removing file at index: " + thisIndex);
    this.selectedFiles.splice(thisIndex, 1);
    console.log("File list is now: " + this.selectedFiles.length);
    this.updateFileList();
  }

  clearHistory(clearAll = false) {
    // Clear chat messages
    const initialMessage =
      this.messagesContainer.querySelector(".message.assistant");
    const children = this.messagesContainer.children;
    let indexes = [];
    for (let i = 0; i < children.length; i++) {
      let checkbox = children[i].children[0];
      if (clearAll) {
        checkbox.checked = true;
      }
      if (checkbox !== "undefined" && checkbox.nodeName === "INPUT") {
        if (checkbox.checked) {
          indexes.push(i);
        }
      }
    }
    // sort indexes in reverse order
    indexes.sort((a, b) => b - a);
    for (let i = 0; i < indexes.length; i++) {
      this.messagesContainer.removeChild(
        this.messagesContainer.children[indexes[i]],
      );
      this.conversationHistory.splice(indexes[i], 1);
    }
    // Update history indicator and reset select toggle
    this.toggleAll.checked = false;
    this.updateHistoryIndicator();
  }

  updateHistoryIndicator() {
    const messageCount = this.conversationHistory.length;
    this.historyIndicator.textContent = `History: ${messageCount} messages`;
  }
}

// Initialize the chat app when the page loads
document.addEventListener("DOMContentLoaded", () => {
  const app = new ChatApp();
  app.getProvidersJSON();
  app.getContextJSON();
  app.getThreadsJSON();
});
