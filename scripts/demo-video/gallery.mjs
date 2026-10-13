// Devpost image gallery: 3:2 stills (1500x1000) of one finished store-review run on gitlab.com, logged out.
// Run: node scripts/demo-video/gallery.mjs run.json   (same run.json as record.mjs). Writes out/gallery/NN-name.png.
import { launch, sleep } from "./cdp.mjs";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const RUN = JSON.parse(readFileSync(process.argv[2], "utf8"));
const P = RUN.project;
const DIR = fileURLToPath(new URL("./out/gallery/", import.meta.url));
mkdirSync(DIR, { recursive: true });

const b = await launch({ width: 1200, height: 800, scale: 1.25, port: 9345 });
// scroll the element holding `text` to `top` px below the viewport top (GitLab scrolls an inner panel, not the window)
const scrollTo = (text, top) => b.evaluate(`(() => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode()); ) {
    if (!n.textContent.includes(${JSON.stringify(text)})) continue;
    const el = n.parentElement; if (el.getBoundingClientRect().height < 2) continue;
    let s = el.parentElement;
    while (s && !(s.scrollHeight > s.clientHeight + 4 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
    (s || window).scrollBy(0, el.getBoundingClientRect().top - ${top});
    return true;
  }
  return false;
})()`);
const shot = async (name, url, { anchor, top = 90, wait = 7000 } = {}) => {
  await b.goto(url, wait);
  await b.evaluate("document.getElementById('rec-cursor')?.remove(); document.getElementById('rec-ripple')?.remove()");
  if (anchor && !(await scrollTo(anchor, top))) console.error(`anchor not found on ${name}: ${anchor}`);
  await sleep(1200);
  await b.shot(DIR + name + ".png");
  console.log("wrote", name);
};

await shot("01-release-issue", `${P}/-/issues/${RUN.issue}`, { anchor: `Release v${RUN.version}`, top: 40 });
await shot("02-review-report", `${P}/-/issues/${RUN.issue}`, { anchor: `Store review for v${RUN.version}`, top: 150 });
await shot("03-fix-mr", `${P}/-/merge_requests/${RUN.fixMr}`, { anchor: "Guideline", top: 150, wait: 9000 });
await shot("04-resume", `${P}/-/issues/${RUN.issue}`, { anchor: "resume pass", top: 150 });
await shot("05-release-mr", `${P}/-/merge_requests/${RUN.releaseMr}`, { anchor: `Store release ${RUN.version}`, top: 40 });
await shot("06-pipeline", `${P}/-/pipelines/${RUN.pipeline}`, { wait: 9000 });
await shot("07-release", `${P}/-/releases/v${RUN.version}`, { anchor: "Release notes", top: 150 });
if (RUN.email && existsSync(RUN.email)) await shot("08-email", "file://" + RUN.email, { wait: 2000 });
await shot("09-live-app", `${RUN.app}/delete-account`, { wait: 4000 });
b.close();
