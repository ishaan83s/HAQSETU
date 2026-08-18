import { useEffect, useState, type ReactNode } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Moon, Sun, ArrowRight } from "lucide-react"

export default function AppShell({ children, landing = false }: { children: ReactNode; landing?: boolean }) {
  const navigate = useNavigate()
  const [light, setLight] = useState(() => localStorage.getItem("haqsetu-theme") === "light")
  useEffect(() => { document.body.classList.toggle("light-theme", light); localStorage.setItem("haqsetu-theme", light ? "light" : "dark") }, [light])
  return <div className="haq-app">
    <div className="ambient ambient-one"/><div className="ambient ambient-two"/>
    <header className="haq-nav">
      <Link className="haq-brand" to="/"><span className="brand-mark">H</span><span>HAQSETU</span></Link>
      <nav className="haq-nav-links">{landing ? <><a href="#features">Features</a><a href="#how">How it works</a><a href="#security">Security</a></> : <><Link to="/incident">Assistant</Link><Link to="/incident">New query</Link></>}</nav>
      <div className="haq-nav-actions">
        <button className="theme-toggle" onClick={() => setLight(v => !v)} aria-label="Toggle theme">{light ? <Moon size={17}/> : <Sun size={17}/>}</button>
        <button className="nav-login" onClick={() => navigate(landing ? "/login" : "/incident")}>{landing ? "Log in" : "Start query"} <ArrowRight size={14}/></button>
      </div>
    </header>
    {children}
    {landing && <footer className="haq-footer"><span>© 2026 HAQSETU — Know Your Rights</span><span>General legal information, not legal advice.</span><span>Built for a safer digital India.</span></footer>}
  </div>
}
