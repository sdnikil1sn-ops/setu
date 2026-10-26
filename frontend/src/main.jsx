import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createClient } from '@supabase/supabase-js';
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowRight, Bell, Building2, CheckCircle2,
  ChevronDown, ChevronLeft, ChevronRight, CircleHelp, Clock3, Command, Download,
  FileSearch, Fingerprint, Gauge, Globe2, Landmark, LayoutDashboard, LockKeyhole,
  Menu, Network, RefreshCw, Search, ShieldCheck, SlidersHorizontal, Sparkles,
  X, Zap
} from 'lucide-react';
import './styles.css';

const apiBase = (import.meta.env.VITE_SETU_API_URL || '').replace(/\/$/, '');
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';
const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } })
  : null;
const fmt = (n) => Number.isFinite(Number(n)) ? Number(n).toLocaleString('en-IN') : '—';
const pretty = (v) => String(v ?? '—').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
const errorMessage = (e) => e?.message || 'The request could not be completed.';
const adjustFont = (delta) => {
  const current = Number(document.documentElement.dataset.fontScale || 100);
  const next = Math.max(85, Math.min(125, current + delta * 10));
  document.documentElement.dataset.fontScale = String(next);
  document.documentElement.style.setProperty('--font-scale', String(next / 100));
  try { localStorage.setItem('setu-font-scale', String(next)); } catch {}
};
const toggleDarkMode = () => {
  const next = !document.documentElement.classList.contains('dark-mode');
  document.documentElement.classList.toggle('dark-mode', next);
  try { localStorage.setItem('setu-dark-mode', next ? 'on' : 'off'); } catch {}
};

