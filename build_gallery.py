import os
import shutil
from PIL import Image
import piexif
from datetime import datetime

ORIG = "images/originals"
LARGE = "images/large"
THUMBS = "images/thumbs"


def safe_clear_contents(folder_path):
    """
    Deletes all files and subdirectories inside a folder
    WITHOUT deleting the folder itself or any .gitkeep files.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if item == ".gitkeep":
            continue
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


# Clear contents safely (preserving .gitkeep)
safe_clear_contents(LARGE)
safe_clear_contents(THUMBS)


def get_exif_date(path):
    """Returns (datetime, is_real_exif)"""
    try:
        exif = piexif.load(path)
        d = exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if d:
            # Standard EXIF format is YYYY:MM:DD
            return datetime.strptime(d.decode(), "%Y:%m:%d %H:%M:%S"), True
    except Exception:
        pass

    # Fallback: file modified time
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts), False


def make_resized_webp(src, dest_folder, original_name, max_size):
    try:
        with Image.open(src) as img:
            # Correctly handle transparency for WebP
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            else:
                img = img.convert("RGB")

            img.thumbnail((max_size, max_size))

            # Robust extension handling (os.path.splitext works with any case)
            base_name = os.path.splitext(original_name)[0]
            final_filename = f"{base_name}.webp"
            final_path = os.path.join(dest_folder, final_filename)

            os.makedirs(dest_folder, exist_ok=True)
            img.save(final_path, format="WEBP", quality=80)
            return final_filename
    except Exception as e:
        print(f"Error processing {src}: {e}")
        return None


# -------- collect files ---------

photos = []
valid_extensions = (".jpg", ".jpeg", ".png", ".webp")

if not os.path.exists(ORIG):
    print(f"Error: '{ORIG}' folder not found. Please create it.")
    exit()

for name in os.listdir(ORIG):
    if name.lower().endswith(valid_extensions):
        path = os.path.join(ORIG, name)
        date, has_exif = get_exif_date(path)

        # Grouping logic
        ym = date.strftime("%Y-%m") if has_exif else "no-timestamp"

        photos.append({
            "original_name": name,
            "path": path,
            "date": date,
            "ym": ym,
            "clean_name": os.path.splitext(name)[0],
            "has_exif": has_exif
        })

# Sort: Dated images first (newest to oldest), then No Timestamp
photos.sort(key=lambda x: (x["has_exif"], x["date"]), reverse=True)

# -------- build images + thumbs ---------

print(f"Converting {len(photos)} images...")
for p in photos:
    make_resized_webp(p["path"], os.path.join(LARGE, p["ym"]), p["original_name"], 1600)
    make_resized_webp(p["path"], os.path.join(THUMBS, p["ym"]), p["original_name"], 400)

# -------- build PAGES ---------

groups = sorted({p["ym"] for p in photos}, reverse=True)

for group in groups:
    title = "No Timestamp Data" if group == "no-timestamp" else group
    page_html = f"<h1>{title}</h1><a href='index.html'>Back</a><br><br>\n"

    for p in photos:
        if p["ym"] == group:
            page_html += f"""
<a href="images/large/{group}/{p['clean_name']}.webp" target="_blank">
  <img src="images/thumbs/{group}/{p['clean_name']}.webp" loading="lazy">
</a>
"""
    with open(f"{group}.html", "w", encoding="utf-8") as f:
        f.write(page_html)

# -------- build ALL PHOTOS page ---------

all_html = "<h1>All Photos</h1><a href='index.html'>Back</a><br><br>\n"
for p in photos:
    all_html += f"""
<a href="images/large/{p['ym']}/{p['clean_name']}.webp" target="_blank">
  <img src="images/thumbs/{p['ym']}/{p['clean_name']}.webp" loading="lazy">
</a>
"""
with open("all.html", "w", encoding="utf-8") as f:
    f.write(all_html)

# -------- build ALBUM INDEX page ---------

index = "<h1>Gallery Index</h1><br>\n"

# Reorder groups so 'no-timestamp' is at the end
sorted_groups = [g for g in groups if g != "no-timestamp"]
if "no-timestamp" in groups:
    sorted_groups.append("no-timestamp")

for group in sorted_groups:
    first = next(p for p in photos if p["ym"] == group)
    cover = f"images/thumbs/{group}/{first['clean_name']}.webp"
    label = "No Timestamp Data" if group == "no-timestamp" else group

    index += f"""
<a href="{group}.html">
  <img src="{cover}" style="width:200px; height:200px; object-fit:cover;">
  <br>{label}
</a>
<br><br>
"""

index += '<a href="all.html">View all photos</a>'

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index)

print("Done! Check your browser.")