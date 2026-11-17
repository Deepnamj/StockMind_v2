// =====================================
// GLOBAL STATE
// =====================================

let currentThread = null;
let pendingApproval = false;

const $ = (id) => document.getElementById(id);


// =====================================
// FORMAT GEMINI / LANGGRAPH RESPONSE
// =====================================

function formatMessage(content) {

  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {

    return content.map(item => {

      if (typeof item === "string") {
        return item;
      }

      if (item && typeof item.text === "string") {
        return item.text;
      }

      return "";

    }).filter(Boolean).join("\n");
  }

  if (content && typeof content === "object") {

    if (typeof content.text === "string") {
      return content.text;
    }

    return JSON.stringify(content, null, 2);
  }

  return String(content ?? "");
}


// =====================================
// DISPLAY CHAT MESSAGE WITH MARKDOWN
// =====================================

function addMessage(content, who) {

  const div = document.createElement("div");

  div.className = "message " + who;

  const formattedContent = formatMessage(content);

  if (
    who === "bot" &&
    window.marked &&
    window.DOMPurify
  ) {

    const html = window.marked.parse(formattedContent);

    div.innerHTML = window.DOMPurify.sanitize(html);

  } else {

    div.textContent = formattedContent;

  }

  $("chatlog").appendChild(div);

  $("chatlog").scrollTop = $("chatlog").scrollHeight;
}


// =====================================
// ESCAPE HTML
// =====================================

function escapeHtml(value) {

  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);

}


// =====================================
// FORMAT FINANCIAL VALUES
// =====================================

function fmt(value) {

  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return value.toLocaleString(undefined, {
      maximumFractionDigits: 2
    });
  }

  return String(value);
}


// =====================================
// FINANCIAL METRIC CARD
// =====================================

function metric(label, value) {

  return `
    <div class="metric">
      <label>${escapeHtml(label)}</label>
      <strong>${escapeHtml(fmt(value))}</strong>
    </div>
  `;
}


// =====================================
// API RESPONSE HELPER
// =====================================

async function readApiResponse(response) {

  const responseText = await response.text();

  let data;

  try {

    data = JSON.parse(responseText);

  } catch (error) {

    throw new Error(
      `Invalid API response (HTTP ${response.status}): ${responseText}`
    );

  }

  if (!response.ok) {
    throw new Error(data.detail || "API request failed");
  }

  return data;
}


// =====================================
// COMPANY SEARCH
// =====================================

async function searchCompanies() {

  const q = $("search").value.trim();

  if (!q) return;

  $("matches").textContent = "Searching companies...";
  $("searchBtn").disabled = true;

  try {

    const response = await fetch(
      `/api/search?q=${encodeURIComponent(q)}`
    );

    const data = await readApiResponse(response);

    $("matches").innerHTML = "";

    const matches = data.matches || [];

    if (!matches.length) {

      $("matches").textContent = "No matching companies found.";

      return;
    }

    matches.forEach(item => {

      const btn = document.createElement("button");

      btn.className = "match secondary";

      btn.textContent =
        `${item.symbol || ""} — ${item.name || "Company"}`;

      btn.onclick = () => loadCompany(item.symbol);

      $("matches").appendChild(btn);

    });

  } catch (error) {

    $("matches").textContent =
      "Search failed: " + error.message;

  } finally {

    $("searchBtn").disabled = false;

  }
}



// =====================================
// LOAD COMPANY OVERVIEW
// =====================================

