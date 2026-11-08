"use strict";

/* Sila search is local and progressive: without scripts every proposal remains visible. */
(() => {
  const search = document.getElementById("sila-search");
  const category = document.getElementById("sila-category");
  const status = document.getElementById("sila-status");
  const count = document.getElementById("result-count");
  const empty = document.getElementById("search-empty");
  const cards = Array.from(document.querySelectorAll("[data-sila-proposal]"));

  if (!search || !category || !status || !count || !empty || !cards.length) return;

  const normalize = (text) => String(text || "").normalize("NFKC").toLocaleLowerCase().trim();

  const update = () => {
    const query = normalize(search.value);
    const selectedCategory = category.value;
    const selectedStatus = status.value;
    let visible = 0;

    for (const card of cards) {
      const text = normalize(card.dataset.search);
      const matches = text.includes(query)
        && (!selectedCategory || card.dataset.category === selectedCategory)
        && (!selectedStatus || card.dataset.status === selectedStatus);
      card.hidden = !matches;
      if (matches) visible += 1;
    }

    count.textContent = visible === 1 ? "1 proposal" : String(visible) + " proposals";
    empty.hidden = visible !== 0;
  };

  search.addEventListener("input", update);
  category.addEventListener("change", update);
  status.addEventListener("change", update);
  update();
})();
