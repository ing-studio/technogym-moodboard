#!/usr/bin/env node
/**
 * frameprobe — measure a scrollytelling deck's real frame behaviour from the terminal.
 *
 *   node frameprobe.mjs <deck.html> --launch --walk --glide
 *   node frameprobe.mjs <deck.html> --port 9333 --glide --stall-ms 150
 *
 * WHY THIS EXISTS. "Frame rate can only be judged by a human opening the file" is false, and the
 * usual headless harness is worse than useless for a scroll deck: headless Chrome renders a WebGL
 * map at about one frame per second AND DELIVERS ZERO IntersectionObserver ENTRIES, so every card
 * reports as never revealed and every beat as never activated. That reads exactly like a broken
 * scroll controller and it is only the harness. A headed Chrome on a debug port measures frames fine.
 * A single frame of 1,363 ms hid behind a clean headless run until this probe was written.
 *
 * WHAT IT MEASURES: frame deltas (percentiles), long tasks, uncaught exceptions, console errors,
 * per-beat card reveal, and unbound data stamps.
 * WHAT IT CANNOT JUDGE: whether the deck LOOKS right. Composition, camera feel, whether a colour
 * reads, whether the copy lands. That still needs a person.
 *
 * READ PERCENTILES, NEVER THE MEAN. On a 120 Hz display the median sits at 8.3 ms whether the deck is
 * healthy or stalling; the damage shows in p99, in max, and in the frame COUNT (a four-second window
 * that collects 4 frames instead of 450).
 *
 * Flags:
 *   --launch          start Chrome with a throwaway profile (else attach to --port)
 *   --port N          debug port, default 9333
 *   --walk            per-beat: card revealed, unbound stamps, parked frame median/p90/max
 *   --glide           continuous scroll in segments: percentiles, slow frames, long tasks
 *   --stall-ms N      a frame at or above this is a hard failure, default 200
 *   --step-sel S      beat selector, default "section.step"
 *   --settle-ms N     wait after load before measuring, default 4000
 *   --keep            leave the browser running (default closes what it launched)
 * Exit code is non-zero on any exception, console error, or frame at or over --stall-ms.
 */

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const argv = process.argv.slice(2);
const VALUE_FLAGS = new Set(["port", "stall-ms", "step-sel", "settle-ms"]);
const flag = (n) => argv.includes("--" + n);
const opt = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
let file = null;
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith("--")) { if (VALUE_FLAGS.has(argv[i].slice(2))) i++; continue; }
  file = argv[i]; break;
}

if (!file) { console.error("usage: node frameprobe.mjs <deck.html> [--launch] [--walk] [--glide]"); process.exit(2); }

const PORT = +opt("port", "9333");
const STALL = +opt("stall-ms", "200");
const STEP_SEL = opt("step-sel", "section.step");
const SETTLE = +opt("settle-ms", "4000");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const CHROME = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
];

let child = null;
if (flag("launch")) {
  const bin = CHROME.find((p) => existsSync(p));
  if (!bin) { console.error("no Chrome found; start one yourself and pass --port"); process.exit(2); }
  const profile = mkdtempSync(join(tmpdir(), "frameprobe-"));
  // A REAL window, not --headless. Software raster cannot answer the question being asked here.
  child = spawn(bin, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
    "--no-first-run", "--no-default-browser-check", "--window-size=1600,1000", "about:blank"],
    { stdio: "ignore", detached: true });
  child.unref();
  await sleep(6000);
}

// A freshly launched Chrome reports an EMPTY /json/list until a target is created. Every first
// attempt at this fails on "cannot read properties of undefined"; create the tab, then attach.
async function target() {
  for (let i = 0; i < 20; i++) {
    const list = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).catch(() => []);
    const page = list.find((t) => t.type === "page");
    if (page) return page;
    await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" }).catch(() => {});
    await sleep(500);
  }
  throw new Error(`no page target on port ${PORT}; is a browser running there?`);
}

