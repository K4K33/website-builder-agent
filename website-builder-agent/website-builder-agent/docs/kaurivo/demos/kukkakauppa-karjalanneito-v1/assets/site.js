/* Concept-only interactions. No tracking or simulated commerce. */
(() => {
  "use strict";
  const toggle = document.querySelector("[data-nav-toggle]");
  const mobile = document.querySelector("[data-mobile-nav]");
  function setNav(open) {
    if (!toggle || !mobile) return;
    toggle.setAttribute("aria-expanded", String(open));
    mobile.setAttribute("data-open", String(open));
    mobile.setAttribute("aria-hidden", String(!open));
    toggle.setAttribute("aria-label", open ? "Sulje valikko" : "Avaa valikko");
  }
  if (toggle && mobile) {
    setNav(false);
    toggle.addEventListener("click", () =>
      setNav(toggle.getAttribute("aria-expanded") !== "true")
    );
    mobile.querySelectorAll("a").forEach((link) =>
      link.addEventListener("click", () => setNav(false))
    );
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setNav(false);
        toggle.focus();
      }
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 830) setNav(false);
    });
  }
  const gallery = document.querySelector("[data-gallery]");
  if (!gallery) return;
  const photos = Array.from(gallery.querySelectorAll("[data-gallery-item]"));
  const filters = Array.from(document.querySelectorAll("[data-gallery-filter]"));
  const count = document.querySelector("[data-gallery-count]");
  let current = "kaikki";
  let activeItems = [];
  function applyFilter(category, updateUrl) {
    const valid = new Set(filters.map((filter) => filter.dataset.galleryFilter));
    current = valid.has(category) ? category : "kaikki";
    let n = 0;
    photos.forEach((figure) => {
      const visible = current === "kaikki" || figure.dataset.category === current;
      figure.hidden = !visible;
      n += visible ? 1 : 0;
    });
    filters.forEach((filter) =>
      filter.setAttribute("aria-pressed", String(filter.dataset.galleryFilter === current))
    );
    if (count) count.textContent = n + " kuvaa";
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.hash = current === "kaikki" ? "galleria" : current;
      window.history.replaceState({}, "", url);
    }
    activeItems = photos.filter((item) => !item.hidden);
  }
  filters.forEach((filter) =>
    filter.addEventListener("click", () => applyFilter(filter.dataset.galleryFilter, true))
  );
  applyFilter(window.location.hash.replace("#", ""), false);
  window.addEventListener("hashchange", () =>
    applyFilter(window.location.hash.replace("#", ""), false)
  );
  const lightbox = document.querySelector("[data-lightbox]");
  if (!lightbox) return;
  const lightboxImage = lightbox.querySelector("[data-lightbox-image]");
  const lightboxCaption = lightbox.querySelector("[data-lightbox-caption]");
  const close = lightbox.querySelector("[data-lightbox-close]");
  const prev = lightbox.querySelector("[data-lightbox-prev]");
  const next = lightbox.querySelector("[data-lightbox-next]");
  let index = 0;
  let formerFocus = null;
  function show(indexToShow) {
    if (!activeItems.length) return;
    index = (indexToShow + activeItems.length) % activeItems.length;
    const figure = activeItems[index];
    const picture = figure.querySelector("img");
    lightboxImage.src = picture.currentSrc || picture.src;
    lightboxImage.alt = picture.alt;
    lightboxCaption.textContent =
      (figure.dataset.label || "Kukkatyö") + " · " +
      (index + 1) + "/" + activeItems.length;
  }
  function openAt(figure) {
    activeItems = photos.filter((item) => !item.hidden);
    const selected = activeItems.indexOf(figure);
    if (selected === -1) return;
    formerFocus = document.activeElement;
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    show(selected);
    close.focus();
  }
  function closeLightbox() {
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    lightboxImage.removeAttribute("src");
    if (formerFocus && typeof formerFocus.focus === "function") formerFocus.focus();
  }
  photos.forEach((figure) => {
    const button = figure.querySelector("button");
    if (button) button.addEventListener("click", () => openAt(figure));
  });
  close.addEventListener("click", closeLightbox);
  prev.addEventListener("click", () => show(index - 1));
  next.addEventListener("click", () => show(index + 1));
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) closeLightbox();
  });
  document.addEventListener("keydown", (event) => {
    if (lightbox.getAttribute("aria-hidden") !== "false") return;
    if (event.key === "Escape") closeLightbox();
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
    if (event.key === "Tab") {
      const controls = [close, prev, next];
      const at = controls.indexOf(document.activeElement);
      if (event.shiftKey && at === 0) {
        event.preventDefault();
        next.focus();
      } else if (!event.shiftKey && at === controls.length - 1) {
        event.preventDefault();
        close.focus();
      }
    }
  });
})();