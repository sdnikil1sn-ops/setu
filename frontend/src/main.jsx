import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createClient } from '@supabase/supabase-js';
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowRight, Bell, Building2, CheckCircle2,
  ChevronDown, ChevronLeft, ChevronRight, CircleHelp, Clock3, Command, Download,
  FileSearch, Fingerprint, Gauge, Globe2, Landmark, LayoutDashboard, LockKeyhole,
  LogOut, Menu, Network, RefreshCw, Search, ShieldCheck, SlidersHorizontal, Sparkles,
  UserCircle2, X, Zap
} from 'lucide-react';
import './styles.css';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from '@xyflow/react';


import '@xyflow/react/dist/style.css';
const apiBase = (import.meta.env.VITE_SETU_API_URL || '').replace(/\/$/, '');

const LANGUAGE_OPTIONS = [
  ['en','English'],['as','অসমীয়া'],['bn','বাংলা'],['brx','बड़ो'],['doi','डोगरी'],
  ['gu','ગુજરાતી'],['hi','हिन्दी'],['kn','ಕನ್ನಡ'],['ks','कॉशुर'],['kok','कोंकणी'],
  ['mai','मैथिली'],['ml','മലയാളം'],['mni','মৈতৈলোন্'],['mr','मराठी'],['ne','नेपाली'],
  ['or','ଓଡ଼ିଆ'],['pa','ਪੰਜਾਬੀ'],['sa','संस्कृतम्'],['sat','ᱥᱟᱱᱛᱟᱲᱤ'],['sd','سنڌي'],
  ['ta','தமிழ்'],['te','తెలుగు'],['ur','اردو']
];
const UI_TRANSLATIONS = {
  en:{overview:'Executive Dashboard',map:'Visual Dependency Map',institutions:'Institution Registry',cases:'Grievance Repository',resolution:'Identity Resolution',coordination:'Cross-Bureau Intelligence',analytics:'Analytical Reports',refresh:'Refresh',language:'Language',dark:'Dark mode',light:'Light mode',title:'Government Intelligence Console',subtitle:'Connecting evidence. Clarifying jurisdiction. Supporting accountable action.',workspace:'SETU INTELLIGENCE WORKSPACE',openMap:'Open intelligence map',relationship:'Case relationship graph',relationshipDetails:'Relationship details',chooseNode:'Select a node to inspect its record, or a connecting line to inspect relationship details.',noDetails:'Select a relationship or record to view details.',illustrative:'Illustrative relationship view',withinSla:'Within SLA',review:'Review required'},
  hi:{overview:'कार्यकारी डैशबोर्ड',map:'दृश्य निर्भरता मानचित्र',institutions:'संस्थान रजिस्ट्री',cases:'शिकायत भंडार',resolution:'पहचान समाधान',coordination:'ब्यूरो समन्वय',analytics:'विश्लेषणात्मक रिपोर्ट',refresh:'रीफ़्रेश करें',language:'भाषा',dark:'डार्क मोड',light:'लाइट मोड',title:'सरकारी इंटेलिजेंस कंसोल',subtitle:'साक्ष्य जोड़ना। अधिकार क्षेत्र स्पष्ट करना। जवाबदेह कार्रवाई में सहायता।',workspace:'सेतु इंटेलिजेंस कार्यक्षेत्र',openMap:'इंटेलिजेंस मानचित्र खोलें',relationship:'मामला संबंध ग्राफ़',relationshipDetails:'संबंध विवरण',chooseNode:'रिकॉर्ड देखने के लिए नोड या संबंध विवरण के लिए रेखा चुनें।',noDetails:'विवरण देखने के लिए कोई रिकॉर्ड या संबंध चुनें।',illustrative:'उदाहरणात्मक संबंध दृश्य',withinSla:'समय-सीमा के भीतर',review:'समीक्षा आवश्यक'},
  ta:{overview:'நிர்வாகக் கட்டுப்பாட்டுப் பலகை',map:'காட்சி சார்பு வரைபடம்',institutions:'நிறுவனப் பதிவேடு',cases:'குறைதீர் பதிவகம்',resolution:'அடையாளத் தீர்வு',coordination:'பிரிவு ஒருங்கிணைப்பு',analytics:'பகுப்பாய்வு அறிக்கைகள்',refresh:'புதுப்பிக்கவும்',language:'மொழி',dark:'இருண்ட பயன்முறை',light:'ஒளி பயன்முறை',title:'அரசு நுண்ணறிவு மையம்',subtitle:'ஆதாரங்களை இணைத்து, அதிகார வரம்பைத் தெளிவுபடுத்தி, பொறுப்பான நடவடிக்கைக்கு ஆதரவு.',workspace:'SETU நுண்ணறிவு பணியிடம்',openMap:'வரைபடத்தைத் திறக்கவும்',relationship:'வழக்கு உறவு வரைபடம்',relationshipDetails:'உறவு விவரங்கள்',chooseNode:'பதிவைப் பார்க்க ஒரு முனையை அல்லது உறவு விவரங்களுக்கு இணைப்பைத் தேர்ந்தெடுக்கவும்.',noDetails:'விவரங்களைக் காண ஒரு பதிவைத் தேர்ந்தெடுக்கவும்.',illustrative:'விளக்க உறவு காட்சி',withinSla:'காலவரம்புக்குள்',review:'மதிப்பாய்வு தேவை'},
  te:{overview:'కార్యనిర్వాహక డ్యాష్‌బోర్డ్',map:'దృశ్య ఆధారిత మ్యాప్',institutions:'సంస్థల రిజిస్ట్రీ',cases:'ఫిర్యాదుల రిపోజిటరీ',resolution:'గుర్తింపు పరిష్కారం',coordination:'బ్యూరో సమన్వయం',analytics:'విశ్లేషణ నివేదికలు',refresh:'రిఫ్రెష్',language:'భాష',dark:'డార్క్ మోడ్',light:'లైట్ మోడ్',title:'ప్రభుత్వ ఇంటెలిజెన్స్ కన్సోల్',subtitle:'ఆధారాలను అనుసంధానించడం. అధికార పరిధిని స్పష్టం చేయడం.',workspace:'SETU ఇంటెలిజెన్స్ వర్క్‌స్పేస్',openMap:'మ్యాప్ తెరవండి',relationship:'కేసు సంబంధ గ్రాఫ్',relationshipDetails:'సంబంధ వివరాలు',chooseNode:'రికార్డు లేదా సంబంధ వివరాలను చూడటానికి ఒక అంశాన్ని ఎంచుకోండి.',noDetails:'వివరాల కోసం రికార్డును ఎంచుకోండి.',illustrative:'సంబంధాల వివరణాత్మక దృశ్యం',withinSla:'గడువులో ఉంది',review:'సమీక్ష అవసరం'},
  bn:{overview:'নির্বাহী ড্যাশবোর্ড',map:'দৃশ্যমান নির্ভরতা মানচিত্র',institutions:'প্রতিষ্ঠান নিবন্ধন',cases:'অভিযোগ ভান্ডার',resolution:'পরিচয় নিরূপণ',coordination:'বিভাগীয় সমন্বয়',analytics:'বিশ্লেষণ প্রতিবেদন',refresh:'রিফ্রেশ',language:'ভাষা',dark:'ডার্ক মোড',light:'লাইট মোড',title:'সরকারি ইন্টেলিজেন্স কনসোল',subtitle:'প্রমাণ সংযুক্ত করা, এখতিয়ার স্পষ্ট করা এবং জবাবদিহিমূলক পদক্ষেপে সহায়তা।',workspace:'SETU ইন্টেলিজেন্স কর্মক্ষেত্র',openMap:'মানচিত্র খুলুন',relationship:'মামলার সম্পর্ক গ্রাফ',relationshipDetails:'সম্পর্কের বিবরণ',chooseNode:'রেকর্ড দেখতে একটি নোড বা সম্পর্ক দেখতে সংযোগরেখা নির্বাচন করুন।',noDetails:'বিবরণ দেখতে একটি রেকর্ড নির্বাচন করুন।',illustrative:'সম্পর্কের ব্যাখ্যামূলক দৃশ্য',withinSla:'সময়সীমার মধ্যে',review:'পর্যালোচনা প্রয়োজন'},
  gu:{overview:'કાર્યકારી ડેશબોર્ડ',map:'દૃશ્ય નિર્ભરતા નકશો',institutions:'સંસ્થા રજિસ્ટ્રી',cases:'ફરિયાદ ભંડાર',resolution:'ઓળખ નિરાકરણ',coordination:'બ્યુરો સંકલન',analytics:'વિશ્લેષણ અહેવાલો',refresh:'રિફ્રેશ',language:'ભાષા',dark:'ડાર્ક મોડ',light:'લાઇટ મોડ',title:'સરકારી ઇન્ટેલિજન્સ કન્સોલ',subtitle:'પુરાવા જોડવા, અધિકારક્ષેત્ર સ્પષ્ટ કરવા અને જવાબદાર કાર્યવાહી માટે સહાય.',workspace:'SETU ઇન્ટેલિજન્સ કાર્યસ્થળ',openMap:'નકશો ખોલો',relationship:'કેસ સંબંધ ગ્રાફ',relationshipDetails:'સંબંધ વિગતો',chooseNode:'રેકોર્ડ અથવા સંબંધની વિગતો જોવા માટે પસંદ કરો.',noDetails:'વિગતો જોવા માટે રેકોર્ડ પસંદ કરો.',illustrative:'સંબંધોનું દૃષ્ટાંતરૂપ દૃશ્ય',withinSla:'સમયમર્યાદામાં',review:'સમીક્ષા જરૂરી'},
  kn:{overview:'ಕಾರ್ಯನಿರ್ವಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',map:'ದೃಶ್ಯ ಅವಲಂಬನೆ ನಕ್ಷೆ',institutions:'ಸಂಸ್ಥೆಗಳ ನೋಂದಣಿ',cases:'ದೂರು ಸಂಗ್ರಹ',resolution:'ಗುರುತು ಪರಿಹಾರ',coordination:'ಬ್ಯೂರೋ ಸಮನ್ವಯ',analytics:'ವಿಶ್ಲೇಷಣಾ ವರದಿಗಳು',refresh:'ರಿಫ್ರೆಶ್',language:'ಭಾಷೆ',dark:'ಡಾರ್ಕ್ ಮೋಡ್',light:'ಲೈಟ್ ಮೋಡ್',title:'ಸರ್ಕಾರಿ ಇಂಟೆಲಿಜೆನ್ಸ್ ಕನ್ಸೋಲ್',subtitle:'ಸಾಕ್ಷ್ಯಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ, ವ್ಯಾಪ್ತಿಯನ್ನು ಸ್ಪಷ್ಟಪಡಿಸಿ, ಹೊಣೆಗಾರ ಕ್ರಮಕ್ಕೆ ಬೆಂಬಲ.',workspace:'SETU ಇಂಟೆಲಿಜೆನ್ಸ್ ಕಾರ್ಯಕ್ಷೇತ್ರ',openMap:'ನಕ್ಷೆ ತೆರೆಯಿರಿ',relationship:'ಪ್ರಕರಣ ಸಂಬಂಧ ಗ್ರಾಫ್',relationshipDetails:'ಸಂಬಂಧದ ವಿವರಗಳು',chooseNode:'ದಾಖಲೆ ಅಥವಾ ಸಂಬಂಧದ ವಿವರಗಳನ್ನು ನೋಡಲು ಆಯ್ಕೆಮಾಡಿ.',noDetails:'ವಿವರಗಳಿಗಾಗಿ ದಾಖಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ.',illustrative:'ಸಂಬಂಧಗಳ ವಿವರಣಾತ್ಮಕ ನೋಟ',withinSla:'ಗಡುವಿನೊಳಗೆ',review:'ಪರಿಶೀಲನೆ ಅಗತ್ಯ'},
  ml:{overview:'എക്സിക്യൂട്ടീവ് ഡാഷ്ബോർഡ്',map:'വിഷ്വൽ ഡിപൻഡൻസി മാപ്പ്',institutions:'സ്ഥാപന രജിസ്ട്രി',cases:'പരാതി ശേഖരം',resolution:'തിരിച്ചറിയൽ പരിഹാരം',coordination:'ബ്യൂറോ ഏകോപനം',analytics:'വിശകലന റിപ്പോർട്ടുകൾ',refresh:'പുതുക്കുക',language:'ഭാഷ',dark:'ഡാർക്ക് മോഡ്',light:'ലൈറ്റ് മോഡ്',title:'സർക്കാർ ഇന്റലിജൻസ് കൺസോൾ',subtitle:'തെളിവുകൾ ബന്ധിപ്പിച്ച് അധികാരപരിധി വ്യക്തമാക്കുകയും ഉത്തരവാദിത്തമുള്ള നടപടിക്ക് പിന്തുണ നൽകുകയും ചെയ്യുന്നു.',workspace:'SETU ഇന്റലിജൻസ് വർക്ക്‌സ്‌പേസ്',openMap:'മാപ്പ് തുറക്കുക',relationship:'കേസ് ബന്ധ ഗ്രാഫ്',relationshipDetails:'ബന്ധ വിശദാംശങ്ങൾ',chooseNode:'രേഖയോ ബന്ധവിവരങ്ങളോ കാണാൻ തിരഞ്ഞെടുക്കുക.',noDetails:'വിശദാംശങ്ങൾ കാണാൻ ഒരു രേഖ തിരഞ്ഞെടുക്കുക.',illustrative:'ബന്ധങ്ങളുടെ വിശദീകരണ കാഴ്ച',withinSla:'സമയപരിധിക്കുള്ളിൽ',review:'പരിശോധന ആവശ്യമാണ്'},
  mr:{overview:'कार्यकारी डॅशबोर्ड',map:'दृश्य अवलंबित्व नकाशा',institutions:'संस्था नोंदणी',cases:'तक्रार संग्रह',resolution:'ओळख निराकरण',coordination:'विभागीय समन्वय',analytics:'विश्लेषण अहवाल',refresh:'रिफ्रेश',language:'भाषा',dark:'डार्क मोड',light:'लाइट मोड',title:'शासकीय इंटेलिजन्स कन्सोल',subtitle:'पुरावे जोडणे, अधिकारक्षेत्र स्पष्ट करणे आणि जबाबदार कृतीस मदत करणे.',workspace:'SETU इंटेलिजन्स कार्यक्षेत्र',openMap:'नकाशा उघडा',relationship:'प्रकरण संबंध आलेख',relationshipDetails:'संबंध तपशील',chooseNode:'नोंद किंवा संबंध तपशील पाहण्यासाठी निवडा.',noDetails:'तपशील पाहण्यासाठी नोंद निवडा.',illustrative:'संबंधांचे स्पष्टीकरणात्मक दृश्य',withinSla:'कालमर्यादेत',review:'पुनरावलोकन आवश्यक'},
  pa:{overview:'ਕਾਰਜਕਾਰੀ ਡੈਸ਼ਬੋਰਡ',map:'ਦ੍ਰਿਸ਼ ਨਿਰਭਰਤਾ ਨਕਸ਼ਾ',institutions:'ਸੰਸਥਾ ਰਜਿਸਟਰੀ',cases:'ਸ਼ਿਕਾਇਤ ਭੰਡਾਰ',resolution:'ਪਛਾਣ ਹੱਲ',coordination:'ਬਿਊਰੋ ਤਾਲਮੇਲ',analytics:'ਵਿਸ਼ਲੇਸ਼ਣ ਰਿਪੋਰਟਾਂ',refresh:'ਤਾਜ਼ਾ ਕਰੋ',language:'ਭਾਸ਼ਾ',dark:'ਡਾਰਕ ਮੋਡ',light:'ਲਾਈਟ ਮੋਡ',title:'ਸਰਕਾਰੀ ਇੰਟੈਲੀਜੈਂਸ ਕੰਸੋਲ',subtitle:'ਸਬੂਤ ਜੋੜਨਾ, ਅਧਿਕਾਰ ਖੇਤਰ ਸਪਸ਼ਟ ਕਰਨਾ ਅਤੇ ਜਵਾਬਦੇਹ ਕਾਰਵਾਈ ਵਿੱਚ ਸਹਾਇਤਾ.',workspace:'SETU ਇੰਟੈਲੀਜੈਂਸ ਵਰਕਸਪੇਸ',openMap:'ਨਕਸ਼ਾ ਖੋਲ੍ਹੋ',relationship:'ਕੇਸ ਸੰਬੰਧ ਗ੍ਰਾਫ',relationshipDetails:'ਸੰਬੰਧ ਵੇਰਵੇ',chooseNode:'ਰਿਕਾਰਡ ਜਾਂ ਸੰਬੰਧ ਦੇ ਵੇਰਵੇ ਵੇਖਣ ਲਈ ਚੁਣੋ।',noDetails:'ਵੇਰਵੇ ਵੇਖਣ ਲਈ ਰਿਕਾਰਡ ਚੁਣੋ।',illustrative:'ਸੰਬੰਧਾਂ ਦਾ ਉਦਾਹਰਣੀ ਦ੍ਰਿਸ਼',withinSla:'ਸਮਾਂ ਸੀਮਾ ਅੰਦਰ',review:'ਸਮੀਖਿਆ ਲੋੜੀਂਦੀ'},
  or:{overview:'କାର୍ଯ୍ୟନିର୍ବାହୀ ଡ୍ୟାସବୋର୍ଡ',map:'ଦୃଶ୍ୟ ନିର୍ଭରତା ମାନଚିତ୍ର',institutions:'ଅନୁଷ୍ଠାନ ରେଜିଷ୍ଟ୍ରି',cases:'ଅଭିଯୋଗ ସଂଗ୍ରହ',resolution:'ପରିଚୟ ସମାଧାନ',coordination:'ବ୍ୟୁରୋ ସମନ୍ୱୟ',analytics:'ବିଶ୍ଳେଷଣ ରିପୋର୍ଟ',refresh:'ରିଫ୍ରେସ୍',language:'ଭାଷା',dark:'ଡାର୍କ ମୋଡ୍',light:'ଲାଇଟ୍ ମୋଡ୍',title:'ସରକାରୀ ଇଣ୍ଟେଲିଜେନ୍ସ କନସୋଲ୍',subtitle:'ପ୍ରମାଣ ସଂଯୋଗ, କ୍ଷେତ୍ରାଧିକାର ସ୍ପଷ୍ଟତା ଏବଂ ଦାୟିତ୍ୱପୂର୍ଣ୍ଣ କାର୍ଯ୍ୟରେ ସହାୟତା।',workspace:'SETU ଇଣ୍ଟେଲିଜେନ୍ସ କାର୍ଯ୍ୟକ୍ଷେତ୍ର',openMap:'ମାନଚିତ୍ର ଖୋଲନ୍ତୁ',relationship:'ମାମଲା ସମ୍ପର୍କ ଗ୍ରାଫ୍',relationshipDetails:'ସମ୍ପର୍କ ବିବରଣୀ',chooseNode:'ରେକର୍ଡ କିମ୍ବା ସମ୍ପର୍କ ବିବରଣୀ ଦେଖିବାକୁ ବାଛନ୍ତୁ।',noDetails:'ବିବରଣୀ ପାଇଁ ରେକର୍ଡ ବାଛନ୍ତୁ।',illustrative:'ସମ୍ପର୍କର ବ୍ୟାଖ୍ୟାତ୍ମକ ଦୃଶ୍ୟ',withinSla:'ସମୟସୀମା ମଧ୍ୟରେ',review:'ସମୀକ୍ଷା ଆବଶ୍ୟକ'}
};
const tFor = (lang, key) => (UI_TRANSLATIONS[lang] && UI_TRANSLATIONS[lang][key]) || UI_TRANSLATIONS.en[key] || key;

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';
const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey, { auth: { persistSession: false, autoRefreshToken: true, detectSessionInUrl: true } })
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
  const [language, setLanguage] = useState(() => { try { return localStorage.getItem('setu-language') || 'en'; } catch { return 'en'; } });
  const t = (key) => tFor(language, key);
  useEffect(() => { try { localStorage.setItem('setu-language', language); } catch {} document.documentElement.lang = language; }, [language]);
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
    <div className="gov-strip"><div className="gov-left"><span className="mini-emblem">✦</span><b>भारत सरकार | GOVERNMENT OF INDIA</b><i/> <span>शिक्षा मंत्रालय | MINISTRY OF EDUCATION</span></div><div className="gov-right"><span className={`health-dot ${health.state}`}/> <button className="text-size" title="Increase text size" aria-label="Increase text size" onClick={()=>adjustFont(1)}>A+</button><button className="text-size" title="Decrease text size" aria-label="Decrease text size" onClick={()=>adjustFont(-1)}>A−</button><button className="contrast-toggle" onClick={toggleDarkMode} aria-label="Toggle dark mode">{document.documentElement.classList.contains('dark-mode')?t('light'):t('dark')}</button><label className="language-control" title={t('language')}><Globe2 size={15}/><select aria-label={t('language')} value={language} onChange={e=>setLanguage(e.target.value)}>{LANGUAGE_OPTIONS.map(([code,name])=><option key={code} value={code}>{name}</option>)}</select></label><div className="account-controls" title={sessionEmail || 'Signed-in profile'}><UserCircle2 size={15}/><span className="account-email">{sessionEmail || 'Authorized user'}</span><button className="account-logout" onClick={signOut} aria-label="Sign out" title="Sign out"><LogOut size={14}/><span>Sign out</span></button></div></div></div>
    <header className="masthead">
      <div className="brand">
        <div className="seal"><Landmark size={27}/><span/></div>
        <div><div className="brand-overline">INSTITUTION COMPLAINT INTELLIGENCE</div><h1>SETU <span>{t("title")}</span></h1><p>{t("subtitle")}</p></div>
      </div>
      <div className="mast-actions">
        <button className="alert-button" onClick={()=>navTo('analytics')}><Bell size={16}/><span>Alerts</span><b>{health.state==='healthy'&&cases.error===''?pendingCount:'—'}</b></button>
      </div>
    </header>
    <div className="nav-wrap">
      <button className="mobile-menu" onClick={()=>setMobileNav(v=>!v)}><Menu size={18}/> Modules</button>
      <nav className={mobileNav?'main-nav open':'main-nav'} aria-label="Main navigation">
        {nav.map(n=>{const Icon=n.icon;return <button key={n.id} className={`nav-item ${active===n.id?'active':''}`} onClick={()=>navTo(n.id)}><Icon size={16}/><span>{t(n.id)}</span>{n.tag&&<small>{n.tag}</small>}</button>})}
      </nav>
    </div>

    <main className="workspace">
      <div className="page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line"/> NATIONAL INSTITUTIONAL OVERSIGHT <span className="muted-dot">/</span> SETU PORTAL</div><h2>{t(active) || 'Executive Dashboard'}</h2><p>{active==='overview'?'A clear operational picture of accessible cases, institutions, and service health.':'Evidence-led tools for institution and complaint intelligence.'}</p></div>
        <div className="heading-actions"><button className="btn btn-outline" onClick={refresh}><RefreshCw size={15}/> {t('refresh')}</button></div>
      </div>

      {active==='overview'&&<Overview counts={counts} cases={cases} institutions={institutions} overlaps={overlaps} health={health} pendingCount={pendingCount} onNav={navTo} onOpenCase={openCase} />}
      {active==='cases'&&<section className="panel"><PanelHead icon={FileSearch} title="Grievance repository" subtitle="Search and inspect cases visible to your authorized role." action={<button className="btn btn-outline" onClick={exportCases}><Download size={15}/> Export CSV</button>}/><div className="filters"><div className="searchbox"><Search size={16}/><input placeholder="Search case, institution, category…" value={caseQuery} onChange={e=>setCaseQuery(e.target.value)}/></div><select value={caseStatus} onChange={e=>setCaseStatus(e.target.value)}><option value="">All statuses</option>{['Pending','Under Process','Disposed','Resolved','Escalated','Transferred'].map(x=><option key={x}>{x}</option>)}</select><input className="filter-input" placeholder="Bureau ID" value={bureau} onChange={e=>setBureau(e.target.value)}/><button className="btn btn-primary" onClick={loadCases}><SlidersHorizontal size={15}/> Apply filters</button></div><CasesTable rows={visibleCases} loading={cases.loading} error={cases.error} onOpen={openCase}/><div className="table-foot">Showing {visibleCases.length} of {fmt(cases.total)} accessible records. Row visibility is controlled by the backend.</div></section>}
      {active==='institutions'&&<section className="panel"><PanelHead icon={Building2} title="Institution master registry" subtitle="Search by institution name, permanent ID, state, or district."/><div className="filters"><div className="searchbox wide"><Search size={16}/><input placeholder="Institution name or permanent ID" value={institutionQuery} onChange={e=>setInstitutionQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&loadInstitutions()}/></div><button className="btn btn-primary" onClick={loadInstitutions}><Search size={15}/> Search institutions</button></div><InstitutionsTable rows={visibleInstitutions} loading={institutions.loading} error={institutions.error}/><div className="table-foot">Showing {visibleInstitutions.length} of {fmt(institutions.total)} returned records.</div></section>}
      {active==='resolution'&&<div className="two-col"><section className="panel"><PanelHead icon={Fingerprint} title="Institution identity resolution" subtitle="Propose a match from the backend's read-only resolver."/><form className="form-stack" onSubmit={resolveInstitution}><label>Raw institution name<input value={resolveName} onChange={e=>setResolveName(e.target.value)} maxLength={300} placeholder="Enter name as received in a complaint"/></label><div className="field-or"><span/> OR <span/></div><label>AICTE / permanent institution ID<input value={resolveId} onChange={e=>setResolveId(e.target.value)} maxLength={100} placeholder="Enter permanent ID if available"/></label><div className="notice-box"><ShieldCheck size={17}/><span>This tool proposes a match only. It does not edit master institution records.</span></div><button className="btn btn-primary" disabled={resolveBusy||(!resolveName.trim()&&!resolveId.trim())}>{resolveBusy?<RefreshCw className="spin" size={16}/>:<Sparkles size={16}/>} {resolveBusy?'Resolving…':'Resolve institution'}</button></form>{resolveError&&<ErrorBox message={resolveError}/>}</section><section className="panel result-panel"><PanelHead icon={CheckCircle2} title="Resolution result" subtitle="Candidate evidence and confidence from the API."/>{resolution?<><div className="result-status"><span className={`status-chip ${resolution.review_required?'amber':'green'}`}>{pretty(resolution.resolution_status)}</span><strong>{resolution.resolution_confidence==null?'—':`${Math.round(Number(resolution.resolution_confidence)*100)}%`}</strong><small>reported confidence</small></div><p className="result-reason">{resolution.reason||'No explanation returned by the resolver.'}</p>{resolution.institution&&<div className="resolved-card"><b>{resolution.institution.name}</b><span>{resolution.institution.permanent_id||'No permanent ID returned'}</span><small>{[resolution.institution.district,resolution.institution.state].filter(Boolean).join(', ')}</small></div>}<h4>Candidate matches</h4>{(resolution.candidates||[]).length?<div className="candidate-list">{resolution.candidates.map((c,i)=><div className="candidate" key={c.institution_id||i}><div><b>{c.name}</b><small>{c.permanent_id||c.institution_id}</small></div><span>{c.score==null?'—':`${Math.round(Number(c.score))}%`}</span></div>)}</div>:<Empty text="No candidates were returned."/>}<p className="footnote">Human verification remains required where flagged by the backend.</p></>:<Empty text="Submit an institution name or ID to view a result."/ >}</section></div>}
      {active==='coordination'&&<section className="panel"><PanelHead icon={Globe2} title="Cross-bureau intelligence" subtitle="Potential overlap candidates for authorized management roles." action={<button className="btn btn-outline" onClick={loadOverlaps}><RefreshCw size={15}/> Refresh candidates</button>}/><div className="method-banner"><Zap size={17}/><div><b>Decision support, not automatic merging</b><p>Review candidates and the evidence behind each possible overlap. This backend exposes candidate retrieval, not a merge or approval action.</p></div></div>{overlaps.error?<ErrorBox message={overlaps.error}/>:overlaps.loading?<Loading/>:overlaps.items.length?<div className="overlap-list">{overlaps.items.map((r,i)=><OverlapCard key={r.id||`${r.case_a||i}`} row={r}/>)}</div>:<Empty text="No accessible overlap candidates returned. This can mean no matches, or that the current account is not authorized."/>}</section>}
      {active === 'map' && (
  <DependencyView
    cases={cases}
    institutions={institutions}
    request={request}
    onOpenCase={openCase}
    onNav={navTo}
  />
)}
      {active==='analytics'&&<Analytics counts={counts} cases={cases} institutions={institutions} overlaps={overlaps} health={health} onSemantic={()=>{}} semanticA={semanticA} semanticB={semanticB} setSemanticA={setSemanticA} setSemanticB={setSemanticB} semanticCheck={semanticCheck} semanticBusy={semanticBusy} semanticResult={semanticResult} semanticError={semanticError}/>}
    </main>
    <footer className="footer"><div className="footer-brand"><div className="footer-seal"><Landmark size={18}/></div><div><b>SETU | Government Intelligence Console</b><span>Institution complaint intelligence · Evidence-led decision support</span></div></div><div className="footer-links"><span>Security first</span><span>Role-scoped access</span><span>Human review</span><span>Public service guidance</span></div><div className="footer-bottom">This interface is an operational aid. Decisions remain with authorized officials. Do not treat unavailable data as zero.</div></footer>
    {notice&&<div className="toast"><CheckCircle2 size={17}/>{notice}<button onClick={()=>setNotice('')}><X size={14}/></button></div>}

    {selectedCase&&<Modal title="Case intelligence dossier" onClose={()=>setSelectedCase(null)} wide><div className="case-dossier"><div className="dossier-top"><span className="status-chip blue">{pretty(selectedCase.status)}</span><span className="case-id">{selectedCase.case_id}</span></div><h3>{selectedCase.institution_name_raw||'Institution not specified'}</h3><p>{selectedCase.text||'No complaint summary was returned.'}</p><div className="detail-grid">{Object.entries(selectedCase).filter(([k,v])=>v!==null&&v!==''&&!['text'].includes(k)).slice(0,24).map(([k,v])=><div key={k}><small>{pretty(k)}</small><b>{typeof v==='boolean'?(v?'Yes':'No'):String(v)}</b></div>)}</div></div></Modal>}
    {caseError&&<Modal title="Case details unavailable" onClose={()=>setCaseError('')}><ErrorBox message={caseError}/><p className="footnote">The This record may not be available to your account.</p></Modal>}
  </div>;
}