const page = await target();
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0; const pend = new Map(); const errs = [];
const send = (m, p = {}) => new Promise((r) => { const n = ++id; pend.set(n, r); ws.send(JSON.stringify({ id: n, method: m, params: p })); });
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); return; }
  if (m.method === "Runtime.exceptionThrown")
    errs.push("EXCEPTION " + (m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text || "").slice(0, 200));
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error")
    errs.push("console.error " + (m.params.args || []).map((a) => a.value ?? a.description).join(" ").slice(0, 200));
};
// If the browser or the tab goes away mid-run, every pending await simply never settles and node
// exits with "unsettled top-level await", which says nothing about what happened. Fail out loud.
let finishing = false;                 // the deliberate shutdown below also closes the socket
ws.onclose = () => {
  if (finishing) return;
  console.error("\nthe debugger socket closed mid-run: the browser or the tab went away.\n" +
    "Relaunch it (--launch) or reopen a tab on the debug port, then run again.");
  process.exit(3);
};
await new Promise((r) => (ws.onopen = r));
await send("Page.enable"); await send("Runtime.enable");

const ev = async (expr, awaitPromise = false) => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise });
  if (r?.exceptionDetails) return { __threw: (r.exceptionDetails.exception?.description || "").slice(0, 200) };
  return r.result?.value;
};

const url = "file://" + encodeURI(resolve(file));
await send("Page.navigate", { url: url + "?frameprobe=" + Date.now() });
for (let i = 0; i < 80; i++) { if (await ev(`document.readyState==="complete"`)) break; await sleep(400); }
await sleep(SETTLE);

const steps = await ev(`[].slice.call(document.querySelectorAll(${JSON.stringify(STEP_SEL)})).map(function(s){return s.dataset.step||""})`);
if (!Array.isArray(steps) || !steps.length) { console.error(`no beats matched ${STEP_SEL}`); process.exit(2); }
console.log(`deck: ${steps.length} beat(s) matching ${STEP_SEL}\n`);

/** sample n frame deltas while running `perFrame` (a JS statement) each frame */
const sampler = (n, perFrame) => `new Promise(function(res){
  var d=[], last=performance.now(), k=0, lt=[];
  var po; try{ po=new PerformanceObserver(function(l){ l.getEntries().forEach(function(e){ lt.push(Math.round(e.duration)); }); });
    po.observe({entryTypes:["longtask"]}); }catch(e){}
  function step(){ var t=performance.now(); d.push(t-last); last=t; k++; ${perFrame}
    if(k<${n}) requestAnimationFrame(step);
    else { if(po) po.disconnect(); var s=d.slice(2).sort(function(a,b){return a-b;});
      if(!s.length) s=[0];
      res({n:s.length, med:+s[Math.floor(s.length*0.5)].toFixed(1), p90:+s[Math.floor(s.length*0.9)].toFixed(1),
           p99:+s[Math.min(s.length-1,Math.floor(s.length*0.99))].toFixed(1), max:+s[s.length-1].toFixed(1),
           over32:s.filter(function(x){return x>32;}).length, over50:s.filter(function(x){return x>50;}).length,
           longtasks:lt.length, longmax:lt.length?Math.max.apply(null,lt):0}); } }
  requestAnimationFrame(step);
})`;

let worst = 0, worstWhere = "";
const note = (ms, where) => { if (ms > worst) { worst = ms; worstWhere = where; } };