async function loadCompany(symbol) {

  if (!symbol) return;

  $("company").innerHTML =
    "<p class='empty-state'>Loading company data...</p>";

  try {

    const response = await fetch(
      `/api/company/${encodeURIComponent(symbol)}`
    );

    const result = await readApiResponse(response);

    const d = result.data || {};

    const profile = d.get_company_profile || {};
    const price = d.get_stock_price || {};
    const f = d.get_company_fundamentals || {};
    const history = d.get_stock_history || {};
    const news = d.get_stock_news || {};

    const name =
      profile.longName ||
      profile.shortName ||
      symbol;

    // Historical chart

    const historyRows = history.prices || [];

    const chart = historyRows.slice(-60);

    let chartHtml =
      "<p class='muted'>Historical chart data unavailable.</p>";

    if (chart.length) {

      const values = chart
        .map(x => Number(x.close))
        .filter(x => Number.isFinite(x));

      if (values.length) {

        const min = Math.min(...values);
        const max = Math.max(...values);
        const span = (max - min) || 1;

        const points = values.map((v, i) => {

          const x =
            (i / (values.length - 1 || 1)) * 600;

          const y =
            110 - ((v - min) / span) * 95;

          return `${x},${y}`;

        }).join(" ");

        chartHtml = `
          <div class="chart-container">

            <svg
              viewBox="0 0 600 120"
              width="100%"
              role="img"
              aria-label="Historical closing prices"
            >

              <line
                x1="0"
                y1="110"
                x2="600"
                y2="110"
                stroke="#344564"
                stroke-width="1"
              />

              <polyline
                points="${points}"
                fill="none"
                stroke="#36d399"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

            </svg>

          </div>
        `;
      }
    }

    // Company news

    const articles = news.news || [];

    let newsHtml = articles.length
      ? `<ul>
          ${articles.map(n => {

            let link = "#";

            try {

              const parsedUrl = new URL(n.link || "#");

              if (
                ["http:", "https:"].includes(parsedUrl.protocol)
              ) {
                link = escapeHtml(parsedUrl.href);
              }

            } catch (error) {}

            return `
              <li>

                <a
                  href="${link}"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ${escapeHtml(n.title || "News article")}
                </a>

                <div class="muted">
                  ${escapeHtml(n.publisher || "")}
                  ${escapeHtml(n.published || "")}
                </div>

              </li>
            `;

          }).join("")}
        </ul>`
      : "<p class='muted'>No news items returned.</p>";

    // Price change styling

    const change = Number(price.change);

    const priceClass =
      Number.isFinite(change)
        ? change >= 0 ? "price-positive" : "price-negative"
        : "";

    // Company dashboard

    $("company").innerHTML = `

      <div class="company-head">

        <div>

          <h2>${escapeHtml(name)}</h2>

          <div class="symbol">
            ${escapeHtml(symbol)}
            · ${escapeHtml(profile.sector || "Sector unavailable")}
            · ${escapeHtml(profile.industry || "Industry unavailable")}
          </div>

        </div>

        <button class="secondary" id="askCompanyBtn">
          Ask AI
        </button>

      </div>

      <div class="price ${priceClass}">
        ${price.price !== undefined
          ? escapeHtml(fmt(price.price))
          : "Price unavailable"}

        <span class="muted">
          ${escapeHtml(price.currency || "")}
        </span>
      </div>

      <div class="muted">
        Previous close: ${escapeHtml(fmt(price.previous_close))}
        · Change: ${escapeHtml(fmt(price.change))}
        (${escapeHtml(fmt(price.change_percent))}%)
        · Data date: ${escapeHtml(price.data_date || "—")}
      </div>

      <div class="section">

        <h3>Company profile</h3>

        <p>
          ${escapeHtml(
            profile.longBusinessSummary ||
            "Company description unavailable."
          )}
        </p>

        <div class="grid">

          ${metric(
            "Headquarters",
            [profile.city, profile.state, profile.country]
              .filter(Boolean).join(", ")
          )}

          ${metric("Website", profile.website)}

          ${metric("Employees", profile.fullTimeEmployees)}

          ${metric("Industry", profile.industry)}

        </div>

      </div>

      <div class="section">

        <h3>Financial fundamentals</h3>

        <div class="grid">

          ${metric("Market capitalization", f.marketCap)}

          ${metric("Trailing P/E", f.trailingPE)}

          ${metric("Forward P/E", f.forwardPE)}

          ${metric("EPS", f.trailingEps)}

          ${metric("Revenue", f.totalRevenue)}

          ${metric("Revenue growth", f.revenueGrowth)}

          ${metric("Profit margin", f.profitMargins)}

          ${metric("Return on equity", f.returnOnEquity)}

        </div>

      </div>

      <div class="section">

        <h3>Historical closing price</h3>

        ${chartHtml}

        <div class="muted">
          Last 6 months · Yahoo Finance via yfinance.
          Historical data may be incomplete or delayed.
        </div>

      </div>

      <div class="section news">

        <h3>Latest company news</h3>

        ${newsHtml}

      </div>

      <div class="section">

        <h3>AI company analysis</h3>

        <p class="muted">
          Ask StockMind to explain these figures, compare this
          company with another, or summarize its recent performance.
          This is AI-generated information, not a verified investment
          recommendation.
        </p>

      </div>

    `;

    $("askCompanyBtn").onclick = () => askAbout(symbol);

  } catch (error) {

    $("company").textContent =
      "Could not load company: " + error.message;

  }
}

