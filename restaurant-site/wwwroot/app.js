const menuGrid = document.querySelector("#menu-grid");
const reservationForm = document.querySelector("#reservation-form");
const reservationDate = reservationForm.elements.date;
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
reservationDate.min = today;
reservationDate.value = today;

let menuItems = [];

function renderMenu(category = "All") {
  const visible = category === "All"
    ? menuItems
    : menuItems.filter((item) => item.category === category);

  menuGrid.innerHTML = visible.map((item) => `
    <article class="menu-item">
      <div class="dish-topline"><span class="dish-number">${item.id} · ${item.vegetarian ? '<span class="veg-mark" aria-label="Vegetarian">✳</span>' : ""}</span><span class="dish-emoji" aria-hidden="true">${item.emoji}</span></div>
      <h3>${escapeHtml(item.name)}</h3>
      <p>${escapeHtml(item.description)}</p>
      <div class="dish-bottom"><span class="dish-category">${escapeHtml(item.category)}</span><span class="dish-price">$${Number(item.price).toFixed(0)}</span></div>
    </article>`).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

document.querySelector(".menu-filters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (!button) return;
  document.querySelectorAll(".filter").forEach((filter) => {
    const active = filter === button;
    filter.classList.toggle("active", active);
    filter.setAttribute("aria-pressed", String(active));
  });
  renderMenu(button.dataset.category);
});

async function loadMenu() {
  try {
    const response = await fetch("/api/menu");
    if (!response.ok) throw new Error("The menu is temporarily unavailable.");
    menuItems = await response.json();
    renderMenu();
    document.querySelector('.filter[data-category="All"] span').textContent =
      String(menuItems.length).padStart(2, "0");
  } catch {
    menuGrid.innerHTML = '<p class="menu-loading">Our menu could not be loaded. Please refresh to try again.</p>';
  }
}

reservationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#form-message");
  const button = reservationForm.querySelector("button[type=submit]");
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Saving your table…";
  message.textContent = "";
  message.classList.remove("error");

  try {
    const payload = Object.fromEntries(new FormData(reservationForm));
    payload.guests = Number(payload.guests);
    const response = await fetch("/api/reservations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      const details = data.errors ? Object.values(data.errors).flat().join(" ") : data.title;
      throw new Error(details || "We couldn't save your reservation.");
    }
    message.textContent = `Wonderful, ${data.name}! Your table request is in. Confirmation: ${data.confirmation}.`;
    reservationForm.reset();
    reservationDate.value = today;
  } catch (error) {
    message.textContent = error.message;
    message.classList.add("error");
  } finally {
    button.disabled = false;
    button.querySelector("span:first-child").textContent = "Request your table";
  }
});

loadMenu();