// THE HARNESS FLOOR, measured before anything else. A window that is occluded, minimised or behind
// another app is throttled by the browser, typically to 30fps, and then EVERY beat reports ~33 ms and
// the run looks uniformly slow while telling you nothing. Sample the interval while the page is
// parked on its first beat, which draws nothing: whatever that costs is the floor, not the deck.
await ev(`window.scrollTo(0,0)`);
await sleep(600);
const floor = await ev(sampler(20, ""), true);
const FLOOR = floor.med;
const THROTTLED = FLOOR > 20;
console.log(`harness floor: ${FLOOR} ms median on an idle beat` +
  (THROTTLED
    ? `  <-- THROTTLED. The browser is not painting at full rate, almost always because the window is
   occluded, minimised or on a hidden desktop. Per-beat medians below are floor-bound and are NOT
   evidence about the deck. Bring the window to the front and run again.`
    : "  (full rate, per-beat numbers are the deck's own)") + "\n");
// a beat is only "slow" if it costs meaningfully more than the floor
const SLOW = Math.max(32, FLOOR * 1.35);

if (flag("walk")) {
  console.log("  #  beat                card   text  unbound   parked med / p90 / max");
  for (let i = 0; i < steps.length; i++) {
    await ev(`document.querySelectorAll(${JSON.stringify(STEP_SEL)})[${i}].scrollIntoView({block:"center"})`);
    await sleep(700);
    const st = await ev(`(function(){var s=document.querySelectorAll(${JSON.stringify(STEP_SEL)})[${i}], c=s.querySelector(".card");
      return {card:!!(c&&c.classList.contains("in")), txt:c?c.innerText.trim().length:0,
        unbound:[].slice.call(s.querySelectorAll("[data-deck],[data-deck-doc]")).filter(function(e){
          var v=(e.textContent||"").trim(); return !v||v==="??";}).length};})()`);
    const f = await ev(sampler(14, ""), true);
    note(f.max, steps[i]);
    console.log(`${String(i + 1).padStart(3)}  ${(steps[i] || "?").padEnd(18)} ${st.card ? " in " : "OUT "} ${String(st.txt).padStart(5)} ${String(st.unbound).padStart(8)}   ` +
      `${String(f.med).padStart(6)} / ${String(f.p90).padStart(6)} / ${String(f.max).padStart(7)}${f.max >= STALL ? "  <-- STALL" : (f.med > SLOW ? "  <-- slow" : "")}`);
  }
  console.log("");
}

if (flag("glide")) {
  const H = await ev("document.documentElement.scrollHeight - innerHeight");
  const SEGS = 6;
  console.log("  segment           frames   med    p90    p99    max   >32  >50  longtasks");
  for (let s = 0; s < SEGS; s++) {
    const from = Math.round((H * s) / SEGS);
    await ev(`window.scrollTo(0,${from})`);
    await sleep(1200);
    const f = await ev(sampler(260, "window.scrollBy(0,16);"), true);
    note(f.max, `glide ${s + 1}/${SEGS}`);
    console.log(`  ${String(s + 1).padStart(2)}/${SEGS} from ${String(from).padStart(6)}  ${String(f.n).padStart(6)} ` +
      `${String(f.med).padStart(6)} ${String(f.p90).padStart(6)} ${String(f.p99).padStart(6)} ${String(f.max).padStart(6)} ` +
      `${String(f.over32).padStart(5)} ${String(f.over50).padStart(4)} ${String(f.longtasks).padStart(10)}` +
      `${f.max >= STALL ? "  <-- STALL" : ""}`);
  }
  console.log("");
}

const uniq = [...new Set(errs)];
console.log(uniq.length ? "errors:\n  " + uniq.join("\n  ") : "errors: none");
console.log(`worst frame: ${worst.toFixed(1)} ms${worstWhere ? " on " + worstWhere : ""} (stall threshold ${STALL} ms, harness floor ${FLOOR} ms)`);
if (THROTTLED) console.log("this run was throttled: treat the per-beat medians as unusable and rerun with the window visible.");
console.log("not measured here: whether the deck looks right. A person still has to open it.");

finishing = true;
if (!flag("keep") && child) { try { process.kill(-child.pid); } catch {} }
process.exit(uniq.length || worst >= STALL ? 1 : 0);
