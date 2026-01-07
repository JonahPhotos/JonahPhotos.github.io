import os
import shutil
from PIL import Image
import piexif
from datetime import datetime

ORIG = "images/originals"
LARGE = "images/large"
THUMBS = "images/thumbs"

# --- CHANGE YOUR INSTAGRAM HERE ---
INSTA_LINK = "https://www.instagram.com/your_username"

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
        print(f"Error processing {original_name}: {e}")
        return None

# -------- collect and process photos ---------
photos = []
valid_exts = (".jpg", ".jpeg", ".png", ".webp")

for name in os.listdir(ORIG):
    if name.lower().endswith(valid_exts):
        path = os.path.join(ORIG, name)
        date, has_exif = get_exif_date(path)
        ym = date.strftime("%Y-%m") if has_exif else "no-timestamp"
        photos.append({
            "name": name,
            "date": date,
            "ym": ym,
            "clean": os.path.splitext(name)[0],
            "exif": has_exif
        })

photos.sort(key=lambda x: (x["exif"], x["date"]), reverse=True)

print(f"Building gallery for {len(photos)} images...")
for p in photos:
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(LARGE, p["ym"]), p["name"], 1600)
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(THUMBS, p["ym"]), p["name"], 400)

# -------- HTML Templates ---------
head_html = """<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css">
    <title>Gallery</title>
</head>"""

lightbox_code = """
<div id="lightbox" onclick="this.style.display='none'">
    <img id="lightbox-img" src="">
</div>
<script>
    function openLightbox(src) {
        document.getElementById('lightbox-img').src = src;
        document.getElementById('lightbox').style.display = 'flex';
    }
</script>"""

def get_header(title, show_home=True):
    links = f'<a href="{INSTA_LINK}" target="_blank">Instagram</a>'
    if show_home:
        links = f'<a href="index.html">Home</a> | ' + links
    return f"<header><nav>{links}</nav><h1>{title}</h1></header>"

# --- Build ALL PHOTOS Page (Properly Styled) ---
all_content = f"<html>{head_html}<body>{get_header('All Photos')} <main class='gallery-grid'>"
for p in photos:
    large_url = f"images/large/{p['ym']}/{p['clean']}.webp"
    thumb_url = f"images/thumbs/{p['ym']}/{p['clean']}.webp"
    all_content += f'<div class="photo-item" onclick="openLightbox(\'{large_url}\')"><img src="{thumb_url}" loading="lazy"></div>'
all_content += f"</main>{lightbox_code}</body></html>"

with open("all.html", "w", encoding="utf-8") as f:
    f.write(all_content)

# --- Build MONTH Pages ---
groups = sorted({p["ym"] for p in photos}, reverse=True)
for group in groups:
    title = "No Timestamp Data" if group == "no-timestamp" else group
    month_content = f"<html>{head_html}<body>{get_header(title)} <main class='gallery-grid'>"
    for p in photos:
        if p["ym"] == group:
            large_url = f"images/large/{group}/{p['clean']}.webp"
            thumb_url = f"images/thumbs/{group}/{p['clean']}.webp"
            month_content += f'<div class="photo-item" onclick="openLightbox(\'{large_url}\')"><img src="{thumb_url}" loading="lazy"></div>'
    month_content += f"</main>{lightbox_code}</body></html>"
    with open(f"{group}.html", "w", encoding="utf-8") as f:
        f.write(month_content)

# --- Build INDEX Page ---
index_content = f"<html>{head_html}<body>{get_header('My Gallery', show_home=False)} <main class='album-grid'>"
sorted_groups = [g for g in groups if g != "no-timestamp"]
if "no-timestamp" in groups: sorted_groups.append("no-timestamp")

for group in sorted_groups:
    first = next(p for p in photos if p["ym"] == group)
    label = "No Timestamp" if group == "no-timestamp" else group
    index_content += f"""
    <a href="{group}.html" class="album-card">
        <img src="images/thumbs/{group}/{first['clean']}.webp">
        <div class="album-info"><h3>{label}</h3></div>
    </a>"""

index_content += f"""
</main>
<footer>
    <a href="all.html" class="all-photos-link">View All Photos</a>
</footer>
</body></html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_content)

print("Done! All pages (including 'all.html') are now styled and ready.")