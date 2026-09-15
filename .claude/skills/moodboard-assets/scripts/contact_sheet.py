#!/usr/bin/env python
"""Numbered thumbnail grids for a fast visual naming pass.

Looking at 60+ images one at a time burns context and attention. A contact sheet shows a dozen at
once with an index burned into each cell, so a naming pass reads a handful of sheets and only opens
an individual image when a thumbnail is genuinely unclear.

Usage:
  python contact_sheet.py <dir> [<dir> ...] [--out _review] [--per 12] [--cols 4] [--cell 420]

Writes <out>/sheet-01.png ... and <out>/index.csv (n, path) so a cell number maps back to a file.
Files are listed in sorted order per directory; non-images are skipped by trying to open them, so an
image with no extension (it happens) is still included.
"""

import argparse
import csv
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps


def list_images(dirs):
    out = []
    for d in dirs:
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            try:
                with Image.open(p) as im:
                    im.verify()
                out.append(p)
            except Exception:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", default="_review")
    ap.add_argument("--per", type=int, default=12)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=420)
    a = ap.parse_args()

    files = list_images(a.dirs)
    if not files:
        sys.exit("no images found")
    os.makedirs(a.out, exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    with open(os.path.join(a.out, "index.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "path"])
        for i, p in enumerate(files, 1):
            w.writerow([i, p.replace("\\", "/")])

    label_h = 40
    for s in range(0, len(files), a.per):
        chunk = files[s:s + a.per]
        rows = (len(chunk) + a.cols - 1) // a.cols
        sheet = Image.new("RGB", (a.cols * a.cell, rows * (a.cell + label_h)), "white")
        draw = ImageDraw.Draw(sheet)
        for j, p in enumerate(chunk):
            n = s + j + 1
            x, y = (j % a.cols) * a.cell, (j // a.cols) * (a.cell + label_h)
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((a.cell - 10, a.cell - 10))
                sheet.paste(im, (x + (a.cell - im.width) // 2, y + label_h + (a.cell - im.height) // 2))
            draw.text((x + 8, y + 6), "%d  %s" % (n, os.path.basename(p)[:26]), fill="black", font=font)
        dst = os.path.join(a.out, "sheet-%02d.png" % (s // a.per + 1))
        sheet.save(dst)
        print("wrote", dst, len(chunk), "images")


if __name__ == "__main__":
    main()
