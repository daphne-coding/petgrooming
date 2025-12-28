"""
Generate a GitHub Pages-ready static site for the pet grooming dataset.

This script reads the scraped Google Maps data in ``google-2025-12-28.csv`` and
an image mapping in ``寵物美容detail.csv`` to produce:

* ``docs/index.html`` – an overview page with search/filter for all shops.
* ``docs/stores/<slug>/index.html`` – a detail page per shop.
* Shared assets in ``docs/assets``.
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "google-2025-12-28.csv"
DETAIL_FILE = BASE_DIR / "寵物美容detail.csv"
DOCS_DIR = BASE_DIR / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
STORES_DIR = DOCS_DIR / "stores"


@dataclass
class Shop:
    name: str
    map_url: str
    rating: Optional[float]
    reviews: Optional[int]
    category: str
    address: str
    status: str
    hours: str
    website: str
    phone: str
    features: List[str]
    image: Optional[str]
    slug: str


def slugify(name: str, existing: Set[str]) -> str:
    normalized = unicodedata.normalize("NFKC", name).strip().lower()
    cleaned = re.sub(r"[^\w-]+", "-", normalized)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-_")
    slug = cleaned or "shop"
    suffix = 2
    while slug in existing:
        slug = f"{cleaned or 'shop'}-{suffix}"
        suffix += 1
    existing.add(slug)
    return slug


def parse_rating(raw: str) -> Optional[float]:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_reviews(raw: str) -> Optional[int]:
    cleaned = raw.strip().strip("()").replace(",", "")
    return int(cleaned) if cleaned.isdigit() else None


def load_images() -> Dict[str, str]:
    images: Dict[str, str] = {}
    if not DETAIL_FILE.exists():
        return images
    with DETAIL_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            map_url = (row.get("hfpxzc href") or "").strip()
            image_url = (row.get("aoRNLd src") or "").strip()
            if map_url and image_url:
                images[map_url] = image_url
    return images


def load_shops(image_lookup: Dict[str, str]) -> List[Shop]:
    shops: List[Shop] = []
    used_slugs: Set[str] = set()
    with DATA_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("qBF1Pd") or "").strip()
            if not name:
                continue
            map_url = (row.get("hfpxzc href") or "").strip()
            rating = parse_rating(row.get("MW4etd") or "")
            reviews = parse_reviews(row.get("UY7F9") or "")
            category = (row.get("W4Efsd") or "").strip()
            address = (row.get("W4Efsd (3)") or "").strip()
            status = (row.get("W4Efsd (4)") or "").strip()
            hours = (row.get("W4Efsd (5)") or "").strip()
            website = (row.get("lcr4fd href") or "").strip()
            phone = (row.get("UsdlK") or "").strip()
            features = [
                (row.get("ah5Ghc") or "").strip(),
                (row.get("ah5Ghc (2)") or "").strip(),
            ]
            features = [feature for feature in features if feature]
            image = image_lookup.get(map_url)
            slug = slugify(name, used_slugs)

            shops.append(
                Shop(
                    name=name,
                    map_url=map_url,
                    rating=rating,
                    reviews=reviews,
                    category=category,
                    address=address,
                    status=status,
                    hours=hours,
                    website=website,
                    phone=phone,
                    features=features,
                    image=image,
                    slug=slug,
                )
            )
    return shops


def write_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "style.css").write_text(
        """
