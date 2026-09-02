#!/usr/bin/env python3
"""
Garden QR Code Scavenger Hunt Site Generator
==============================================

WHAT THIS DOES
Drop your finished plant info-images (photo + text already baked into
the image) into the `images/` folder. This script will:

  1. Create one HTML page per image in `site/` — the page shows that
     image, full-width, plus records the scan as part of a scavenger
     hunt game (powered by Firebase — see setup below).
  2. Build a shared `leaderboard.html` showing everyone's progress,
     ranked by how many unique plants they've found.
  3. Write out `links.txt` — one URL per plant, labeled by name — so
     you can generate QR codes yourself with whatever tool you like.
  4. Copy everything into `site/` so you can push that one folder
     straight to GitHub Pages.

SETUP (one time)
  A) pip install Pillow

  B) Set up a free Firebase project (this is what stores everyone's
     scans so the leaderboard works across different people's phones):
       1. Go to https://console.firebase.google.com and create a project
          (any name, Google Analytics not needed — you can skip it).
       2. In the left sidebar, go to "Build" -> "Firestore Database" ->
          "Create database". Choose "Start in test mode" for now.
       3. Click the gear icon (Project settings) -> scroll to "Your apps"
          -> click the "</>" (web) icon -> register the app (any nickname).
       4. It will show you a `firebaseConfig = {...}` object. Copy those
          values into `firebase-config.js` in this folder (a template is
          already there — just fill in the blanks).
       5. (Recommended, do this within a few days) In Firestore ->
          Rules, replace the default rules with:

            rules_version = '2';
            service cloud.firestore {
              match /databases/{database}/documents {
                match /scans/{docId} {
                  allow read: if true;
                  allow write: if request.resource.data.name is string
                               && request.resource.data.name.size() < 40
                               && request.resource.data.plants is list
                               && request.resource.data.count is int;
                }
              }
            }

          This keeps the database open enough for the game to work
          but stops it being used for anything else. Test mode rules
          expire after 30 days, so don't skip this step.

HOW TO USE
  1. Put your plant images in the `images/` folder. The filename
     (minus extension) becomes the plant's URL slug, e.g.
     "white-oak.jpg" -> yoursite.com/plants/white-oak.html

  2. Edit BASE_URL below to your GitHub Pages URL, e.g.:
       https://yourusername.github.io/garden-signs

  3. Fill in `firebase-config.js` with your real Firebase project
     values (see setup step B above).

  4. Run:
       python3 generate_site.py

  5. Push the *contents* of `site/` to your GitHub repo. Feed the
     URLs in `links.txt` into any QR code generator to make your signs.

RE-RUNNING
  Safe to re-run any time — regenerates `site/` from scratch based on
  what's in `images/`. Your `firebase-config.js` in the project root
  is untouched; it just gets copied into `site/` each time.
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
FIREBASE_CONFIG_FILE = "firebase-config.js"

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


FIREBASE_SDK_TAGS = """<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js"></script>"""

GAME_CSS = """
  .gg-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
    font-family: -apple-system, sans-serif;
  }
  .gg-modal {
    background: #fff; border-radius: 12px;
    padding: 24px 20px; max-width: 320px; width: 85%;
    text-align: center;
  }
  .gg-modal h2 { margin: 0 0 8px; font-size: 18px; }
  .gg-modal p { margin: 0 0 16px; font-size: 14px; color: #555; }
  .gg-modal input {
    width: 100%; box-sizing: border-box;
    padding: 10px; font-size: 15px;
    border: 1px solid #ccc; border-radius: 8px;
    margin-bottom: 12px;
  }
  .gg-modal button {
    width: 100%; padding: 10px; font-size: 15px;
    background: #2f6b3a; color: #fff; border: none;
    border-radius: 8px; cursor: pointer;
  }
  .gg-banner {
    position: fixed; left: 0; right: 0; bottom: 0;
    transform: translateY(100%);
    transition: transform 0.3s ease;
    z-index: 999;
    font-family: -apple-system, sans-serif;
  }
  .gg-banner.gg-show { transform: translateY(0); }
  .gg-banner-inner {
    background: rgba(20,20,20,0.92);
    color: #fff; padding: 14px 16px;
    font-size: 14px; text-align: center;
  }
  .gg-banner-inner a { color: #9fd8a8; }
  .gg-complete { background: rgba(47,107,58,0.96); }
  .gg-reward { font-size: 13px; opacity: 0.9; }
  .about-btn {
    position: fixed; top: 16px; right: 16px;
    background: rgba(0,0,0,0.6); color: #fff;
    font-family: -apple-system, sans-serif; font-size: 13px;
    text-decoration: none; padding: 8px 14px;
    border-radius: 20px; backdrop-filter: blur(4px);
    z-index: 998;
  }
"""

