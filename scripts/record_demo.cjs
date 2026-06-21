/* Records a captioned, safe product walkthrough. Captions are DOM overlays captured in the video. */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const output = path.join(root, "demo-recordings");
const baseUrl = process.env.DEMO_BASE_URL || "https://trustfall-8eks.vercel.app";
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function caption(page, text) {
  await page.evaluate((value) => {
    let box = document.getElementById("trustfall-demo-caption");
    if (!box) {
      box = document.createElement("div");
      box.id = "trustfall-demo-caption";
      Object.assign(box.style, { position: "fixed", left: "50%", bottom: "28px", transform: "translateX(-50%)", zIndex: "999999", maxWidth: "900px", padding: "13px 20px", borderRadius: "12px", background: "rgba(2, 6, 23, .90)", color: "#f8fafc", border: "1px solid rgba(34,211,238,.7)", boxShadow: "0 8px 32px rgba(0,0,0,.45)", font: "600 20px/1.25 Arial, sans-serif", textAlign: "center" });
      document.body.appendChild(box);
    }
    box.textContent = value;
  }, text);
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: output, size: { width: 1280, height: 720 } } });
  const page = await context.newPage();
  await page.goto(`${baseUrl}/demo`, { waitUntil: "networkidle" });
  await caption(page, "Trustfall turns real-world scam signals into safer, human-grounded guidance.");
  await pause(3200);
  await page.locator('[data-demo="begin"]').click();
  await page.locator('[data-demo="collection"]').scrollIntoViewIfNeeded();
  await caption(page, "Wave 1 collects message signals while keeping raw emails out of the data store.");
  await pause(3200);
  await page.locator('[data-demo="redact"]').click();
  await caption(page, "Names, links, phone numbers, and codes become privacy-preserving placeholders.");
  await pause(3200);
  await page.locator('[data-demo="labeling"]').scrollIntoViewIfNeeded();
  await caption(page, "Wave 2 asks independent people to label risk, scam type, red flags, and the safest action.");
  await pause(3400);
  await page.locator('[data-demo="save-label"]').click();
  await page.locator('[data-demo="results"]').scrollIntoViewIfNeeded();
  await caption(page, "Only quality-gated consensus labels enter the Qwen fine-tuning pipeline.");
  await pause(3200);
  await caption(page, "Trustfall reports both model improvement and the limits of a small pilot dataset.");
  await pause(3500);
  const video = page.video();
  await page.close();
  await context.close();
  const saved = await video.path();
  const finalPath = path.join(output, "trustfall-captioned-demo.webm");
  fs.copyFileSync(saved, finalPath);
  await browser.close();
  console.log(`Wrote ${finalPath}`);
}

main().catch((error) => { console.error(error); process.exit(1); });