:root {
  --bg: #0b132b;
  --panel: #1c2541;
  --accent: #5bc0be;
  --accent-2: #3a506b;
  --text: #f6f8ff;
  --muted: #b8c1ec;
  --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Inter", "Noto Sans TC", system-ui, -apple-system, sans-serif;
  background: radial-gradient(circle at 20% 20%, rgba(91,192,190,0.08), transparent 35%), var(--bg);
  color: var(--text);
  line-height: 1.6;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.hero {
  background: linear-gradient(135deg, rgba(91,192,190,0.12), rgba(58,80,107,0.55));
  border: 1px solid rgba(91,192,190,0.25);
  padding: 28px;
  border-radius: 18px;
  box-shadow: var(--shadow);
  margin-bottom: 28px;
}

.hero h1 { margin: 0 0 12px; font-size: 30px; letter-spacing: 0.02em; }
.hero p { margin: 0 0 10px; color: var(--muted); }

.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.search {
  background: var(--panel);
  border: 1px solid rgba(91,192,190,0.25);
  border-radius: 14px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.search input, .search select {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: var(--text);
  outline: none;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
  margin-top: 18px;
}

.card {
  background: var(--panel);
  border: 1px solid rgba(91,192,190,0.18);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 36px rgba(0,0,0,0.4);
}

.card__body { padding: 16px; }
.card__title { margin: 0 0 6px; font-size: 20px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(91,192,190,0.14);
  border: 1px solid rgba(91,192,190,0.3);
  color: var(--text);
  font-size: 14px;
}

.meta { color: var(--muted); font-size: 14px; margin: 6px 0; }
.cta { display: inline-flex; gap: 8px; align-items: center; margin-top: 12px; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  border: none;
  background: var(--accent);
  color: #041121;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 10px 20px rgba(91,192,190,0.35);
}
.btn.secondary {
  background: var(--accent-2);
  color: var(--text);
  box-shadow: none;
  border: 1px solid rgba(255,255,255,0.08);
}

.gallery {
  width: 100%;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(91,192,190,0.1), rgba(58,80,107,0.25));
  border: 1px solid rgba(91,192,190,0.2);
  box-shadow: var(--shadow);
  min-height: 200px;
}
.gallery img {
  width: 100%;
  display: block;
  object-fit: cover;
}
.placeholder {
  min-height: 200px;
  display: grid;
  place-items: center;
  color: var(--muted);
}

.detail-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  margin-top: 18px;
}

.panel {
  background: var(--panel);
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(91,192,190,0.2);
  box-shadow: var(--shadow);
}
.panel h2 { margin: 0 0 10px; font-size: 18px; }
.list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
.list li { color: var(--text); }
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; }

.back-link { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); margin-bottom: 10px; }
.back-link:hover { color: var(--text); }

.footer {
  margin-top: 26px;
  color: var(--muted);
  text-align: center;
  font-size: 14px;
}
        """.strip()
    )
    (ASSETS_DIR / "script.js").write_text(
        """
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
        """.strip()
    )


def render_rating(shop: Shop) -> str:
    if shop.rating is None:
        return "暫無評分"
    review_text = f"（{shop.reviews} 則評論）" if shop.reviews is not None else ""
    return f"{shop.rating:.1f} / 5 {review_text}"


def render_card(shop: Shop) -> str:
    search_text = " ".join(
        filter(
            None,
            [
                shop.name,
                shop.category,
                shop.address,
                shop.status,
            ],
        )
    ).lower()
    return f"""
      <article class="card" data-card data-category="{html.escape(shop.category)}" data-search="{html.escape(search_text)}">
        <div class="card__body">
          <div class="chip">{html.escape(shop.category or '寵物美容')}</div>
          <h2 class="card__title">{html.escape(shop.name)}</h2>
          <div class="meta">⭐ {html.escape(render_rating(shop))}</div>
          <div class="meta">📍 {html.escape(shop.address or '地址未提供')}</div>
          <div class="cta">
            <a class="btn" href="./stores/{shop.slug}/" aria-label="前往 {html.escape(shop.name)} 的獨立頁面">查看店家</a>
            <a class="btn secondary" href="{html.escape(shop.map_url)}" target="_blank" rel="noopener">Google 地圖</a>
          </div>
        </div>
      </article>
    """


def build_index(shops: Iterable[Shop]) -> None:
    shops = list(shops)
    categories = sorted({shop.category for shop in shops if shop.category})
    cards = "\n".join(render_card(shop) for shop in shops)
    options = '<option value="">全部類別</option>' + "".join(
        f'<option value="{html.escape(cat)}">{html.escape(cat)}</option>' for cat in categories
    )
    html_body = f"""
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>寵物美容店家地圖 | 目錄</title>
  <link rel="stylesheet" href="./assets/style.css" />
