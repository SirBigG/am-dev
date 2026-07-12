document.addEventListener("DOMContentLoaded", function () {
  const source = document.querySelector("[data-medium-editor='body']");
  if (!source) return;
  const surface = document.createElement("div");
  surface.className = "medium-editor__surface";
  surface.contentEditable = "true";
  surface.setAttribute("role", "textbox");
  surface.setAttribute("aria-multiline", "true");

  const appendTextBlock = (tag, text) => { const el = document.createElement(tag); el.textContent = text; surface.appendChild(el); };
  source.value.split(/\n\n+/).filter(Boolean).forEach((block) => {
    const lines = block.split("\n");
    if (block.startsWith("## ")) appendTextBlock("h2", block.slice(3));
    else if (block.startsWith("### ")) appendTextBlock("h3", block.slice(4));
    else if (block.startsWith("> ")) appendTextBlock("blockquote", block.slice(2));
    else if (lines.every((line) => /^[-*] /.test(line))) { const ul=document.createElement("ul"); lines.forEach(line=>{const li=document.createElement("li");li.textContent=line.slice(2);ul.appendChild(li);}); surface.appendChild(ul); }
    else if (lines.every((line) => /^\d+\. /.test(line))) { const ol=document.createElement("ol"); lines.forEach(line=>{const li=document.createElement("li");li.textContent=line.replace(/^\d+\. /,"");ol.appendChild(li);}); surface.appendChild(ol); }
    else if (block === "---") surface.appendChild(document.createElement("hr"));
    else { const image=block.match(/^!\[([^\]]+)\]\(([^)]+)\)$/); if(image){const figure=document.createElement("figure");const img=document.createElement("img");img.src=image[2];img.alt=image[1];const caption=document.createElement("figcaption");caption.textContent=image[1];figure.append(img,caption);surface.appendChild(figure);} else appendTextBlock("p", block.replace(/\n/g," ")); }
  });
  if (!surface.children.length) appendTextBlock("p", "");
  source.hidden = true; source.insertAdjacentElement("afterend", surface);
  const toolbar=document.querySelector(".medium-editor__toolbar"), toggleBlocks=document.querySelector("[data-toggle-blocks]");
  if(toolbar&&toggleBlocks) toggleBlocks.addEventListener("click",()=>{toolbar.hidden=!toolbar.hidden;toggleBlocks.classList.toggle("is-open",!toolbar.hidden);if(!toolbar.hidden)surface.focus();});
  const publishPanel=document.querySelector("[data-publish-panel]");
  document.querySelectorAll("[data-open-publish]").forEach(button=>button.addEventListener("click",()=>{if(publishPanel){publishPanel.hidden=false;document.body.classList.add("has-publish-panel");}}));
  document.querySelectorAll("[data-close-publish]").forEach(button=>button.addEventListener("click",()=>{if(publishPanel){publishPanel.hidden=true;document.body.classList.remove("has-publish-panel");}}));

  const focus = () => surface.focus();
  document.querySelectorAll("[data-editor-prefix]").forEach((button) => button.addEventListener("click", () => {
    focus(); const prefix=button.dataset.editorPrefix;
    if(prefix==="## ") document.execCommand("formatBlock",false,"h2");
    else if(prefix==="### ") document.execCommand("formatBlock",false,"h3");
    else if(prefix==="> ") document.execCommand("formatBlock",false,"blockquote");
    else if(prefix==="- ") document.execCommand("insertUnorderedList");
    else if(prefix==="1. ") document.execCommand("insertOrderedList");
  }));
  document.querySelectorAll("[data-editor-block]").forEach((button) => button.addEventListener("click", () => { focus(); document.execCommand("insertHTML",false,"<hr><p><br></p>"); }));

  const serialize = () => Array.from(surface.children).map((node) => {
    const text=node.textContent.trim(); const tag=node.tagName.toLowerCase();
    if(tag==="h2") return `## ${text}`; if(tag==="h3") return `### ${text}`; if(tag==="blockquote") return `> ${text}`;
    if(tag==="ul") return Array.from(node.querySelectorAll(":scope > li")).map(li=>`- ${li.textContent.trim()}`).join("\n");
    if(tag==="ol") return Array.from(node.querySelectorAll(":scope > li")).map((li,i)=>`${i+1}. ${li.textContent.trim()}`).join("\n");
    if(tag==="hr") return "---";
    if(tag==="figure"){const img=node.querySelector("img");return img?`![${img.alt}](${img.getAttribute("src")})`:"";}
    return text;
  }).filter(Boolean).join("\n\n");

  const imageButton=document.querySelector("[data-editor-image]"), imageInput=document.querySelector("[data-editor-image-file]"), form=source.closest("form");
  if(imageButton&&imageInput&&form){imageButton.addEventListener("click",()=>imageInput.click());imageInput.addEventListener("change",async()=>{const file=imageInput.files[0];if(!file)return;const alt=window.prompt("Опишіть зображення для людей, які його не бачать")||"";if(!alt.trim()){imageInput.value="";return;}imageButton.disabled=true;const data=new FormData();data.append("image",file);data.append("alt_text",alt);try{const response=await fetch(form.dataset.imageUploadUrl,{method:"POST",body:data,headers:{"X-CSRFToken":form.querySelector("[name=csrfmiddlewaretoken]").value}});if(!response.ok)throw new Error("upload");const result=await response.json();focus();document.execCommand("insertHTML",false,`<figure><img src="${result.url}" alt="${result.alt.replace(/[\"<>]/g,"")}"><figcaption>${result.alt.replace(/[<>]/g,"")}</figcaption></figure><p><br></p>`);}catch(_){window.alert("Не вдалося завантажити зображення. Перевірте формат і розмір файлу.");}finally{imageButton.disabled=false;imageInput.value="";}});}
  form.addEventListener("submit",()=>{source.value=serialize();source.hidden=false;});
});