function App() {
  const [active, setActive] = useState('overview');
  const [mobileNav, setMobileNav] = useState(false);
  const [token, setToken] = useState('');
  const [sessionEmail, setSessionEmail] = useState('');
  const [sessionReady, setSessionReady] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [health, setHealth] = useState({state:'checking', data:null, error:''});
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState({items:[], total:0, error:'', loading:false});
  const [institutions, setInstitutions] = useState({items:[], total:0, error:'', loading:false});
  const [overlaps, setOverlaps] = useState({items:[], error:'', loading:false});
  const [caseQuery, setCaseQuery] = useState('');
  const [institutionQuery, setInstitutionQuery] = useState('');
  const [caseStatus, setCaseStatus] = useState('');
  const [bureau, setBureau] = useState('');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseError, setCaseError] = useState('');
  const [resolveName, setResolveName] = useState('');
  const [resolveId, setResolveId] = useState('');
  const [resolution, setResolution] = useState(null);
  const [resolveBusy, setResolveBusy] = useState(false);
  const [resolveError, setResolveError] = useState('');
  const [semanticA, setSemanticA] = useState('');
  const [semanticB, setSemanticB] = useState('');
  const [semanticResult, setSemanticResult] = useState(null);
  const [semanticError, setSemanticError] = useState('');
  const [semanticBusy, setSemanticBusy] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let alive = true;
    if (!supabase) { setSessionReady(true); return () => { alive = false; }; }
    supabase.auth.getSession().then(({ data, error }) => {
      if (!alive) return;
      if (error) setLoginError(error.message);
      const session = data?.session;
      setToken(session?.access_token || '');
      setSessionEmail(session?.user?.email || '');
      setSessionReady(true);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!alive) return;
      setToken(session?.access_token || '');
      setSessionEmail(session?.user?.email || '');
      setSessionReady(true);
      if (!session) {
        setSummary(null);
        setCases({items:[],total:0,error:'',loading:false});
        setInstitutions({items:[],total:0,error:'',loading:false});
        setOverlaps({items:[],error:'',loading:false});
      }
    });
    return () => { alive = false; listener?.subscription?.unsubscribe(); };
  }, []);

  const signIn = async (e) => {
    e.preventDefault();
    setLoginError('');
    if (!supabase) {
      setLoginError('Supabase Auth is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to .env.local.');
      return;
    }
    setLoginBusy(true);
    try {
      const { error } = await supabase.auth.signInWithPassword({ email: loginEmail.trim(), password: loginPassword });
      if (error) throw error;
      setLoginPassword('');
    } catch (e) {
      setLoginError(e?.message || 'Sign-in failed. Check your credentials and try again.');
    } finally {
      setLoginBusy(false);
    }
  };
  const signOut = async () => {
    if (supabase) await supabase.auth.signOut();
    setToken('');
    setSessionEmail('');
    setNotice('Signed out. Protected SETU data is no longer available.');
  };

  const request = useCallback(async (path, options={}) => {
    const headers = {'Accept':'application/json', ...(options.headers || {})};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (options.body) headers['Content-Type'] = 'application/json';
    const response = await fetch(`${apiBase}${path}`, {...options, headers});
    const bodyText = await response.text();
    let data = null;
    try { data = bodyText ? JSON.parse(bodyText) : null; } catch { data = bodyText; }
    if (!response.ok) {
      const detail = typeof data === 'object' && data ? data.detail : '';
      const message = Array.isArray(detail) ? detail.map(x=>x.msg).join('; ') : detail;
      throw new Error(message || `API returned HTTP ${response.status}`);
    }
    return data;
  }, [token]);

  const loadHealth = useCallback(async () => {
    setHealth({state:'checking',data:null,error:''});
    try {
      const data = await request('/health');
      setHealth({state: data?.status === 'healthy' ? 'healthy' : 'warning', data, error:''});
    } catch(e) { setHealth({state:'offline',data:null,error:errorMessage(e)}); }
  }, [request]);

  const loadSummary = useCallback(async () => {
    try { const d = await request('/api/v1/summary'); setSummary(d?.actual_counts || d); }
    catch { setSummary(null); }
  }, [request]);

  const loadCases = useCallback(async () => {
    setCases(s=>({...s,loading:true,error:''}));
    const params = new URLSearchParams({limit:'100',offset:'0'});
    if (caseStatus) params.set('status',caseStatus);
    if (bureau) params.set('bureau_id',bureau);
    try {
      const d = await request(`/api/v1/cases?${params}`);
      setCases({items:Array.isArray(d?.items)?d.items:[],total:Number(d?.total||0),error:'',loading:false});
    } catch(e) { setCases({items:[],total:0,error:errorMessage(e),loading:false}); }
  }, [request, caseStatus, bureau]);

  const loadInstitutions = useCallback(async () => {
    setInstitutions(s=>({...s,loading:true,error:''}));
    const params = new URLSearchParams({limit:'100',offset:'0'});
    if (institutionQuery.trim()) params.set('search',institutionQuery.trim());
    try {
      const d = await request(`/api/v1/institutions?${params}`);
      setInstitutions({items:Array.isArray(d?.items)?d.items:[],total:Number(d?.total||0),error:'',loading:false});
    } catch(e) { setInstitutions({items:[],total:0,error:errorMessage(e),loading:false}); }
  }, [request, institutionQuery]);

  const loadOverlaps = useCallback(async () => {
    setOverlaps(s=>({...s,loading:true,error:''}));
    try {
      const d = await request('/api/v1/overlaps/candidates?limit=50&minimum_score=50');
      const items = Array.isArray(d) ? d : (d?.items || d?.candidates || []);
      setOverlaps({items:Array.isArray(items)?items:[],error:'',loading:false});
    } catch(e) { setOverlaps({items:[],error:errorMessage(e),loading:false}); }
  }, [request]);

  const refresh = useCallback(async () => {
    await loadHealth();
    await Promise.all([loadSummary(),loadCases(),loadInstitutions(),loadOverlaps()]);
  }, [loadHealth,loadSummary,loadCases,loadInstitutions,loadOverlaps]);

  useEffect(()=>{ if (token) refresh(); },[refresh, token]);
  useEffect(()=>{ if(notice){ const t=setTimeout(()=>setNotice(''),4200); return ()=>clearTimeout(t); } },[notice]);

  const visibleCases = useMemo(() => cases.items.filter(c => {
    const q=caseQuery.trim().toLowerCase();
    return !q || [c.case_id,c.case_ref,c.institution_name_raw,c.category,c.text,c.current_bureau_id,c.status].some(v=>String(v??'').toLowerCase().includes(q));
  }),[cases.items,caseQuery]);
  const visibleInstitutions = institutions.items.filter(i => {
    const q=institutionQuery.trim().toLowerCase();
    return !q || [i.name,i.permanent_id,i.state,i.district].some(v=>String(v??'').toLowerCase().includes(q));
  });
  const counts = summary || {};
  const pendingCount = cases.items.filter(c=>/pending|open|progress|await/i.test(String(c.status||''))).length;
  const restrictedCount = cases.items.filter(c=>c.is_restricted).length;
  const nav = [
    {id:'overview',label:'Executive Dashboard',icon:LayoutDashboard},
    {id:'map',label:'Visual Dependency Map',icon:Network,tag:'PRIMARY'},
    {id:'institutions',label:'Institution Registry',icon:Building2},
    {id:'cases',label:'Grievance Repository',icon:FileSearch},
    {id:'resolution',label:'Identity Resolution',icon:Fingerprint},
    {id:'coordination',label:'Cross-Bureau Intelligence',icon:Globe2},
    {id:'analytics',label:'Analytical Reports',icon:Gauge}
  ];

  const openCase = async (id) => {
    if(!id) return;
    setSelectedCase(null); setCaseError('');
    try { setSelectedCase(await request(`/api/v1/cases/${encodeURIComponent(id)}`)); }
    catch(e) { setCaseError(errorMessage(e)); }
  };
  const resolveInstitution = async (e) => {
    e.preventDefault(); setResolveBusy(true); setResolution(null); setResolveError('');
    try { setResolution(await request('/api/v1/institutions/resolve',{method:'POST',body:JSON.stringify({raw_name:resolveName||null,raw_permanent_id:resolveId||null})})); }
    catch(e) { setResolveError(errorMessage(e)); }
    finally { setResolveBusy(false); }
  };
  const semanticCheck = async (e) => {
    e.preventDefault(); setSemanticBusy(true); setSemanticResult(null); setSemanticError('');
    try { setSemanticResult(await request('/api/v1/overlaps/semantic-check',{method:'POST',body:JSON.stringify({text_a:semanticA,text_b:semanticB})})); }
    catch(e) { setSemanticError(errorMessage(e)); }
    finally { setSemanticBusy(false); }
  };
  const exportCases = () => {
    const rows=visibleCases;
    if(!rows.length){setNotice('There are no accessible case rows to export.');return;}
    const cols=['case_id','case_ref','institution_name_raw','category','status','current_bureau_id','received_date','expected_disposal_date','sla_state','region_id'];
    const esc=v=>`"${String(v??'').replaceAll('"','""')}"`;
    const csv=[cols.join(','),...rows.map(r=>cols.map(c=>esc(r[c])).join(','))].join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));
    const a=document.createElement('a');a.href=url;a.download='setu-accessible-cases.csv';a.click();URL.revokeObjectURL(url);
  };
  const navTo = id => {setActive(id);setMobileNav(false);};

  if (!sessionReady) return <div className="auth-screen"><div className="auth-card"><div className="auth-emblem"><Landmark size={30}/></div><span className="auth-kicker">SETU · SECURE WORKSPACE</span><h1>Checking your session</h1><p>Verifying your staff sign-in before loading protected records.</p><div className="loading"><span className="spinner"/>Checking authentication…</div></div></div>;

  if (!token) return <div className="auth-screen"><div className="auth-card"><div className="auth-emblem"><Landmark size={30}/></div><span className="auth-kicker">GOVERNMENT INTELLIGENCE CONSOLE</span><h1>Sign in to SETU</h1><p>Only authenticated users can open the SETU workspace. Your account must also have a linked, approved SETU staff profile.</p>
    {!supabase && <div className="error-box"><AlertTriangle size={17}/><div><b>Authentication is not configured</b><p>Add your Supabase project URL and public publishable/anon key to <code>.env.local</code>, then restart the frontend. Do not use a service-role key.</p></div></div>}
    <form className="auth-form" onSubmit={signIn}><label>Email address<input type="email" value={loginEmail} onChange={e=>setLoginEmail(e.target.value)} autoComplete="username" required placeholder="staff@example.gov.in"/></label><label>Password<input type="password" value={loginPassword} onChange={e=>setLoginPassword(e.target.value)} autoComplete="current-password" required placeholder="Your account password"/></label>{loginError&&<div className="auth-error" role="alert">{loginError}</div>}<button className="btn btn-primary auth-submit" disabled={loginBusy||!supabase}>{loginBusy?<RefreshCw className="spin" size={16}/>:<LockKeyhole size={16}/>} {loginBusy?'Signing in…':'Sign in securely'}</button></form>
    <div className="auth-security"><ShieldCheck size={15}/> No protected API requests are made until a Supabase session is established.</div>
  </div><div className="auth-footer">SETU · Role-scoped access · Authorized staff only</div></div>;

  return <div className="app-shell">
    <div className="gov-strip"><div className="gov-left"><span className="mini-emblem">✦</span><b>भारत सरकार | GOVERNMENT OF INDIA</b><i/> <span>शिक्षा मंत्रालय | MINISTRY OF EDUCATION</span></div><div className="gov-right"><span className={`health-dot ${health.state}`}/>{health.state==='healthy'?'SYSTEM OPERATIONAL':health.state==='checking'?'CHECKING SERVICES':health.state==='warning'?'DATABASE STATUS WARNING':'API UNAVAILABLE'}<span className="strip-divider"/> <button className="text-size" title="Increase text size" aria-label="Increase text size" onClick={()=>adjustFont(1)}>A+</button><button className="text-size" title="Decrease text size" aria-label="Decrease text size" onClick={()=>adjustFont(-1)}>A−</button><button className="contrast-toggle" onClick={toggleDarkMode} aria-label="Toggle dark mode">{document.documentElement.classList.contains('dark-mode')?'Light mode':'Dark mode'}</button></div></div>
    <header className="masthead">
      <div className="brand">
        <div className="seal"><Landmark size={27}/><span/></div>
        <div><div className="brand-overline">INSTITUTION COMPLAINT INTELLIGENCE</div><h1>SETU <span>Government Intelligence Console</span></h1><p>Connecting evidence. Clarifying jurisdiction. Supporting accountable action.</p></div>
      </div>
      <div className="mast-actions">
        <div className={`service-pill ${health.state}`}><Activity size={15}/><span>{health.state==='healthy'?'API Connected':health.state==='checking'?'Checking API':health.state==='warning'?'Database Warning':'API Offline'}</span></div>
        <button className="outline-light" onClick={signOut}><LockKeyhole size={15}/>{sessionEmail || 'Staff session'} · Sign out</button>
        <button className="alert-button" onClick={()=>navTo('analytics')}><Bell size={16}/><span>Alerts</span><b>{health.state==='healthy'&&cases.error===''?pendingCount:'—'}</b></button>
      </div>
    </header>
    <div className="nav-wrap">
      <button className="mobile-menu" onClick={()=>setMobileNav(v=>!v)}><Menu size={18}/> Modules</button>
      <nav className={mobileNav?'main-nav open':'main-nav'} aria-label="Main navigation">
        {nav.map(n=>{const Icon=n.icon;return <button key={n.id} className={`nav-item ${active===n.id?'active':''}`} onClick={()=>navTo(n.id)}><Icon size={16}/><span>{n.label}</span>{n.tag&&<small>{n.tag}</small>}</button>})}
      </nav>
    </div>

    <main className="workspace">
      <div className="page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line"/> NATIONAL INSTITUTIONAL OVERSIGHT <span className="muted-dot">/</span> SETU PORTAL</div><h2>{nav.find(n=>n.id===active)?.label || 'Executive Dashboard'}</h2><p>{active==='overview'?'A clear operational picture of accessible cases, institutions, and service health.':'Evidence-led tools for institution and complaint intelligence.'}</p></div>
        <div className="heading-actions"><span className="live-time"><span className="live-dot"/> LIVE DATA WHEN AUTHORIZED</span><button className="btn btn-outline" onClick={refresh}><RefreshCw size={15}/> Refresh</button><button className="btn btn-primary" onClick={signOut}><ShieldCheck size={15}/> Sign out</button></div>
      </div>

      {health.state==='offline'&&<div className="alert-banner danger"><div className="alert-icon"><AlertTriangle size={20}/></div><div><strong>API connection unavailable</strong><p>{health.error || 'Unable to reach the FastAPI service.'} Check the backend port configured in .env.local and confirm FastAPI is running.</p></div><button className="banner-link" onClick={loadHealth}>Retry connection <ArrowRight size={14}/></button></div>}
      {health.state==='warning'&&<div className="alert-banner warning"><div className="alert-icon"><AlertTriangle size={20}/></div><div><strong>Backend responds, but database health is not confirmed</strong><p>{health.data?.database || 'Review the health response before relying on live data.'}</p></div><button className="banner-link" onClick={loadHealth}>Check again <ArrowRight size={14}/></button></div>}
      {health.state==='healthy'&&(!token)&&<div className="alert-banner info"><div className="alert-icon"><ShieldCheck size={20}/></div><div><strong>API is reachable — staff authentication is not configured in this tab</strong><p>Public health is working. Protected case and management endpoints need a valid Supabase access token and an approved SETU profile.</p></div><button className="banner-link" onClick={()=>navTo('overview')}>Configure access <ArrowRight size={14}/></button></div>}

      {active==='overview'&&<Overview counts={counts} cases={cases} institutions={institutions} overlaps={overlaps} health={health} pendingCount={pendingCount} onNav={navTo} onOpenCase={openCase} />}
      {active==='cases'&&<section className="panel"><PanelHead icon={FileSearch} title="Grievance repository" subtitle="Search and inspect cases visible to your authorized role." action={<button className="btn btn-outline" onClick={exportCases}><Download size={15}/> Export CSV</button>}/><div className="filters"><div className="searchbox"><Search size={16}/><input placeholder="Search case, institution, category…" value={caseQuery} onChange={e=>setCaseQuery(e.target.value)}/></div><select value={caseStatus} onChange={e=>setCaseStatus(e.target.value)}><option value="">All statuses</option>{['Pending','Under Process','Disposed','Resolved','Escalated','Transferred'].map(x=><option key={x}>{x}</option>)}</select><input className="filter-input" placeholder="Bureau ID" value={bureau} onChange={e=>setBureau(e.target.value)}/><button className="btn btn-primary" onClick={loadCases}><SlidersHorizontal size={15}/> Apply filters</button></div><CasesTable rows={visibleCases} loading={cases.loading} error={cases.error} onOpen={openCase}/><div className="table-foot">Showing {visibleCases.length} of {fmt(cases.total)} accessible records. Row visibility is controlled by the backend.</div></section>}
      {active==='institutions'&&<section className="panel"><PanelHead icon={Building2} title="Institution master registry" subtitle="Search by institution name, permanent ID, state, or district."/><div className="filters"><div className="searchbox wide"><Search size={16}/><input placeholder="Institution name or permanent ID" value={institutionQuery} onChange={e=>setInstitutionQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&loadInstitutions()}/></div><button className="btn btn-primary" onClick={loadInstitutions}><Search size={15}/> Search institutions</button></div><InstitutionsTable rows={visibleInstitutions} loading={institutions.loading} error={institutions.error}/><div className="table-foot">Showing {visibleInstitutions.length} of {fmt(institutions.total)} returned records.</div></section>}
      {active==='resolution'&&<div className="two-col"><section className="panel"><PanelHead icon={Fingerprint} title="Institution identity resolution" subtitle="Propose a match from the backend's read-only resolver."/><form className="form-stack" onSubmit={resolveInstitution}><label>Raw institution name<input value={resolveName} onChange={e=>setResolveName(e.target.value)} maxLength={300} placeholder="Enter name as received in a complaint"/></label><div className="field-or"><span/> OR <span/></div><label>AICTE / permanent institution ID<input value={resolveId} onChange={e=>setResolveId(e.target.value)} maxLength={100} placeholder="Enter permanent ID if available"/></label><div className="notice-box"><ShieldCheck size={17}/><span>This tool proposes a match only. It does not edit master institution records.</span></div><button className="btn btn-primary" disabled={resolveBusy||(!resolveName.trim()&&!resolveId.trim())}>{resolveBusy?<RefreshCw className="spin" size={16}/>:<Sparkles size={16}/>} {resolveBusy?'Resolving…':'Resolve institution'}</button></form>{resolveError&&<ErrorBox message={resolveError}/>}</section><section className="panel result-panel"><PanelHead icon={CheckCircle2} title="Resolution result" subtitle="Candidate evidence and confidence from the API."/>{resolution?<><div className="result-status"><span className={`status-chip ${resolution.review_required?'amber':'green'}`}>{pretty(resolution.resolution_status)}</span><strong>{resolution.resolution_confidence==null?'—':`${Math.round(Number(resolution.resolution_confidence)*100)}%`}</strong><small>reported confidence</small></div><p className="result-reason">{resolution.reason||'No explanation returned by the resolver.'}</p>{resolution.institution&&<div className="resolved-card"><b>{resolution.institution.name}</b><span>{resolution.institution.permanent_id||'No permanent ID returned'}</span><small>{[resolution.institution.district,resolution.institution.state].filter(Boolean).join(', ')}</small></div>}<h4>Candidate matches</h4>{(resolution.candidates||[]).length?<div className="candidate-list">{resolution.candidates.map((c,i)=><div className="candidate" key={c.institution_id||i}><div><b>{c.name}</b><small>{c.permanent_id||c.institution_id}</small></div><span>{c.score==null?'—':`${Math.round(Number(c.score))}%`}</span></div>)}</div>:<Empty text="No candidates were returned."/>}<p className="footnote">Human verification remains required where flagged by the backend.</p></>:<Empty text="Submit an institution name or ID to view a result."/ >}</section></div>}
      {active==='coordination'&&<section className="panel"><PanelHead icon={Globe2} title="Cross-bureau intelligence" subtitle="Potential overlap candidates for authorized management roles." action={<button className="btn btn-outline" onClick={loadOverlaps}><RefreshCw size={15}/> Refresh candidates</button>}/><div className="method-banner"><Zap size={17}/><div><b>Decision support, not automatic merging</b><p>Review candidates and the evidence behind each possible overlap. This backend exposes candidate retrieval, not a merge or approval action.</p></div></div>{overlaps.error?<ErrorBox message={overlaps.error}/>:overlaps.loading?<Loading/>:overlaps.items.length?<div className="overlap-list">{overlaps.items.map((r,i)=><OverlapCard key={r.id||`${r.case_a||i}`} row={r}/>)}</div>:<Empty text="No accessible overlap candidates returned. This can mean no matches, or that the current account is not authorized."/>}</section>}
      {active==='map'&&<DependencyView cases={cases} institutions={institutions} onOpenCase={openCase} onNav={navTo}/>}
      {active==='analytics'&&<Analytics counts={counts} cases={cases} institutions={institutions} overlaps={overlaps} health={health} onSemantic={()=>{}} semanticA={semanticA} semanticB={semanticB} setSemanticA={setSemanticA} setSemanticB={setSemanticB} semanticCheck={semanticCheck} semanticBusy={semanticBusy} semanticResult={semanticResult} semanticError={semanticError}/>}
    </main>
    <footer className="footer"><div className="footer-brand"><div className="footer-seal"><Landmark size={18}/></div><div><b>SETU | Government Intelligence Console</b><span>Institution complaint intelligence · Evidence-led decision support</span></div></div><div className="footer-links"><span>Security first</span><span>Role-scoped access</span><span>Human review</span><a href={`${apiBase}/docs`} target="_blank" rel="noreferrer">API documentation ↗</a></div><div className="footer-bottom">This interface is an operational aid. Decisions remain with authorized officials. Do not treat unavailable data as zero.</div></footer>
    {notice&&<div className="toast"><CheckCircle2 size={17}/>{notice}<button onClick={()=>setNotice('')}><X size={14}/></button></div>}

    {selectedCase&&<Modal title="Case intelligence dossier" onClose={()=>setSelectedCase(null)} wide><div className="case-dossier"><div className="dossier-top"><span className="status-chip blue">{pretty(selectedCase.status)}</span><span className="case-id">{selectedCase.case_id}</span></div><h3>{selectedCase.institution_name_raw||'Institution not specified'}</h3><p>{selectedCase.text||'No complaint summary was returned.'}</p><div className="detail-grid">{Object.entries(selectedCase).filter(([k,v])=>v!==null&&v!==''&&!['text'].includes(k)).slice(0,24).map(([k,v])=><div key={k}><small>{pretty(k)}</small><b>{typeof v==='boolean'?(v?'Yes':'No'):String(v)}</b></div>)}</div></div></Modal>}
    {caseError&&<Modal title="Case details unavailable" onClose={()=>setCaseError('')}><ErrorBox message={caseError}/><p className="footnote">The backend may restrict this record for your role or the supplied ID may not exist.</p></Modal>}
  </div>;
}

