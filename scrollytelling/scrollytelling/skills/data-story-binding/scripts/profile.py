#!/usr/bin/env python3
"""Profile a data folder into a compact, cached, project-agnostic summary.

The only thing read after this step; the raw folder is never opened again. Emits YAML (or JSON if
PyYAML is absent) under ~8 KB, warning rather than silently exceeding. Degrades gracefully when
pandas / openpyxl / geo libraries are missing: identity + size + kind always land.

Usage:  python3 profile.py <dir> [-o profile.yaml] [--budget-kb 8]

See ../references/profile_spec.md for the output shape and how to read it.
"""

import os
import re
import sys
import json
import hashlib
import argparse
import datetime as _dt

PROFILER_VERSION = 2                      # bump on any logic change; invalidates the on-disk cache
RAW_EMBED_LIMIT = 2 * 1024 * 1024        # hard-refuse embedding any raw source over this
MAX_COLS_EMIT = 40                       # cap columns per file to hold the size budget
SAMPLE_N = 4                             # samples per column (spec says 3-5)
CACHE_NAME = ".profile_cache.json"

TIME_HINTS = ("date", "year", "month", "day", "time", "ts", "timestamp")
LAT_HINTS = ("lat", "latitude", "y")
LON_HINTS = ("lon", "lng", "long", "longitude", "x")
ID_HINTS = ("id", "device", "uid", "user", "imei", "maid")
GEO_HINTS = ("geometry", "geom", "the_geom", "wkt")

try:
    import yaml  # noqa
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False


def _tokens(name):
    return [t for t in re.split(r"[^a-z0-9]+", str(name).lower()) if t]


def _hit(name, hints):
    """Token-boundary match: a hint matches only as a whole token (or a token prefix for
    multi-char hints), never as a loose substring. Stops 'ts' matching 'units'."""
    toks = _tokens(name)
    for h in hints:
        for t in toks:
            if t == h:
                return True
            if len(h) >= 3 and (t.startswith(h) or t.endswith(h)):
                return True
    return False


def sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def kind_of(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    return {"xlsx": "xlsx", "xls": "xlsx", "csv": "csv", "tsv": "csv",
            "geojson": "geojson", "json": "json", "gpkg": "gpkg",
            "parquet": "parquet", "pq": "parquet"}.get(ext, "other")


def guess_role(name, dtype, distinct, nrows):
    n = name.lower()
    if _hit(name, GEO_HINTS):
        return "geo"
    if _hit(name, TIME_HINTS):
        return "time"
    if nrows and distinct >= 0.99 * nrows:
        return "key"
    if dtype in ("object", "string", "str", "category") and (not nrows or distinct <= 0.5 * nrows):
        return "label"
    return "measure"


def guess_unit(name):
    n = name.lower()
    if any(t in n for t in ("m2", "sqm", "sq_m", "area", "gla")):
        return "m2"
    if any(t in n for t in ("pct", "percent", "share", "rate", "ratio")) or "%" in n:
        return "pct"
    if any(t in n for t in ("price", "spend", "sales", "revenue", "cost", "sar", "usd", "eur", "value")):
        return "currency"
    if any(t in n for t in ("count", "units", "n_", "num", "qty")):
        return "count"
    return "none"


def _samples(values):
    out, seen = [], set()
    for v in values:
        if v is None:
            continue
        s = v.item() if hasattr(v, "item") else v
        try:
            key = repr(s)
        except Exception:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= SAMPLE_N:
            break
    return out


def profile_tabular_csv(path):
    """Stdlib CSV profiler (no pandas needed)."""
    import csv
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {"rows": 0, "columns": []}
        cols = {h: {"vals": [], "null": 0, "distinct": set()} for h in header}
        nrows = 0
        for row in reader:
            nrows += 1
            for h, v in zip(header, row):
                c = cols[h]
                if v == "":
                    c["null"] += 1
                else:
                    if len(c["vals"]) < 500:
                        c["vals"].append(v)
                    if len(c["distinct"]) < 5000:
                        c["distinct"].add(v)
            if nrows >= 200000:
                break
    columns = []
    for h in header[:MAX_COLS_EMIT]:
        c = cols[h]
        distinct = len(c["distinct"])
        dtype = "num" if c["vals"] and all(_isnum(x) for x in c["vals"][:50]) else "object"
        columns.append({
            "name": h, "dtype": dtype,
            "null_pct": round(100 * c["null"] / nrows, 1) if nrows else 0.0,
            "distinct": distinct,
            "role": guess_role(h, dtype, distinct, nrows),
            "unit": guess_unit(h),
            "samples": _samples(c["vals"]),
        })
    out = {"rows": nrows, "columns": columns}
    if len(header) > MAX_COLS_EMIT:
        out["columns_truncated"] = len(header) - MAX_COLS_EMIT
    return out


def _isnum(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def profile_xlsx(path):
    try:
        import openpyxl
    except Exception:
        return {"note": "openpyxl not installed; identity only"}
    wb = openpyxl.load_workbook(path, read_only=False, data_only=False)
    sheets = wb.sheetnames
    first = wb[sheets[0]]
    header = [c.value for c in next(first.iter_rows(min_row=1, max_row=1))]
    formulas = {}
    for row in first.iter_rows(min_row=2, max_row=min(first.max_row, 40)):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                col = header[cell.column - 1] if cell.column - 1 < len(header) else cell.coordinate
                formulas.setdefault(str(col), cell.value)
    cols = []
    for idx, h in enumerate(header[:MAX_COLS_EMIT], start=1):
        if h is None:
            continue
        vals = []
        for row in first.iter_rows(min_row=2, max_row=min(first.max_row, 500),
                                   min_col=idx, max_col=idx):
            v = row[0].value
            if v is not None and not (isinstance(v, str) and v.startswith("=")):
                vals.append(v)
        dtype = "num" if vals and all(_isnum(x) for x in vals[:50]) else "object"
        entry = {"name": str(h), "dtype": dtype,
                 "distinct": len(set(map(repr, vals))),
                 "role": guess_role(str(h), dtype, len(set(map(repr, vals))), first.max_row),
                 "unit": guess_unit(str(h)), "samples": _samples(vals)}
        if str(h) in formulas:
            entry["formula"] = formulas[str(h)]
        cols.append(entry)
    return {"sheets": sheets, "rows": max(first.max_row - 1, 0), "columns": cols}


def profile_geojson(path):
    """Stdlib geojson profiler."""
    with open(path, encoding="utf-8", errors="replace") as f:
        try:
            gj = json.load(f)
        except Exception as e:
            return {"note": "geojson parse failed: %s" % e}
    feats = gj.get("features", [])
    crs = gj.get("crs")
    crs_s = "EPSG:4326 (assumed, no crs member)"
    if crs:
        name = crs.get("properties", {}).get("name", "")
        crs_s = "%s (declared)" % name if name else "declared"
    gtype = feats[0]["geometry"]["type"] if feats and feats[0].get("geometry") else None
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    prec = 0

    def scan(coords):
        nonlocal minx, miny, maxx, maxy, prec
        if coords and isinstance(coords[0], (int, float)):
            x, y = coords[0], coords[1]
            minx, maxx = min(minx, x), max(maxx, x)
            miny, maxy = min(miny, y), max(maxy, y)
            prec = max(prec, len(str(x).split(".")[-1]) if "." in str(x) else 0)
        else:
            for c in coords or []:
                scan(c)

    for ft in feats[:5000]:
        g = ft.get("geometry")
        if g and g.get("coordinates") is not None:
            scan(g["coordinates"])
    bbox = [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)] if feats else None
    return {"geometry": gtype, "features": len(feats), "crs": crs_s,
            "bbox": bbox, "coord_precision": prec, "validity_pct": None}


def is_sensitive(cols):
    names = [c.get("name", "") for c in cols]
    has_id = any(_hit(n, ID_HINTS) for n in names)
    has_lat = any(_hit(n, LAT_HINTS) for n in names)
    has_lon = any(_hit(n, LON_HINTS) for n in names)
    has_time = any(_hit(n, TIME_HINTS) for n in names)
    return has_id and has_lat and has_lon and has_time


def profile_file(path, rel):
    size = os.path.getsize(path)
    k = kind_of(path)
    entry = {"path": rel, "bytes": size, "kind": k}
    try:
        entry["id"] = sha8(path)
    except Exception:
        entry["id"] = None
    body = {}
    try:
        if k == "csv":
            body = profile_tabular_csv(path)
        elif k == "xlsx":
            body = profile_xlsx(path)
        elif k == "geojson":
            body = profile_geojson(path)
    except Exception as e:
        body = {"note": "profiler error: %s" % e}
    entry.update(body)
    cols = body.get("columns", [])
    if cols:
        entry["sensitive"] = is_sensitive(cols)
        uniq = [c["name"] for c in cols if body.get("rows")
                and c.get("distinct", 0) >= 0.99 * body["rows"]]
        if uniq:
            entry["candidate_keys"] = uniq[:6]
    entry["vintage"] = "unknown"
    return entry


def dump(obj, budget_kb):
    if _HAVE_YAML:
        text = yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, allow_unicode=True)
        ext = "yaml"
    else:
        text = json.dumps(obj, indent=2, default=str)
        ext = "json"
    size_kb = len(text.encode("utf-8")) / 1024
    if size_kb > budget_kb:
        obj.setdefault("warnings", []).append(
            "profile is %.1f KB, over the %d KB budget; consider fewer files or --budget-kb" % (size_kb, budget_kb))
        if _HAVE_YAML:
            text = yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, allow_unicode=True)
        else:
            text = json.dumps(obj, indent=2, default=str)
    return text, ext, size_kb


def main():
    ap = argparse.ArgumentParser(description="Profile a data folder into a compact summary.")
    ap.add_argument("dir")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--budget-kb", type=float, default=8.0)
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        print("not a directory: %s" % root, file=sys.stderr)
        return 2

    cache_path = os.path.join(root, CACHE_NAME)
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}
    new_cache = {}

    files, warnings, total = [], [], 0
    for dirpath, _dirs, names in os.walk(root):
        for name in sorted(names):
            if name == CACHE_NAME:
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            try:
                st = os.stat(path)
            except OSError:
                continue
            total += st.st_size
            sig = "v%d:%d:%d" % (PROFILER_VERSION, int(st.st_mtime), st.st_size)
            if cache.get(rel, {}).get("sig") == sig:
                entry = cache[rel]["entry"]
            else:
                entry = profile_file(path, rel)
            new_cache[rel] = {"sig": sig, "entry": entry}
            if st.st_size > RAW_EMBED_LIMIT:
                warnings.append("%s is %.0f MB; hard-refuse embedding raw (sample or aggregate first)"
                                % (rel, st.st_size / 1024 / 1024))
            files.append(entry)

    out = {
        "root": root,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "total_bytes": total,
        "file_count": len(files),
        "files": files,
    }
    if warnings:
        out["warnings"] = warnings

    text, ext, size_kb = dump(out, args.budget_kb)
    dest = args.out or os.path.join(os.getcwd(), "profile.%s" % ext)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        json.dump(new_cache, open(cache_path, "w"))
    except Exception:
        pass
    print("wrote %s (%.1f KB, %d files, %.1f MB scanned)"
          % (dest, size_kb, len(files), total / 1024 / 1024), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
