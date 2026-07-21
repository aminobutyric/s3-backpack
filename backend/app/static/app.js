(() => {
  "use strict";

  const STORAGE_KEY = "s3gw_api_key";

  // ---- API key -----------------------------------------------------------
  const keyInput = document.getElementById("api-key");
  const keyStatus = document.getElementById("key-status");

  function getApiKey() {
    return sessionStorage.getItem(STORAGE_KEY) || "";
  }

  function setApiKey(value) {
    if (value) {
      sessionStorage.setItem(STORAGE_KEY, value);
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
    updateKeyStatus();
  }

  function updateKeyStatus() {
    const has = Boolean(getApiKey());
    keyStatus.dataset.state = has ? "set" : "empty";
    keyStatus.textContent = has ? "set" : "not set";
  }

  keyInput.value = getApiKey();
  updateKeyStatus();
  keyInput.addEventListener("change", () => {
    setApiKey(keyInput.value.trim());
    if (document.querySelector('[data-panel="browse"]:not([hidden])')) {
      loadObjects();
    }
  });

  function authHeaders(extra = {}) {
    const key = getApiKey();
    return key ? { "X-API-Key": key, ...extra } : { ...extra };
  }

  // ---- Tabs ----------------------------------------------------------------
  const tabButtons = document.querySelectorAll(".tab[data-tab]");
  const panels = document.querySelectorAll(".panels [data-panel]");

  function activateTab(tabId) {
    tabButtons.forEach((btn) => {
      const active = btn.dataset.tab === tabId;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", String(active));
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.panel !== tabId;
    });
    if (tabId === "browse") loadObjects();
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
  });

  // ---- Browse ----------------------------------------------------------------
  const objectsBody = document.getElementById("objects-body");
  const prefixFilter = document.getElementById("prefix-filter");
  const refreshBtn = document.getElementById("refresh-objects");

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    const units = ["KB", "MB", "GB", "TB"];
    let value = bytes;
    let unit = -1;
    do {
      value /= 1024;
      unit += 1;
    } while (value >= 1024 && unit < units.length - 1);
    return `${value.toFixed(1)} ${units[unit]}`;
  }

  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleString(undefined, {
        year: "numeric", month: "short", day: "2-digit",
        hour: "2-digit", minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  function renderEmpty(message) {
    objectsBody.innerHTML = `<tr class="row-empty"><td colspan="4">${message}</td></tr>`;
  }

  async function loadObjects() {
    if (!getApiKey()) {
      renderEmpty("Set an API key above to load objects.");
      return;
    }
    renderEmpty("Loading\u2026");
    try {
      const prefix = encodeURIComponent(prefixFilter.value.trim());
      const res = await fetch(`/api/objects?prefix=${prefix}`, {
        headers: authHeaders(),
      });
      if (res.status === 401) {
        renderEmpty("Invalid API key.");
        return;
      }
      if (!res.ok) {
        renderEmpty(`Could not load objects (${res.status}).`);
        return;
      }
      const data = await res.json();
      renderObjects(data.objects || []);
    } catch (err) {
      renderEmpty("Could not reach the gateway. Check your connection.");
    }
  }

  function renderObjects(objects) {
    if (objects.length === 0) {
      renderEmpty(
        prefixFilter.value.trim()
          ? "No objects match this prefix."
          : "No objects yet. Upload one to get started."
      );
      return;
    }
    objectsBody.innerHTML = "";
    for (const obj of objects) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(obj.key)}</td>
        <td class="col-size">${formatSize(obj.size)}</td>
        <td class="col-modified">${formatDate(obj.last_modified)}</td>
        <td class="row-actions">
          <button type="button" data-action="download">Download</button>
          <button type="button" data-action="delete" class="danger">Delete</button>
        </td>
      `;
      tr.querySelector('[data-action="download"]').addEventListener("click", () => downloadObject(obj.key));
      tr.querySelector('[data-action="delete"]').addEventListener("click", () => deleteObject(obj.key, tr));
      objectsBody.appendChild(tr);
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  async function downloadObject(key) {
    try {
      const res = await fetch(`/api/objects/${encodeObjectKey(key)}`, {
        headers: authHeaders(),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = downloadFilename(res, key);
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      /* silent — a failed download simply doesn't start */
    }
  }

  async function deleteObject(key, row) {
    if (!window.confirm(`Delete "${key}"? This can't be undone.`)) return;
    try {
      const res = await fetch(`/api/objects/${encodeObjectKey(key)}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        row.remove();
        if (!objectsBody.querySelector("tr")) {
          renderEmpty("No objects yet. Upload one to get started.");
        }
      }
    } catch {
      /* silent — row stays, user can retry */
    }
  }

  let filterDebounce;
  prefixFilter.addEventListener("input", () => {
    clearTimeout(filterDebounce);
    filterDebounce = setTimeout(loadObjects, 300);
  });
  refreshBtn.addEventListener("click", loadObjects);

  function encodeObjectKey(key) {
    return key.split("/").map(encodeURIComponent).join("/");
  }

  function downloadFilename(response, fallbackKey) {
    const disposition = response.headers.get("Content-Disposition") || "";
    const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
    if (encoded) {
      try {
        return decodeURIComponent(encoded);
      } catch {
        // Fall back to the stored key when a header is malformed.
      }
    }
    return fallbackKey.split("/").pop() || fallbackKey;
  }

  // ---- Upload ----------------------------------------------------------------
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const keyOverride = document.getElementById("key-override");
  const uploadList = document.getElementById("upload-list");

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("is-dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("is-dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer?.files;
    if (files?.length) uploadFiles(files);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) uploadFiles(fileInput.files);
    fileInput.value = "";
  });

  function uploadFiles(fileList) {
    if (!getApiKey()) {
      window.alert("Set an API key above before uploading.");
      return;
    }
    const files = Array.from(fileList);
    const override = files.length === 1 ? keyOverride.value.trim() : "";
    files.forEach((file) => uploadOne(file, override));
  }

  function uploadOne(file, overrideKey) {
    const item = document.createElement("li");
    item.className = "upload-item";
    item.innerHTML = `
      <span class="name">${escapeHtml(file.name)}</span>
      <span class="bar"><span class="bar-fill"></span></span>
      <span class="status">0%</span>
    `;
    uploadList.prepend(item);

    const fill = item.querySelector(".bar-fill");
    const status = item.querySelector(".status");

    const form = new FormData();
    form.append("file", file);
    if (overrideKey) form.append("key", overrideKey);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/objects");
    const key = getApiKey();
    if (key) xhr.setRequestHeader("X-API-Key", key);

    xhr.upload.addEventListener("progress", (e) => {
      if (!e.lengthComputable) return;
      const pct = Math.round((e.loaded / e.total) * 100);
      fill.style.width = `${pct}%`;
      status.textContent = `${pct}%`;
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        item.classList.add("is-done");
        status.textContent = "done";
      } else {
        item.classList.add("is-error");
        status.textContent = xhr.status === 401 ? "unauthorized" : "failed";
      }
    });

    xhr.addEventListener("error", () => {
      item.classList.add("is-error");
      status.textContent = "failed";
    });

    xhr.send(form);
  }

  // ---- init ----------------------------------------------------------------
  loadObjects();
})();
