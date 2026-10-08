/* Auth page client logic — login / signup / forgot password.
   Validation lives here AND on the server (backend/app/auth.py); the UI never
   blocks logic that the API does not enforce as well. */

(function () {
  "use strict";

  if (!window.AUTH_NEXT) window.AUTH_NEXT = "/";

  // ------------------------------------------------------------ helpers
  const $ = (id) => document.getElementById(id);
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  function setMsg(id, text, ok) {
    const el = $(id);
    if (!el) return;
    el.textContent = text || "";
    el.classList.toggle("ok", Boolean(ok));
  }

  function setInvalid(input, invalid) {
    input.classList.toggle("invalid", Boolean(invalid));
  }

  function showError(text) {
    const el = $("form-error");
    if (el) el.textContent = text;
  }

  function setLoading(btn, loading) {
    const label = btn.querySelector(".btn-label");
    const spinner = btn.querySelector(".spinner");
    btn.disabled = loading;
    if (spinner) spinner.hidden = !loading;
    if (label && loading) label.setAttribute("data-text", label.textContent);
    if (label && !loading && label.dataset.text) {
      label.textContent = label.dataset.text;
    }
  }

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    return { res, data };
  }

  // ------------------------------------------------- password visibility
  document.querySelectorAll(".pw-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = $(btn.dataset.target);
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "🙈" : "👁";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      input.focus({ preventScroll: true });
    });
  });

  // ------------------------------------------------- login
  const loginForm = $("login-form");
  if (loginForm) {
    const email = $("email");
    const password = $("password");
    const btn = $("login-btn");

    const validateEmail = () => {
      const ok = EMAIL_RE.test(email.value.trim());
      setInvalid(email, email.value.trim() !== "" && !ok);
      return ok;
    };
    const validatePassword = () => {
      const ok = password.value !== "";
      setInvalid(password, !ok && password.value !== "");
      return ok;
    };

    email.addEventListener("input", () => {
      validateEmail();
      showError("");
    });
    password.addEventListener("input", () => {
      validatePassword();
      showError("");
    });

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      showError("");
      if (!validateEmail() || !validatePassword()) {
        setMsg("email-msg", EMAIL_RE.test(email.value.trim()) ? "" : "Enter a valid email address.");
        setMsg("password-msg", password.value !== "" ? "" : "Password is required.");
        email.focus();
        return;
      }
      setLoading(btn, true);
      const { res, data } = await postJSON("/api/auth/login", {
        email: email.value.trim(),
        password: password.value,
        remember: Boolean($("remember") && $("remember").checked),
      });
      setLoading(btn, false);
      if (res.ok) {
        window.location.assign(AUTH_NEXT || "/");
      } else {
        showError(data.detail || "Invalid email or password.");
        password.value = "";
        password.focus();
      }
    });
  }

  // ------------------------------------------------- signup
  const signupForm = $("signup-form");
  if (signupForm) {
    const name = $("full_name");
    const email = $("email");
    const password = $("password");
    const confirm = $("confirm");
    const btn = $("signup-btn");

    const validators = {
      full_name: () => name.value.trim() !== "",
      email: () => EMAIL_RE.test(email.value.trim()),
      password: () => password.value.length >= 6,
      confirm: () => confirm.value === password.value && password.value !== "",
    };
    const messages = {
      full_name: "Full name is required.",
      email: "Enter a valid email address.",
      password: "Password must be at least 6 characters.",
      confirm: "Passwords do not match.",
    };

    Object.keys(validators).forEach((key) => {
      const field = $("signup-form");
      const input = $(key);
      input.addEventListener("input", () => {
        setInvalid(input, !validators[key]() && input.value !== "");
        setMsg(key + "-msg", "", false);
        showError("");
      });
    });

    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      showError("");
      let firstInvalid = null;
      for (const key of Object.keys(validators)) {
        const input = $(key);
        const ok = validators[key]();
        setInvalid(input, !ok);
        setMsg(key + "-msg", ok ? "" : messages[key]);
        if (!ok && !firstInvalid) firstInvalid = input;
      }
      if (firstInvalid) {
        firstInvalid.focus();
        return;
      }
      setLoading(btn, true);
      const { res, data } = await postJSON("/api/auth/signup", {
        full_name: name.value.trim(),
        email: email.value.trim(),
        password: password.value,
      });
      setLoading(btn, false);
      if (res.ok) {
        window.location.assign("/");
      } else {
        showError(data.detail || "Could not create your account.");
      }
    });
  }

  // ------------------------------------------------- forgot password
  const forgotForm = $("forgot-form");
  if (forgotForm) {
    const email = $("email");
    const btn = $("forgot-btn");
    const success = $("form-success");

    email.addEventListener("input", () => {
      const ok = EMAIL_RE.test(email.value.trim());
      setInvalid(email, !ok && email.value.trim() !== "");
      setMsg("email-msg", "", false);
      showError("");
      if (success) success.hidden = true;
    });

    forgotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      showError("");
      const ok = EMAIL_RE.test(email.value.trim());
      setInvalid(email, !ok);
      setMsg("email-msg", ok ? "" : "Enter a valid email address.");
      if (!ok) {
        email.focus();
        return;
      }
      setLoading(btn, true);
      const { res, data } = await postJSON("/api/auth/forgot", {
        email: email.value.trim(),
      });
      setLoading(btn, false);
      if (res.ok) {
        if (success) {
          success.textContent =
            "The reset link request was received. " +
            (data.message || "No email service is connected in demo mode — nothing was sent.");
          success.hidden = false;
        }
        email.value = "";
      } else {
        showError(data.detail || "Something went wrong. Please try again.");
      }
    });
  }
})();