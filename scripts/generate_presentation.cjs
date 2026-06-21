/* Generate an editable Trustfall presentation from presentation/trustfall-metrics.json. */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const root = path.resolve(__dirname, "..");
const presentation = path.join(root, "presentation");
const metrics = JSON.parse(fs.readFileSync(path.join(presentation, "trustfall-metrics.json"), "utf8"));
const assets = path.join(presentation, "assets");
const out = path.join(presentation, "Trustfall_Project_Story.pptx");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Trustfall";
pptx.subject = "Trustfall: privacy-first human data to scam-safety model";
pptx.title = "Trustfall — Human data, safer inboxes";
pptx.company = "Trustfall";
pptx.lang = "en-US";
pptx.theme = { headFontFace: "Aptos Display", bodyFontFace: "Aptos", lang: "en-US" };
pptx.defineLayout({ name: "TRUSTFALL", width: 13.333, height: 7.5 });
pptx.layout = "TRUSTFALL";

const C = { navy: "050B1C", ink: "111827", slate: "334155", muted: "94A3B8", pale: "EAF2FF", card: "0D1730", cyan: "22D3EE", blue: "2563EB", violet: "8B5CF6", green: "34D399", amber: "FBBF24", white: "F8FAFC", red: "FB7185" };
const W = 13.333, H = 7.5;
const img = (name) => path.join(assets, name);
function base(slide, dark = false) {
  slide.background = { color: dark ? C.navy : "F8FAFC" };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 0.12, fill: { color: C.cyan }, line: { color: C.cyan } });
  slide.addText("TRUSTFALL", { x: 0.55, y: 0.3, w: 2, h: 0.25, fontFace: "Aptos Display", fontSize: 10, bold: true, color: dark ? C.cyan : C.blue, charSpacing: 1.5, margin: 0 });
}
function title(slide, text, sub, dark = false) {
  slide.addText(text, { x: 0.55, y: 0.7, w: 8.8, h: 0.65, fontSize: 28, bold: true, color: dark ? C.white : C.ink, margin: 0, breakLine: false });
  if (sub) slide.addText(sub, { x: 0.57, y: 1.4, w: 9.6, h: 0.36, fontSize: 11.5, color: dark ? "CBD5E1" : C.slate, margin: 0 });
}
function footer(slide, n, dark = false) {
  slide.addText(`${n}  |  Live metric refresh: ${metrics.generated_at}`, { x: 0.55, y: 7.13, w: 5.2, h: 0.18, fontSize: 7.5, color: dark ? "64748B" : C.muted, margin: 0 });
}
function pill(slide, text, x, y, color = C.cyan) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w: 1.75, h: 0.35, rectRadius: 0.08, fill: { color, transparency: 12 }, line: { color, transparency: 100 } });
  slide.addText(text, { x: x + 0.12, y: y + 0.09, w: 1.5, h: 0.12, fontSize: 7.5, bold: true, color: C.navy, align: "center", margin: 0 });
}
function stat(slide, value, label, x, y, color = C.cyan, dark = false) {
  slide.addText(String(value), { x, y, w: 2.25, h: 0.48, fontSize: 25, bold: true, color, margin: 0 });
  slide.addText(label, { x, y: y + 0.58, w: 2.45, h: 0.38, fontSize: 9.5, color: dark ? "CBD5E1" : C.slate, margin: 0 });
}
function card(slide, x, y, w, h, dark = false) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: dark ? "101E3D" : "FFFFFF" }, line: { color: dark ? "1E3A5F" : "D7E1EE", pt: 1 } });
}
function bullet(slide, text, x, y, color = C.ink, size = 13) {
  slide.addText([{ text: "• ", options: { color: C.cyan, bold: true } }, { text }], { x, y, w: 5.5, h: 0.42, fontSize: size, color, margin: 0, breakLine: false, bullet: { indent: 0 } });
}
function chart(slide, type, data, opts) {
  slide.addChart(type, data, { showLegend: false, showTitle: false, showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.slate, dataLabelFormatCode: "0", valAxisLabelColor: C.slate, catAxisLabelColor: C.slate, chartColors: [C.cyan, C.blue, C.violet, C.green, C.amber, C.red], chartArea: { fill: { color: "FFFFFF", transparency: 100 }, border: { color: "FFFFFF", transparency: 100 } }, plotArea: { fill: { color: "FFFFFF", transparency: 100 }, border: { color: "FFFFFF", transparency: 100 } }, ...opts });
}

