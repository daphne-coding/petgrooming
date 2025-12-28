const searchInput = document.querySelector('[data-search]');
const categoryFilter = document.querySelector('[data-category]');
const shopCards = Array.from(document.querySelectorAll('[data-card]'));

function filterCards() {
  const term = (searchInput?.value || "").toLowerCase();
  const category = categoryFilter?.value || "";

  shopCards.forEach((card) => {
    const haystack = card.dataset.search || "";
    const cardCategory = card.dataset.category || "";
    const matchesTerm = haystack.includes(term);
    const matchesCategory = !category || cardCategory === category;
    card.style.display = matchesTerm && matchesCategory ? "block" : "none";
  });
}

searchInput?.addEventListener("input", filterCards);
categoryFilter?.addEventListener("change", filterCards);