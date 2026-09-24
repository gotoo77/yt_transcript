/* Dark by default; explicit choice persists locally across both screens. */
(() => {
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  function apply(theme) {
    const dark = theme !== "light";
    root.setAttribute("data-bs-theme", dark ? "dark" : "light");
    button.setAttribute("aria-pressed", String(!dark));
    button.setAttribute("aria-label", dark ? "Activer le thème clair" : "Activer le thème sombre");
    button.textContent = dark ? "☀ Thème clair" : "☾ Thème sombre";
  }
  let saved = null;
  try { saved = localStorage.getItem("yt-transcript-theme"); } catch (_) { /* Storage may be unavailable. */ }
  apply(saved === "light" ? "light" : "dark");
  button.addEventListener("click", () => {
    const next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem("yt-transcript-theme", next); } catch (_) { /* Still usable without storage. */ }
    window.dispatchEvent(new CustomEvent("yt-theme-change", {detail:{theme:next}}));
  });
})();
