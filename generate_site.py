#!/usr/bin/env python3
"""
Garden QR Code Site Generator
==============================

WHAT THIS DOES
Drop your finished plant info-images (photo + text already baked into
the image) into the `images/` folder. This script will:

  1. Create one bare-bones HTML page per image in `site/` — the page
     shows ONLY that image, full-width, nothing else on it.
  2. Write out `links.txt` — one URL per plant, labeled by name — so
     you can generate QR codes yourself with whatever tool you like.
  3. Copy everything into `site/` so you can push that one folder
     straight to GitHub Pages.

SETUP (one time)
  pip install Pillow

HOW TO USE
  1. Put your plant images in the `images/` folder.
     Name them however you like, e.g. "white-oak.jpg", "japanese-maple.png"
     The filename (minus extension) becomes the plant's URL slug and the
     label under its QR code, so name them something readable.

  2. Edit BASE_URL below to match your GitHub Pages URL, e.g.:
       https://yourusername.github.io/garden-signs
     (This is "https://<username>.github.io/<repo-name>" — no trailing slash)

  3. Run:
       python3 generate_site.py

  4. You'll get:
       site/index.html          <- simple gallery of all plants (for you)
       site/about.html           <- "About this project" page (edit the text
                                     inside ABOUT_PAGE_TEMPLATE below)
       site/plants/oak.html      <- one page per plant, image + About button
       site/plants/images/...    <- the images, copied in
       links.txt                  <- one URL per plant, ready for a QR generator

  5. Push the *contents* of `site/` to your GitHub repo (root, or /docs —
     whatever you've set GitHub Pages to serve from). Then feed the URLs
     in `links.txt` into any QR code generator to make your signs.

RE-RUNNING
  Safe to re-run any time you add/remove/rename images — it just
  regenerates everything from scratch based on what's currently in
  images/.
"""

import os
import re
import shutil
import sys

# ============================================================
# CONFIG — change this to your actual GitHub Pages URL
# ============================================================
BASE_URL = "https://yourusername.github.io/your-repo-name"

IMAGES_DIR = "images"
SITE_DIR = "site"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def slugify(name: str) -> str:
    """Turn a filename like 'White Oak #1.jpg' into 'white-oak-1'."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def prettify(slug: str) -> str:
    """Turn 'white-oak' into 'White Oak' for labels/titles."""
    return slug.replace("-", " ").replace("_", " ").title()


def find_plant_images():
    if not os.path.isdir(IMAGES_DIR):
        print(f"ERROR: '{IMAGES_DIR}/' folder not found. Create it and add your plant images.")
        sys.exit(1)

    plants = []
    seen_slugs = set()
    for filename in sorted(os.listdir(IMAGES_DIR)):
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in VALID_EXTENSIONS:
            continue
        slug = slugify(stem)
        if not slug:
            print(f"WARNING: skipping '{filename}' — couldn't make a valid name from it.")
            continue
        if slug in seen_slugs:
            print(f"WARNING: '{filename}' produces the same URL slug as another image "
                  f"('{slug}') — rename one of them so they don't collide.")
            continue
        seen_slugs.add(slug)
        plants.append({
            "slug": slug,
            "label": prettify(stem),
            "filename": filename,
            "src_path": os.path.join(IMAGES_DIR, filename),
        })

    if not plants:
        print(f"No images found in '{IMAGES_DIR}/'. Add some .jpg/.png files and re-run.")
        sys.exit(1)

    return plants


PLANT_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: #000;
  }}
  img {{
    display: block;
    width: 100%;
    height: auto;
  }}
  .about-btn {{
    position: fixed;
    bottom: 16px;
    right: 16px;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    font-family: -apple-system, sans-serif;
    font-size: 13px;
    text-decoration: none;
    padding: 8px 14px;
    border-radius: 20px;
    backdrop-filter: blur(4px);
  }}
</style>
</head>
<body>
<img src="images/{filename}" alt="{title}">
<a class="about-btn" href="../about.html">About this project</a>
</body>
</html>
"""

