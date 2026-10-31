/* Kaurivo private customer feedback.
   Uses Kaurivo-only Supabase Edge Function and a 43-character,
   one-time customer invitation token kept in the URL fragment.
   No API keys or private account records are exposed to visitors. */
(function () {
  "use strict";
  var form = document.getElementById("customer-feedback-form");
  if (!form) return;
  var stars = Array.prototype.slice.call(form.querySelectorAll('input[name="rating"]'));
  var output = document.getElementById("rating-output");
  var status = document.getElementById("feedback-status");
  var submit = document.getElementById("feedback-submit");
  var token = new URLSearchParams(window.location.hash.replace(/^#/, "")).get("invite") || "";
  var tokenIsValid = /^[A-Za-z0-9_-]{43}$/.test(token);
  var params = new URLSearchParams(window.location.search);
  var lang = params.get("lang") === "fi" ? "fi" : "en";
  var texts = {
    en: { selected: "Selected: ", stars: " / 5 stars",
      placeholder: "Select your rating",
      saving: "Sending feedback…",
      success: "Thank you! Your feedback has been saved privately in Kaurivo’s database.",
      failed: "We couldn't confirm delivery. Your feedback has not been marked as sent. Try again later or contact Kaurivo by email.",
      network: "Could not connect to the feedback service. Your feedback has not been saved. Please try again.",
      choose: "Choose 1–5 stars before submitting.",
      invite: "A personal feedback link is required. Please open the link in your Kaurivo customer email.",
      used: "This feedback invitation is invalid, expired or already used. Contact Kaurivo if you need a new link." },
    fi: { selected: "Valittu: ", stars: " / 5 tähteä",
      placeholder: "Valitse arvosana",
      saving: "Lähetetään palautetta…",
      success: "Kiitos! Palaute tallennettiin Kaurivon omaan tietokantaan.",
      failed: "Lähetystä ei voitu vahvistaa. Palautetta ei merkitty lähetetyksi. Yritä myöhemmin tai ota yhteyttä Kaurivoon.",
      network: "Palautepalveluun ei saatu yhteyttä. Palautetta ei tallennettu. Yritä uudelleen.",
      choose: "Valitse ensin arvosana 1–5 tähteä.",
      invite: "Palautteen lähettämiseen tarvitaan henkilökohtainen kutsulinkki. Avaa Kaurivon lähettämä asiakassähköposti.",
      used: "Palautekutsu on virheellinen, vanhentunut tai jo käytetty. Pyydä tarvittaessa uusi linkki Kaurivolta." }
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
  // Invite token is in the URL fragment, never in the HTTP request path
  // to GitHub Pages or its analytics. A token alone is not publicly verifiable.
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
    if (!tokenIsValid) {
      message(strings().invite, "error");
      return;
    }
    if (!form.reportValidity()) return;
    var honeypot = form.querySelector('input[name="_honey"]');
    if (honeypot && honeypot.value) return;
    var payload = {
      invitation: token,
      rating: Number(selected.value),
      message: document.getElementById("feedback-message").value,
      company: document.getElementById("feedback-company").value,
      email: document.getElementById("feedback-email").value
    };
    submit.disabled = true;
    message(strings().saving, "pending");
    try {
      var response = await fetch(form.action, {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(payload),
        credentials: "omit"
      });
      var data;
      try { data = await response.json(); }
      catch (_) { data = null; }
      // A successful API response must explicitly confirm the database write.
      var isSuccess = response.ok && data && data.success === true;
      if (!isSuccess) {
        message(data && data.error === "invalid_or_used" ? strings().used : strings().failed, "error");
        return;
      }
      message(strings().success, "success");
      // Prevent forwarding a used bearer token when copying this page URL.
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
      }
      token = "";
      tokenIsValid = false;
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