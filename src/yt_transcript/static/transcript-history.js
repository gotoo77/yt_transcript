/* Saved transcription browser; content rendered with textContent, never HTML. */
(() => {
 const list = document.getElementById("transcript-history-list");
 const status = document.getElementById("transcript-history-status");
 const refresh = document.getElementById("transcript-history-refresh");
 if (!list || !status || !refresh) return;
 async function load() {
  status.textContent = "Chargement des transcriptions…";
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
    title.textContent = item.video_id + " · " + item.characters + " caractères · " + new Date(item.created_at).toLocaleString();
    const excerpt = document.createElement("p");
    excerpt.className = "text-muted";
    excerpt.textContent = item.preview;
    const open = document.createElement("button");
    open.type = "button"; open.className = "btn btn-primary me-2 mb-2";
    open.textContent = "Ouvrir " + item.video_id;
    open.addEventListener("click", async () => {
     try {
      const result = await fetch("/transcripts/" + encodeURIComponent(item.video_id));
      if (!result.ok) throw new Error("HTTP " + result.status);
      const record = await result.json();
      document.getElementById("video-id").value = record.video_id;
      document.getElementById("transcript-textarea").value = record.transcript;
      document.getElementById("analyze-btn").disabled = false;
      document.getElementById("summary-btn").disabled = false;
      status.textContent = "Transcription restaurée : " + record.video_id;
      document.getElementById("transcript-textarea").focus();
     } catch (_) { status.textContent = "Impossible de restaurer la transcription."; }
    });
    const remove = document.createElement("button");
    remove.type = "button"; remove.className = "btn btn-outline-danger mb-2";
    remove.textContent = "Supprimer " + item.video_id;
    remove.addEventListener("click", async () => {
     if (!window.confirm("Supprimer la transcription " + item.video_id + " ?")) return;
     try {
      const result = await fetch("/transcripts/" + encodeURIComponent(item.video_id), {method:"DELETE"});
      if (!result.ok) throw new Error("HTTP " + result.status);
      await load();
      status.textContent = "Transcription supprimée.";
     } catch (_) { status.textContent = "Impossible de supprimer la transcription."; }
    });
    li.append(title,excerpt,open,remove); list.append(li);
   }
   status.textContent = data.transcripts.length ? data.transcripts.length + " transcription(s) sauvegardée(s)." : "Aucune transcription sauvegardée.";
  } catch (_) { status.textContent = "Impossible de charger l'historique."; }
 }
 refresh.addEventListener("click",load);
 document.getElementById("transcribe-btn")?.addEventListener("click", () => {
  const button = document.getElementById("transcribe-btn");
  const observer = new MutationObserver(() => {
   if (!button.disabled) { observer.disconnect(); load(); }
  });
  observer.observe(button,{attributes:true,attributeFilter:["disabled"]});
 });
 load();
})();