// 1 — cover
{ const s = pptx.addSlide(); s.background = { color: C.navy }; s.addImage({ path: img("cover-laptop.jpg"), x: 6.85, y: 0, w: 6.48, h: 7.5, transparency: 25 }); s.addShape(pptx.ShapeType.rect, { x: 6.3, y: 0, w: 7.03, h: 7.5, fill: { color: C.navy, transparency: 38 }, line: { color: C.navy, transparency: 100 } }); s.addShape(pptx.ShapeType.rect, { x: 0.55, y: 1.05, w: 0.12, h: 1.25, fill: { color: C.cyan }, line: { color: C.cyan } }); s.addText("TRUSTFALL", { x: 0.9, y: 0.75, w: 2.2, h: 0.25, fontSize: 11, bold: true, color: C.cyan, charSpacing: 2, margin: 0 }); s.addText("Human data.\nSafer inboxes.", { x: 0.9, y: 1.25, w: 5.6, h: 1.6, fontSize: 39, bold: true, color: C.white, margin: 0, breakLine: false }); s.addText("A privacy-first workflow that turns real, redacted messages into human-labeled scam-safety intelligence.", { x: 0.92, y: 3.15, w: 4.7, h: 0.75, fontSize: 15, color: "CBD5E1", breakLine: false, margin: 0 }); pill(s, "Berkeley Hackathon 2026", 0.9, 4.35); s.addText("Collection → redaction → consensus labels → Qwen adaptation", { x: 0.92, y: 5.12, w: 4.9, h: 0.35, fontSize: 10.5, color: "94A3B8", margin: 0 }); }

// 2 — problem
{ const s = pptx.addSlide(); base(s); title(s, "The inbox is an adversarial interface.", "Scams borrow the visual language of trust. People need a calm, practical second opinion at the moment of uncertainty."); s.addImage({ path: img("cybersecurity.jpg"), x: 8.65, y: 1.95, w: 4.1, h: 4.5 }); card(s, 0.6, 2.05, 2.35, 3.35); card(s, 3.15, 2.05, 2.35, 3.35); card(s, 5.7, 2.05, 2.35, 3.35); [["Real signals", "Tone, links, sender mismatch, and urgency matter together."], ["Private by default", "Raw emails should not become a training-data liability."], ["Advice people use", "A risk score is not enough; people need the next safe action."]].forEach(([h, b], i) => { const x = 0.85 + i * 2.55; s.addText(String(i + 1).padStart(2, "0"), { x, y: 2.45, w: 0.5, h: 0.25, fontSize: 10, bold: true, color: C.cyan, margin: 0 }); s.addText(h, { x, y: 2.9, w: 1.85, h: 0.35, fontSize: 16, bold: true, color: C.ink, margin: 0 }); s.addText(b, { x, y: 3.55, w: 1.85, h: 1.1, fontSize: 10.5, color: C.slate, margin: 0, breakLine: false }); }); footer(s, 2); }