// =====================================
// ASK AI ABOUT A COMPANY
// =====================================

function askAbout(symbol) {

  $("question").value =
    `Give me an overview of ${symbol}, including its business and financial fundamentals.`;

  sendQuestion();
}


// =====================================
// CHAT WITH STOCKMIND
// =====================================

async function sendQuestion() {

  const message = $("question").value.trim();

  if (!message) return;

  $("question").value = "";

  addMessage(message, "user");

  $("chatStatus").textContent = "StockMind is thinking...";
  $("chatStatus").className = "status";

  $("sendBtn").disabled = true;

  try {

    const response = await fetch("/api/chat", {

      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        message,
        thread_id: currentThread
      })

    });

    const data = await readApiResponse(response);

    currentThread = data.thread_id;

    if (data.status === "approval_required") {

      pendingApproval = true;

      $("approval").classList.remove("hidden");

      $("approvalText").textContent =
        JSON.stringify(data.approval, null, 2);

      addMessage(
        data.reply || "Approval required.",
        "bot"
      );

    } else {

      addMessage(
        data.reply || "No response returned.",
        "bot"
      );

    }

    $("chatStatus").textContent = "";

  } catch (error) {

    $("chatStatus").textContent =
      "Error: " + error.message;

    $("chatStatus").className = "status error";

  } finally {

    $("sendBtn").disabled = false;

  }
}


// =====================================
// HUMAN APPROVAL / REJECTION
// =====================================

async function sendDecision(decision) {

  if (!currentThread || !pendingApproval) return;

  $("chatStatus").textContent = "Resuming workflow...";
  $("chatStatus").className = "status";

  $("approveBtn").disabled = true;
  $("rejectBtn").disabled = true;

  try {

    const response = await fetch("/api/approve", {

      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        thread_id: currentThread,
        decision
      })

    });

    const data = await readApiResponse(response);

    if (data.status === "approval_required") {

      pendingApproval = true;

      $("approvalText").textContent =
        JSON.stringify(data.approval, null, 2);

      addMessage(
        "Another approval is required.",
        "bot"
      );

    } else {

      pendingApproval = false;

      $("approval").classList.add("hidden");

      addMessage(
        data.reply || "Workflow completed.",
        "bot"
      );

      $("chatStatus").textContent =
        decision === "approve"
          ? "Simulation approved."
          : "Simulation rejected.";

      $("chatStatus").className = "status success";

    }

  } catch (error) {

    $("chatStatus").textContent =
      "Error: " + error.message;

    $("chatStatus").className = "status error";

  } finally {

    $("approveBtn").disabled = false;
    $("rejectBtn").disabled = false;

  }
}


// =====================================
// EVENT LISTENERS
// =====================================

$("searchBtn").onclick = searchCompanies;

$("search").addEventListener("keydown", event => {

  if (event.key === "Enter") {
    searchCompanies();
  }

});

$("sendBtn").onclick = sendQuestion;

$("question").addEventListener("keydown", event => {

  if (event.key === "Enter") {
    sendQuestion();
  }

});

$("approveBtn").onclick = () => {
  sendDecision("approve");
};

$("rejectBtn").onclick = () => {
  sendDecision("reject");
};