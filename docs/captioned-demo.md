# Captioned product demo

The `/demo` route is a fully synthetic, non-persistent walkthrough. It is safe to record: it does not show worker messages or call production write APIs.

After `/demo` is deployed, install the recorder once and create the video:

```bash
npm install
npx playwright install chromium
DEMO_BASE_URL="https://trustfall-8eks.vercel.app" npm run demo:record
```

The output is `demo-recordings/trustfall-captioned-demo.webm`. It already contains synchronized on-screen captions. Upload it directly to Loom, YouTube, or Drive. If a platform needs MP4, convert it with any local video converter after recording.

The five caption beats are built into the script: product overview, collection, redaction, human labeling, and measured model result.
