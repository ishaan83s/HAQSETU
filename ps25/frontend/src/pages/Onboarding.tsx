import { useNavigate } from "react-router-dom"
import { ArrowRight, Check, LockKeyhole, Scale, ShieldCheck, Sparkles } from "lucide-react"
import AppShell from "@/components/AppShell"

export default function Onboarding() {
 const navigate=useNavigate()
 return <AppShell landing><main>
  <section className="landing-hero">
   <div className="hero-copy">
    <div className="eyebrow"><span className="pulse"/> AI-powered legal awareness</div>
    <h1>Know your rights.<br/><span>Act with confidence.</span></h1>
    <p className="hero-text">Tell HAQSETU what happened in your own words. Get simple, practical legal-awareness guidance, evidence tips, next steps, and verified official resources.</p>
    <div className="hero-actions"><button className="primary-btn" onClick={()=>navigate("/login")}>Get started <ArrowRight size={17}/></button><a className="secondary-btn" href="#how">See how it works</a></div>
    <div className="trust-row"><span><Check size={14}/> Privacy-first</span><span><Check size={14}/> Explainable guidance</span><span><Check size={14}/> India-focused</span></div>
   </div>
   <div className="hero-visual"><div className="grid-glow"/>
    <div className="assistant-card"><div className="assistant-head"><div className="assistant-avatar">H</div><div><strong>HAQSETU Assistant</strong><small>Legal awareness <span className="online-dot"/></small></div><ShieldCheck className="shield-icon" size={20}/></div>
     <div className="chat-preview"><div className="preview-bubble user">My employer has not paid my salary.</div><div className="preview-bubble bot"><span className="mini-k">H</span>I’ll help you understand the situation, what records to keep, and which official resources may be relevant.</div><div className="legal-note"><Scale size={18}/><div><b>Legal awareness</b><small>Clear guidance with verified sources.</small></div></div></div>
     <div className="chat-input-preview"><span>Describe your situation...</span><span className="send-preview">↑</span></div>
    </div>
    <div className="floating-card privacy-card"><span className="float-icon"><LockKeyhole size={15}/></span><div><b>Privacy protected</b><small>Purpose-based guidance</small></div></div>
    <div className="floating-card verified-card"><span className="check-icon"><Check size={15}/></span><div><b>Official resources</b><small>Verified portals & helplines</small></div></div>
   </div>
  </section>
  <section className="stats"><div><strong>01</strong><span>Describe what happened</span></div><div><strong>02</strong><span>Understand your options</span></div><div><strong>03</strong><span>Take safer next steps</span></div></section>
  <section className="landing-section" id="features"><div className="section-label">BUILT FOR REAL PEOPLE</div><h2>Everything you need to navigate a legal situation.</h2><p className="section-sub">One calm, simple interface for legal awareness, evidence preservation and trusted resources.</p>
   <div className="feature-grid">
    <article><Sparkles/><h3>AI Legal Awareness Assistant</h3><p>Explain what happened in plain language and get structured guidance without legal jargon.</p></article>
    <article><Scale/><h3>Simple Legal Explainer</h3><p>Understand potential issues, rights and responsibilities in a way that is easier to act on.</p></article>
    <article><ShieldCheck/><h3>Evidence & Safety</h3><p>Know which records to preserve and what practical steps can reduce further risk.</p></article>
    <article><LockKeyhole/><h3>Verified Resources</h3><p>Find official authorities, legal-aid contacts and relevant portals alongside your guidance.</p></article>
   </div>
  </section>
  <section className="how-section" id="how"><div><div className="section-label">HOW IT WORKS</div><h2>From confusion to confidence.</h2><p className="section-sub">A focused three-step experience designed to keep the user in control.</p></div>
   <div className="steps"><div className="step"><span>01</span><div><h3>Tell us</h3><p>Describe the incident in your own words or use voice input.</p></div></div><div className="step"><span>02</span><div><h3>Understand</h3><p>Receive a clear summary, possible legal considerations and urgency guidance.</p></div></div><div className="step"><span>03</span><div><h3>Act safely</h3><p>Preserve evidence, follow practical next steps and use official resources.</p></div></div></div>
  </section>
  <section className="security-section" id="security"><div className="security-box"><div className="security-icon"><ShieldCheck size={23}/></div><div><div className="section-label">PRIVACY BY DESIGN</div><h2>Your situation. Your decision.</h2><p>HAQSETU is designed to give people understandable information while keeping the experience focused on consent, safety and trustworthy sources.</p></div><div className="security-pills"><span>Clarity</span><span>Safety</span><span>Auditability</span></div></div></section>
 </main></AppShell>
}
