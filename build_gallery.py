import os
from PIL import Image
import piexif
from datetime import datetime

ORIG = "images/originals"
LARGE = "images/large"
THUMBS = "images/thumbs"

os.makedirs(LARGE, exist_ok=True)
os.makedirs(THUMBS, exist_ok=True)

def get_exif_date(path):
    try:
        exif = piexif.load(path)
        d = exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if d:
            return datetime.strptime(d.decode(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    # fallback: file modified time
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts)

def make_resized_webp(src, dest, max_size):
    img = Image.open(src).convert("RGB")
    img.thumbnail((max_size, max_size))
    dest = dest.replace(".jpg", ".webp").replace(".jpeg", ".webp").replace(".png", ".webp")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest, format="WEBP", quality=80)
    return os.path.basename(dest)

# -------- collect files ---------

photos = []

for name in os.listdir(ORIG):
    lower = name.lower()
    if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        path = os.path.join(ORIG, name)
        date = get_exif_date(path)
        ym = date.strftime("%Y-%m")  # year-month group
        photos.append((name, path, date, ym))

# newest first
photos.sort(key=lambda x: x[2], reverse=True)

# -------- build images + thumbs ---------

for name, path, date, ym in photos:

    large_dir = os.path.join(LARGE, ym)
    thumb_dir = os.path.join(THUMBS, ym)

    os.makedirs(large_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    large_name = make_resized_webp(path, os.path.join(large_dir, name), 1600)
    thumb_name = make_resized_webp(path, os.path.join(thumb_dir, name), 400)

# -------- build MONTH pages ---------

months = sorted({p[3] for p in photos}, reverse=True)

for ym in months:
    month_html = f"<h1>{ym}</h1><a href='index.html'>Back</a><br><br>\n"

    for name, path, date, m in photos:
        if m == ym:
            month_html += f"""
<a href="images/large/{ym}/{name.split('.')[0]}.webp" target="_blank">
  <img src="images/thumbs/{ym}/{name.split('.')[0]}.webp" loading="lazy">
</a>
"""

    with open(f"{ym}.html", "w", encoding="utf-8") as f:
        f.write(month_html)

# -------- build ALL PHOTOS page ---------

all_html = "<h1>All Photos (Newest First)</h1><a href='index.html'>Back</a><br><br>\n"

for name, path, date, ym in photos:
    all_html += f"""
<a href="images/large/{ym}/{name.split('.')[0]}.webp" target="_blank">
  <img src="images/thumbs/{ym}/{name.split('.')[0]}.webp" loading="lazy">
</a>
"""

with open("all.html", "w", encoding="utf-8") as f:
    f.write(all_html)

# -------- build ALBUM INDEX page ---------

index = "<h1>Albums by Year–Month</h1><br>\n"

for ym in months:
    # first image thumbnail for cover
    first = next(p for p in photos if p[3] == ym)
    cover = f"images/thumbs/{ym}/{first[0].split('.')[0]}.webp"

    index += f"""
<a href="{ym}.html">
  <img src="{cover}" style="width:200px">
  <br>{ym}
</a>
<br><br>
"""

index += '<a href="all.html">View all photos (newest first)</a>'

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index)
