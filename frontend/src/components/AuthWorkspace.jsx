import { useEffect, useState } from "react";
import { api, waitForBackend } from "@/lib/api";
import { AuthContext } from "@/lib/authContext";

const button = "rounded border px-4 py-2 text-sm font-semibold disabled:opacity-50";

export default function AuthWorkspace({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [choosing, setChoosing] = useState(false);
  const [profile, setProfile] = useState(false);
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [startupError, setStartupError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    waitForBackend(controller.signal).then(async () => {
      if (!controller.signal.aborted) {
        const access = await api.demoAccess();
        if (access.public_read_only) {
          setUser({ name: "Judge", mode: "ONLINE", provider: "Groq", hosted: true, readOnly: true });
        } else {
          try { setUser(await api.session()); } catch { /* no session yet */ }
        }
        setLoading(false);
      }
    }).catch(reason => { if (!controller.signal.aborted) { setStartupError(reason.message); setLoading(false); } });
    const expired = () => { setUser(null); setHealth(null); setProfile(false); };
    const unavailable = (event) => setHealth({ ready: false, message: event.detail });
    window.addEventListener("bidlens:unauthenticated", expired);
    window.addEventListener("bidlens:ai-unavailable", unavailable);
    return () => { controller.abort(); window.removeEventListener("bidlens:unauthenticated", expired); window.removeEventListener("bidlens:ai-unavailable", unavailable); };
  }, []);
  const retry = async () => {
    setBusy(true); setError("");
    try { const result = await api.aiHealth(); setHealth(result); return result.ready; }
    catch (reason) { setError(reason.message); return false; }
    finally { setBusy(false); }
  };
  const choose = async (mode) => {
    setBusy(true); setError(""); setHealth(null);
    try { setUser(await api.setMode(mode)); setChoosing(false); setProfile(false); const result = await api.aiHealth(); setHealth(result); }
    catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  };
  const logout = async () => {
    try { await api.logout(); setUser(null); setHealth(null); setProfile(false); setChoosing(false); }
    catch (reason) { setError(reason.message); }
  };
  if (loading) return <div role="status" className="p-8 text-gray-600"><h1 className="font-bold">Starting BidLens demo server…</h1><p>The free prototype server may take up to a minute to wake.</p></div>;
  if (startupError) return <div role="alert" className="p-8"><p>{startupError}</p><button className={button} onClick={() => window.location.reload()}>Retry connection</button></div>;
  if (!user) return <Login onLogin={(value) => { setUser(value); setChoosing(!value.mode); setError(""); }} />;
  const value = { user, openProfile: () => setProfile(true), changeMode: () => setChoosing(true) };
  if (user.readOnly) return <AuthContext.Provider value={value}><div className="public-judge"><style>{`.public-judge [data-demo-write], .public-judge form { display: none !important; }`}</style>{children}</div></AuthContext.Provider>;
  return <AuthContext.Provider value={value}>
    {choosing || !user.mode ? <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6"><div className="w-full max-w-2xl"><h1 className="text-2xl font-bold">Choose Processing Mode</h1><p className="mt-2 text-sm text-gray-600">Select where AI will process your documents.</p><div className="mt-6 grid gap-4 sm:grid-cols-2">{(user.hosted ? ["ONLINE"] : ["OFFLINE", "ONLINE"]).map(mode => <section key={mode} className="border bg-white p-5"><h2 className="font-bold">{mode} MODE {user.recommended_mode === mode && <span className="text-xs font-normal text-[#B3432E]">· Recommended</span>}</h2><p className="mt-3 text-sm font-semibold">{mode === "OFFLINE" ? "Ollama + Qwen 2.5 3B" : "Groq API"}</p><p className="mt-2 text-sm text-gray-600">{mode === "OFFLINE" ? "Best for local/private processing. Requires Ollama and the Qwen model on the backend machine." : "Best for hosted/deployed use. Requires network access and a configured server-side API key. Document excerpts are sent to Groq."}</p><button disabled={busy} onClick={() => choose(mode)} className={`${button} mt-5 bg-[#B3432E] text-white`}>Use {mode === "OFFLINE" ? "Offline" : "Online"} Mode</button></section>)}</div>{user.hosted && <p className="mt-3 text-sm text-gray-600">Offline mode is local-only. Hosted processing uses Groq with lightweight lexical retrieval.</p>}{error && <p role="alert" className="mt-3 text-red-700">{error}</p>}{user.mode && <button onClick={() => setChoosing(false)} className={`${button} mt-4`}>Back to workspace</button>}</div></div> : <>
      {(busy || health || error) && <div role="status" className={`flex flex-wrap items-center gap-3 border-b px-5 py-2 text-sm ${health?.ready ? "bg-white text-gray-600" : "bg-orange-50 text-gray-800"}`}><span>{busy ? "Checking AI availability…" : error || health?.message}</span>{!busy && health && !health.ready && <><button onClick={retry} className={button}>Retry</button>{!user.hosted && <button onClick={() => choose(user.mode === "OFFLINE" ? "ONLINE" : "OFFLINE")} className={button}>Switch to {user.mode === "OFFLINE" ? "Online" : "Offline"} Mode</button>}</>}</div>}
      {children}
    </>}
    {profile && <div role="dialog" aria-modal="true" aria-label="Profile" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><section className="w-full max-w-md border bg-white p-6"><div className="flex justify-between"><h2 className="text-xl font-bold">Profile</h2><button onClick={() => setProfile(false)} className={button}>Close</button></div><dl className="my-5 grid grid-cols-2 gap-3 text-sm">{Object.entries({ Name: user.name, Username: user.username, Role: user.role, Prototype: user.prototype, "Current Processing Mode": user.mode, "AI Provider": user.provider, Model: user.model }).map(([label, text]) => <div key={label} className="contents"><dt className="text-gray-500">{label}</dt><dd>{text}</dd></div>)}</dl><p className="mb-4 text-xs text-gray-500">Temporary prototype authentication</p><div className="flex gap-2"><button onClick={() => { setProfile(false); setChoosing(true); }} className={button}>Change Processing Mode</button><button onClick={logout} className={`${button} text-[#B3432E]`}>Logout</button></div></section></div>}
  </AuthContext.Provider>;
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setError("");
    try { onLogin(await api.login(username, password)); setPassword(""); }
    catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  };
  return <div className="flex min-h-screen items-center justify-center bg-gray-50 p-5"><form onSubmit={submit} className="w-full max-w-sm border bg-white p-7"><p className="font-bold tracking-widest text-[#B3432E]">BIDLENS</p><h1 className="mt-5 text-2xl font-bold">Sign in to BidLens</h1><p className="mt-2 text-sm text-gray-500">Procurement Compliance Workspace</p><label className="mt-6 block text-sm">Username<input autoComplete="username" required value={username} onChange={e => setUsername(e.target.value)} className="mt-1 w-full rounded border p-2" /></label><label className="mt-4 block text-sm">Password<input autoComplete="current-password" type="password" required value={password} onChange={e => setPassword(e.target.value)} className="mt-1 w-full rounded border p-2" /></label>{error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}<button disabled={busy} className={`${button} mt-5 w-full bg-[#B3432E] text-white`}>{busy ? "Signing in…" : "Sign In"}</button><p className="mt-4 text-xs text-gray-500">Temporary prototype access</p></form></div>;
}
