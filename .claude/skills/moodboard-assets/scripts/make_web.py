#!/usr/bin/env python
"""Web derivatives for the deck: assets/source/** -> assets/web/** as WebP, paths written to catalog.json.

  python make_web.py [--force]

- Photos: EXIF orientation applied, transparency flattened onto the warm ground colour, long edge
  <= 1600 px.
- Floor plans: the sheets are 7016 px wide and mostly white paper, so each is TRIMMED to the drawing's
  bounding box (plus a small margin) before resizing to <= 3200 px wide. Zooming the deck into one area
  then stays sharp. The crop box in source pixels is stored as `trim` so areas can be traced back.
- Skips files whose derivative is newer than the source unless --force.

Area boxes in story/areas.json are fractions (0-1) of the WEB plan image, i.e. of the trimmed drawing.
"""

import argparse
import json
import os
import sys

from PIL import Image, ImageChops, ImageOps

CATALOG = "assets/catalog.json"
WEB = "assets/web"
GROUND = (244, 239, 231)          # keep in sync with --bg in design_system.css
PHOTO_MAX = 1600
PLAN_MAX_W = 3200
QUALITY = 82


def trim_box(im, margin=0.015):
    g = im.convert("L")
    small = g.copy()
    small.thumbnail((1400, 1400))
    s = g.width / small.width
    diff = ImageChops.difference(small, Image.new("L", small.size, 255)).point(lambda v: 255 if v > 12 else 0)
    bb = diff.getbbox()
    if not bb:
        return (0, 0, im.width, im.height)
    m = int(max(im.width, im.height) * margin)
    return (max(0, int(bb[0] * s) - m), max(0, int(bb[1] * s) - m),
            min(im.width, int(bb[2] * s) + m), min(im.height, int(bb[3] * s) + m))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    cat = json.load(open(CATALOG, encoding="utf-8"))
    made = skipped = 0
    for e in cat["images"]:
        src = e["file"]
        dst = "%s/%s/%s.webp" % (WEB, e["chapter"], e["id"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        is_plan = e["chapter"].endswith("floor-plan")
        if not a.force and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src) and "web" in e:
            skipped += 1
            continue
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, GROUND)
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert("RGB")
            if is_plan:
                box = trim_box(im)
                im = im.crop(box)
                e["trim"] = list(box)
                if im.width > PLAN_MAX_W:
                    im = im.resize((PLAN_MAX_W, round(im.height * PLAN_MAX_W / im.width)), Image.LANCZOS)
            else:
                im.thumbnail((PHOTO_MAX, PHOTO_MAX), Image.LANCZOS)
            im.save(dst, "WEBP", quality=QUALITY, method=6)
            e["web"] = dst
            e["web_w"], e["web_h"] = im.size
            e["web_bytes"] = os.path.getsize(dst)
            made += 1

    with open(CATALOG, "w", encoding="utf-8") as fh:
        json.dump(cat, fh, indent=2, ensure_ascii=False)
    total = sum(e.get("web_bytes", 0) for e in cat["images"])
    print("ok: %d written, %d up to date, web total %.1f MB" % (made, skipped, total / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
