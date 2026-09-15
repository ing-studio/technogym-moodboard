#!/usr/bin/env node
/**
 * shotbeat: screenshot one beat of the scroll deck in a real, headed browser.
 *
 *   node shotbeat.mjs <deck.html> --beat <data-step> --out shot.png [--launch]
 *   node shotbeat.mjs deck/index.html --beat plan --out deck/build/plan.png --launch --crop 600,100,800,600
 *
 * Flags:
 *   --beat S        data-step to park on (required)
 *   --out F         PNG path (required; folders are created)
 *   --launch        start a throwaway Chrome/Edge on --port (else attach to one already running)
 *   --port N        debug port, default 9333
 *   --width/--height viewport, default 1600x1000 (use 390x844 to check the narrow layout)
 *   --settle N      max ms to wait for every image to load, default 8000
 *   --hold N        ms after scrolling for the beat's transitions to finish, default 2000
 *   --crop x,y,w,h  crop in CSS px and upscale (--zoom, default 2); needs python + Pillow
 *
 * Traps:
 *  1. HEADLESS DELIVERS NO IntersectionObserver ENTRIES, so no beat activates and every card stays
 *     hidden. That looks like a broken deck and is only the harness. This script runs headed.
 *  2. Wait for images, then wait again after the scroll: the 140 ms commit debounce plus ~1 s of
 *     fade/zoom/reveal. A shot taken early photographs a transition.
 *  3. Keep deviceScaleFactor at 1; crop and upscale for detail.
 *  4. Node's built-in WebSocket (Node 22+) is used; no npm install.
 *
 * A shot proves geometry (did the area land, does the card fit). It does not judge composition.
 */

import fs from "node:fs";
import { spawn } from "node:child_process";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf("--" + n); return i < 0 ? d : argv[i + 1]; };
const has = (n) => argv.includes("--" + n);

const deck = argv.find((a) => !a.startsWith("--") && /\.html?$/i.test(a));
const beat = flag("beat"), out = flag("out");
if (!deck || !beat || !out) {
  console.error("usage: node shotbeat.mjs <deck.html> --beat <data-step> --out <shot.png> [--launch]");
  process.exit(2);
}
const PORT = +flag("port", 9333), W = +flag("width", 1600), H = +flag("height", 1000);
const SETTLE = +flag("settle", 8000), HOLD = +flag("hold", 2000), ZOOM = +flag("zoom", 2), CROP = flag("crop");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const BROWSERS = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
];

let child = null;
const die = (msg, code = 1) => { console.error(msg); if (child) child.kill(); process.exit(code); };

if (has("launch")) {
  const bin = BROWSERS.find((p) => fs.existsSync(p));
  if (!bin) die("no Chrome or Edge found; start one with --remote-debugging-port and omit --launch", 2);
  child = spawn(bin, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${fs.mkdtempSync(join(tmpdir(), "shotbeat-"))}`,
    `--window-size=${W},${H}`,
    "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files", "about:blank",
  ], { stdio: "ignore" });
  for (let i = 0; i < 60; i++) {
    try { await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break; } catch { await sleep(250); }
  }
}

let targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json().catch(() => null);
let page = targets && targets.find((t) => t.type === "page");
if (!page) {   // a fresh browser can report no page target until one is created
  page = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json().catch(() => null);
}
if (!page) die(`no page target on port ${PORT}; is a headed browser running there?`, 2);

const ws = new WebSocket(page.webSocketDebuggerUrl);
let dead = null, id = 0;
const waits = new Map();
ws.addEventListener("close", (e) => { dead = `debugger socket closed (${e.code}); the tab likely died`; });
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && waits.has(m.id)) { waits.get(m.id)(m.result); waits.delete(m.id); }
});
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
const send = (method, params = {}) => new Promise((res, rej) => {
  if (dead) return rej(new Error(dead));
  const i = ++id; waits.set(i, res); ws.send(JSON.stringify({ id: i, method, params }));
});
const evaluate = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true }))?.result?.value;

await send("Page.enable");
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W <= 720 });
await send("Page.navigate", { url: pathToFileURL(resolve(deck)).href });

const hit = await (async () => {
  for (let t = 0; t < 40; t++) {
    const v = await evaluate(`(()=>{const e=document.querySelector('[data-step=${JSON.stringify(beat)}]');
      if(!e) return document.readyState==="complete" ? "MISSING" : "WAIT"; e.scrollIntoView(); return "ok";})()`);
    if (v === "ok" || v === "MISSING") return v;
    await sleep(250);
  }
  return "MISSING";
})();
if (hit !== "ok") die(`no beat with data-step="${beat}" in ${deck}`);

const t0 = Date.now();
await sleep(400);
while (Date.now() - t0 < SETTLE) {
  const done = await evaluate(`[].every.call(document.images, i => !i.getAttribute("src") || i.complete)`);
  if (done) break;
  await sleep(250);
}
await sleep(HOLD);

const errors = await evaluate(`(window.__APP && window.__APP.state && window.__APP.state.id) || "none"`);
const shot = await send("Page.captureScreenshot", { format: "png" });
if (dead) die(dead);
fs.mkdirSync(dirname(resolve(out)), { recursive: true });
const buf = Buffer.from(shot.data, "base64");

if (CROP) {
  const [x, y, w, h] = CROP.split(",").map(Number);
  const tmp = out + ".full.png";
  fs.writeFileSync(tmp, buf);
  const py = `from PIL import Image
im = Image.open(${JSON.stringify(tmp)}); s = im.width / ${W}
b = tuple(round(v * s) for v in (${x}, ${y}, ${x + w}, ${y + h}))
im.crop(b).resize((round((b[2]-b[0])*${ZOOM}), round((b[3]-b[1])*${ZOOM}))).save(${JSON.stringify(out)})`;
  const r = spawn(process.platform === "win32" ? "python" : "python3", ["-c", py], { stdio: "inherit" });
  await new Promise((res) => r.on("exit", res));
  fs.unlinkSync(tmp);
} else {
  fs.writeFileSync(out, buf);
}
console.log(`wrote ${out}  ${(fs.statSync(out).size / 1024).toFixed(0)} KB  beat=${beat}  active scene=${errors}`);
if (child) child.kill();
process.exit(0);