ABOUT_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>About this project</title>
<style>
  body {
    font-family: -apple-system, sans-serif;
    background: #fafaf7;
    color: #333;
    max-width: 500px;
    margin: 0 auto;
    padding: 32px 20px;
    line-height: 1.6;
  }
  h1 {
    font-size: 22px;
  }
  a.back {
    display: inline-block;
    margin-top: 24px;
    color: #556;
  }
</style>
</head>
<body>
<h1>About this project</h1>
<p>
  EDIT ME: Write a short blurb here about the garden and why these
  QR codes exist — who put it together, what it's for, anything you'd
  want a visitor scanning a sign to know.
</p>
<a class="back" href="javascript:history.back()">&larr; Back</a>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Garden Plants</title>
<style>
  body {{
    font-family: -apple-system, sans-serif;
    background: #fafaf7;
    margin: 0;
    padding: 24px;
  }}
  h1 {{
    font-size: 20px;
    color: #333;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px;
    margin-top: 16px;
  }}
  .card {{
    text-decoration: none;
    color: #333;
    text-align: center;
    font-size: 13px;
  }}
  .card img {{
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    border-radius: 8px;
    display: block;
    margin-bottom: 6px;
  }}
</style>
</head>
<body>
<h1>Garden Plants (internal index)</h1>
<div class="grid">
{cards}
</div>
</body>
</html>
"""


def build_site(plants):
    if os.path.isdir(SITE_DIR):
        shutil.rmtree(SITE_DIR)
    plants_dir = os.path.join(SITE_DIR, "plants")
    plants_images_dir = os.path.join(plants_dir, "images")
    os.makedirs(plants_images_dir, exist_ok=True)

    cards_html = []
    for plant in plants:
        # copy image
        dest_image = os.path.join(plants_images_dir, plant["filename"])
        shutil.copy2(plant["src_path"], dest_image)

        # write plant page
        page_html = PLANT_PAGE_TEMPLATE.format(
            title=plant["label"],
            filename=plant["filename"],
        )
        page_path = os.path.join(plants_dir, f"{plant['slug']}.html")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        page_url = f"plants/{plant['slug']}.html"
        cards_html.append(
            f'  <a class="card" href="{page_url}">'
            f'<img src="{page_url.replace(".html", "")}/../images/{plant["filename"]}" '
            f'onerror="this.src=\'plants/images/{plant["filename"]}\'">'
            f'{plant["label"]}</a>'
        )

    # simpler, reliable index (fixed relative path, avoids the onerror hack above)
    cards_html = [
        f'  <a class="card" href="plants/{p["slug"]}.html">'
        f'<img src="plants/images/{p["filename"]}">{p["label"]}</a>'
        for p in plants
    ]
    index_html = INDEX_TEMPLATE.format(cards="\n".join(cards_html))
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # about page — shared by every plant page's "About this project" button
    with open(os.path.join(SITE_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(ABOUT_PAGE_TEMPLATE)

    print(f"Built {len(plants)} plant page(s) in '{SITE_DIR}/'")


def build_links_file(plants):
    lines = []
    for plant in plants:
        page_url = f"{BASE_URL.rstrip('/')}/plants/{plant['slug']}.html"
        lines.append(f"{plant['label']}: {page_url}")

    with open("links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if BASE_URL.strip("/") == "https://yourusername.github.io/your-repo-name":
        print("\nWARNING: BASE_URL is still the placeholder value — links.txt won't be correct")
        print("until you edit BASE_URL at the top of this script and re-run.")

    print(f"Wrote {len(plants)} link(s) to 'links.txt' — use these to generate your own QR codes.")


def main():
    plants = find_plant_images()
    build_site(plants)
    build_links_file(plants)

    print("\nDone. Next steps:")
    print(f"  1. Make sure BASE_URL at the top of this script matches your real GitHub Pages URL.")
    print(f"  2. Push the CONTENTS of '{SITE_DIR}/' to your GitHub Pages repo.")
    print(f"  3. Open 'links.txt' and generate a QR code for each URL with whatever tool you like.")


if __name__ == "__main__":
    main()
