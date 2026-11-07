/* Explicit late-file preview; all identity/QC/concurrency decisions are server validated. */
window.initPostQcRna = function ({ state, busy, isDirty, setExporting }) {
  const panel = document.getElementById("post-qc-upload");
  if (!panel) return;
  const picker = panel.querySelector("input[type=file]");
  const previewButton = panel.querySelector("[data-preview-post-qc]");
  const applyButton = panel.querySelector("[data-apply-post-qc]");
  const status = panel.querySelector("[role=status]");
  const preview = panel.querySelector("[data-post-qc-preview]");
  let token = null;
  let files = [];
  picker.addEventListener("change", () => {
    token = null;
    files = Array.from(picker.files);
    preview.replaceChildren();
    applyButton.hidden = true;
    status.textContent = "";
  });
  function showPreview(result) {
    preview.replaceChildren();
    const scope = document.createElement("p");
    scope.textContent = `Replaces these source categories: ${result.replacementScope.map((item) => `${item.sampleId} / ${item.kind}`).join(", ")}. Replaced findings require fresh review. Other findings and notes are kept.`;
    preview.append(scope);
    for (const file of result.files) {
      const heading = document.createElement("h4");
      heading.textContent = `${file.name} — ${file.rows.length} source candidates`;
      const table = document.createElement("table");
      table.setAttribute("data-fixed-columns", "");
      const head = table.createTHead().insertRow();
      for (const label of [
        "RNA sample",
        "Event",
        "Nomenclature",
        "Source support (%)",
        "Report support",
        "Outcome",
        "Technical QC",
        "Column interpretation",
      ]) {
        const cell = document.createElement("th");
        cell.scope = "col";
        cell.textContent = label;
        head.append(cell);
      }
      const body = table.createTBody();
      for (const item of file.rows) {
        const row = body.insertRow();
        for (const value of [
          item.sampleId,
          item.kind,
          item.label,
          item.rawSupport,
          item.support,
          item.outcome || "Not provided",
          item.qc,
          item.columnsSwapped
            ? "Reversed: Outcome contains QC; QC_Verdict contains consequence"
            : "Standard: QC_Verdict contains QC; Outcome contains consequence",
        ]) {
          row.insertCell().textContent = value ?? "";
        }
      }
      const scroll = document.createElement("div");
      scroll.className = "table-scroll";
      scroll.tabIndex = 0;
      scroll.setAttribute("role", "region");
      scroll.setAttribute("aria-label", `Post-QC preview ${file.name}`);
      scroll.append(table);
      preview.append(heading, scroll);
    }
  }
  async function submit(apply) {
    if (busy() || state.status !== "DRAFT") return;
    if (isDirty()) {
      status.textContent = "Save changes before loading post-QC files.";
      return;
    }
    files = Array.from(picker.files);
    if (!files.length || (apply && !token)) {
      status.textContent = "Choose the workbooks and preview them first.";
      return;
    }
    const data = new FormData();
    files.forEach((file) => data.append("files", file));
    data.set("baseRevision", String(state.revision));
    data.set(
      "expectedVersion",
      String(window.prontoWorkingConfig?.version ?? 0),
    );
    if (apply) data.set("previewToken", token);
    setExporting(true);
    panel.setAttribute("aria-busy", "true");
    status.textContent = apply
      ? "Importing confirmed sources …"
      : "Checking identity and technical QC …";
    try {
      const response = await fetch(panel.dataset.url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": panel.dataset.csrf },
        body: data,
      });
      const result = await response.json();
      if (!response.ok)
        throw new Error(
          result.error?.message ||
            "Post-QC import failed. Reload and preview again.",
        );
      if (apply) {
        window.location.reload();
        return;
      }
      token = result.previewToken;
      showPreview(result);
      applyButton.hidden = false;
      status.textContent =
        "Check sample, QC and column interpretation, then confirm. PASS makes an event eligible; clinical classification and report selection remain yours.";
    } catch (error) {
      token = null;
      applyButton.hidden = true;
      status.textContent = error.message;
    } finally {
      panel.setAttribute("aria-busy", "false");
      setExporting(false);
    }
  }
  previewButton.addEventListener("click", () => submit(false));
  applyButton.addEventListener("click", () => submit(true));
};
