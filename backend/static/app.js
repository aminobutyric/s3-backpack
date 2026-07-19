"use strict";

const API_KEY_STORAGE = "s3gw.apiKey";

const state = {
  apiKey: sessionStorage.getItem(API_KEY_STORAGE),
  deleteKey: null,
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  Object.assign(elements, {
    authDialog: document.querySelector("#auth-dialog"),
    authError: document.querySelector("#auth-error"),
    authForm: document.querySelector("#auth-form"),
    apiKey: document.querySelector("#api-key"),
    cancelDelete: document.querySelector("#cancel-delete"),
    changeKey: document.querySelector("#change-key"),
    connectionDot: document.querySelector("#connection-dot"),
    connectionLabel: document.querySelector("#connection-label"),
    deleteDialog: document.querySelector("#delete-dialog"),
    deleteForm: document.querySelector("#delete-form"),
    deleteKey: document.querySelector("#delete-key"),
    dropZone: document.querySelector("#drop-zone"),
    emptyState: document.querySelector("#empty-state"),
    file: document.querySelector("#file"),
    fileLabel: document.querySelector("#file-label"),
    objectCount: document.querySelector("#object-count"),
    objectKey: document.querySelector("#object-key"),
    objectRows: document.querySelector("#object-rows"),
    prefix: document.querySelector("#prefix"),
    prefixForm: document.querySelector("#prefix-form"),
    refresh: document.querySelector("#refresh"),
    tableError: document.querySelector("#table-error"),
    tableLoading: document.querySelector("#table-loading"),
    tableWrap: document.querySelector("#object-table-wrap"),
    toast: document.querySelector("#toast"),
    uploadButton: document.querySelector("#upload-button"),
    uploadForm: document.querySelector("#upload-form"),
    uploadResult: document.querySelector("#upload-result"),
  });

  bindEvents();
  if (state.apiKey) {
    loadObjects();
  } else {
    showAuthDialog();
  }
});

function bindEvents() {
  elements.authForm.addEventListener("submit", connect);
  elements.changeKey.addEventListener("click", showAuthDialog);
  elements.prefixForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadObjects();
  });
  elements.refresh.addEventListener("click", loadObjects);
  elements.uploadForm.addEventListener("submit", uploadObject);
  elements.deleteForm.addEventListener("submit", deleteObject);
  elements.cancelDelete.addEventListener("click", () => elements.deleteDialog.close());
  elements.file.addEventListener("change", updateFileLabel);

  for (const eventName of ["dragenter", "dragover"]) {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.add("dragging");
    });
  }
  for (const eventName of ["dragleave", "drop"]) {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.remove("dragging");
    });
  }
  elements.dropZone.addEventListener("drop", (event) => {
    if (event.dataTransfer.files.length) {
      elements.file.files = event.dataTransfer.files;
      updateFileLabel();
    }
  });
}

async function connect(event) {
  event.preventDefault();
  const candidate = elements.apiKey.value.trim();
  if (!candidate) {
    return;
  }

  setFormBusy(elements.authForm, true);
  elements.authError.hidden = true;
  try {
    const response = await fetch("/api/objects?prefix=", {
      headers: { "X-API-Key": candidate },
    });
    if (!response.ok) {
      throw new Error(response.status === 401 ? "Invalid API key." : "Gateway unavailable.");
    }
    state.apiKey = candidate;
    sessionStorage.setItem(API_KEY_STORAGE, candidate);
    elements.authDialog.close();
    setConnection(true);
    await loadObjects();
  } catch (error) {
    elements.authError.textContent = error.message;
    elements.authError.hidden = false;
    setConnection(false);
  } finally {
    setFormBusy(elements.authForm, false);
  }
}

async function loadObjects() {
  if (!state.apiKey) {
    showAuthDialog();
    return;
  }

  showTableState("loading");
  const prefix = encodeURIComponent(elements.prefix.value.trim());
  try {
    const response = await apiFetch(`/api/objects?prefix=${prefix}`);
    const payload = await response.json();
    renderObjects(payload.objects);
    setConnection(true);
  } catch (error) {
    if (error.name !== "AuthError") {
      elements.tableError.textContent = error.message;
      showTableState("error");
    }
  }
}

