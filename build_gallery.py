import os
import shutil
from PIL import Image
import piexif
from datetime import datetime

ORIG = "images/originals"
LARGE = "images/large"
THUMBS = "images/thumbs"

# --- CHANGE YOUR INSTAGRAM HERE ---
INSTA_LINK = "https://www.instagram.com/jo.nah8309/"

def safe_clear_contents(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if item == ".gitkeep": continue
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

safe_clear_contents(LARGE)
safe_clear_contents(THUMBS)

def get_exif_date(path):
    try:
        exif = piexif.load(path)
        d = exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if d:
            return datetime.strptime(d.decode(), "%Y:%m:%d %H:%M:%S"), True
    except: pass
    return datetime.fromtimestamp(os.path.getmtime(path)), False

def make_resized_webp(src, dest_folder, original_name, max_size):
    try:
        with Image.open(src) as img:
            img = img.convert("RGB")
            img.thumbnail((max_size, max_size))
            base_name = os.path.splitext(original_name)[0]
            final_filename = f"{base_name}.webp"
            final_path = os.path.join(dest_folder, final_filename)
            os.makedirs(dest_folder, exist_ok=True)
            img.save(final_path, format="WEBP", quality=80)
            return final_filename
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- Process ---
photos = []
valid_exts = (".jpg", ".jpeg", ".png", ".webp")
for name in os.listdir(ORIG):
    if name.lower().endswith(valid_exts):
        path = os.path.join(ORIG, name)
        date, has_exif = get_exif_date(path)
        ym = date.strftime("%Y-%m") if has_exif else "no-timestamp"
        photos.append({"name": name, "date": date, "ym": ym, "clean": os.path.splitext(name)[0], "exif": has_exif})

photos.sort(key=lambda x: (x["exif"], x["date"]), reverse=True)

for p in photos:
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(LARGE, p["ym"]), p["name"], 1600)
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(THUMBS, p["ym"]), p["name"], 400)

# --- HTML Header & Lightbox JS ---
head_html = """<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css">
    <title>Gallery</title>
</head>"""

# Updated Lightbox with Next/Prev/Close logic
lightbox_code = """
<div id="lightbox">
    <span class="close" onclick="closeLightbox()">&times;</span>
    <span class="nav-btn prev" onclick="changeImage(-1)">&#10094;</span>
    <img id="lightbox-img" src="">
    <div id="caption"></div>
    <span class="nav-btn next" onclick="changeImage(1)">&#10095;</span>
</div>

<script>
    let images = [];
    let currentIndex = 0;

    function initLightbox() {
        const items = document.querySelectorAll('.photo-item');
        images = Array.from(items).map(item => ({
            large: item.getAttribute('data-large'),
            name: item.getAttribute('data-name')
        }));
    }

    function openLightbox(index) {
        currentIndex = index;
        updateLightbox();
        document.getElementById('lightbox').style.display = 'flex';
    }

    function closeLightbox() {
        document.getElementById('lightbox').style.display = 'none';
    }

    function changeImage(dir) {
        currentIndex += dir;
        if (currentIndex >= images.length) currentIndex = 0;
        if (currentIndex < 0) currentIndex = images.length - 1;
        updateLightbox();
    }

    function updateLightbox() {
        const img = document.getElementById('lightbox-img');
        const cap = document.getElementById('caption');
        img.src = images[currentIndex].large;
        cap.innerText = images[currentIndex].name;
    }

    // Keyboard controls
    document.addEventListener('keydown', e => {
        if (document.getElementById('lightbox').style.display === 'flex') {
            if (e.key === "Escape") closeLightbox();
            if (e.key === "ArrowRight") changeImage(1);
            if (e.key === "ArrowLeft") changeImage(-1);
        }
    });

    window.onload = initLightbox;
</script>"""

def get_header(title, show_home=True):
    home_link = f'<a href="index.html" class="nav-btn-link">Home</a>' if show_home else ""
    insta_link = f'<a href="{INSTA_LINK}" target="_blank" class="nav-btn-link">Instagram</a>'
    return f"<header><nav>{home_link} {insta_link}</nav><h1>{title}</h1></header>"

# --- Build Pages ---
def build_photo_grid(page_photos):
    grid = "<main class='gallery-grid'>"
    for i, p in enumerate(page_photos):
        large = f"images/large/{p['ym']}/{p['clean']}.webp"
        thumb = f"images/thumbs/{p['ym']}/{p['clean']}.webp"
        grid += f'<div class="photo-item" data-large="{large}" data-name="{p["name"]}" onclick="openLightbox({i})"><img src="{thumb}" loading="lazy"></div>'
    return grid + "</main>"

# All Photos
with open("all.html", "w", encoding="utf-8") as f:
    f.write(f"<html>{head_html}<body>{get_header('All Photos')}{build_photo_grid(photos)}{lightbox_code}</body></html>")

# Months
groups = sorted({p["ym"] for p in photos}, reverse=True)
for group in groups:
    title = "No Timestamp Data" if group == "no-timestamp" else group
    m_photos = [p for p in photos if p["ym"] == group]
    with open(f"{group}.html", "w", encoding="utf-8") as f:
        f.write(f"<html>{head_html}<body>{get_header(title)}{build_photo_grid(m_photos)}{lightbox_code}</body></html>")

# Index
index_html = f"<html>{head_html}<body>{get_header('My Gallery', False)}<main class='album-grid'>"
sorted_groups = [g for g in groups if g != "no-timestamp"]
if "no-timestamp" in groups: sorted_groups.append("no-timestamp")
for group in sorted_groups:
    first = next(p for p in photos if p["ym"] == group)
    index_html += f'<a href="{group}.html" class="album-card"><img src="images/thumbs/{group}/{first["clean"]}.webp"><div class="album-info"><h3>{group if group != "no-timestamp" else "No Timestamp"}</h3></div></a>'
index_html += "</div><footer><a href='all.html' class='all-photos-link'>View All Photos</a></footer></body></html>"
with open("index.html", "w", encoding="utf-8") as f: f.write(index_html)