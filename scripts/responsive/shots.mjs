// R8 check on the real web build: drives build/web headlessly through onboarding, sign-in (anonymous), a job, an entry,
// the timesheet and the account tab, and screenshots every screen at five sizes. Run: node scripts/responsive/shots.mjs
// Needs a current `flutter build web` (with semantics enabled on the web). Writes scripts/responsive/out/.
// The anonymous account and its data are deleted at the end, through the app's own Delete account flow.
import { createServer } from "node:http";
import { readFileSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { launch, sleep } from "../demo-video/cdp.mjs";

const ROOT = fileURLToPath(new URL("../../build/web/", import.meta.url));
const OUT = fileURLToPath(new URL("./out/", import.meta.url));
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png",
  ".svg": "image/svg+xml", ".wasm": "application/wasm", ".otf": "font/otf", ".ttf": "font/ttf", ".css": "text/css" };
// static server with SPA fallback, so deep links load the app
const server = createServer((req, res) => {
  let p = join(ROOT, decodeURIComponent(req.url.split("?")[0]));
  if (!existsSync(p) || p.endsWith("/")) p = join(ROOT, "index.html");
  res.writeHead(200, { "Content-Type": TYPES[extname(p)] || "application/octet-stream" });
  res.end(readFileSync(p));
}).listen(8791);
const BASE = "http://localhost:8791";

const SIZES = { "360x740": [360, 740], "390x844": [390, 844], "820x1180": [820, 1180], "1180x820": [1180, 820], "1440x900": [1440, 900] };
const b = await launch({ width: 390, height: 844, scale: 2, port: 9346 });
const resize = async ([w, h]) => {
  await b.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 2, mobile: w < 1000 });
  await b.send("Emulation.setTouchEmulationEnabled", { enabled: w < 1000 });
  await sleep(1500);
};
const hScroll = () => b.evaluate("document.documentElement.scrollWidth - innerWidth");
const shotAll = async (name) => {
  for (const [label, size] of Object.entries(SIZES)) {
    await resize(size);
    await b.evaluate("document.getElementById('rec-cursor')?.remove(); document.getElementById('rec-ripple')?.remove()");
    await b.shot(`${OUT}${name}@${label}.png`);
    const over = await hScroll();
    if (over > 0) console.error(`HORIZONTAL SCROLL ${over}px: ${name}@${label}`);
  }
  await resize(SIZES["390x844"]);
  console.log("shot", name);
};
const tap = (text, opts = {}) => b.click(text, opts);
const typeInto = async (label, text) => { await tap(label); await sleep(400); await b.type(text); await sleep(300); };
const go = async (path) => { await b.evaluate(`history.pushState({}, '', '${path}'); dispatchEvent(new PopStateEvent('popstate'))`); await sleep(2500); };

await b.goto(BASE + "/", 9000);
await shotAll("01-onboarding");
await tap("Get Started"); await sleep(3000);
await shotAll("02-sign-in");
await tap("Sign in anonymously"); await sleep(5000);
await shotAll("03-jobs-empty");
await tap("New job"); await sleep(2000);
await typeInto("Job name", "Website redesign");
await typeInto("Rate per hour", "45.50");
await shotAll("04-job-form");
await tap("Save", { gone: true }); await sleep(3000);
await tap("New job"); await sleep(2000);
await typeInto("Job name", "Mobile app QA");
await typeInto("Rate per hour", "30");
await tap("Save", { gone: true }); await sleep(3000);
await shotAll("05-jobs");
await tap("Website redesign"); await sleep(3000);
await tap("New entry"); await sleep(2500);
for (let i = 0; i < 6; i++) { await b.click("15 minutes more", { nth: 1 }).catch(() => {}); await sleep(150); }
await shotAll("06-entry-editor");
await tap("Save", { gone: true }); await sleep(3000);
await shotAll("07-job-entries");
await go("/entries");
await shotAll("08-timesheet");
await go("/account");
await shotAll("09-account");

// clean up: delete the anonymous account and its data through the app
await tap("Delete account"); await sleep(1500);
await tap("Delete", { exact: true }); await sleep(6000);
console.log("after cleanup:", (await b.evaluate("location.pathname")));
b.close(); server.close();