function renderObjects(objects) {
  elements.objectRows.replaceChildren();
  elements.objectCount.textContent = `${objects.length} ${objects.length === 1 ? "object" : "objects"}`;

  if (!objects.length) {
    showTableState("empty");
    return;
  }

  for (const object of objects) {
    const row = document.createElement("tr");

    const keyCell = document.createElement("td");
    keyCell.className = "object-key";
    keyCell.textContent = object.key;

    const sizeCell = document.createElement("td");
    sizeCell.textContent = formatBytes(object.size);

    const modifiedCell = document.createElement("td");
    modifiedCell.textContent = formatDate(object.last_modified);

    const actionCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "row-actions";
    actions.append(
      actionButton("Download", "button button-secondary button-small", () => downloadObject(object.key)),
      actionButton("Delete", "button button-quiet button-small state-error", () => confirmDelete(object.key)),
    );
    actionCell.append(actions);
    row.append(keyCell, sizeCell, modifiedCell, actionCell);
    elements.objectRows.append(row);
  }
  showTableState("table");
}

async function uploadObject(event) {
  event.preventDefault();
  if (!elements.file.files.length) {
    return;
  }

  elements.uploadButton.disabled = true;
  elements.uploadButton.textContent = "Uploading...";
  elements.uploadResult.hidden = true;
  try {
    const formData = new FormData();
    formData.append("file", elements.file.files[0]);
    const key = elements.objectKey.value.trim();
    if (key) {
      formData.append("key", key);
    }

    const response = await apiFetch("/api/objects", {
      method: "POST",
      body: formData,
    });
    const uploaded = await response.json();
    const detail = uploaded.compression
      ? `Stored as ${uploaded.key} - saved ${uploaded.savings_percent}%`
      : `Stored as ${uploaded.key}`;
    elements.uploadResult.textContent = detail;
    elements.uploadResult.hidden = false;
    elements.uploadForm.reset();
    updateFileLabel();
    showToast("Upload complete.");
    await loadObjects();
  } catch (error) {
    if (error.name !== "AuthError") {
      showToast(error.message, true);
    }
  } finally {
    elements.uploadButton.disabled = false;
    elements.uploadButton.textContent = "Upload";
  }
}

async function downloadObject(key) {
  try {
    const response = await apiFetch(`/api/objects/${encodeObjectKey(key)}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = key.split("/").pop() || "download";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    if (error.name !== "AuthError") {
      showToast(error.message, true);
    }
  }
}

function confirmDelete(key) {
  state.deleteKey = key;
  elements.deleteKey.textContent = key;
  elements.deleteDialog.showModal();
}

async function deleteObject(event) {
  event.preventDefault();
  if (!state.deleteKey) {
    return;
  }

  const key = state.deleteKey;
  const submit = elements.deleteForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    await apiFetch(`/api/objects/${encodeObjectKey(key)}`, { method: "DELETE" });
    elements.deleteDialog.close();
    state.deleteKey = null;
    showToast("Object deleted.");
    await loadObjects();
  } catch (error) {
    if (error.name !== "AuthError") {
      showToast(error.message, true);
    }
  } finally {
    submit.disabled = false;
  }
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-API-Key", state.apiKey);
  const response = await fetch(path, { ...options, headers });

  if (response.status === 401) {
    state.apiKey = null;
    sessionStorage.removeItem(API_KEY_STORAGE);
    setConnection(false);
    showAuthDialog();
    const error = new Error("Authentication required.");
    error.name = "AuthError";
    throw error;
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // The default status message is enough for non-JSON errors.
    }
    throw new Error(message);
  }
  return response;
}

function showAuthDialog() {
  elements.apiKey.value = "";
  elements.authError.hidden = true;
  if (!elements.authDialog.open) {
    elements.authDialog.showModal();
  }
  requestAnimationFrame(() => elements.apiKey.focus());
}

function showTableState(name) {
  elements.tableLoading.hidden = name !== "loading";
  elements.tableError.hidden = name !== "error";
  elements.emptyState.hidden = name !== "empty";
  elements.tableWrap.hidden = name !== "table";
}

function setConnection(connected) {
  elements.connectionDot.classList.toggle("connected", connected);
  elements.connectionLabel.textContent = connected ? "Connected" : "Not connected";
}

function setFormBusy(form, busy) {
  for (const control of form.elements) {
    control.disabled = busy;
  }
}

function updateFileLabel() {
  elements.fileLabel.textContent = elements.file.files[0]?.name || "Choose a file";
}

function actionButton(label, className, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}

function encodeObjectKey(key) {
  return key.split("/").map(encodeURIComponent).join("/");
}

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unit = units[0];
  for (let index = 1; value >= 1024 && index < units.length; index += 1) {
    value /= 1024;
    unit = units[index];
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${unit}`;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

let toastTimer;
function showToast(message, isError = false) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.style.background = isError ? "#9f3030" : "#26322c";
  elements.toast.hidden = false;
  toastTimer = setTimeout(() => {
    elements.toast.hidden = true;
  }, 3500);
}