function PanelHead({icon:Icon,title,subtitle,action}){return <div className="panel-head"><div className="panel-title-icon"><Icon size={18}/></div><div className="panel-title"><h3>{title}</h3><p>{subtitle}</p></div>{action&&<div className="panel-action">{action}</div>}</div>}
function StatCard({label,value,sub,icon:Icon,tone='navy',loading=false}){return <div className={`stat-card tone-${tone}`}><div className="stat-top"><span>{label}</span><div className="stat-icon"><Icon size={17}/></div></div><strong>{loading?'…':value}</strong><div className="stat-sub">{sub}</div><div className="stat-rule"/></div>}
function Overview({counts,cases,institutions,overlaps,health,pendingCount,onNav,onOpenCase}){
 const caseRows=cases.items.slice(0,6);
 const summaryAvailable=Object.keys(counts||{}).length>0;
 return <><div className="section-label"><span>OPERATIONAL SNAPSHOT</span><span className="section-note"><span className="live-dot"/> Current operational overview</span></div>
 <div className="stats-grid">
 <StatCard label="INSTITUTIONS RETURNED" value={fmt(institutions.total)} sub={institutions.error?'Access unavailable':'Registry query results'} icon={Building2} tone="blue" loading={institutions.loading}/>
 <StatCard label="ACCESSIBLE CASES" value={cases.error?'—':fmt(cases.total)} sub={cases.error?'Staff access required':'Visible to this staff role'} icon={FileSearch} tone="orange" loading={cases.loading}/>
 <StatCard label="OPEN / ACTIVE" value={cases.error?'—':fmt(pendingCount)} sub="Based on returned status labels" icon={Clock3} tone="purple" loading={cases.loading}/>
 <StatCard label="OVERLAP CANDIDATES" value={overlaps.error?'—':fmt(overlaps.items.length)} sub={overlaps.error?'Management access may be required':'Candidate pairs returned'} icon={Network} tone="red" loading={overlaps.loading}/>
 </div>
 <div className="feature-banner"><div className="feature-symbol"><Network size={25}/><span/></div><div className="feature-copy"><div className="feature-kicker">{"SETU INTELLIGENCE WORKSPACE"}</div><h3>Connect cases, institutions and jurisdictional signals.</h3><p>Move from an institution lookup to case context, identity resolution and cross-bureau candidate review without losing the evidence trail.</p><div className="feature-chips"><span><CheckCircle2 size={13}/> Role-scoped data</span><span><CheckCircle2 size={13}/> Explainable review</span><span><CheckCircle2 size={13}/> Human decision</span></div></div><button className="feature-cta" onClick={()=>onNav('map')}>{"Open intelligence map"} <ArrowRight size={16}/></button></div>
 <div className="dashboard-grid">
 <section className="panel table-panel"><PanelHead icon={FileSearch} title="Recent accessible cases" subtitle="Recent records for review." action={<button className="inline-link" onClick={()=>onNav('cases')}>Open repository <ArrowRight size={14}/></button>}/>{cases.error?<ErrorBox message={cases.error}/>:cases.loading?<Loading/>:<CasesTable rows={caseRows} loading={false} onOpen={onOpenCase} compact/>}</section>
 <section className="panel table-panel"><PanelHead icon={Building2} title="Institution registry" subtitle="Searchable master data for identity checks." action={<button className="inline-link" onClick={()=>onNav('institutions')}>Browse registry <ArrowRight size={14}/></button>}/>{institutions.error?<ErrorBox message={institutions.error}/>:institutions.loading?<Loading/>:<InstitutionsTable rows={institutions.items.slice(0,6)} loading={false} compact/>}</section>
 
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

function DependencyView({ cases, institutions, request, onOpenCase, onNav }) {
  const [graph, setGraph] = useState({
    nodes: [],
    edges: [],
    loading: true,
    error: '',
    notice: '',
  });
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [usingIllustrativeGraph, setUsingIllustrativeGraph] = useState(false);

  const buildIllustrativeGraph = () => {
    const records = [
      { id: 'ILL-001', label: 'Application review delay', category: 'Approval application', status: 'Under scrutiny', bureau_name: 'Regional Scrutiny Cell', sla_state: 'Due in 2 days', institution_name: 'National Institute of Applied Studies', summary: 'Illustrative application review case.' },
      { id: 'ILL-002', label: 'Missing compliance documents', category: 'Compliance', status: 'Awaiting institution', bureau_name: 'Compliance Desk', sla_state: 'Clock paused', institution_name: 'National Institute of Applied Studies', summary: 'Illustrative compliance documentation case.' },
      { id: 'ILL-003', label: 'Faculty information verification', category: 'Verification', status: 'In progress', bureau_name: 'Regional Scrutiny Cell', sla_state: 'Within SLA', institution_name: 'Institute for Technical Learning', summary: 'Illustrative faculty verification case.' },
      { id: 'ILL-004', label: 'Approval condition follow-up', category: 'Approval condition', status: 'Pending review', bureau_name: 'Monitoring Unit', sla_state: 'Review required', institution_name: 'Central Technical Institute', summary: 'Illustrative approval condition follow-up.' },
      { id: 'ILL-005', label: 'Renewal documentation check', category: 'Renewal', status: 'Open', bureau_name: 'Compliance Desk', sla_state: 'Due in 5 days', institution_name: 'National Institute of Applied Studies', summary: 'Illustrative renewal documentation case.' },
    ];
    const links = [
      { id:'ILL-LINK-01', source:'ILL-001', target:'ILL-002', status:'suggested', relationship_type:'Illustrative relationship', score:0.75, tier:'High', scope:'institution', reasons:['Shared institution context'], requires_human_review:true },
      { id:'ILL-LINK-02', source:'ILL-002', target:'ILL-003', status:'pending_review', relationship_type:'Illustrative relationship', score:0.55, tier:'Medium', scope:'institution', reasons:['Potentially related compliance evidence'], requires_human_review:true },
      { id:'ILL-LINK-03', source:'ILL-002', target:'ILL-005', status:'suggested', relationship_type:'Illustrative relationship', score:0.72, tier:'High', scope:'institution', reasons:['Related documentation workflow'], requires_human_review:true },
      { id:'ILL-LINK-04', source:'ILL-004', target:'ILL-005', status:'pending_review', relationship_type:'Illustrative relationship', score:0.48, tier:'Review', scope:'institution', reasons:['Related approval lifecycle'], requires_human_review:true },
    ];
    
const nodes = records.map((node, index) => ({
  id: node.id,
  position: {
    x: (index % 3) * 290,
    y: Math.floor(index / 3) * 185,
  },
  data: {
    record: node,
    label: (
      <div style={{ width: 205, padding: 4 }}>
        <strong>{node.label || node.id}</strong>
        <div style={{ fontSize: 11, marginTop: 7 }}>
          {node.category || 'Case record'}
        </div>
        <div style={{ fontSize: 11, marginTop: 4 }}>
          Status: {node.status || 'Under review'}
        </div>
        <div style={{ fontSize: 11, marginTop: 4 }}>
          Unit: {node.bureau_name || 'Unassigned'}
        </div>
        <div style={{ fontSize: 11, marginTop: 4 }}>
          SLA: {node.sla_state || 'Not available'}
        </div>
        <div style={{ fontSize: 10, marginTop: 7, opacity: 0.75 }}>
          Select to inspect record
        </div>
      </div>
    ),
  },
  style: {
    width: 235,
    minHeight: 130,
    borderRadius: 10,
    border: '1px solid #b9d0d5',
    background: '#fff',
    color: '#17324d',
    padding: 10,
    fontSize: 12,
    boxShadow: '0 3px 12px rgba(15,23,42,.06)',
  },
}));

    const edges = links.map(edge=>({id:edge.id,source:edge.source,target:edge.target,type:'smoothstep',label:edge.status,markerEnd:{type:MarkerType.ArrowClosed,color:'#c17a20'},style:{stroke:'#c17a20',strokeWidth:1.8,strokeDasharray:'6 4'},labelStyle:{fill:'#334155',fontSize:10},labelBgStyle:{fill:'#fff',fillOpacity:.95},data:edge}));
    return {nodes,edges,records};
  };

  const loadGraph = useCallback(async () => {
    setGraph(previous => ({
      ...previous,
      loading: true,
      error: '',
    }));

    try {
      const data = await request('/api/v1/dependency-map?limit=100');

      const rawNodes = Array.isArray(data?.nodes) ? data.nodes : [];
      const rawEdges = Array.isArray(data?.edges) ? data.edges : [];

      const nodes = rawNodes.map((node, index) => {
        const columns = 3;
        const x = (index % columns) * 290;
        const y = Math.floor(index / columns) * 170;

        return {
          id: String(node.id),
          position: { x, y },
          data: {
            record: node,
            label: (
              <div style={{ width: 205, padding: 4 }}>
                <strong>{node.label || node.id}</strong>
                <div style={{ fontSize: 11, marginTop: 7 }}>
                  {node.category || 'Uncategorised'}
                </div>
                <div style={{ fontSize: 11, marginTop: 4 }}>
                  Status: {node.status || 'Unknown'}
                </div>
                <div style={{ fontSize: 11, marginTop: 4 }}>
                  Bureau: {node.bureau_name || 'Unassigned'}
                </div>
                <div style={{ fontSize: 11, marginTop: 4 }}>
                  SLA: {node.sla_state || 'Not available'}
                </div>
                <div style={{ fontSize: 10, marginTop: 7, opacity: 0.75 }}>
                  Select to open case
                </div>
              </div>
            ),
          },
          style: {
            width: 235,
            minHeight: 130,
            borderRadius: 10,
            border: '1px solid #cbd5e1',
            background: '#ffffff',
            color: '#172b4d',
            padding: 10,
            fontSize: 12,
            boxShadow: '0 3px 12px rgba(15, 23, 42, 0.06)',
          },
        };
      });

      const nodeIds = new Set(nodes.map(node => node.id));

      const edges = rawEdges
        .filter(edge =>
          nodeIds.has(String(edge.source)) &&
          nodeIds.has(String(edge.target))
        )
        .map(edge => ({
          id: String(edge.id),
          source: String(edge.source),
          target: String(edge.target),
          type: 'smoothstep',
          label: String(edge.status || 'unspecified'),
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: edge.requires_human_review ? '#c17a20' : '#4776a8',
          },
          style: {
            stroke: edge.requires_human_review ? '#c17a20' : '#4776a8',
            strokeWidth: 1.8,
            strokeDasharray: edge.requires_human_review ? '6 4' : undefined,
          },
          labelStyle: {
            fill: '#334155',
            fontSize: 10,
          },
          labelBgStyle: {
            fill: '#ffffff',
            fillOpacity: 0.95,
          },
          data: edge,
        }));

      if (nodes.length === 0 || edges.length === 0) {
        const fallback = buildIllustrativeGraph();
        setGraph({ nodes: fallback.nodes, edges: fallback.edges, loading: false, error: '', notice: 'Illustrative relationship graph shown because no eligible live relationships were returned. These example records are not stored as actual case records.' });
        setUsingIllustrativeGraph(true);
        setSelectedNode(null);
      } else {
        setGraph({ nodes, edges, loading: false, error: '', notice: data?.notice || '' });
        setUsingIllustrativeGraph(false);
        setSelectedNode(null);
      }
      setSelectedEdge(null);
    } catch (error) {
      const fallback = buildIllustrativeGraph();
      setGraph({ nodes: fallback.nodes, edges: fallback.edges, loading: false, error: '', notice: 'Illustrative relationship graph shown because live relationship data could not be retrieved. These example records are not actual case records.' });
      setUsingIllustrativeGraph(true);
      setSelectedNode(null);
      setSelectedEdge(null);
    }
  }, [request]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  return (
    <>
      <div className="feature-banner compact-feature">
        <div className="feature-symbol">
          <Network size={25} />
        </div>
        <div className="feature-copy">
          <div className="feature-kicker">
            CASE RELATIONSHIPS
          </div>
          <h3>Visualise recorded relationships across cases.</h3>
          <p>
            Explore linked cases, review relationship evidence and identify
            records requiring human review.
          </p>
        </div>
        <button className="feature-cta" onClick={() => onNav('coordination')}>
          Review candidates <ArrowRight size={16} />
        </button>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <PanelHead
            icon={Network}
            title="Case relationship graph"
            subtitle="Select a node to inspect its record, or a connecting line to inspect relationship details."
          />

          <div
            style={{
              display: 'flex',
              gap: 20,
              flexWrap: 'wrap',
              marginBottom: 14,
              fontSize: 12,
            }}
          >
            <span>Cases: <strong>{graph.nodes.length}</strong></span>
            <span>Links: <strong>{graph.edges.length}</strong></span>
            <span style={{ color: '#b7791f' }}>{"Dashed line: review required"}</span>
          </div>

          {graph.loading && (
            <div className="empty-state">Loading relationship graph…</div>
          )}

          {!graph.loading && graph.error && (
            <ErrorBox message={graph.error} />
          )}

          {usingIllustrativeGraph && <div className="notice-box amber-notice" style={{marginBottom:12}}><CircleHelp size={15}/><span>Illustrative relationship view. The records and links below are examples for navigation and are not actual institutional records.</span></div>}

          {!graph.loading && !graph.error &&
            graph.nodes.length > 0 && (
              <div
                style={{
                  height: 600,
                  width: '100%',
                  border: '1px solid #e2e8f0',
                  borderRadius: 10,
                  overflow: 'hidden',
                }}
              >
                <ReactFlow
                  nodes={graph.nodes}
                  edges={graph.edges}
                  fitView
                  fitViewOptions={{ padding: 0.2 }}
                  minZoom={0.15}
                  maxZoom={1.8}
                  onNodeClick={(_, node) => { setSelectedNode(node.data?.record || node); setSelectedEdge(null); if (!usingIllustrativeGraph) onOpenCase(node.id); }}
                  onEdgeClick={(_, edge) => setSelectedEdge(edge.data)}
                >
                  <Background gap={22} color="#dbe4ef" />
                  <MiniMap pannable zoomable />
                  <Controls />
                </ReactFlow>
              </div>
            )}

          <div className="diagram-disclaimer" style={{ marginTop: 14 }}>
            <CircleHelp size={15} />
            {graph.notice ||
              'Case links are not necessarily confirmed operational dependencies. Review their status and evidence before acting.'}
          </div>

          <div style={{ marginTop: 14 }}>
            <button className="btn btn-outline" onClick={loadGraph}>
              <RefreshCw size={15} /> Refresh graph
            </button>
          </div>
        </section>

        <section className="panel">
          <PanelHead
            icon={FileSearch}
            title="Relationship details"
            subtitle="Select a connecting line to inspect its recorded metadata."
          />

          {selectedNode && !selectedEdge && <div className="record-detail-stack"><div><small>Record ID</small><h3>{selectedNode.id}</h3></div><div><small>Record title</small><p><strong>{selectedNode.label || selectedNode.id}</strong></p></div><div><small>Institution</small><p>{selectedNode.institution_name || 'Institution details are not available'}</p></div><div><small>Category / status</small><p>{selectedNode.category || '—'} · {selectedNode.status || '—'}</p></div><div><small>Responsible unit</small><p>{selectedNode.bureau_name || 'Unassigned'}</p></div><div><small>SLA state</small><p>{selectedNode.sla_state || 'Not available'}</p></div><div><small>Summary</small><p>{selectedNode.summary || 'Relationship record selected for review.'}</p></div>{usingIllustrativeGraph&&<div className="notice-box amber-notice"><CircleHelp size={15}/><span>Illustrative record only. It cannot be opened as a live case.</span></div>}</div>}
          {!selectedEdge && !selectedNode && (
            <Empty text="Select a graph node to inspect its record, or a connecting line to inspect relationship details." />
          )}

          {selectedEdge && (
            <div style={{ display: 'grid', gap: 14 }}>
              <div>
                <small>Relationship status</small>
                <h3>{selectedEdge.status || 'Unspecified'}</h3>
              </div>

              <div>
                <small>Relationship type</small>
                <p>{selectedEdge.relationship_type || 'Case link'}</p>
              </div>

              <div>
                <small>Recorded score (not a probability)</small>
                <p>
                  {selectedEdge.score == null
                    ? 'Not available'
                    : selectedEdge.score}
                </p>
              </div>

              <div>
                <small>Tier / scope</small>
                <p>
                  {selectedEdge.tier || 'Not specified'} /{' '}
                  {selectedEdge.scope || 'Not specified'}
                </p>
              </div>

              <div>
                <small>Reasons returned by API</small>
                <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                  {JSON.stringify(selectedEdge.reasons ?? [], null, 2)}
                </pre>
              </div>

              <div>
                <small>Recorded note</small>
                <p>{selectedEdge.note || 'No note recorded.'}</p>
              </div>

              <div>
                <small>Last decision timestamp</small>
                <p>
                  {selectedEdge.decided_at
                    ? String(selectedEdge.decided_at)
                    : 'Not recorded'}
                </p>
              </div>

              <div>
                <strong>
                  {selectedEdge.requires_human_review
                    ? 'Human review required'
                    : 'Recorded as accepted or confirmed'}
                </strong>
              </div>
            </div>
          )}
        </section>
      </div>

      <div className="dashboard-grid two-panels" style={{ marginTop: 18 }}>
        <section className="panel">
          <PanelHead
            icon={FileSearch}
            title="Cases available in the register"
            subtitle={`${cases.items.length} case rows currently loaded`}
          />
          {cases.error ? (
            <ErrorBox message={cases.error} />
          ) : (
            cases.items.slice(0, 5).map((item, index) => (
              <button
                key={item.case_id || index}
                className="case-node"
                onClick={() => onOpenCase(item.case_id)}
              >
                <span className="case-node-icon">
                  <FileSearch size={15} />
                </span>
                <span>
                  <b>{item.case_ref || item.case_id}</b>
                  <small>{item.institution_name_raw || item.category || 'Case'}</small>
                </span>
                <Status value={item.status} />
              </button>
            ))
          )}
        </section>

        <section className="panel">
          <PanelHead
            icon={Building2}
            title="Institution records"
            subtitle={`${institutions.items.length} institution rows currently loaded`}
          />
          <InstitutionsTable
            rows={institutions.items.slice(0, 5)}
            loading={institutions.loading}
            error={institutions.error}
            compact
          />
        </section>
      </div>
    </>
  );
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
