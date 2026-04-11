/* main.js - Frontend logic for AI Tools Recommendation System */

(function () {
  "use strict";

  /* ── DOM refs ───────────────────────────────────────────────────── */
  const queryInput    = document.getElementById("queryInput");
  const searchBtn     = document.getElementById("searchBtn");
  const resultsSection= document.getElementById("resultsSection");
  const cardsGrid     = document.getElementById("cardsGrid");
  const resultsQuery  = document.getElementById("resultsQuery");
  const loadingOverlay= document.getElementById("loadingOverlay");
  const toast         = document.getElementById("toast");
  const retrainBtn    = document.getElementById("retrainBtn");
  const modalBackdrop = document.getElementById("modalBackdrop");
  const modalMsg      = document.getElementById("modalMsg");
  const modalStats    = document.getElementById("modalStats");
  const closeModal    = document.getElementById("closeModal");

  /* ── State ──────────────────────────────────────────────────────── */
  let currentQuery = "";
  let toastTimer   = null;

  /* ── Category emoji map ─────────────────────────────────────────── */
  const categoryEmoji = {
    "Text Generation": "✍️",
    "Image Generation": "🎨",
    "Image Editing": "🖼️",
    "Video Generation": "🎬",
    "Audio Generation": "🎵",
    "Coding": "💻",
    "Research": "🔬",
    "Productivity": "⚡",
    "Writing": "📝",
    "Translation": "🌍",
    "Audio Transcription": "🎙️",
    "Presentation": "📊",
    "3D Generation": "🧊",
    "Video Editing": "✂️",
    "Chatbot": "🤖",
    "AI Platform": "🔧",
    "Automation": "⚙️",
    "Meeting Assistant": "📅",
    "Design": "🎭",
  };

  /* ── Toast ──────────────────────────────────────────────────────── */
  function showToast(msg, type = "success", duration = 3000) {
    clearTimeout(toastTimer);
    toast.textContent = msg;
    toast.className = `toast ${type} show`;
    toastTimer = setTimeout(() => { toast.className = "toast"; }, duration);
  }

  /* ── Loading ────────────────────────────────────────────────────── */
  function setLoading(on) {
    loadingOverlay.style.display = on ? "flex" : "none";
    searchBtn.disabled = on;
  }

  /* ── Recommend ──────────────────────────────────────────────────── */
  async function recommend(query) {
    if (!query.trim()) {
      showToast("Please describe your problem first.", "error");
      queryInput.focus();
      return;
    }

    currentQuery = query.trim();
    setLoading(true);
    resultsSection.style.display = "none";

    try {
      const res = await fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentQuery }),
      });
      const data = await res.json();

      if (!res.ok || data.error) {
        showToast(data.error || "Something went wrong.", "error");
        return;
      }

      renderResults(data.query, data.recommendations);
    } catch (err) {
      showToast("Network error. Is the Flask server running?", "error");
    } finally {
      setLoading(false);
    }
  }

  /* ── Render Results ─────────────────────────────────────────────── */
  function renderResults(query, tools) {
    resultsQuery.textContent = `"${query}"`;
    cardsGrid.innerHTML = "";

    if (!tools || tools.length === 0) {
      cardsGrid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;color:var(--muted);padding:48px 0;">
          <div style="font-size:48px;margin-bottom:16px;">🤔</div>
          <p>No strong matches found. Try rephrasing your query.</p>
        </div>`;
    } else {
      tools.forEach((tool, i) => {
        const card = buildCard(tool, i);
        card.style.animationDelay = `${i * 0.08}s`;
        cardsGrid.appendChild(card);
      });
    }

    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ── Build Card ─────────────────────────────────────────────────── */
  function buildCard(tool, index) {
    const card = document.createElement("div");
    card.className = "tool-card";

    const emoji = categoryEmoji[tool.category] || "🛠️";
    const scorePercent = Math.min(100, Math.round(tool.score * 200));

    card.innerHTML = `
      <div class="card-rank">#${tool.rank}</div>

      <div class="card-header">
        <div class="card-icon-wrap">
          <img
            class="card-icon"
            src="${escHtml(tool.icon_url)}"
            alt="${escHtml(tool.tool_name)} icon"
            onerror="this.style.display='none';this.nextElementSibling.style.display='block';"
          />
          <span class="card-icon-fallback" style="display:none;">${emoji}</span>
        </div>
        <div class="card-meta">
          <div class="card-name">${escHtml(tool.tool_name)}</div>
          <div class="card-category">${emoji} ${escHtml(tool.category)}</div>
        </div>
      </div>

      <p class="card-description">${escHtml(tool.description)}</p>

      <div class="card-score-bar">
        <div class="card-score-fill" style="width:0%" data-target="${scorePercent}"></div>
      </div>

      <div class="card-actions">
        <a href="${escHtml(tool.website_link)}" target="_blank" rel="noopener" class="btn-visit">
          Visit ↗
        </a>
        <div class="feedback-btns">
          <button class="btn-feedback" data-tool="${escHtml(tool.tool_name)}" data-vote="useful" title="Useful">👍</button>
          <button class="btn-feedback" data-tool="${escHtml(tool.tool_name)}" data-vote="not_useful" title="Not useful">👎</button>
        </div>
      </div>
    `;

    // Feedback listeners
    card.querySelectorAll(".btn-feedback").forEach(btn => {
      btn.addEventListener("click", () => handleFeedback(btn, tool.tool_name));
    });

    // Animate score bar after paint
    requestAnimationFrame(() => {
      setTimeout(() => {
        const fill = card.querySelector(".card-score-fill");
        if (fill) fill.style.width = fill.dataset.target + "%";
      }, 100 + index * 80);
    });

    return card;
  }

  /* ── Handle Feedback ────────────────────────────────────────────── */
  async function handleFeedback(btn, toolName) {
    const vote = btn.dataset.vote;
    const siblingBtns = btn.closest(".feedback-btns").querySelectorAll(".btn-feedback");

    siblingBtns.forEach(b => (b.disabled = true));

    try {
      const res = await fetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentQuery, tool_name: toolName, feedback: vote }),
      });
      const data = await res.json();

      if (res.ok) {
        btn.classList.add(vote === "useful" ? "voted-up" : "voted-down");
        showToast(
          vote === "useful" ? `👍 Thanks! "${toolName}" ranked higher.` : `👎 Noted! "${toolName}" ranked lower.`,
          "success"
        );
      } else {
        showToast(data.error || "Feedback failed.", "error");
        siblingBtns.forEach(b => (b.disabled = false));
      }
    } catch {
      showToast("Could not send feedback.", "error");
      siblingBtns.forEach(b => (b.disabled = false));
    }
  }

  /* ── Retrain Model ──────────────────────────────────────────────── */
  async function updateModel() {
    retrainBtn.disabled = true;
    retrainBtn.textContent = "↺ Updating…";

    try {
      const res  = await fetch("/update-model", { method: "POST" });
      const data = await res.json();

      if (res.ok) {
        modalMsg.textContent = data.message || "Model retrained with latest feedback.";
        const s = data.feedback_stats || {};
        modalStats.innerHTML = `
          <div><strong>Total feedback:</strong> ${s.total || 0}</div>
          <div><strong>👍 Useful:</strong> ${s.useful || 0}</div>
          <div><strong>👎 Not useful:</strong> ${s.not_useful || 0}</div>
        `;
        modalBackdrop.style.display = "flex";
      } else {
        showToast(data.error || "Retraining failed.", "error");
      }
    } catch {
      showToast("Could not reach server.", "error");
    } finally {
      retrainBtn.disabled = false;
      retrainBtn.textContent = "↺ Update Model";
    }
  }

  /* ── Utilities ──────────────────────────────────────────────────── */
  function escHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ── Event Listeners ────────────────────────────────────────────── */
  searchBtn.addEventListener("click", () => recommend(queryInput.value));

  queryInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      recommend(queryInput.value);
    }
  });

  document.querySelectorAll(".hint").forEach(h => {
    h.addEventListener("click", () => {
      queryInput.value = h.dataset.q;
      recommend(h.dataset.q);
    });
  });

  retrainBtn.addEventListener("click", updateModel);

  closeModal.addEventListener("click", () => {
    modalBackdrop.style.display = "none";
  });

  modalBackdrop.addEventListener("click", e => {
    if (e.target === modalBackdrop) modalBackdrop.style.display = "none";
  });

  /* ── Auto-resize textarea ───────────────────────────────────────── */
  queryInput.addEventListener("input", () => {
    queryInput.style.height = "auto";
    queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + "px";
  });

})();
