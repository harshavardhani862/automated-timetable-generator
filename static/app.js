const fileInput = document.querySelector("#schedule-file");
const fileName = document.querySelector("#file-name");
const fileMeta = document.querySelector("#file-meta");
const dropzone = document.querySelector("#dropzone");
const importForm = document.querySelector("#import-form");
const importButton = document.querySelector("#import-submit");

function displayFile(file) {
  if (!file || !fileName || !fileMeta) return;
  fileName.textContent = file.name;
  fileMeta.textContent = `${(file.size / 1024).toFixed(1)} KB · Ready to import`;
}

fileInput?.addEventListener("change", () => displayFile(fileInput.files?.[0]));

for (const eventName of ["dragenter", "dragover"]) {
  dropzone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropzone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
  });
}

dropzone?.addEventListener("drop", (event) => {
  const files = event.dataTransfer?.files;
  if (!files?.length || !fileInput) return;
  const transfer = new DataTransfer();
  transfer.items.add(files[0]);
  fileInput.files = transfer.files;
  displayFile(files[0]);
});

importForm?.addEventListener("submit", () => {
  if (!importButton) return;
  importButton.disabled = true;
  importButton.innerHTML = '<span class="button-spinner" aria-hidden="true"></span> Importing schedule…';
});
