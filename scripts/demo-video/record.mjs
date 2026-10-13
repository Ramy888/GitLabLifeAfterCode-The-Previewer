// Records the demo as a replay of one finished store-review run on gitlab.com: headless Chrome, logged out
// (the project is public), a drawn pointer, no Claude overlay. Each cue names the DevSecOps stage it shows.
// Run: node scripts/demo-video/record.mjs [run.json]   (defaults to the v2.1.1 run below)
// Then, inside scripts/demo-video/out/:
//   ffmpeg -f concat -safe 0 -i list.txt -vf "scale=1920:1200,format=yuv420p" -r 30 -c:v libx264 -crf 18 previewer-silent.mp4
import { launch, sleep } from "./cdp.mjs";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const RUN = {
  project: "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/1947121/showcase",
  version: "2.1.1",
  issue: 3,          // the release issue assigned to The Previewer
  fixMr: 2,          // one fix MR the flow opened (its diff is the "create" beat)
  releaseMr: 9,      // the store-review/<version> MR
  pipeline: 2938382351, // the pipeline of the release MR's merge commit on main
  app: "https://time-tracker-web-57342278583.us-central1.run.app",
  email: null,       // optional local HTML of the release email (store-review notify --html-out)
  ...(process.argv[2] ? JSON.parse(readFileSync(process.argv[2], "utf8")) : {}),
};
const P = RUN.project;

const DIR = fileURLToPath(new URL("./out/", import.meta.url));
rmSync(DIR, { recursive: true, force: true }); mkdirSync(DIR + "frames", { recursive: true });

const b = await launch({ scale: 4 / 3 });
const cues = [];
const cue = (stage, text) => { cues.push({ at: b.mark(), stage, text }); console.log(b.mark().toFixed(1), `[${stage}]`, text); };
const hover = (x, y) => b.moveTo({ x, y });

// GitLab note bodies and tables are plain divs and cells, which cdp.find does not scan: locate by text instead
const locate = (text, { within = "body" } = {}) => b.evaluate(`(() => {
  const want = ${JSON.stringify(text)};
  const walker = document.createTreeWalker(document.querySelector(${JSON.stringify(within)}) || document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode()); ) {
    if (!n.textContent.includes(want)) continue;
    const el = n.parentElement, r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    document.querySelectorAll('[data-rec-text]').forEach((e) => e.removeAttribute('data-rec-text'));
    el.setAttribute('data-rec-text', '1');
    return { x: r.x + Math.min(r.width, 600) / 2, y: r.y + r.height / 2 };
  }
  return null;
})()`);
// wait for lazily loaded content (issue notes, pipeline graph) instead of trusting a fixed sleep
const waitFor = async (text, ms = 20000) => {
  for (let t = 0; t < ms; t += 250) { const p = await locate(text); if (p) return p; await sleep(250); }
  await b.shot(DIR + "../fail.png");
  throw new Error(`not on page after ${ms / 1000} s: ${text} (${await b.evaluate("location.href")})`);
};
// smooth-scroll the element holding `text` to `top` px from the viewport top, then point at it
const scrollTo = async (text, { top = 180, point = true } = {}) => {
  await waitFor(text);
  await b.evaluate(`(() => {
    const el = document.querySelector('[data-rec-text]');
    let s = el.parentElement;
    while (s && !(s.scrollHeight > s.clientHeight + 4 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
    const dy = el.getBoundingClientRect().top - ${top};
    (s || window).scrollBy({ top: dy, behavior: 'smooth' });
  })()`);
  await sleep(1300);
  if (point) { const p = await locate(text); if (p) await hover(p.x, p.y); }
};
// page loads are cut out of the video: pause, navigate, wait for the content, resume
const open = async (url, ready) => {
  b.pause();
  await b.goto(url, 2500);
  if (ready) await waitFor(ready);
  await sleep(800); await b.ensureCursor();
  await b.resume();
};

// 1. plan: the release issue, assigned to the flow's service account
await b.goto(`${P}/-/issues/${RUN.issue}`, 4000);
await waitFor(`Release v${RUN.version}`);
await b.startRec();
const t0 = b.mark();
cue("plan", `A release issue for v${RUN.version}, assigned to The Previewer`);
await sleep(1500); const title = await locate(`Release v${RUN.version}`); await hover(title.x, title.y); await sleep(2500);
await scrollTo("assigned to", { top: 300 }); await sleep(3000);

