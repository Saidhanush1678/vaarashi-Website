document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }
  const dateInput = document.querySelector("[data-date-input]");
  if (dateInput) {
    const localToday = new Date();
    const offset = localToday.getTimezoneOffset();
    const localDate = new Date(localToday.getTime() - offset * 60000).toISOString().slice(0, 10);
    dateInput.min = localDate;
    if (!dateInput.value) dateInput.value = localDate;
  }
});
