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
    return None

def make_resized_webp(src, dest, max_size):
    img = Image.open(src).convert("RGB")
    img.thumbnail((max_size, max_size))
    dest_webp = dest.replace(".jpg", ".webp").replace(".png", ".webp")
    img.save(dest_webp, format="WEBP", quality=80)
    return os.path.basename(dest_webp)

files = []
for name in os.listdir(ORIG):
    lower = name.lower()
    if lower.endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(ORIG, name)
        date = get_exif_date(path)
        files.append((name, date))

# newest first
files.sort(key=lambda x: (x[1] is None, x[1]), reverse=True)

gallery_html = ""

for name, _ in files:
    orig = os.path.join(ORIG, name)

    large_name = make_resized_webp(orig, os.path.join(LARGE, name), 1600)
    thumb_name = make_resized_webp(orig, os.path.join(THUMBS, name), 400)

    gallery_html += f'''
<a href="images/large/{large_name}" target="_blank">
  <img src="images/thumbs/{thumb_name}" loading="lazy" alt="">
</a>
'''

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.index("<!-- GALLERY_START -->") + len("<!-- GALLERY_START -->")
end = html.index("<!-- GALLERY_END -->")

new_html = html[:start] + "\n" + gallery_html + "\n" + html[end:]

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_html)

