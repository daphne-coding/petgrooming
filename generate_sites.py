"""Generate static pages for each grooming shop for GitHub Pages.

This script reads the exported CSV files in the repository root and
creates a GitHub Pages–ready static site inside the ``docs`` folder.

Usage::

    python generate_sites.py

The command regenerates ``docs/`` from the current CSV content.
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).parent
DATA_FILE = ROOT / "google-2025-12-28.csv"
DETAIL_FILE = ROOT / "寵物美容detail.csv"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"


def slugify(name: str) -> str:
    """Create a URL-friendly slug while keeping non-Latin characters."""

    normalized = unicodedata.normalize("NFKC", name).strip()
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[-\s]+", "-", normalized)
    return normalized.strip("-")


def clean_field(value: str) -> str:
    return value.replace("⋅", "").replace("·", "").strip()


def load_images() -> Dict[str, str]:
    image_map: Dict[str, str] = {}
    with DETAIL_FILE.open(encoding="utf-8") as detail_fp:
        reader = csv.reader(detail_fp)
        header = next(reader, [])
        for row in reader:
            if len(row) < 2:
                continue
            link, image = row[0].strip(), row[1].strip()
            if link:
                image_map[link] = image
    return image_map


def load_shops() -> List[dict]:
    with DATA_FILE.open(encoding="utf-8") as data_fp:
        reader = csv.reader(data_fp)
        header = next(reader, [])
        rows = list(reader)

    image_map = load_images()
    shops: List[dict] = []
    used_slugs: set[str] = set()

    for row in rows:
        if not row or len(row) < 3:
            continue

        record = {header[idx]: (row[idx].strip() if idx < len(row) else "") for idx in range(len(header))}
        map_url = record.get("hfpxzc href", "")
        name = record.get("qBF1Pd", "")
        if not map_url or not name:
            continue

        rating = record.get("MW4etd", "")
        reviews = clean_field(record.get("UY7F9", "").strip("()"))
        category = record.get("W4Efsd", "")
        address = record.get("W4Efsd (3)", "")
        status = clean_field(record.get("W4Efsd (4)", ""))
        opening = clean_field(record.get("W4Efsd (5)", ""))
        website = record.get("lcr4fd href", "")
        phone = clean_field(record.get("UsdlK", ""))

        options = []
        for key in ("ah5Ghc", "M4A5Cf", "ah5Ghc (2)"):
            value = clean_field(record.get(key, ""))
            if value:
                options.append(value)

        slug_base = slugify(name) or "shop"
        slug = slug_base
        counter = 2
        while slug in used_slugs:
            slug = f"{slug_base}-{counter}"
            counter += 1
        used_slugs.add(slug)

        shops.append(
            {
                "name": name,
                "slug": slug,
                "map_url": map_url,
                "rating": rating,
                "reviews": reviews,
                "category": category,
                "address": address,
                "status": status,
                "opening": opening,
                "website": website,
                "phone": phone,
                "options": options,
                "image": image_map.get(map_url, ""),
            }
        )

    return shops


def render_shop_page(shop: dict) -> str:
    image_section = (
        f'<div class="hero" style="background-image: url({html.escape(shop["image"])});"></div>'
        if shop.get("image")
        else "<div class=\"hero placeholder\">本店家尚未提供照片</div>"
    )

    options_list = "".join(f"<li>{html.escape(option)}</li>" for option in shop.get("options", []))
    options_block = (
        f"<section><h2>服務選項</h2><ul class=\"pill-list\">{options_list}</ul></section>" if options_list else ""
    )

    details = []
    for label, key in (
        ("評分", "rating"),
        ("評論數", "reviews"),
        ("分類", "category"),
        ("地址", "address"),
        ("電話", "phone"),
        ("營業資訊", "opening"),
        ("目前狀態", "status"),
    ):
        value = shop.get(key, "")
        if value:
            details.append(f"<li><span class=\"label\">{label}</span><span class=\"value\">{html.escape(value)}</span></li>")

    website_link = (
        f"<a class=\"button secondary\" href=\"{html.escape(shop['website'])}\" target=\"_blank\" rel=\"noopener noreferrer\">官方網站</a>"
        if shop.get("website")
        else ""
    )

    map_link = (
        f"<a class=\"button\" href=\"{html.escape(shop['map_url'])}\" target=\"_blank\" rel=\"noopener noreferrer\">在地圖上查看</a>"
        if shop.get("map_url")
        else ""
    )

    return f"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(shop['name'])} ｜ 寵物美容</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/style.css" />
</head>
<body>
  <header class="page-header">
    <div>
      <a class="back-link" href="../../index.html">← 返回所有店家</a>
      <h1>{html.escape(shop['name'])}</h1>
      <p class="subtitle">為您找到最適合的寵物美容夥伴</p>
    </div>
    <div class="cta-group">
      {map_link}
      {website_link}
    </div>
  </header>

  {image_section}

  <main class="content">
    <section class="card">
      <h2>店家資訊</h2>
      <ul class="details">
        {''.join(details)}
      </ul>
    </section>

    {options_block}
  </main>

  <footer class="footer">資料來源：Google 地圖；圖片來源：店家公開照片。</footer>
</body>
</html>
"""