// 3 — workflow
{ const s = pptx.addSlide(); base(s, true); title(s, "Trustfall converts lived experience into an inspectable learning loop.", "Every stage is intentionally narrow: collect safely, remove identifiers, ask humans for judgment, then adapt the model.", true); const steps = [["01", "Collect", "Real messages via Terac"], ["02", "Redact", "Client + server safety layers"], ["03", "Label", "Independent human judgments"], ["04", "Learn", "LoRA adapter + holdout test"]]; steps.forEach(([n,h,b], i) => { const x=0.7+i*3.15; card(s,x,2.45,2.62,2.45,true); s.addText(n,{x:x+.25,y:2.75,w:.6,h:.25,fontSize:10,bold:true,color:C.cyan,margin:0});s.addText(h,{x:x+.25,y:3.25,w:1.8,h:.4,fontSize:20,bold:true,color:C.white,margin:0});s.addText(b,{x:x+.25,y:3.9,w:1.9,h:.5,fontSize:10.5,color:"CBD5E1",margin:0}); if(i<3)s.addText("→",{x:x+2.72,y:3.35,w:.35,h:.3,fontSize:18,color:C.cyan,margin:0}); }); footer(s,3,true); }

// 4 — privacy
{ const s=pptx.addSlide(); base(s); title(s,"Privacy is product architecture—not a cleanup step.","Trustfall keeps the useful evidence while stripping the sensitive payload."); s.addImage({path:img("cover-laptop.jpg"),x:8.5,y:1.9,w:4.2,h:4.55,transparency:5}); const items=[["Raw .eml stays client-side","Headers, attachments, and original files are not stored."],["Identifiers become placeholders","Names display as [PERSON]; links are defanged and tracking is removed."],["Training uses sanitized fields","Only redacted text and structured safety features reach the model pipeline."]]; items.forEach(([h,b],i)=>{const y=2.0+i*1.4; s.addShape(pptx.ShapeType.ellipse,{x:.75,y:y+.08,w:.42,h:.42,fill:{color:C.cyan},line:{color:C.cyan}});s.addText("✓",{x:.84,y:y+.16,w:.2,h:.15,fontSize:9,bold:true,color:C.navy,margin:0});s.addText(h,{x:1.4,y,w:5.85,h:.32,fontSize:15,bold:true,color:C.ink,margin:0});s.addText(b,{x:1.4,y:y+.47,w:5.9,h:.36,fontSize:10.5,color:C.slate,margin:0});});footer(s,4); }

// 5 — collection
{ const s=pptx.addSlide(); base(s,true); title(s,"The pilot is real: people submit, people review, the system learns.","Live operations are separated from synthetic QA fixtures and the model never edits source evidence.",true); s.addImage({path:img("team.jpg"),x:8.55,y:1.85,w:3.9,h:4.9,transparency:8}); stat(s,metrics.real_messages,"real sanitized messages",.8,2.25,C.cyan,true);stat(s,metrics.planned_labelers,"Wave 2 labeler capacity",3.35,2.25,C.green,true);stat(s,metrics.saved_labels,"human labels saved",5.9,2.25,C.amber,true); s.addText("The collection and labeling layer is already running in production through Terac. Every metric in this deck comes from the same database the app uses.",{x:.8,y:4.25,w:6.75,h:.8,fontSize:15,color:"CBD5E1",margin:0,breakLine:false}); footer(s,5,true); }

// 6 — labeling distribution
{ const s=pptx.addSlide(); base(s); title(s,"Consensus is a quality gate, not a checkbox.","Messages need two independent labels and sufficient agreement before they enter a training snapshot."); const dist=metrics.labels_per_message||{}; const labels=Object.keys(dist).map(k=>`${k} labels`); const values=Object.keys(dist).map(k=>dist[k]); chart(s,pptx.ChartType.bar,[{name:"Messages",labels,values}],{x:.75,y:2.1,w:6.2,h:3.95,catAxisLabelFontSize:10,valAxisLabelFontSize:9,valAxisMinVal:0,valAxisTitle:"Messages",showValue:true,showCatName:false}); card(s,7.5,2.15,4.75,3.75); const t=metrics.training_snapshot||{}; stat(s,t.eligible_messages||0,"consensus-eligible in current snapshot",7.85,2.55,C.blue); stat(s,t.train_messages||0,"training examples",10.25,2.55,C.violet); stat(s,t.eval_messages||0,"frozen holdout",7.85,4.4,C.green); s.addText("Quality exclusions stay visible: unreadable records, insufficient labels, and low agreement are not silently treated as truth.",{x:7.85,y:5.18,w:3.95,h:.45,fontSize:9.5,color:C.slate,margin:0}); footer(s,6); }

