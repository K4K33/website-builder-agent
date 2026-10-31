/* Kaurivo private customer feedback.
   No third-party credentials in client; FormSubmit email submission only.
   Never claim that feedback was saved unless the provider confirms success. */
(function () {
  "use strict";
  var form = document.getElementById("customer-feedback-form");
  if (!form) return;
  var stars = Array.prototype.slice.call(form.querySelectorAll('input[name="rating"]'));
  var output = document.getElementById("rating-output");
  var status = document.getElementById("feedback-status");
  var submit = document.getElementById("feedback-submit");
  var reference = document.getElementById("feedback-ref");
  var params = new URLSearchParams(window.location.search);
  var lang = params.get("lang") === "fi" ? "fi" : "en";
  var texts = {
    en: { selected: "Selected: ", stars: " / 5 stars",
      placeholder: "Select your rating",
      saving: "Sending feedback…",
      success: "Thank you! Your private feedback was received by the form service.",
      failed: "We couldn't confirm delivery. Your feedback has not been marked as sent. Try again later or contact Kaurivo by email.",
      network: "Could not connect to the feedback service. Your feedback has not been saved. Please try again.",
      choose: "Choose 1–5 stars before submitting." },
    fi: { selected: "Valittu: ", stars: " / 5 tähteä",
      placeholder: "Valitse arvosana",
      saving: "Lähetetään palautetta…",
      success: "Kiitos! Palaute vastaanotettiin lomakepalvelussa.",
      failed: "Lähetystä ei voitu vahvistaa. Palautetta ei merkitty lähetetyksi. Yritä myöhemmin tai ota yhteyttä Kaurivoon.",
      network: "Palautepalveluun ei saatu yhteyttä. Palautetta ei tallennettu. Yritä uudelleen.",
      choose: "Valitse ensin arvosana 1–5 tähteä." }
  };
  function strings() {
    return texts[document.documentElement.lang === "fi" ? "fi" : lang];
  }
  var selected = null;
  function paint() {
    selected = stars.find(function (el) { return el.checked; }) || null;
    var value = selected ? Number(selected.value) : 0;
    stars.forEach(function (input) {
      input.parentElement.classList.toggle("is-lit", Number(input.value) <= value);
    });
    output.textContent = value
      ? strings().selected + value + strings().stars
      : strings().placeholder;
  }
  stars.forEach(function (input) {
    input.addEventListener("change", paint);
  });
  if (/^[1-5]$/.test(params.get("rating") || "")) {
    var preset = stars.find(function (input) { return input.value === params.get("rating"); });
    if (preset) preset.checked = true;
  }
  if (reference) {
    var ref = params.get("ref") || "";
    // The reference must not include email addresses or other personal data.
    if (/^[a-zA-Z0-9_-]{4,50}$/.test(ref)) reference.value = ref;
  }
  paint();
  var observer = new MutationObserver(function () { paint(); });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  function message(text, kind) {
    status.textContent = text;
    status.className = "feedback-status feedback-status-" + kind;
  }
  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (submit.disabled) return;
    if (!selected) {
      message(strings().choose, "error");
      stars[0].focus();
      return;
    }
    if (!form.reportValidity()) return;
    var honeypot = form.querySelector('input[name="_honey"]');
    if (honeypot && honeypot.value) return;
    var payload = {};
    var values = new FormData(form);
    values.forEach(function (value, key) { payload[key] = String(value); });
    // Provide a recognisable subject and stage to ease later automatic triage.
    payload.rating = String(selected.value);
    payload.feedback_stage = "post_sale_experience";
    payload.submitted_from = "kaurivo_website";
    submit.disabled = true;
    message(strings().saving, "pending");
    try {
      var response = await fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(payload),
        credentials: "omit"
      });
      var data;
      try { data = await response.json(); }
      catch (_) { data = null; }
      // FormSubmit may report HTTP 200 even on activation/error; check explicit status.
      var isSuccess = response.ok && data &&
        (data.success === true || data.success === "true");
      if (!isSuccess) {
        message(strings().failed, "error");
        return;
      }
      message(strings().success, "success");
      form.classList.add("feedback-sent");
      // Avoid resubmission; leave rating visible as confirmation.
      form.querySelectorAll("input,textarea,button").forEach(function (el) {
        el.disabled = true;
      });
    } catch (err) {
      message(strings().network, "error");
    } finally {
      if (!form.classList.contains("feedback-sent")) submit.disabled = false;
    }
  });
})();