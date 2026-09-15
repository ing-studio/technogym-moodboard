#!/usr/bin/env node
/**
 * shotbeat — screenshot one beat of a scroll deck, from the terminal.
 *
 * WHY. The static and frame checks answer "does it run". They cannot answer "is the marker on the
 * line", "did that layer land where the data says", "does the legend still fit". Those need pixels,
 * and asking a person to scroll to beat 27 for every small geometry change does not scale. This
 * parks the deck on one beat in a REAL headed browser and writes a PNG.
 *
 *   node shotbeat.mjs <deck.html> --beat <data-step> --out shot.png [--launch]
 *   node shotbeat.mjs deck.html --beat geo-roads --out a.png --crop 640,150,460,750 --zoom 2
 *
 * Flags:
 *   --beat S        data-step of the beat to park on. Required.
 *   --out F         PNG path. Required.
 *   --launch        start a throwaway Chrome on --port (else attach to one already there)
 *   --port N        debug port, default 9333
 *   --width N       viewport width, default 1600
 *   --height N      viewport height, default 1000
 *   --scale N       deviceScaleFactor, default 1. SEE THE TRAP BELOW BEFORE RAISING IT.
 *   --settle N      ms to wait after load, default 10000; the map has to finish its first paint
 *   --hold N        ms to wait after scrolling, default 5000; camera moves are animated
 *   --crop x,y,w,h  crop in CSS pixels, then upscale 2x. Cheap way to inspect one corner.
 *   --zoom N        upscale factor for --crop, default 2
 *
 * FOUR TRAPS, all of which cost real time before they were written down.
 *
 *  1. HEADLESS CANNOT DO THIS. Headless Chrome renders a WebGL map at about one frame per second and
 *     delivers zero IntersectionObserver entries, so the beat never activates and the shot is of a
 *     deck that looks broken. Headed, on a debug port, is the only mode that measures or photographs
 *     a scroll deck honestly.
 *  2. deviceScaleFactor 2 KILLS THE RENDERER on a deck with a heavy full-viewport canvas. The tab
 *     dies mid-wait and the only symptom is the debugger socket closing with code 1006 and no error.
 *     Default is 1. If you need detail, use --crop and upscale, which costs nothing.
 *  3. NO `ws` PACKAGE. Node's built-in WebSocket is used, so this runs with no install anywhere. It
 *     is the browser API, not the npm one: `addEventListener`, not `.on`.
 *  4. WAIT LONG, TWICE. A deck this size needs ~10 s to load and ~5 s to settle after the scroll,
 *     because the camera move is animated and the overlay redraws behind it. Shoot early and you
 *     photograph a half-finished transition and read it as a bug.
 *
 * WHAT IT STILL CANNOT JUDGE: composition, whether the copy reads, whether a colour works. A shot
 * proves a geometry claim. It does not replace a person opening the file.
 */

import fs from "node:fs";
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf("--" + n); return i < 0 ? d : argv[i + 1]; };
const has  = (n) => argv.includes("--" + n);

const deck = argv.find(a => !a.startsWith("--") && /\.html?$/i.test(a));
const beat = flag("beat");
const out  = flag("out");
if (!deck || !beat || !out) {
  console.error("usage: shotbeat.mjs <deck.html> --beat <data-step> --out <shot.png> [--launch]");
  process.exit(2);
}
const PORT   = +flag("port", 9333);
const W      = +flag("width", 1600);
const H      = +flag("height", 1000);
const SCALE  = +flag("scale", 1);
const SETTLE = +flag("settle", 10000);
const HOLD   = +flag("hold", 5000);
const ZOOM   = +flag("zoom", 2);
const CROP   = flag("crop");

if (SCALE > 1) console.error(`warn: --scale ${SCALE} can kill the renderer on a heavy canvas deck; --crop is safer`);

const sleep = ms => new Promise(r => setTimeout(r, ms));

const CHROME = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].find(p => fs.existsSync(p));

let child = null;
const die = (msg, code = 1) => { console.error(msg); if (child) child.kill(); process.exit(code); };

if (has("launch")) {
  if (!CHROME) die("no Chrome found; start one yourself with --remote-debugging-port", 2);
  child = spawn(CHROME, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "shotbeat-"))}`,
    "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files", "about:blank",
  ], { stdio: "ignore", detached: false });
  for (let i = 0; i < 40; i++) {
    try { await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break; } catch { await sleep(250); }
  }
}

const targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json().catch(() => null);
const page = targets && targets.find(t => t.type === "page");
if (!page) die(`no page target on port ${PORT}; is a headed browser running there?`, 2);

const ws = new WebSocket(page.webSocketDebuggerUrl);
let dead = null;
ws.addEventListener("close", e => { dead = `debugger socket closed (${e.code}) — the tab most likely died; try a lower --scale`; });
let id = 0; const waits = new Map();
const send = (method, params = {}) => new Promise((res, rej) => {
  if (dead) return rej(new Error(dead));
  const i = ++id; waits.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
await new Promise(r => ws.addEventListener("open", r, { once: true }));
ws.addEventListener("message", ev => {
  const m = JSON.parse(ev.data);
  if (m.id && waits.has(m.id)) { waits.get(m.id)(m.result); waits.delete(m.id); }
});

await send("Page.enable");
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: SCALE, mobile: false });
await send("Page.navigate", { url: "file://" + encodeURI(resolve(deck)) });
await sleep(SETTLE);

const hit = await send("Runtime.evaluate", { expression:
  `(()=>{const e=document.querySelector('[data-step=${JSON.stringify(beat)}]');
     if(!e) return "MISSING"; e.scrollIntoView(); return "ok";})()` });
if (hit?.result?.value !== "ok") die(`no beat with data-step="${beat}" in this deck`);
await sleep(HOLD);

const shot = await send("Page.captureScreenshot", { format: "png" });
if (dead) die(dead);
let buf = Buffer.from(shot.data, "base64");

if (CROP) {
  const [x, y, w, h] = CROP.split(",").map(Number);
  const tmp = out + ".full.png";
  fs.writeFileSync(tmp, buf);
  const py = `from PIL import Image
im = Image.open(${JSON.stringify(tmp)})
s = im.width / ${W}
b = tuple(round(v * s) for v in (${x}, ${y}, ${x + w}, ${y + h}))
im.crop(b).resize((round((b[2]-b[0])*${ZOOM}), round((b[3]-b[1])*${ZOOM}))).save(${JSON.stringify(out)})`;
  const r = spawn("python3", ["-c", py], { stdio: "inherit" });
  await new Promise(res => r.on("exit", res));
  fs.unlinkSync(tmp);
} else {
  fs.writeFileSync(out, buf);
}
console.log(`wrote ${out}  ${(fs.statSync(out).size / 1024).toFixed(0)} KB  beat=${beat}`);
if (child) child.kill();
process.exit(0);
