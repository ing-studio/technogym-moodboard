#!/usr/bin/env python
"""Web derivatives for the deck: assets/source/** -> assets/web/** as WebP, paths written to catalog.json.

  python make_web.py [--force]

- Photos: EXIF orientation applied, transparency flattened onto the warm ground colour, long edge
  <= 1600 px.
- Floor plans: the sheets are 7016 px wide and mostly white paper, so each is TRIMMED to the drawing's
  bounding box (plus a small margin) before resizing to <= 3200 px wide. Zooming the deck into one area
  then stays sharp. The crop box in source pixels is stored as `trim` so areas can be traced back.
  The white paper is then made TRANSPARENT ("colour to alpha" against white), so a plan sits directly on
  the deck's ground with no sheet behind it. Lines and hatching keep their exact look over any colour,
  and it still works while a layer fades (a CSS blend mode would not).
- Skips files whose derivative is newer than the source unless --force.

Boxes in story/annotations.json are fractions (0-1) of the WEB image, i.e. of the trimmed drawing for plans.
"""

import argparse
import json
import os
import sys

from PIL import Image, ImageChops, ImageMath, ImageOps

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


def sheet_to_alpha(im, floor=14):
    """White paper -> transparency. alpha = 255 - min(r,g,b); colours are un-mixed from white so that the
    drawing composited on any ground equals the original multiplied onto it. `floor` removes JPEG paper noise."""
    r, g, b = im.split()
    a_raw = ImageChops.invert(ImageChops.darker(ImageChops.darker(r, g), b))
    unmix = lambda c: ImageMath.lambda_eval(
        lambda A: A["convert"](255 - (255 - A["c"]) * 255 / A["max"](A["a"], 1), "L"), c=c, a=a_raw)
    alpha = a_raw.point(lambda v: 0 if v < floor else min(255, (v - floor) * 255 // (255 - floor)))
    return Image.merge("RGBA", [unmix(r), unmix(g), unmix(b), alpha])


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
                im = sheet_to_alpha(im)
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
