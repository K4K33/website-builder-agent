/* Kaurivo Motion Kit v1: progressive enhancement only.
   All content is in the HTML; without this script (or with reduced motion)
   every stage, project and comparison stays readable and usable. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 1. Process reveal: the active real stage follows scroll position.
  document.querySelectorAll("[data-k-process]").forEach(function (root) {
    if (reduce || !("IntersectionObserver" in window)) { root.classList.add("k-static"); return; }
    var frames = root.querySelectorAll(".k-process__frame");
    var steps = root.querySelectorAll(".k-process__step");
    var track = root.querySelector(".k-process__track");
    var current = -1;
    function show(index) {
      if (index === current) return;
      current = index;
      frames.forEach(function (f, i) { f.classList.toggle("is-active", i === index); f.setAttribute("aria-hidden", i === index ? "false" : "true"); });
      steps.forEach(function (s, i) { s.classList.toggle("is-active", i === index); if (i === index) s.setAttribute("aria-current", "step"); else s.removeAttribute("aria-current"); });
    }
    function update() {
      var rect = track.getBoundingClientRect();
      var span = Math.max(1, rect.height - window.innerHeight);
      var progress = Math.min(1, Math.max(0, -rect.top / span));
      show(Math.min(frames.length - 1, Math.floor(progress * frames.length)));
    }
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(function () { update(); ticking = false; }); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  });

  // 2. Cinematic scene: one settle movement after the image is decoded.
  document.querySelectorAll("[data-k-cine]").forEach(function (root) {
    if (reduce) return;
    var img = root.querySelector("img");
    function go() { root.classList.add("is-ready"); }
    if (img && !img.complete) img.addEventListener("load", go, { once: true }); else go();
  });

  // 5. Project explorer: buttons move one project; native swipe/scroll stays.
  document.querySelectorAll("[data-k-explore]").forEach(function (root) {
    var track = root.querySelector(".k-explore__track");
    var prev = root.querySelector("[data-k-prev]");
    var next = root.querySelector("[data-k-next]");
    if (!track || !prev || !next) return;
    function step() { var item = track.querySelector(".k-explore__item"); return item ? item.getBoundingClientRect().width + 16 : 300; }
    function sync() {
      prev.disabled = track.scrollLeft <= 4;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
    }
    prev.addEventListener("click", function () { track.scrollBy({ left: -step(), behavior: reduce ? "auto" : "smooth" }); });
    next.addEventListener("click", function () { track.scrollBy({ left: step(), behavior: reduce ? "auto" : "smooth" }); });
    track.addEventListener("scroll", sync, { passive: true });
    sync();
  });

  // 6. Before / after: a native range input drives the split (keyboard ok).
  document.querySelectorAll("[data-k-compare]").forEach(function (root) {
    var input = root.querySelector("input[type=range]");
    if (!input) return;
    function set() { root.style.setProperty("--k-pos", input.value + "%"); }
    input.addEventListener("input", set);
    set();
  });
})();
