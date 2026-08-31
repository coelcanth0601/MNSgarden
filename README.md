[README.md](https://github.com/user-attachments/files/31650766/README.md)
# Garden QR Code Site

## Setup (one time)
```
pip install qrcode[pil]
pip install Pillow
```

## Use it
1. Drop your finished plant images into `images/` (name them clearly,
   e.g. "white-oak.jpg" — the filename becomes the page URL and the
   label on the printed QR code).
2. Open `generate_site.py` and change `BASE_URL` near the top to your
   real GitHub Pages URL, e.g. `https://yourusername.github.io/garden-signs`
3. Run:
   ```
   python3 generate_site.py
   ```
4. Push everything inside `site/` to your GitHub Pages repo.
5. Print the QR codes from `qrcodes/` — each one is already labeled
   with the plant name so you know which is which.

Re-run the script any time you add, remove, or rename plant images —
it rebuilds everything from what's currently in `images/`.