function PanelHead({icon:Icon,title,subtitle,action}){return <div className="panel-head"><div className="panel-title-icon"><Icon size={18}/></div><div className="panel-title"><h3>{title}</h3><p>{subtitle}</p></div>{action&&<div className="panel-action">{action}</div>}</div>}
function StatCard({label,value,sub,icon:Icon,tone='navy',loading=false}){return <div className={`stat-card tone-${tone}`}><div className="stat-top"><span>{label}</span><div className="stat-icon"><Icon size={17}/></div></div><strong>{loading?'…':value}</strong><div className="stat-sub">{sub}</div><div className="stat-rule"/></div>}
function Overview({counts,cases,institutions,overlaps,health,pendingCount,onNav,onOpenCase}){
 const caseRows=cases.items.slice(0,6);
 const summaryAvailable=Object.keys(counts||{}).length>0;
 return <><div className="section-label"><span>OPERATIONAL SNAPSHOT</span><span className="section-note"><span className="live-dot"/> Values reflect accessible API responses</span></div>
 <div className="stats-grid">
 <StatCard label="INSTITUTIONS RETURNED" value={fmt(institutions.total)} sub={institutions.error?'Access unavailable':'Registry query results'} icon={Building2} tone="blue" loading={institutions.loading}/>
 <StatCard label="ACCESSIBLE CASES" value={cases.error?'—':fmt(cases.total)} sub={cases.error?'Staff access required':'Visible to this staff role'} icon={FileSearch} tone="orange" loading={cases.loading}/>
 <StatCard label="OPEN / ACTIVE" value={cases.error?'—':fmt(pendingCount)} sub="Based on returned status labels" icon={Clock3} tone="purple" loading={cases.loading}/>
 <StatCard label="OVERLAP CANDIDATES" value={overlaps.error?'—':fmt(overlaps.items.length)} sub={overlaps.error?'Management access may be required':'Candidate pairs returned'} icon={Network} tone="red" loading={overlaps.loading}/>
 </div>
 <div className="feature-banner"><div className="feature-symbol"><Network size={25}/><span/></div><div className="feature-copy"><div className="feature-kicker">SETU INTELLIGENCE WORKSPACE <span>CORE MODULE</span></div><h3>Connect cases, institutions and jurisdictional signals.</h3><p>Move from an institution lookup to case context, identity resolution and cross-bureau candidate review without losing the evidence trail.</p><div className="feature-chips"><span><CheckCircle2 size={13}/> Role-scoped data</span><span><CheckCircle2 size={13}/> Explainable review</span><span><CheckCircle2 size={13}/> Human decision</span></div></div><button className="feature-cta" onClick={()=>onNav('map')}>Open intelligence map <ArrowRight size={16}/></button></div>
 <div className="dashboard-grid">
 <section className="panel table-panel"><PanelHead icon={FileSearch} title="Recent accessible cases" subtitle="Latest records returned by the API." action={<button className="inline-link" onClick={()=>onNav('cases')}>Open repository <ArrowRight size={14}/></button>}/>{cases.error?<ErrorBox message={cases.error}/>:cases.loading?<Loading/>:<CasesTable rows={caseRows} loading={false} onOpen={onOpenCase} compact/>}</section>
 <section className="panel table-panel"><PanelHead icon={Building2} title="Institution registry" subtitle="Searchable master data for identity checks." action={<button className="inline-link" onClick={()=>onNav('institutions')}>Browse registry <ArrowRight size={14}/></button>}/>{institutions.error?<ErrorBox message={institutions.error}/>:institutions.loading?<Loading/>:<InstitutionsTable rows={institutions.items.slice(0,6)} loading={false} compact/>}</section>
 <section className="panel signal-panel"><PanelHead icon={Activity} title="Service & access status" subtitle="Live checks, not decorative status indicators."/><div className="service-list"><ServiceRow label="FastAPI health" value={health.state==='healthy'?'Connected':health.state==='checking'?'Checking':health.state==='warning'?'Warning':'Unavailable'} state={health.state}/><ServiceRow label="Case repository" value={cases.error?'Access denied / unavailable':`${fmt(cases.total)} accessible`} state={cases.error?'warning':'healthy'}/><ServiceRow label="Institution registry" value={institutions.error?'Unavailable':`${fmt(institutions.total)} returned`} state={institutions.error?'warning':'healthy'}/><ServiceRow label="Overlap intelligence" value={overlaps.error?'Restricted / unavailable':`${fmt(overlaps.items.length)} candidates`} state={overlaps.error?'warning':'healthy'}/></div><div className="subtle-note"><ShieldCheck size={15}/> Access is enforced by the backend, not by hiding frontend controls.</div></section>
 <section className="panel signal-panel"><PanelHead icon={Sparkles} title="Recommended workflow" subtitle="A practical path for a reviewer."/><div className="workflow"><WorkflowStep n="01" title="Find institution" desc="Search by name or permanent ID." onClick={()=>onNav('institutions')}/><WorkflowStep n="02" title="Resolve identity" desc="Inspect candidates and match evidence." onClick={()=>onNav('resolution')}/><WorkflowStep n="03" title="Review case context" desc="Open only records your role can access." onClick={()=>onNav('cases')}/><WorkflowStep n="04" title="Assess possible overlap" desc="Use candidate scores as a prompt for human review." onClick={()=>onNav('coordination')}/></div></section>
 </div></>;
}
function ServiceRow({label,value,state}){return <div className="service-row"><span className={`service-indicator ${state}`}/><span>{label}</span><b>{value}</b></div>}
function WorkflowStep({n,title,desc,onClick}){return <button className="workflow-step" onClick={onClick}><span className="step-num">{n}</span><span className="step-content"><b>{title}</b><small>{desc}</small></span><ChevronRight size={16}/></button>}
function CasesTable({rows,loading,error,onOpen,compact=false}){
 if(error)return <ErrorBox message={error}/>; if(loading)return <Loading/>; if(!rows?.length)return <Empty text="No case rows are available for this query or role." />;
 return <div className="table-scroll"><table className="data-table"><thead><tr><th>CASE ID</th><th>INSTITUTION / SUMMARY</th><th>CATEGORY</th><th>BUREAU</th><th>STATUS</th>{!compact&&<th>NEXT ACTION</th>}</tr></thead><tbody>{rows.map((r,i)=><tr key={r.case_id||i}><td><button className="table-id" onClick={()=>onOpen?.(r.case_id)}>{r.case_ref||r.case_id||'Open case'}</button><small className="cell-sub">{r.received_date||'Date not supplied'}</small></td><td><b className="cell-main">{r.institution_name_raw||r.institution_id||'Institution not supplied'}</b><small className="cell-sub clamp">{r.text||'No summary supplied'}</small></td><td>{r.category||'—'}</td><td><span className="bureau-pill">{r.current_bureau_id||'Unassigned'}</span></td><td><Status value={r.status}/></td>{!compact&&<td><button className="row-action" onClick={()=>onOpen?.(r.case_id)}>Inspect <ArrowRight size={13}/></button></td>}</tr>)}</tbody></table></div>;
}
function InstitutionsTable({rows,loading,error,compact=false}){
 if(error)return <ErrorBox message={error}/>; if(loading)return <Loading/>; if(!rows?.length)return <Empty text="No institution records returned. Search or check API access." />;
 return <div className="table-scroll"><table className="data-table"><thead><tr><th>INSTITUTION</th><th>PERMANENT ID</th><th>LOCATION</th>{!compact&&<th>RECORD ID</th>}</tr></thead><tbody>{rows.map((r,i)=><tr key={r.institution_id||i}><td><b className="cell-main">{r.name||'Unnamed institution'}</b><small className="cell-sub">{r.address||'Address not supplied'}</small></td><td><span className="mono-id">{r.permanent_id||'—'}</span></td><td>{[r.district,r.state].filter(Boolean).join(', ')||'—'}</td>{!compact&&<td><span className="cell-sub">{r.institution_id||'—'}</span></td>}</tr>)}</tbody></table></div>;
}
function Status({value}){const s=String(value||'Unknown');const cls=/dispos|resolv|closed|complete/i.test(s)?'green':/escalat|overdue|reject/i.test(s)?'red':/progress|review|pending|open/i.test(s)?'amber':'blue';return <span className={`status-chip ${cls}`}><i/>{pretty(s)}</span>}
function OverlapCard({row}){
 const a=row.case_a_ref||row.case_a||row.case_a_id||'Candidate A', b=row.case_b_ref||row.case_b||row.case_b_id||'Candidate B';
 const score=Number(row.score??row.similarity_score??row.overlap_score??row.confidence);
 const reasons=row.reasons||row.evidence||row.matched_on;
 return <article className="overlap-card"><div className="overlap-ends"><div><small>CASE / SOURCE A</small><b>{a}</b><span>{row.source_a||row.institution_a||'Reference returned by API'}</span></div><div className="overlap-link"><Network size={18}/><span>Potential relationship</span></div><div><small>CASE / SOURCE B</small><b>{b}</b><span>{row.source_b||row.institution_b||'Reference returned by API'}</span></div></div><div className="overlap-bottom"><span className="status-chip amber">Human review required</span>{Number.isFinite(score)&&<span className="score-pill">Signal score <b>{score.toFixed(1)}%</b></span>}<span className="overlap-reason">{Array.isArray(reasons)?reasons.join(', '):typeof reasons==='string'?reasons:'Compare underlying case evidence before concluding.'}</span></div></article>;
}
function DependencyView({cases,institutions,onOpenCase,onNav}){
 const roles=[['Admin / Senior Management','System-wide view','#174c85'],['Regional Officer','Region-scoped view','#7352a5'],['Bureau Head','Bureau-scoped view','#14866d'],['Desk Officer','Assigned cases','#bb6b24']];
 return <><div className="feature-banner compact-feature"><div className="feature-symbol"><Network size={25}/></div><div className="feature-copy"><div className="feature-kicker">JURISDICTIONAL VISIBILITY <span>ROLE AWARE</span></div><h3>Understand how SETU's access model shapes the case landscape.</h3><p>The current API supplies cases and overlap candidates, but not a dedicated graph endpoint. This view uses returned records and makes that limitation explicit.</p></div><button className="feature-cta" onClick={()=>onNav('coordination')}>Review candidates <ArrowRight size={16}/></button></div>
 <div className="map-legend"><span><i className="legend-dot blue-dot"/>Role scope</span><span><i className="legend-line"/>Accessible case</span><span><i className="legend-dot orange-dot"/>Institution record</span><span className="map-note">No hidden or inaccessible records are inferred.</span></div>
 <div className="visual-workspace"><div className="map-toolbar"><b>SETU CASE LANDSCAPE</b><span>{fmt(cases.items.length)} case rows · {fmt(institutions.items.length)} institutions returned</span><button className="btn btn-outline" onClick={()=>onNav('cases')}>Open case register</button></div><div className="diagram-grid"><div className="role-rail">{roles.map(([a,b,c])=><div className="role-node" key={a} style={{'--node-color':c}}><span className="role-node-dot"/><div><b>{a}</b><small>{b}</small></div><ChevronRight size={14}/></div>)}</div><div className="diagram-center"><div className="diagram-orbit orbit-one"/><div className="diagram-orbit orbit-two"/><div className="diagram-core"><Landmark size={25}/><b>SETU</b><small>API-backed workspace</small></div><div className="diagram-caption"><Network size={14}/> Relationship visualization preview</div></div><div className="case-node-list">{cases.error?<ErrorBox message={cases.error}/>:cases.items.slice(0,7).map((c,i)=><button key={c.case_id||i} className="case-node" onClick={()=>onOpenCase(c.case_id)}><span className="case-node-icon"><FileSearch size={15}/></span><span><b>{c.case_ref||c.case_id}</b><small>{c.institution_name_raw||c.category||'Case record'}</small></span><Status value={c.status}/></button>)}</div></div><div className="diagram-disclaimer"><CircleHelp size={15}/> The backend does not currently return dependency edges or graph coordinates. Lines are not fabricated; use the cross-bureau candidate endpoint for real candidate relationships.</div></div>
 <div className="dashboard-grid two-panels"><section className="panel"><PanelHead icon={Building2} title="Institution anchors" subtitle="Records returned from the institution API."/><InstitutionsTable rows={institutions.items.slice(0,5)} loading={institutions.loading} error={institutions.error} compact/></section><section className="panel"><PanelHead icon={ShieldCheck} title="Role scope at a glance" subtitle="The backend enforces the final access decision."/><div className="role-explainer">{roles.map(([a,b,c])=><div key={a}><span style={{background:c}}/><b>{a}</b><small>{b}</small></div>)}</div></section></div></>;
}
function Analytics({counts,cases,institutions,overlaps,health,semanticA,semanticB,setSemanticA,setSemanticB,semanticCheck,semanticBusy,semanticResult,semanticError}){
 const statusCounts=cases.items.reduce((acc,c)=>{const k=pretty(c.status||'Unknown');acc[k]=(acc[k]||0)+1;return acc;},{});
 const bureauCounts=cases.items.reduce((acc,c)=>{const k=c.current_bureau_id||'Unassigned';acc[k]=(acc[k]||0)+1;return acc;},{});
 return <><div className="stats-grid analytics-stats"><StatCard label="SUMMARY API" value={Object.keys(counts||{}).length?'Available':'Restricted / unavailable'} sub="Management endpoint" icon={Gauge} tone="blue"/><StatCard label="STATUS GROUPS" value={Object.keys(statusCounts).length||'—'} sub="From accessible case rows" icon={Activity} tone="purple"/><StatCard label="BUREAU GROUPS" value={Object.keys(bureauCounts).length||'—'} sub="From accessible case rows" icon={Landmark} tone="orange"/><StatCard label="SERVICE HEALTH" value={health.state==='healthy'?'Healthy':pretty(health.state)} sub="GET /health" icon={ShieldCheck} tone="green"/></div>
 <div className="dashboard-grid"><section className="panel"><PanelHead icon={Activity} title="Case status distribution" subtitle="Derived only from case records returned to this session."/><BarList values={statusCounts}/></section><section className="panel"><PanelHead icon={Landmark} title="Accessible bureau workload" subtitle="Count of returned case records grouped by bureau."/><BarList values={bureauCounts}/></section></div>
 <section className="panel semantic-panel"><PanelHead icon={Sparkles} title="Semantic comparison lab" subtitle="Development-only endpoint. Sends text to the backend for comparison; no database write is performed."/><div className="notice-box amber-notice"><AlertTriangle size={17}/><span>This endpoint may be disabled (404) and requires an authorized management profile. Use synthetic or approved text only.</span></div><form className="semantic-form" onSubmit={semanticCheck}><label>Text A<textarea value={semanticA} onChange={e=>setSemanticA(e.target.value)} maxLength={3000} required placeholder="Enter first synthetic complaint description"/></label><label>Text B<textarea value={semanticB} onChange={e=>setSemanticB(e.target.value)} maxLength={3000} required placeholder="Enter second synthetic complaint description"/></label><button className="btn btn-primary" disabled={semanticBusy}>{semanticBusy?<RefreshCw className="spin" size={15}/>:<Sparkles size={15}/>} Compare text</button></form>{semanticError&&<ErrorBox message={semanticError}/ >}{semanticResult&&<pre className="json-result">{JSON.stringify(semanticResult,null,2)}</pre>}</section></>;
}
function BarList({values}){const entries=Object.entries(values||{}).sort((a,b)=>b[1]-a[1]);if(!entries.length)return <Empty text="No accessible rows available to calculate this breakdown."/>;const max=Math.max(...entries.map(x=>x[1]),1);return <div className="bar-list">{entries.slice(0,10).map(([name,n])=><div className="bar-row" key={name}><div><span>{name}</span><b>{fmt(n)}</b></div><div className="bar-track"><i style={{width:`${Math.max(4,n/max*100)}%`}}/></div></div>)}</div>}
function Loading(){return <div className="loading"><span className="spinner"/>Loading data from SETU API…</div>}
function Empty({text}){return <div className="empty-state"><div className="empty-icon"><FileSearch size={20}/></div><b>No data to display</b><p>{text}</p></div>}
function ErrorBox({message}){return <div className="error-box"><AlertTriangle size={17}/><div><b>Request unavailable</b><p>{message}</p></div></div>}
function Modal({title,onClose,children,wide=false}){useEffect(()=>{const f=e=>e.key==='Escape'&&onClose();window.addEventListener('keydown',f);return()=>window.removeEventListener('keydown',f)},[onClose]);return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><section className={`modal ${wide?'modal-wide':''}`} role="dialog" aria-modal="true" aria-label={title}><header><div><span className="modal-eyebrow">SETU SECURE WORKSPACE</span><h3>{title}</h3></div><button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18}/></button></header><div className="modal-body">{children}</div></section></div>}
createRoot(document.getElementById('root')).render(<App/>);