// 2. secure + verify: the review report, one row per store, gated readiness with a band
cue("secure", "The Previewer reviews the app the way both stores will: readiness, band, blockers");
await scrollTo(`Store review for v${RUN.version}`, { top: 140 }); await sleep(2500);
await scrollTo("Readiness", { top: 140 }); await sleep(4000);

// 3. govern: the one human handoff, and the reply that resumes the flow
cue("govern", "One handoff: what only a human can provide. A reply resumes the flow");
await scrollTo("I need these from you to continue", { top: 200 }); await sleep(3500);
await scrollTo("resume pass", { top: 160 }); await sleep(3500);

// 4. create: a fix MR the flow opened for a safe finding
await open(`${P}/-/merge_requests/${RUN.fixMr}`, "Guideline");
cue("create", "Safe findings become fix merge requests, each citing the guideline it answers");
await sleep(2000); await hover(900, 420); await sleep(2500); await b.wheel(360); await sleep(3000);

// 5. package + release: the release MR carries the committed reviewer judgement
await open(`${P}/-/merge_requests/${RUN.releaseMr}`, `Store release ${RUN.version}`);
cue("release", "The release MR: the outcome a human approves by merging");
await sleep(1500); const mrTitle = await locate(`Store release ${RUN.version}`); await hover(mrTitle.x, mrTitle.y); await sleep(3000);
await b.wheel(420); await sleep(3500);

// 6. verify + package + release + monitor: the merge pipeline, stage by stage
await open(`${P}/-/pipelines/${RUN.pipeline}`, "review:scan");
cue("verify", "On merge: tests, scan, benchmark, builds, then the GitLab Release and the email");
await sleep(1500);
for (const job of ["flutter:test", "review:scan", "build:web", "release:gitlab", "notify:release"]) {
  const p = await locate(job); if (p) { await hover(p.x, p.y); await sleep(1400); }
}
await sleep(1500);

// 7. release: the GitLab Release with the per-store reports
await open(`${P}/-/releases/v${RUN.version}`, "Release notes");
cue("release", "A GitLab Release: per-store readiness, evidence for every finding");
await sleep(1500); await scrollTo("Readiness", { top: 260 }); await sleep(4000);
await b.wheel(600); await sleep(3000);

// 8. monitor: the release email (a local render of what notify:release sent)
if (RUN.email && existsSync(RUN.email)) {
  await open("file://" + RUN.email, null);
  cue("monitor", "The team gets the outcome by email, with the scores and the Release link");
  await sleep(2000); await hover(760, 380); await sleep(4000);
}

// 9. configure: the live web build on Cloud Run (store-required pages only, no third-party sign-in buttons)
await open(`${RUN.app}/delete-account`, null);
cue("configure", "Deployed by the same pipeline to Google Cloud Run, with the pages both stores require");
await sleep(2000); await hover(700, 360); await sleep(4000);

const { frames, end } = await b.stopRec();
b.close();

// frames -> constant 30 fps: each output slot shows the newest frame captured by then
const FPS = 30, start = frames[0].t, slots = Math.ceil((end - start) * FPS);
const list = []; let j = 0; const written = new Map();
for (let s = 0; s < slots; s++) {
  const t = start + s / FPS;
  while (j + 1 < frames.length && frames[j + 1].t <= t) j++;
  if (!written.has(j)) { const name = `frames/${String(j).padStart(5, "0")}.jpg`; writeFileSync(DIR + name, Buffer.from(frames[j].data, "base64")); written.set(j, name); }
  list.push(`file '${written.get(j)}'`, `duration ${(1 / FPS).toFixed(6)}`);
}
list.push(list[list.length - 2]);
writeFileSync(DIR + "list.txt", list.join("\n") + "\n");
writeFileSync(DIR + "cues.json", JSON.stringify(cues.map((c) => ({ ...c, at: Math.max(0, c.at - start) })), null, 1));
console.log(`frames ${frames.length}, length ${(end - start).toFixed(1)} s (from ${t0.toFixed(1)})`);