PLANT_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  html, body {{ margin: 0; padding: 0; background: #000; }}
  img {{ display: block; width: 100%; height: auto; }}
{game_css}
</style>
</head>
<body>
<img src="images/{filename}" alt="{title}">
<a class="about-btn" href="../about.html">About this project</a>

{firebase_sdk}
<script src="../firebase-config.js"></script>
<script src="../game.js"></script>
<script>
  window.addEventListener("load", function () {{
    recordScan("{slug}", {total_plants});
  }});
</script>
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
    background: #fafaf7; color: #333;
    max-width: 500px; margin: 0 auto; padding: 32px 20px;
    line-height: 1.6;
  }
  h1 { font-size: 22px; }
  a.back, a.lb-link { display: inline-block; margin-top: 16px; color: #556; }
</style>
</head>
<body>
<h1>About this project</h1>
<p>
  EDIT ME: Write a short blurb here about the garden and why these
  QR codes exist — who put it together, what it's for, anything you'd
  want a visitor scanning a sign to know.
</p>
<a class="lb-link" href="leaderboard.html">View the Leaderboard &rarr;</a><br>
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
    background: #fafaf7; margin: 0; padding: 24px;
  }}
  h1 {{ font-size: 20px; color: #333; }}
  .top-links a {{ font-size: 14px; color: #2f6b3a; margin-right: 16px; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px; margin-top: 16px;
  }}
  .card {{ text-decoration: none; color: #333; text-align: center; font-size: 13px; }}
  .card img {{
    width: 100%; aspect-ratio: 1 / 1; object-fit: cover;
    border-radius: 8px; display: block; margin-bottom: 6px;
  }}
</style>
</head>
<body>
<h1>Garden Plants (internal index)</h1>
<div class="top-links">
  <a href="leaderboard.html">🏆 Leaderboard</a>
  <a href="about.html">About this project</a>
</div>
<div class="grid">
{cards}
</div>
</body>
</html>
"""

LEADERBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Leaderboard</title>
<style>
  body {{
    font-family: -apple-system, sans-serif;
    background: #fafaf7; color: #333;
    max-width: 480px; margin: 0 auto; padding: 24px 20px;
  }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  .sub {{ font-size: 13px; color: #777; margin-bottom: 20px; }}
  .lb-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 10px 8px; border-bottom: 1px solid #e5e2da;
    font-size: 15px;
  }}
  .lb-rank {{ width: 24px; color: #999; font-size: 13px; }}
  .lb-name {{ flex: 1; }}
  .lb-count {{ font-size: 13px; color: #555; }}
  .lb-complete {{ background: #eef6ec; border-radius: 8px; }}
  a.back {{ display: inline-block; margin-top: 20px; color: #556; font-size: 14px; }}
</style>
</head>
<body>
<h1>🌿 Leaderboard</h1>
<div class="sub">{total_plants} plants total — find them all to win!</div>
<div id="leaderboard-list">Loading…</div>
<a class="back" href="index.html">&larr; Back</a>

{firebase_sdk}
<script src="firebase-config.js"></script>
<script src="game.js"></script>
<script src="leaderboard.js"></script>
<script>
  window.addEventListener("load", function () {{
    loadLeaderboard({total_plants});
  }});
</script>
</body>
</html>
"""

GAME_JS = """// game.js - shared logic for the garden scavenger hunt

const GG_NAME_KEY = "gardenGamePlayerName";

function getDb() {
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }
  return firebase.firestore();
}

function ggSlug(name) {
  return name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function getPlayerName() {
  return localStorage.getItem(GG_NAME_KEY);
}

function setPlayerName(name) {
  localStorage.setItem(GG_NAME_KEY, name);
}

function ensurePlayerName(callback) {
  const existing = getPlayerName();
  if (existing) {
    callback(existing);
    return;
  }
  showNamePrompt(callback);
}

function showNamePrompt(callback) {
  const overlay = document.createElement("div");
  overlay.className = "gg-overlay";
  overlay.innerHTML =
    '<div class="gg-modal">' +
    '<h2>Join the Garden Hunt!</h2>' +
    '<p>Enter your name to start tracking which plants you\\'ve found.</p>' +
    '<input type="text" id="gg-name-input" placeholder="Your name" maxlength="30">' +
    '<button id="gg-name-submit">Let\\'s go</button>' +
    '</div>';
  document.body.appendChild(overlay);

  const input = document.getElementById("gg-name-input");
  input.focus();

  const submit = function () {
    const name = input.value.trim();
    if (!name) {
      input.focus();
      return;
    }
    setPlayerName(name);
    overlay.remove();
    callback(name);
  };

  document.getElementById("gg-name-submit").addEventListener("click", submit);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") submit();
  });
}

function recordScan(plantSlug, totalPlants) {
  ensurePlayerName(function (name) {
    const db = getDb();
    const docId = ggSlug(name);
    const docRef = db.collection("scans").doc(docId);

    docRef.get().then(function (doc) {
      let plants = [];
      if (doc.exists) {
        plants = doc.data().plants || [];
      }
      if (plants.indexOf(plantSlug) === -1) {
        plants.push(plantSlug);
      }
      return docRef.set({
        name: name,
        plants: plants,
        count: plants.length,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true }).then(function () {
        showProgress(plants.length, totalPlants, name, false);
      });
    }).catch(function (err) {
      console.error("Garden game error:", err);
      showProgress(0, totalPlants, name, true);
    });
  });
}

function showProgress(found, total, name, offline) {
  const banner = document.createElement("div");
  banner.className = "gg-banner";
  if (!offline && found >= total) {
    banner.innerHTML =
      '<div class="gg-banner-inner gg-complete">' +
      '\\ud83c\\udfc6 You found all ' + total + ' plants, ' + escapeHtmlGG(name) + '!<br>' +
      '<span class="gg-reward">EDIT ME in generate_site.py: put your reward instructions here</span><br>' +
      '<a href="../leaderboard.html">View Leaderboard</a>' +
      '</div>';
  } else if (offline) {
    banner.innerHTML =
      '<div class="gg-banner-inner">Couldn\\'t save this scan right now \\u2014 check your connection.</div>';
  } else {
    banner.innerHTML =
      '<div class="gg-banner-inner">\\ud83c\\udf3f ' + found + ' / ' + total + ' plants found \\u2014 ' +
      '<a href="../leaderboard.html">Leaderboard</a></div>';
  }
  document.body.appendChild(banner);
  setTimeout(function () { banner.classList.add("gg-show"); }, 50);
}

function escapeHtmlGG(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
"""

LEADERBOARD_JS = """// leaderboard.js

function loadLeaderboard(totalPlants) {
  const db = getDb();
  const listEl = document.getElementById("leaderboard-list");

  db.collection("scans").orderBy("count", "desc").limit(100).get().then(function (snapshot) {
    if (snapshot.empty) {
      listEl.innerHTML = "<p>No one has scanned a plant yet \\u2014 be the first!</p>";
      return;
    }
    listEl.innerHTML = "";
    let rank = 1;
    snapshot.forEach(function (doc) {
      const data = doc.data();
      const complete = data.count >= totalPlants;
      const row = document.createElement("div");
      row.className = "lb-row" + (complete ? " lb-complete" : "");
      row.innerHTML =
        '<span class="lb-rank">' + rank + '</span>' +
        '<span class="lb-name">' + escapeHtmlGG(data.name) + '</span>' +
        '<span class="lb-count">' + data.count + ' / ' + totalPlants + (complete ? " \\ud83c\\udfc6" : "") + '</span>';
      listEl.appendChild(row);
      rank++;
    });
  }).catch(function (err) {
    listEl.innerHTML = "<p>Couldn't load the leaderboard right now.</p>";
    console.error(err);
  });
}
"""

FIREBASE_CONFIG_TEMPLATE = """// firebase-config.js
// Fill this in with the values from your Firebase project:
// Firebase Console -> Project settings -> Your apps -> Web app -> SDK setup and configuration
// See README.md / the top of generate_site.py for step-by-step setup instructions.

const firebaseConfig = {
  apiKey: "PASTE_ME",
  authDomain: "PASTE_ME",
  projectId: "PASTE_ME",
  storageBucket: "PASTE_ME",
  messagingSenderId: "PASTE_ME",
  appId: "PASTE_ME"
};
"""


def ensure_firebase_config_template():
    if not os.path.exists(FIREBASE_CONFIG_FILE):
        with open(FIREBASE_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(FIREBASE_CONFIG_TEMPLATE)
        print(f"Created '{FIREBASE_CONFIG_FILE}' template — fill in your real Firebase values "
              f"before deploying (see setup instructions at the top of this script).")


def build_site(plants):
    if os.path.isdir(SITE_DIR):
        shutil.rmtree(SITE_DIR)
    plants_dir = os.path.join(SITE_DIR, "plants")
    plants_images_dir = os.path.join(plants_dir, "images")
    os.makedirs(plants_images_dir, exist_ok=True)

    total_plants = len(plants)

    for plant in plants:
        dest_image = os.path.join(plants_images_dir, plant["filename"])
        shutil.copy2(plant["src_path"], dest_image)

        page_html = PLANT_PAGE_TEMPLATE.format(
            title=plant["label"],
            filename=plant["filename"],
            slug=plant["slug"],
            total_plants=total_plants,
            game_css=GAME_CSS,
            firebase_sdk=FIREBASE_SDK_TAGS,
        )
        page_path = os.path.join(plants_dir, f"{plant['slug']}.html")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    cards_html = [
        f'  <a class="card" href="plants/{p["slug"]}.html">'
        f'<img src="plants/images/{p["filename"]}">{p["label"]}</a>'
        for p in plants
    ]
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE.format(cards="\n".join(cards_html)))

    with open(os.path.join(SITE_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(ABOUT_PAGE_TEMPLATE)

    with open(os.path.join(SITE_DIR, "leaderboard.html"), "w", encoding="utf-8") as f:
        f.write(LEADERBOARD_TEMPLATE.format(total_plants=total_plants, firebase_sdk=FIREBASE_SDK_TAGS))

    with open(os.path.join(SITE_DIR, "game.js"), "w", encoding="utf-8") as f:
        f.write(GAME_JS)

    with open(os.path.join(SITE_DIR, "leaderboard.js"), "w", encoding="utf-8") as f:
        f.write(LEADERBOARD_JS)

    # copy the user's real firebase config into the built site
    shutil.copy2(FIREBASE_CONFIG_FILE, os.path.join(SITE_DIR, FIREBASE_CONFIG_FILE))

    print(f"Built {total_plants} plant page(s), leaderboard, and game logic in '{SITE_DIR}/'")


def build_links_file(plants):
    lines = [f"{p['label']}: {BASE_URL.rstrip('/')}/plants/{p['slug']}.html" for p in plants]
    with open("links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if BASE_URL.strip("/") == "https://yourusername.github.io/your-repo-name":
        print("\nWARNING: BASE_URL is still the placeholder value — links.txt won't be correct "
              "until you edit BASE_URL at the top of this script and re-run.")

    print(f"Wrote {len(plants)} link(s) to 'links.txt' — use these to generate your own QR codes.")


def check_firebase_config():
    with open(FIREBASE_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    if "PASTE_ME" in content:
        print(f"\nWARNING: '{FIREBASE_CONFIG_FILE}' still has placeholder values — "
              f"the game/leaderboard won't work until you fill in your real Firebase config.")


def main():
    ensure_firebase_config_template()
    plants = find_plant_images()
    build_site(plants)
    build_links_file(plants)
    check_firebase_config()

    print("\nDone. Next steps:")
    print("  1. Make sure BASE_URL at the top of this script matches your real GitHub Pages URL.")
    print(f"  2. Make sure '{FIREBASE_CONFIG_FILE}' has your real Firebase project values.")
    print(f"  3. Push the CONTENTS of '{SITE_DIR}/' to your GitHub Pages repo.")
    print("  4. Open 'links.txt' and generate a QR code for each URL with whatever tool you like.")


if __name__ == "__main__":
    main()