def render_index(shops: List[dict]) -> str:
    cards = []
    for shop in shops:
        image_style = f"style=\"background-image: url({html.escape(shop['image'])});\"" if shop.get("image") else ""
        card = f"""
      <a class="card shop-card" href="stores/{shop['slug']}/index.html">
        <div class="thumb" {image_style}></div>
        <div class="card-body">
          <h2>{html.escape(shop['name'])}</h2>
          <p class="meta">{html.escape(shop.get('category', ''))}</p>
          <p class="meta">⭐ {html.escape(shop.get('rating', ''))}（{html.escape(shop.get('reviews', '0'))} 則評論）</p>
          <p class="address">{html.escape(shop.get('address', ''))}</p>
        </div>
      </a>
"""
        cards.append(card)

    return f"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>台中寵物美容店家導覽</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header class="hero-banner">
    <div>
      <p class="eyebrow">GitHub Pages</p>
      <h1>寵物美容店家專屬頁面</h1>
      <p class="subtitle">每間店家都擁有獨立介紹頁，讓飼主快速找到理想的美容夥伴。</p>
    </div>
    <div class="pill">共 {len(shops)} 間店家</div>
  </header>

  <main class="grid">{''.join(cards)}</main>

  <footer class="footer">資料來源：Google 地圖；圖片來源：店家公開照片。</footer>
</body>
</html>
"""


def write_style() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    style = """
:root {
  --bg: #f6f7fb;
  --primary: #3c7dd9;
  --text: #122033;
  --muted: #5a6a85;
  --card: #ffffff;
  --border: #e2e8f0;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: 'Noto Sans TC', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}

a { color: inherit; text-decoration: none; }

.hero-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 48px 24px;
  gap: 24px;
  background: radial-gradient(circle at 20% 20%, #eef3ff, #f6f7fb 45%);
  border-bottom: 1px solid var(--border);
}

.hero-banner h1 { margin: 8px 0 12px; font-size: 32px; }
.hero-banner .subtitle { margin: 0; color: var(--muted); max-width: 760px; }
.eyebrow { margin: 0; letter-spacing: 0.08em; color: var(--primary); font-weight: 700; }
.pill { background: #e8f1ff; color: var(--primary); padding: 10px 14px; border-radius: 999px; font-weight: 700; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; padding: 24px; }

.card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; box-shadow: 0 10px 30px rgba(18,32,51,0.08); transition: transform .2s ease, box-shadow .2s ease; }
.card:hover { transform: translateY(-4px); box-shadow: 0 14px 34px rgba(18,32,51,0.12); }

.shop-card { display: flex; flex-direction: column; }
.shop-card .thumb { height: 160px; background: linear-gradient(120deg, #dbeafe, #e5e7eb); background-size: cover; background-position: center; border-radius: 10px; }
.shop-card .card-body { padding: 12px 4px 0; }
.shop-card h2 { margin: 0 0 6px; font-size: 20px; }
.meta { margin: 2px 0; color: var(--muted); }
.address { margin: 6px 0 0; color: var(--text); font-weight: 500; }

.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; padding: 24px; background: #fff; border-bottom: 1px solid var(--border); }
.page-header h1 { margin: 4px 0 6px; }
.page-header .subtitle { margin: 0; color: var(--muted); }
.back-link { color: var(--primary); font-weight: 700; }

.cta-group { display: flex; gap: 8px; }
.button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 14px; background: var(--primary); color: #fff; border-radius: 10px; font-weight: 700; }
.button.secondary { background: #122033; }

.hero { width: 100%; height: 320px; background-size: cover; background-position: center; }
.hero.placeholder { display: grid; place-items: center; color: var(--muted); background: repeating-linear-gradient(45deg, #f1f5f9, #f1f5f9 10px, #e2e8f0 10px, #e2e8f0 20px); font-weight: 700; }

.content { padding: 24px; display: grid; gap: 16px; }
.details { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.details li { display: grid; grid-template-columns: 120px 1fr; gap: 8px; padding: 12px; background: #f8fafc; border-radius: 10px; }
.details .label { color: var(--muted); font-weight: 700; }
.details .value { word-break: break-word; }

.pill-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.pill-list li { padding: 8px 12px; background: #eef2ff; color: #312e81; border-radius: 999px; font-weight: 700; }

.footer { padding: 24px; color: var(--muted); text-align: center; }

@media (max-width: 720px) {
  .hero-banner { flex-direction: column; align-items: flex-start; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .details li { grid-template-columns: 1fr; }
}
"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "style.css").write_text(style, encoding="utf-8")


def write_site() -> None:
    shops = load_shops()
    shops.sort(key=lambda item: item["name"])

    write_style()

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "index.html").write_text(render_index(shops), encoding="utf-8")

    for shop in shops:
        shop_dir = DOCS_DIR / "stores" / shop["slug"]
        shop_dir.mkdir(parents=True, exist_ok=True)
        (shop_dir / "index.html").write_text(render_shop_page(shop), encoding="utf-8")


if __name__ == "__main__":
    write_site()
    print(f"Generated site in {DOCS_DIR.resolve()}")
