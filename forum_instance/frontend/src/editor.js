import EditorJS from "@editorjs/editorjs";
import Header from "@editorjs/header";
import List from "@editorjs/list";
import Quote from "@editorjs/quote";
import Delimiter from "@editorjs/delimiter";
import ImageTool from "@editorjs/image";
import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import "./editor.css";

const editImage = (file) => new Promise((resolve, reject) => {
  const url = URL.createObjectURL(file);
  const modal = document.createElement("div");
  modal.className = "image-editor-modal";
  modal.innerHTML = `<div class="image-editor-modal__dialog" role="dialog" aria-modal="true" aria-label="Редагування зображення"><div class="image-editor-modal__canvas"><img alt="Попередній перегляд"></div><div class="image-editor-modal__controls"><button type="button" data-action="rotate-left">↶ Повернути</button><button type="button" data-action="rotate-right">↷ Повернути</button><button type="button" data-action="zoom-out">−</button><button type="button" data-action="zoom-in">+</button><button type="button" data-action="reset">Скинути</button><span></span><button type="button" data-action="cancel">Скасувати</button><button type="button" class="is-primary" data-action="apply">Застосувати</button></div></div>`;
  document.body.appendChild(modal);
  const image = modal.querySelector("img"); image.src = url;
  const cropper = new Cropper(image, {viewMode: 1, autoCropArea: 1, background: false, responsive: true});
  const close = () => {cropper.destroy(); URL.revokeObjectURL(url); modal.remove();};
  modal.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    if (action === "rotate-left") cropper.rotate(-90);
    if (action === "rotate-right") cropper.rotate(90);
    if (action === "zoom-out") cropper.zoom(-0.1);
    if (action === "zoom-in") cropper.zoom(0.1);
    if (action === "reset") cropper.reset();
    if (action === "cancel") {close(); reject(new Error("cancelled"));}
    if (action === "apply") cropper.getCroppedCanvas({maxWidth: 2560, maxHeight: 2560, imageSmoothingQuality: "high"}).toBlob((blob) => {const edited = new File([blob], file.name.replace(/\.[^.]+$/, ".webp"), {type: "image/webp"}); close(); resolve(edited);}, "image/webp", 0.9);
  });
});

document.addEventListener("DOMContentLoaded", async () => {
  const source = document.querySelector("[data-medium-editor='body']");
  if (!source) return;
  const form = source.closest("form");
  const status = form.querySelector(".medium-compose__status");
  const holder = document.createElement("div");
  const pendingImages = new Map();
  holder.id = "community-block-editor";
  source.required = false;
  source.hidden = true;
  source.after(holder);

  let data = {blocks: []};
  try {
    const parsed = JSON.parse(source.value);
    if (parsed && Array.isArray(parsed.blocks)) data = parsed;
  } catch (_) {
    if (source.value.trim()) data.blocks = [{type: "paragraph", data: {text: source.value.replace(/</g, "&lt;").replace(/\n/g, "<br>")}}];
  }

  const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
  const uploadPendingImage = async (file) => {
    const editedFile = await editImage(file);
    const previewUrl = URL.createObjectURL(editedFile);
    pendingImages.set(previewUrl, editedFile);
    return {success: 1, file: {url: previewUrl, name: editedFile.name}};
  };
  const editor = new EditorJS({
    holder, data, autofocus: true, placeholder: "Розкажіть свою історію…",
    inlineToolbar: ["bold", "italic", "link"],
    tools: {
      header: {class: Header, config: {levels: [2, 3], defaultLevel: 2}},
      list: {class: List, inlineToolbar: true}, quote: {class: Quote, inlineToolbar: true},
      delimiter: Delimiter,
      image: {class: ImageTool, config: {uploader: {uploadByFile: uploadPendingImage}}},
    },
    i18n: {messages: {toolNames: {Text: "Текст", Heading: "Заголовок", List: "Список", Quote: "Цитата", Delimiter: "Розділювач", Image: "Зображення"}}},
  });

  const panel = document.querySelector("[data-publish-panel]");
  const closeButton = panel.querySelector("[data-close-publish]");
  let dirty = false;
  let submitting = false;
  const markDirty = () => { dirty = true; status.textContent = "Є незбережені зміни"; };
  form.addEventListener("input", markDirty);
  form.addEventListener("change", markDirty);
  window.addEventListener("beforeunload", (event) => {
    if (!dirty || submitting) return;
    event.preventDefault();
    event.returnValue = "";
  });
  const openPanel = () => {
    panel.hidden = false;
    document.body.classList.add("has-publish-panel");
    closeButton.focus();
  };
  const closePanel = () => {
    panel.hidden = true;
    document.body.classList.remove("has-publish-panel");
    document.querySelector("[data-open-publish]")?.focus();
  };
  document.querySelectorAll("[data-open-publish]").forEach((button) => button.addEventListener("click", openPanel));
  document.querySelectorAll("[data-close-publish]").forEach((button) => button.addEventListener("click", closePanel));
  panel.addEventListener("keydown", (event) => { if (event.key === "Escape") closePanel(); });
  if (form.querySelector(".errorlist")) openPanel();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button[type=submit]");
    let error = form.querySelector("[data-editor-upload-error]");
    if (!error) {error = document.createElement("p"); error.dataset.editorUploadError = ""; error.className = "community-alert community-alert--error"; submit.parentElement.before(error);}
    error.hidden = true;
    submit.disabled = true;
    submit.textContent = "Завантаження…";
    try {
      const documentData = await editor.save();
      const hasContent = documentData.blocks.some((block) => {
        if (block.type === "image") return Boolean(block.data?.file?.url);
        if (block.type === "delimiter") return false;
        if (block.type === "list") return Array.isArray(block.data?.items) && block.data.items.length > 0;
        return Boolean(String(block.data?.text || "").replace(/<[^>]*>/g, "").trim());
      });
      if (!hasContent) {
        error.textContent = "Додайте текст або зображення до публікації.";
        error.hidden = false;
        submit.disabled = false;
        submit.textContent = "Опублікувати зараз";
        return;
      }
      for (const block of documentData.blocks) {
        if (block.type !== "image" || !pendingImages.has(block.data.file.url)) continue;
        const previewUrl = block.data.file.url;
        const upload = new FormData();
        upload.append("image", pendingImages.get(previewUrl));
        const response = await fetch(form.dataset.imageUploadUrl, {method: "POST", body: upload, headers: {"X-CSRFToken": csrf}});
        const result = await response.json();
        if (!response.ok || result.success !== 1) throw new Error("image-upload");
        block.data.file = result.file;
        URL.revokeObjectURL(previewUrl);
        pendingImages.delete(previewUrl);
      }
      source.value = JSON.stringify(documentData);
      source.hidden = false;
      submitting = true;
      dirty = false;
      status.textContent = "Збереження…";
      form.submit();
    } catch (_) {
      error.textContent = "Не вдалося завантажити одне із зображень. Перевірте формат, розмір і спробуйте ще раз.";
      error.hidden = false;
      submit.disabled = false;
      submit.textContent = "Опублікувати зараз";
    }
  });
});