// 7 — Qwen baseline
{ const s=pptx.addSlide(); base(s,true); title(s,"Start with a baseline, not a claim.","Qwen/Qwen3-0.6B first reads the original sanitized Wave 1 data. Its outputs become the before-training reference.",true); s.addImage({path:img("data-dashboard.jpg"),x:8.45,y:1.85,w:4.2,h:4.95,transparency:12}); const b=metrics.model_comparison?.baseline||{}; stat(s,`${Math.round((b.valid_json_rate||0)*100)}%`,"valid JSON on held-out messages",.8,2.3,C.cyan,true);stat(s,`${Math.round((b.risk_exact_accuracy||0)*100)}%`,"risk-level exact match",3.65,2.3,C.amber,true);stat(s,`${Math.round((b.scam_type_exact_accuracy||0)*100)}%`,"scam-type exact match",6.5,2.3,C.red,true); s.addText("The baseline gives us something far more honest than a demo screenshot: a concrete point of comparison for formatting, safety-taxonomy alignment, and advice quality.",{x:.82,y:4.25,w:6.8,h:.75,fontSize:14,color:"CBD5E1",margin:0});footer(s,7,true); }

// 8 — comparison
{ const s=pptx.addSlide(); base(s); title(s,"Fine-tuning improves structured behavior—while the evidence stays modest.","The LoRA adapter was trained on the frozen consensus snapshot and evaluated only on unseen messages."); const b=metrics.model_comparison?.baseline||{}, f=metrics.model_comparison?.fine_tuned||{}; chart(s,pptx.ChartType.bar,[{name:"Baseline",labels:["Valid JSON","Risk exact","Scam type exact"],values:[(b.valid_json_rate||0)*100,(b.risk_exact_accuracy||0)*100,(b.scam_type_exact_accuracy||0)*100]},{name:"Fine-tuned",labels:["Valid JSON","Risk exact","Scam type exact"],values:[(f.valid_json_rate||0)*100,(f.risk_exact_accuracy||0)*100,(f.scam_type_exact_accuracy||0)*100]}],{x:.75,y:2.0,w:7.1,h:4.2,showLegend:true,legendPos:"b",legendFontSize:10,catAxisLabelFontSize:10,valAxisLabelFontSize:9,valAxisMaxVal:100,valAxisMinVal:0,valAxisMajorUnit:25,valAxisTitle:"Percent",chartColors:[C.slate,C.cyan],showValue:true}); card(s,8.3,2.08,4.1,3.92); s.addText("What changed",{x:8.65,y:2.48,w:2.7,h:.3,fontSize:18,bold:true,color:C.ink,margin:0}); bullet(s,"Valid JSON rose to 100% on the frozen holdout.",8.65,3.15,C.slate,11);bullet(s,"Exact accuracy is directional only: the holdout has just 4 examples.",8.65,4.0,C.slate,11);bullet(s,"The adapter is a pilot artifact, not a production claim.",8.65,4.85,C.slate,11); footer(s,8); }

// 9 — architecture
{ const s=pptx.addSlide(); base(s); title(s,"A pipeline that is inspectable at every handoff.","The operational app, data store, and local ML workflow stay deliberately separate."); const cols=[["Production app","Vercel + Next.js\nTerac task routes\nAdmin review"],["Data layer","Neon Postgres\nSanitized messages\nAssignments + labels"],["ML workstation","Qwen baseline\nConsensus export\nLoRA adapter + holdout"]];cols.forEach(([h,b],i)=>{const x=.75+i*4.15;card(s,x,2.2,3.5,3.2);s.addText(h,{x:x+.28,y:2.6,w:2.6,h:.34,fontSize:18,bold:true,color:C.ink,margin:0});s.addText(b,{x:x+.28,y:3.35,w:2.7,h:1.2,fontSize:12,color:C.slate,breakLine:false,margin:0});if(i<2)s.addText("→",{x:x+3.58,y:3.55,w:.4,h:.3,fontSize:20,color:C.cyan,margin:0});}); footer(s,9); }

