/* Dark by default; explicit choice persists locally across both screens. */
(() => {
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  function apply(theme) {
    const dark = theme !== "light";
    const t = window.YTI18n?.t || ((key) => key);
    root.setAttribute("data-bs-theme", dark ? "dark" : "light");
    button.setAttribute("aria-pressed", String(!dark));
    button.setAttribute("aria-label", dark ? t("theme.lightAria") : t("theme.darkAria"));
    button.textContent = dark ? t("theme.light") : t("theme.dark");
  }
  let saved = null;
  try { saved = localStorage.getItem("yt-transcript-theme"); } catch (_) { /* Storage may be unavailable. */ }
  apply(saved === "light" ? "light" : "dark");
  window.addEventListener("yt-language-change", () => {
    apply(root.getAttribute("data-bs-theme") === "light" ? "light" : "dark");
  });

  button.addEventListener("click", () => {
    const next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem("yt-transcript-theme", next); } catch (_) { /* Still usable without storage. */ }
    window.dispatchEvent(new CustomEvent("yt-theme-change", {detail:{theme:next}}));
  });
})();
