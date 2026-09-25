/* Saved transcription browser; content rendered with textContent, never HTML. */
(() => {
 const list = document.getElementById("transcript-history-list");
 const status = document.getElementById("transcript-history-status");
 const refresh = document.getElementById("transcript-history-refresh");
 const t = (key, params = {}) => window.YTI18n?.t(key, params) ?? key;
 const dateLocale = () => window.YTI18n?.getDateLocale?.() ?? "fr-FR";
 if (!list || !status || !refresh) return;
 async function load() {
  status.textContent = t("saved.loading");
  list.replaceChildren();
  try {
   const response = await fetch("/transcripts");
   if (!response.ok) throw new Error("HTTP " + response.status);
   const data = await response.json();
   for (const item of data.transcripts) {
    const li = document.createElement("li");
    li.className = "list-group-item";
    const title = document.createElement("p");
    title.className = "mb-1";
    title.textContent = item.video_id + " · " + t("saved.characters", {count:item.characters}) + " · " + new Date(item.created_at).toLocaleString(dateLocale());
    const excerpt = document.createElement("p");
    excerpt.className = "text-muted";
    excerpt.textContent = item.preview;
    const open = document.createElement("button");
    open.type = "button"; open.className = "btn btn-primary me-2 mb-2";
    open.textContent = t("saved.open", {id:item.video_id});
    open.addEventListener("click", async () => {
     try {
      const result = await fetch("/transcripts/" + encodeURIComponent(item.video_id));
      if (!result.ok) throw new Error("HTTP " + result.status);
      const record = await result.json();
      document.getElementById("video-id").value = record.video_id;
      const textarea = document.getElementById("transcript-textarea");
      textarea.value = record.transcript;
      // Programmatic value changes do not fire "input". Reuse the main
      // transcript-state handler so every text-dependent action is restored.
      textarea.dispatchEvent(new Event("input", {bubbles:true}));
      status.textContent = t("saved.restored", {id:record.video_id});
      textarea.focus();
     } catch (_) { status.textContent = t("saved.restoreError"); }
    });
    const remove = document.createElement("button");
    remove.type = "button"; remove.className = "btn btn-outline-danger mb-2";
    remove.textContent = t("saved.remove", {id:item.video_id});
    remove.addEventListener("click", async () => {
     if (!window.confirm(t("saved.confirmRemove", {id:item.video_id}))) return;
     try {
      const result = await fetch("/transcripts/" + encodeURIComponent(item.video_id), {method:"DELETE"});
      if (!result.ok) throw new Error("HTTP " + result.status);
      await load();
      status.textContent = t("saved.deleted");
     } catch (_) { status.textContent = t("saved.deleteError"); }
    });
    li.append(title,excerpt,open,remove); list.append(li);
   }
   status.textContent = data.transcripts.length ? t("saved.count", {count:data.transcripts.length}) : t("saved.empty");
  } catch (_) { status.textContent = t("saved.loadError"); }
 }
 refresh.addEventListener("click",load);
 window.addEventListener("yt-language-change", load);
 document.getElementById("transcribe-btn")?.addEventListener("click", () => {
  const button = document.getElementById("transcribe-btn");
  const observer = new MutationObserver(() => {
   if (!button.disabled) { observer.disconnect(); load(); }
  });
  observer.observe(button,{attributes:true,attributeFilter:["disabled"]});
 });
 load();
})();