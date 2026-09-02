# Garden QR Code Scavenger Hunt

## Setup (one time)

**A) Python side**
```
pip install Pillow
```

**B) Firebase (free) — powers the shared leaderboard**
1. Go to https://console.firebase.google.com and create a project
   (any name; skip Google Analytics if asked).
2. Left sidebar -> Build -> Firestore Database -> Create database ->
   "Start in test mode".
3. Gear icon (Project settings) -> scroll to "Your apps" -> click the
   "</>" web icon -> register the app (any nickname).
4. Copy the `firebaseConfig = {...}` values it shows you.
5. // Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAOgwCjyvAbFBqvGHKLnizxK79zL2o6xIM",
  authDomain: "mnsgarden.firebaseapp.com",
  projectId: "mnsgarden",
  storageBucket: "mnsgarden.firebasestorage.app",
  messagingSenderId: "638032840690",
  appId: "1:638032840690:web:abc3109bef0e84c1408d6b"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
6. Run `python3 generate_site.py` once — it creates a
   `firebase-config.js` template in this folder. Paste your real
   values into it.
7. **Recommended, within ~30 days:** In Firestore -> Rules, replace
   the defaults with:
   ```
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
   ```
   Test-mode rules expire after 30 days and the game will stop
   working until you set real rules.

## Use it
1. Drop your finished plant images into `images/`.
2. Edit `BASE_URL` near the top of `generate_site.py` to your real
   GitHub Pages URL.
3. Make sure `firebase-config.js` has your real values (not
   PASTE_ME placeholders).
4. Run:
   ```
   python3 generate_site.py
   ```
5. Push everything inside `site/` to your GitHub Pages repo.
6. Open `links.txt` and generate a QR code for each URL.

## How the game works
- First time someone scans any plant, they're asked for their name
  (stored on their phone, so they won't be asked again).
- Each scan is recorded to Firebase against that name.
- A banner shows their progress ("3 / 12 plants found") with a link
  to the leaderboard.
- Finding all plants shows a "you won" banner — edit the reward text
  in `generate_site.py`, inside `GAME_JS`, look for `EDIT ME`.
- `leaderboard.html` ranks everyone by plants found, with a 🏆 next
  to anyone who's completed the full set.

Re-run the script any time you add/remove plant images — it rebuilds
`site/` from scratch. Your `firebase-config.js` is untouched by
re-runs; it just gets copied into `site/` each time.
