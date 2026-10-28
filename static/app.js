const airportData = {
  "New York": ["JFK", "United States"], London: ["LHR", "United Kingdom"],
  Paris: ["CDG", "France"], Tokyo: ["HND", "Japan"],
  Singapore: ["SIN", "Singapore"], Dubai: ["DXB", "United Arab Emirates"],
  Lisbon: ["LIS", "Portugal"], Reykjavik: ["KEF", "Iceland"],
  "Cape Town": ["CPT", "South Africa"], Bali: ["DPS", "Indonesia"],
};

const searchForm = document.querySelector("#flight-search");
const resultsArea = document.querySelector("#results");
const fromSelect = document.querySelector("#from-city");
const toSelect = document.querySelector("#to-city");
const dateInput = document.querySelector("#travel-date");
const bookingDialog = document.querySelector("#booking-dialog");
const bookingForm = document.querySelector("#booking-form");

dateInput.min = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
dateInput.value = dateInput.min;

function updateAirportLabels() {
  const [fromCode, fromCountry] = airportData[fromSelect.value];
  const [toCode, toCountry] = airportData[toSelect.value];
  document.querySelector("#from-code").textContent = `${fromCode} · ${fromCountry}`;
  document.querySelector("#to-code").textContent = `${toCode} · ${toCountry}`;
}

fromSelect.addEventListener("change", updateAirportLabels);
toSelect.addEventListener("change", updateAirportLabels);
document.querySelector("#swap-cities").addEventListener("click", () => {
  [fromSelect.value, toSelect.value] = [toSelect.value, fromSelect.value];
  updateAirportLabels();
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function formatDate(value) {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    weekday: "short", month: "short", day: "numeric",
  });
}

function renderFlights(data) {
  const heading = `<div class="results-heading"><div><h3>${escapeHtml(data.route.from)} to ${escapeHtml(data.route.to)}</h3><p>${formatDate(data.route.date)} · ${data.flights.length} sample flights</p></div><span>Sorted by price</span></div>`;
  const cards = data.flights.map((flight) => `
    <article class="flight-card">
      <div class="airline"><span class="airline-mark" style="background:${escapeHtml(flight.color)}">${escapeHtml(flight.mark)}</span><span><strong>${escapeHtml(flight.airline)}</strong><small>${escapeHtml(flight.stops)}</small></span></div>
      <div class="flight-route">
        <span class="flight-time"><strong>${escapeHtml(flight.depart)}</strong><small>${escapeHtml(flight.fromCode)}</small></span>
        <span class="flight-duration"><small>${escapeHtml(flight.duration)}</small><span class="flight-line"></span></span>
        <span class="flight-time"><strong>${escapeHtml(flight.arrive)}</strong><small>${escapeHtml(flight.toCode)}</small></span>
      </div>
      <div class="flight-price"><strong>$${Number(flight.price).toLocaleString()}</strong><small>per traveler · sample fare</small></div>
      <button class="book-button" type="button" data-flight="${escapeHtml(flight.id)}" data-airline="${escapeHtml(flight.airline)}" data-price="${Number(flight.price)}">Choose flight ↗</button>
    </article>`).join("");
  resultsArea.innerHTML = heading + cards;
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = searchForm.querySelector(".search-button");
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Finding flights…";
  resultsArea.innerHTML = "";
  const params = new URLSearchParams(new FormData(searchForm));
  try {
    const response = await fetch(`/api/flights?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Couldn't search flights.");
    renderFlights(data);
    resultsArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    resultsArea.innerHTML = `<div class="error-message">${escapeHtml(error.message)}</div>`;
  } finally {
    button.disabled = false;
    button.querySelector("span:first-child").textContent = "Search flights";
  }
});

resultsArea.addEventListener("click", (event) => {
  const button = event.target.closest("[data-flight]");
  if (!button) return;
  bookingForm.elements.flightId.value = button.dataset.flight;
  document.querySelector("#booking-summary").textContent =
    `${button.dataset.airline} · $${Number(button.dataset.price).toLocaleString()} per traveler.`;
  document.querySelector("#booking-message").textContent = "";
  document.querySelector("#booking-message").classList.remove("error");
  bookingDialog.showModal();
});

bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#booking-message");
  const submit = bookingForm.querySelector("button[type=submit]");
  submit.disabled = true;
  message.textContent = "Confirming your demo booking…";
  message.classList.remove("error");
  try {
    const response = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(new FormData(bookingForm))),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Couldn't complete this booking.");
    message.textContent = `You're going places, ${data.booking.name}! Demo confirmation ${data.booking.reference} is ready.`;
    bookingForm.reset();
  } catch (error) {
    message.textContent = error.message;
    message.classList.add("error");
  } finally {
    submit.disabled = false;
  }
});

const chatPanel = document.querySelector("#chat-panel");
const chatLauncher = document.querySelector("#chat-launcher");
const chatMessages = document.querySelector("#chat-messages");
const chatForm = document.querySelector("#chat-form");

function setChatOpen(open) {
  chatPanel.hidden = !open;
  chatLauncher.setAttribute("aria-expanded", String(open));
  if (open) document.querySelector("#chat-text").focus();
}

chatLauncher.addEventListener("click", () => setChatOpen(chatPanel.hidden));
document.querySelector("#close-chat").addEventListener("click", () => setChatOpen(false));

function appendMessage(text, kind) {
  const node = document.createElement("div");
  node.className = `message ${kind}-message`;
  node.textContent = text;
  chatMessages.append(node);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatMessages.addEventListener("click", (event) => {
  const suggestion = event.target.closest(".suggestion-row button");
  if (!suggestion) return;
  document.querySelector("#chat-text").value = suggestion.textContent;
  chatForm.requestSubmit();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#chat-text");
  const message = input.value.trim();
  if (!message) return;
  appendMessage(message, "user");
  input.value = "";
  const pending = document.createElement("div");
  pending.className = "message bot-message";
  pending.textContent = "One moment…";
  chatMessages.append(pending);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  try {
    const response = await fetch("/api/concierge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "I couldn't send that just now.");
    pending.textContent = data.reply;
  } catch (error) {
    pending.textContent = error.message;
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
});

updateAirportLabels();