// 10 — what makes it defensible
{ const s=pptx.addSlide(); base(s,true); title(s,"What makes Trustfall more than a scam classifier demo.","The product is the feedback loop: real examples, privacy boundaries, human judgment, and measured model change.",true); const points=[["Real-world inputs","Collected through a live task workflow—not a fabricated benchmark."],["Human consensus","Independent labels create a visible quality gate."],["Before / after evidence","A frozen holdout protects the story from self-deception."],["Re-runnable metrics","One refresh script updates the deck as data arrives."]];points.forEach(([h,b],i)=>{const x=.75+(i%2)*6.25,y=2.15+Math.floor(i/2)*1.9;card(s,x,y,5.7,1.35,true);s.addText(h,{x:x+.25,y:y+.25,w:2.6,h:.27,fontSize:15,bold:true,color:C.cyan,margin:0});s.addText(b,{x:x+.25,y:y+.68,w:4.9,h:.34,fontSize:10,color:"CBD5E1",margin:0});});footer(s,10,true); }

// 11 — roadmap
{ const s=pptx.addSlide(); base(s); title(s,"The next build is stronger agreement—not a bigger claim.","The pilot has proven the loop. More completed labels make the next training snapshot materially more credible."); const stages=[["Now","Finish active Wave 2 labels\nRefresh metrics\nRebuild consensus snapshot"],["Next","Retrain adapter\nExpand frozen holdout\nReview disagreements"],["Then","Prototype the end-user warning experience\nTest whether advice changes safer behavior"]]; stages.forEach(([h,b],i)=>{const x=.75+i*4.15;card(s,x,2.3,3.55,2.7);s.addText(h,{x:x+.25,y:2.66,w:1.5,h:.3,fontSize:18,bold:true,color:[C.cyan,C.blue,C.violet][i],margin:0});s.addText(b,{x:x+.25,y:3.3,w:2.9,h:1.1,fontSize:11,color:C.slate,margin:0});});s.addText("Trustfall is designed to become more useful as human judgment accumulates—without relaxing the privacy rules that make the data usable in the first place.",{x:.8,y:5.75,w:10.9,h:.42,fontSize:13,color:C.slate,italic:true,margin:0});footer(s,11); }

// 12 — close + credits
{ const s=pptx.addSlide(); s.background={color:C.navy}; s.addText("Trustfall",{x:.7,y:1.05,w:3,h:.5,fontSize:31,bold:true,color:C.white,margin:0});s.addText("Build safer inboxes from human judgment—without treating private messages as raw material.",{x:.73,y:1.82,w:6.5,h:.75,fontSize:17,color:"CBD5E1",margin:0});s.addShape(pptx.ShapeType.line,{x:.75,y:3.0,w:4.9,h:0,line:{color:C.cyan,pt:1.5}});s.addText("Deck refresh",{x:.75,y:3.45,w:1.4,h:.2,fontSize:10,bold:true,color:C.cyan,margin:0});s.addText("set -a; source .env.local; set +a\n.venv-qwen/bin/python scripts/refresh_presentation_metrics.py\nnode scripts/generate_presentation.cjs",{x:.75,y:3.8,w:7.6,h:.95,fontFace:"Aptos Mono",fontSize:10,color:C.white,margin:0});s.addText("Photography credits: Unsplash — cover laptop (photo-1516321318423-f06f85e504b3), cybersecurity (photo-1550751827-4bd374c3f58b), analytics (photo-1551288049-bebda4e38f71), team (photo-1521737711867-e3b97375f902).",{x:.75,y:6.4,w:11.5,h:.35,fontSize:7.5,color:"94A3B8",margin:0});footer(s,12,true); }

pptx.writeFile({ fileName: out });
console.log(`Wrote ${out}`);
