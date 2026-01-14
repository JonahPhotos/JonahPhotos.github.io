import os
import shutil
from PIL import Image
import piexif
from datetime import datetime

ORIG = "images/originals"
LARGE = "images/large"
THUMBS = "images/thumbs"
INSTA_LINK = "https://www.instagram.com/jo.nah8309/"


def safe_clear_contents(folder_path):
    if os.path.exists(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if item == ".gitkeep": continue
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.makedirs(folder_path, exist_ok=True)


# Clear old processed images
safe_clear_contents(LARGE)
safe_clear_contents(THUMBS)


def get_photo_metadata(path):
    """Checks multiple EXIF tags for 'Astro' and extracts date."""
    is_astro = False
    date = None
    has_exif = False

    try:
        exif_dict = piexif.load(path)

        # 1. Check Standard Description (0th IFD)
        desc = exif_dict.get("0th", {}).get(piexif.ImageIFD.ImageDescription)

        # 2. Check Windows 'Title' (XPTitle is stored in 0th IFD as byte sequence)
        win_title = exif_dict.get("0th", {}).get(piexif.ImageIFD.XPTitle)

        # 3. Check User Comment (Exif IFD)
        comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)

        # Helper to search for 'astro' in various formats
        for field in [desc, win_title, comment]:
            if field:
                # Convert bytes to string safely and check for 'astro'
                if b"astro" in str(field).lower().encode():
                    is_astro = True
                    break

        # Get EXIF Date
        d = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if d:
            date = datetime.strptime(d.decode(), "%Y:%m:%d %H:%M:%S")
            has_exif = True
    except Exception as e:
        print(f"Error reading metadata for {path}: {e}")

    if not date:
        date = datetime.fromtimestamp(os.path.getmtime(path))

    return date, is_astro, has_exif


def make_resized_webp(src, dest_folder, original_name, max_size):
    with Image.open(src) as img:
        img = img.convert("RGB")
        img.thumbnail((max_size, max_size))
        base = os.path.splitext(original_name)[0]
        final_path = os.path.join(dest_folder, f"{base}.webp")
        os.makedirs(dest_folder, exist_ok=True)
        img.save(final_path, format="WEBP", quality=80)


# 1. Process all photos in the originals folder
photos = []
for name in os.listdir(ORIG):
    if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        path = os.path.join(ORIG, name)
        date, is_astro, has_exif = get_photo_metadata(path)

        # Assign folder name: Astro takes priority over date
        if is_astro:
            ym = "Astro"
        else:
            ym = date.strftime("%Y-%m") if has_exif else "no-timestamp"

        photos.append({
            "name": name,
            "date": date,
            "ym": ym,
            "clean": os.path.splitext(name)[0],
            "exif": has_exif
        })

# Sort photos for the "All Photos" view
photos.sort(key=lambda x: (x["date"]), reverse=True)

# 2. Save processed images into their assigned folders
for p in photos:
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(LARGE, p["ym"]), p["name"], 1600)
    make_resized_webp(os.path.join(ORIG, p["name"]), os.path.join(THUMBS, p["ym"]), p["name"], 400)

# --- HTML Generation Elements ---
head = f"""<html><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css?v={datetime.now().timestamp()}">
    <style>
        .device-instruction {{ font-size: 0.9rem; color: #888; margin-top: -20px; margin-bottom: 20px; font-style: italic; }}
    </style>
</head>"""


def get_header(title, show_home=True):
    h = f'<a href="index.html" class="nav-btn-link">Home</a>' if show_home else ""
    i = f'<a href="{INSTA_LINK}" target="_blank" class="nav-btn-link">Instagram</a>'
    instruction = '<div id="instruction" class="device-instruction"></div>'
    script = """<script>
        document.addEventListener("DOMContentLoaded", function() {
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            const text = isMobile ? "Tap to enlarge" : "Click to enlarge";
            const el = document.getElementById("instruction");
            if (el) el.innerText = text;
        });
    </script>"""
    return f"<header><nav class='top-nav'>{h} {i}</nav><h1>{title}</h1>{instruction}{script}</header>"


lb_code = """
<div id="lightbox" class="lightbox-overlay">
    <span class="lb-close" onclick="closeLightbox()">&times;</span>
    <span class="lb-prev" onclick="changeImage(-1)">&#10094;</span>
    <div class="lb-content">
        <img id="lightbox-img" src="">
        <div id="lb-caption"></div>
    </div>
    <span class="lb-next" onclick="changeImage(1)">&#10095;</span>
</div>
<script>
    let images = []; let currentIndex = 0;
    function openLightbox(index) {
        images = Array.from(document.querySelectorAll('.photo-item')).map(i => ({
            large: i.getAttribute('data-large'), name: i.getAttribute('data-name')
        }));
        currentIndex = index;
        updateLightbox();
        document.getElementById('lightbox').style.display = 'flex';
    }
    function closeLightbox() { document.getElementById('lightbox').style.display = 'none'; }
    function changeImage(dir) {
        currentIndex = (currentIndex + dir + images.length) % images.length;
        updateLightbox();
    }
    function updateLightbox() {
        document.getElementById('lightbox-img').src = images[currentIndex].large;
        document.getElementById('lb-caption').innerText = images[currentIndex].name;
    }
    document.addEventListener('keydown', e => {
        if (e.key === "Escape") closeLightbox();
        if (e.key === "ArrowRight") changeImage(1);
        if (e.key === "ArrowLeft") changeImage(-1);
    });
</script>"""


def build_grid(subset):
    g = "<main class='gallery-grid'>"
    for i, p in enumerate(subset):
        l = f"images/large/{p['ym']}/{p['clean']}.webp"
        t = f"images/thumbs/{p['ym']}/{p['clean']}.webp"
        g += f'<div class="photo-item" data-large="{l}" data-name="{p["name"]}" onclick="openLightbox({i})"><img src="{t}"></div>'
    return g + "</main>"


# 3. Generate the Homepage (Index)
idx = f"{head}<body>{get_header('Gallery', False)}<main class='album-grid'>"

# Unique list of folders sorted: Astro first, then dates, then no-timestamp
groups = list(set(p["ym"] for p in photos))
sorted_groups = sorted(groups, key=lambda x: (x == "Astro", x != "no-timestamp", x), reverse=True)

for g in sorted_groups:
    first = next(p for p in photos if p["ym"] == g)
    if g == "Astro":
        label = "Astrophotography"
    elif g == "no-timestamp":
        label = "No Timestamp"
    else:
        label = g

    idx += f'<a href="{g}.html" class="album-card"><img src="images/thumbs/{g}/{first["clean"]}.webp"><p>{label}</p></a>'

idx += '</main><footer><br><a href="all.html" class="all-photos-link">View All Photos</a></footer></body></html>'

with open("index.html", "w") as f:
    f.write(idx)

# 4. Generate the Month/Category Pages
with open("all.html", "w") as f:
    f.write(f"{head}<body>{get_header('All Photos')}{build_grid(photos)}{lb_code}</body></html>")

for g in groups:
    subset = [p for p in photos if p['ym'] == g]
    title = "Astrophotography" if g == "Astro" else g
    with open(f"{g}.html", "w") as f:
        f.write(f"{head}<body>{get_header(title)}{build_grid(subset)}{lb_code}</body></html>")