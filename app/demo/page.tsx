"use client";

import { useState } from "react";

const raw = "Hi Jordan,\n\nYour package is waiting. Confirm delivery at https://track-fast.example/claim?code=884219 or call 555-0100 today.\n\nThanks,\nMaya";
const redacted = "Hi [PERSON],\n\nYour package is waiting. Confirm delivery at [LINK] or call [PHONE] today.\n\nThanks,\n[PERSON]";

export default function DemoPage() {
  const [step, setStep] = useState(0);
  const [showRaw, setShowRaw] = useState(true);
  const [labelSaved, setLabelSaved] = useState(false);

  return <main className="mx-auto max-w-6xl px-6 py-8">
    <section className="rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-slate-900 to-slate-950 p-8 shadow-2xl" data-demo="hero">
      <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">Trustfall · interactive product demo</p>
      <h1 className="mt-3 max-w-3xl text-5xl font-bold leading-tight">Human judgment makes scam safety better.</h1>
      <p className="mt-4 max-w-2xl text-lg text-slate-300">A privacy-first workflow from real-world signals to human labels to a measured model improvement.</p>
      <button className="btn mt-6" data-demo="begin" onClick={() => setStep(1)}>Start the safe walkthrough</button>
    </section>

    {step >= 1 && <section className="mt-8 grid gap-6 lg:grid-cols-2" data-demo="collection">
      <article className="card"><p className="font-semibold text-cyan-300">WAVE 1 · MESSAGE COLLECTION</p><h2 className="mt-2 text-2xl font-bold">Capture the signal, not the identity.</h2><p className="mt-3 text-sm text-slate-400">This is a synthetic demo message. It is never submitted or stored.</p><div className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-4"><p className="whitespace-pre-wrap text-sm leading-6 text-slate-200">{showRaw ? raw : redacted}</p></div><button className="btn mt-5" data-demo="redact" onClick={() => { setShowRaw(false); setStep(2); }}>Redact this message</button></article>
      <article className="card"><p className="font-semibold text-cyan-300">PRIVACY LAYER</p><h2 className="mt-2 text-2xl font-bold">Useful evidence survives.</h2><div className="mt-6 grid grid-cols-2 gap-3 text-sm"><div className="rounded-xl bg-slate-800 p-3"><b className="text-cyan-300">[PERSON]</b><br />Names become placeholders</div><div className="rounded-xl bg-slate-800 p-3"><b className="text-cyan-300">[LINK]</b><br />URLs are defanged</div><div className="rounded-xl bg-slate-800 p-3"><b className="text-cyan-300">[PHONE]</b><br />Contact data removed</div><div className="rounded-xl bg-slate-800 p-3"><b className="text-cyan-300">Metadata</b><br />Safety features retained</div></div><p className="mt-6 text-sm text-slate-400">The model receives sanitized text and safety-relevant structure—not raw emails, headers, or attachments.</p></article>
    </section>}

    {step >= 2 && <section className="mt-8 grid gap-6 lg:grid-cols-2" data-demo="labeling">
      <article className="card"><p className="font-semibold text-cyan-300">WAVE 2 · HUMAN LABELING</p><h2 className="mt-2 text-2xl font-bold">Independent people turn signals into judgment.</h2><div className="mt-5 rounded-xl border border-cyan-400/30 bg-slate-950 p-4"><p className="whitespace-pre-wrap text-sm leading-6">{redacted}</p></div><div className="mt-5 grid grid-cols-2 gap-3 text-sm"><div className="rounded-lg border border-slate-600 p-3"><span className="text-slate-400">Risk level</span><br /><b>High</b></div><div className="rounded-lg border border-slate-600 p-3"><span className="text-slate-400">Scam type</span><br /><b>Delivery phishing</b></div><div className="rounded-lg border border-slate-600 p-3"><span className="text-slate-400">Red flags</span><br /><b>Urgency · Link</b></div><div className="rounded-lg border border-slate-600 p-3"><span className="text-slate-400">Safe action</span><br /><b>Use official app</b></div></div><button className="btn mt-5" data-demo="save-label" onClick={() => { setLabelSaved(true); setStep(3); }}>{labelSaved ? "Label saved" : "Save human judgment"}</button></article>
      <article className="card"><p className="font-semibold text-cyan-300">QUALITY GATE</p><h2 className="mt-2 text-2xl font-bold">Consensus before training.</h2><ol className="mt-5 space-y-4 text-sm text-slate-300"><li><span className="mr-3 text-cyan-300">01</span>Two independent labels are required.</li><li><span className="mr-3 text-cyan-300">02</span>Low-agreement and unreadable records are surfaced, not hidden.</li><li><span className="mr-3 text-cyan-300">03</span>Only final consensus targets enter a versioned training snapshot.</li></ol></article>
    </section>}

    {step >= 3 && <section className="mt-8 grid gap-5 sm:grid-cols-3" data-demo="results">
      {[ ["50", "real sanitized messages"], ["78", "human labels saved"], ["100%", "valid JSON after pilot LoRA"] ].map(([value, label]) => <article className="card" key={label}><p className="text-4xl font-bold text-cyan-300">{value}</p><p className="mt-2 text-sm text-slate-300">{label}</p></article>)}
      <article className="card sm:col-span-3"><p className="font-semibold text-cyan-300">MODEL RESULT · SMALL-DATA PILOT</p><h2 className="mt-2 text-2xl font-bold">Measured improvement, presented honestly.</h2><div className="mt-5 grid gap-4 sm:grid-cols-3"><div className="rounded-xl bg-slate-800 p-4"><span className="text-sm text-slate-400">Valid JSON</span><p className="mt-2 text-xl font-bold">75% → <span className="text-cyan-300">100%</span></p></div><div className="rounded-xl bg-slate-800 p-4"><span className="text-sm text-slate-400">Risk exact match</span><p className="mt-2 text-xl font-bold">0% → <span className="text-cyan-300">25%</span></p></div><div className="rounded-xl bg-slate-800 p-4"><span className="text-sm text-slate-400">Scam type exact</span><p className="mt-2 text-xl font-bold">0% → <span className="text-cyan-300">25%</span></p></div></div><p className="mt-4 text-xs text-slate-400">Pilot result on a four-message frozen holdout. Trustfall reports the limitation instead of overstating accuracy.</p></article>
    </section>}
  </main>;
}