</head>
<body>
  <main class="page">
    <section class="hero">
      <h1>台中寵物美容店家索引</h1>
      <p>為每一間店建立專屬介紹頁面，附上評價、地址、營業資訊與地圖連結，方便飼主快速找到最適合的美容服務。</p>
      <div class="controls">
        <label class="search">
          <span role="img" aria-label="搜索">🔍</span>
          <input type="search" placeholder="搜尋店名、地址、營業狀態..." data-search />
        </label>
        <label class="search">
          <span role="img" aria-label="篩選">🎯</span>
          <select data-category>{options}</select>
        </label>
      </div>
    </section>
    <section class="card-grid">
      {cards}
    </section>
    <p class="footer">共 {len(shops)} 間店家。資料來自 google-2025-12-28.csv 與 寵物美容detail.csv。</p>
  </main>
  <script src="./assets/script.js"></script>
</body>
</html>
    """.strip()
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "index.html").write_text(html_body, encoding="utf-8")


def build_store_page(shop: Shop) -> None:
    STORES_DIR.mkdir(parents=True, exist_ok=True)
    store_dir = STORES_DIR / shop.slug
    store_dir.mkdir(parents=True, exist_ok=True)
    image_block = (
        f'<div class="gallery"><img src="{html.escape(shop.image)}" alt="{html.escape(shop.name)} 外觀或作品集" loading="lazy" /></div>'
        if shop.image
        else '<div class="gallery placeholder">暫無圖片</div>'
    )
    feature_tags = "".join(f'<span class="chip">{html.escape(feature)}</span>' for feature in shop.features)
    website_link = (
        f'<a class="btn" href="{html.escape(shop.website)}" target="_blank" rel="noopener">造訪官網 / 社群</a>'
        if shop.website
        else ""
    )
    phone_link = (
        f'<a class="btn secondary" href="tel:{html.escape(shop.phone)}">撥打電話</a>' if shop.phone else ""
    )

    html_body = f"""
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(shop.name)} | 寵物美容店家</title>
  <link rel="stylesheet" href="../assets/style.css" />
</head>
<body>
  <main class="page">
    <a class="back-link" href="../../index.html">← 返回店家清單</a>
    <section class="hero">
      <h1>{html.escape(shop.name)}</h1>
      <p>{html.escape(shop.category or '寵物美容')}</p>
      <div class="tag-row">
        <span class="chip">⭐ {html.escape(render_rating(shop))}</span>
        {feature_tags or '<span class="chip">寵物美容</span>'}
      </div>
      <div class="cta" style="margin-top:14px; flex-wrap: wrap;">
        <a class="btn secondary" href="{html.escape(shop.map_url)}" target="_blank" rel="noopener">在 Google 地圖查看</a>
        {website_link}
        {phone_link}
      </div>
    </section>

    <div class="detail-grid">
      <div class="panel">
        <h2>店家介紹</h2>
        <ul class="list">
          <li>📍 地址：{html.escape(shop.address or '未提供')}</li>
          <li>⌚ 狀態：{html.escape(shop.status or '請電洽')}</li>
          <li>🗓️ 營業時間：{html.escape(shop.hours or '未提供')}</li>
          {"<li>☎️ 電話：" + html.escape(shop.phone) + "</li>" if shop.phone else ""}
        </ul>
      </div>
      <div class="panel">
        <h2>店家圖片</h2>
        {image_block}
      </div>
    </div>

    <div class="panel" style="margin-top:18px;">
      <h2>快速連結</h2>
      <div class="cta" style="flex-wrap: wrap;">
        <a class="btn secondary" href="{html.escape(shop.map_url)}" target="_blank" rel="noopener">Google 地圖</a>
        {website_link}
        {phone_link}
      </div>
    </div>

    <p class="footer">資料來自 google-2025-12-28.csv 與 寵物美容detail.csv。最後更新：自動生成頁面。</p>
  </main>
</body>
</html>
    """.strip()
    (store_dir / "index.html").write_text(html_body, encoding="utf-8")


def generate() -> None:
    images = load_images()
    shops = load_shops(images)
    write_assets()
    build_index(shops)
    for shop in shops:
        build_store_page(shop)
    print(f"Generated {len(shops)} shop pages.")


if __name__ == "__main__":
    generate()
