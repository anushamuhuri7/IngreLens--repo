import React, { useEffect, useRef, useState } from 'react';
import { Aperture, ArrowLeft, Camera, Check, ChevronRight, Clock3, Crop, FileImage, History as HistoryIcon, Home, LogOut, Plus, RotateCcw, ShieldCheck, Sparkles, Trash2, Upload, UserRound, X } from 'lucide-react';
import { auth, request, submitScan } from './lib/api';

const initialProfile = { goals: ['Low sodium'], allergies: [], conditions: [], medicines: [], age: '' };
const tagGroups = [
  ['goals', 'Health goals', 'Add a goal, e.g. Low Sodium'],
  ['allergies', 'Allergies & conditions', 'Add allergy or condition'],
  ['medicines', 'Current medicines', 'Add a medicine'],
];

function Brand() {
  return (
    <div className="brand" data-testid="brand-mark">
      <span className="brand-icon"><Aperture size={21} /></span>
      <b>Ingre<span>Lens</span></b>
    </div>
  );
}

function Auth({ onDone }) {
  const [signup, setSignup] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const data = await auth(signup ? '/api/auth/register' : '/api/auth/login', form);
      localStorage.setItem('ingrelens_token', data.token);
      onDone(data.user);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return (
    <main className="auth-shell">
      <div className="auth-pane">
        <Brand />
        <div className="auth-copy">
          <span className="kicker">PERSONAL HEALTH SHIELD</span>
          <h1>{signup ? 'Make every choice feel clearer.' : 'Your health, in focus.'}</h1>
          <p>{signup ? 'Create your private profile to get label insights made for you.' : 'Understand what goes into every food and medicine you bring home.'}</p>
        </div>
        <form onSubmit={submit} className="form" data-testid="auth-form">
          {signup && (
            <label>NAME
              <input data-testid="auth-name-input" required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Your name" />
            </label>
          )}
          <label>EMAIL ADDRESS
            <input data-testid="auth-email-input" required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" />
          </label>
          <label>PASSWORD
            <input data-testid="auth-password-input" required minLength="8" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" />
          </label>
          {error && <p className="error" data-testid="auth-error">{error}</p>}
          <button className="button primary" data-testid="auth-submit-button" disabled={busy}>{busy ? 'Checking…' : signup ? 'Create account' : 'Log in'} <ChevronRight size={18} /></button>
        </form>
        <div className="auth-switch">
          <span>{signup ? 'Already have an account?' : 'New to IngreLens?'}</span>
          <button data-testid="auth-switch-button" onClick={() => setSignup(!signup)}>{signup ? 'Log in' : 'Create an account'} <ArrowLeft size={14} /></button>
        </div>
      </div>
      <div className="auth-art">
        <div className="art-copy">
          <span>SCAN WITH CONFIDENCE</span>
          <strong>Small label.<br />Big clarity.</strong>
          <p>Personalized reading for the everyday decisions that matter.</p>
        </div>
        <div className="art-ring"><Aperture size={100} /></div>
      </div>
    </main>
  );
}

function Nav({ page, go }) {
  const items = [['home', Home, 'Home'], ['scan', Camera, 'Scan'], ['history', Clock3, 'History'], ['profile', UserRound, 'Profile']];
  return (
    <nav className="nav" data-testid="bottom-navigation">
      {items.map(([id, Icon, label]) => (
        <button key={id} className={page === id ? 'active' : ''} data-testid={`nav-${id}-button`} onClick={() => go(id)}>
          <Icon size={20} /><span>{label}</span>
        </button>
      ))}
    </nav>
  );
}

function HomePage({ user, go, startScan, profile }) {
  return (
    <div className="page">
      <header className="topbar"><Brand /><button className="avatar" data-testid="home-profile-button" onClick={() => go('profile')}>{(user.name || 'I')[0]}</button></header>
      <section className="welcome">
        <span className="kicker">● PERSONAL SHIELD ACTIVE</span>
        <h1>Hello, {user.name || 'there'}</h1>
        <p>Make your next choice with a little more clarity.</p>
      </section>
      <section className="insights">
        <div className="section-head"><h2>Health news & AI insights</h2><span><Sparkles size={14} /> Tailored to you</span></div>
        <div className="news-grid">
          <article className="news-card"><div className="news-photo photo-one" /><div><span className="kicker">AI INSIGHT</span><h3>Hidden sodium: decoding labels for everyday care</h3><button data-testid="news-read-more-button">Read more <ChevronRight size={14} /></button></div></article>
          <article className="news-card"><div className="news-photo photo-two" /><div><span className="kicker">NUTRITION</span><h3>Spotting ultra-processed foods in seconds</h3><button data-testid="news-second-read-more-button">Read more <ChevronRight size={14} /></button></div></article>
        </div>
      </section>
      <section>
        <div className="section-head"><h2>Quick scan</h2><span>{profile.allergies.length} profile filters</span></div>
        <div className="scan-options">
          <button data-testid="quick-scan-medicine-button" onClick={() => startScan('MEDICINE')}><span className="option-icon medicine"><ShieldCheck /></span><b>Scan medicine</b><small>Check directions & safety</small><ChevronRight /></button>
          <button data-testid="quick-scan-food-button" onClick={() => startScan('FOOD')}><span className="option-icon food"><Sparkles /></span><b>Scan food</b><small>Evaluate ingredients & risk</small><ChevronRight /></button>
        </div>
      </section>
      <section className="shield-note">
        <ShieldCheck size={20} />
        <div><b>Your profile is shaping every result</b><p>{profile.goals.length ? `Goal: ${profile.goals.join(', ')}` : 'Add health goals to personalize your shield.'}</p></div>
        <button data-testid="edit-profile-from-home-button" onClick={() => go('profile')}><ChevronRight /></button>
      </section>
    </div>
  );
}

function CropEditor({ src, onCancel, onDone }) {
  const containerRef = useRef(null);
  const imgRef = useRef(null);
  const [layout, setLayout] = useState({ w: 320, h: 240, natW: 1, natH: 1 });
  const [box, setBox] = useState({ x: 0.1, y: 0.2, w: 0.8, h: 0.6 });
  const drag = useRef(null);

  function onImageLoad() {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container) return;
    const rect = container.getBoundingClientRect();
    setLayout({ w: rect.width, h: rect.height, natW: img.naturalWidth, natH: img.naturalHeight });
  }

  function pointer(e) {
    const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX, y: t.clientY };
  }

  function start(mode) {
    return (e) => {
      e.preventDefault();
      const p = pointer(e);
      drag.current = { mode, start: p, box: { ...box } };
      window.addEventListener('mousemove', move); window.addEventListener('mouseup', end);
      window.addEventListener('touchmove', move, { passive: false }); window.addEventListener('touchend', end);
    };
  }

  function move(e) {
    if (!drag.current) return;
    e.preventDefault?.();
    const p = pointer(e);
    const dx = (p.x - drag.current.start.x) / layout.w;
    const dy = (p.y - drag.current.start.y) / layout.h;
    const { mode, box: b } = drag.current;
    let next = { ...b };
    if (mode === 'move') {
      next.x = Math.min(Math.max(0, b.x + dx), 1 - b.w);
      next.y = Math.min(Math.max(0, b.y + dy), 1 - b.h);
    } else if (mode === 'br') {
      next.w = Math.min(Math.max(0.15, b.w + dx), 1 - b.x);
      next.h = Math.min(Math.max(0.15, b.h + dy), 1 - b.y);
    } else if (mode === 'tl') {
      const nw = Math.min(Math.max(0.15, b.w - dx), b.x + b.w);
      const nh = Math.min(Math.max(0.15, b.h - dy), b.y + b.h);
      next = { x: b.x + b.w - nw, y: b.y + b.h - nh, w: nw, h: nh };
    }
    setBox(next);
  }

  function end() {
    drag.current = null;
    window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', end);
    window.removeEventListener('touchmove', move); window.removeEventListener('touchend', end);
  }

  function reset() { setBox({ x: 0.1, y: 0.2, w: 0.8, h: 0.6 }); }

  function apply() {
    const img = imgRef.current; if (!img) return;
    const cx = Math.round(box.x * img.naturalWidth);
    const cy = Math.round(box.y * img.naturalHeight);
    const cw = Math.round(box.w * img.naturalWidth);
    const ch = Math.round(box.h * img.naturalHeight);
    const canvas = document.createElement('canvas'); canvas.width = cw; canvas.height = ch;
    canvas.getContext('2d').drawImage(img, cx, cy, cw, ch, 0, 0, cw, ch);
    canvas.toBlob(blob => {
      if (!blob) return;
      const file = new File([blob], 'cropped-label.jpg', { type: 'image/jpeg' });
      onDone(file, URL.createObjectURL(blob));
    }, 'image/jpeg', 0.92);
  }

  return (
    <div className="crop-overlay" data-testid="crop-editor">
      <header>
        <button data-testid="crop-cancel-button" onClick={onCancel}><X /></button>
        <span>ADJUST CROP</span>
        <button data-testid="crop-reset-button" onClick={reset}><RotateCcw size={18} /></button>
      </header>
      <div className="crop-stage" ref={containerRef}>
        <img ref={imgRef} src={src} onLoad={onImageLoad} alt="Label to crop" draggable={false} />
        <div
          className="crop-box"
          style={{ left: `${box.x * 100}%`, top: `${box.y * 100}%`, width: `${box.w * 100}%`, height: `${box.h * 100}%` }}
          onMouseDown={start('move')} onTouchStart={start('move')}
          data-testid="crop-box"
        >
          <span className="crop-handle tl" onMouseDown={start('tl')} onTouchStart={start('tl')} data-testid="crop-handle-tl" />
          <span className="crop-handle br" onMouseDown={start('br')} onTouchStart={start('br')} data-testid="crop-handle-br" />
        </div>
      </div>
      <div className="crop-actions">
        <button data-testid="crop-apply-button" className="button primary" onClick={apply}><Check size={17} /> Use crop</button>
        <p>Drag the box or its corners to keep only the ingredient list.</p>
      </div>
    </div>
  );
}

function ScanPage({ mode, go, onResult }) {
  const [camera, setCamera] = useState(false);
  const [stream, setStream] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [text, setText] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [cropping, setCropping] = useState(false);
  const video = useRef(null);
  const input = useRef(null);
  useEffect(() => () => stream?.getTracks().forEach(t => t.stop()), [stream]);

  async function openCamera() {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      setStream(s); setCamera(true);
      setTimeout(() => { if (video.current) video.current.srcObject = s; }, 50);
    } catch {
      setError('Camera access is unavailable. Upload a clear label photo instead.');
    }
  }

  function capture() {
    const canvas = document.createElement('canvas');
    canvas.width = video.current.videoWidth;
    canvas.height = video.current.videoHeight;
    canvas.getContext('2d').drawImage(video.current, 0, 0);
    canvas.toBlob(blob => {
      const next = new File([blob], 'camera-label.jpg', { type: 'image/jpeg' });
      setFile(next); setPreview(URL.createObjectURL(next));
      setCamera(false); stream?.getTracks().forEach(t => t.stop());
    }, 'image/jpeg', 0.9);
  }

  function pickFile(e) {
    const next = e.target.files?.[0];
    if (!next) return;
    setFile(next); setPreview(URL.createObjectURL(next));
    setCamera(false); stream?.getTracks().forEach(t => t.stop());
  }

  async function analyze(e) {
    e.preventDefault();
    if (!file && !text.trim()) return;
    setBusy(true); setError('');
    try {
      onResult(await submitScan({ file, text, productName: name || (mode === 'FOOD' ? 'Food label' : 'Medicine label'), mode }));
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  if (cropping && preview) {
    return <CropEditor src={preview} onCancel={() => setCropping(false)} onDone={(nextFile, nextPreview) => { setFile(nextFile); setPreview(nextPreview); setCropping(false); }} />;
  }

  if (camera) {
    return (
      <div className="camera-screen">
        <header>
          <button data-testid="camera-close-button" onClick={() => { setCamera(false); stream?.getTracks().forEach(t => t.stop()); }}><X /></button>
          <span>{mode} SCAN MODE</span>
          <span />
        </header>
        <div className="camera-body">
          <video ref={video} autoPlay playsInline data-testid="camera-video" />
          <div className="guide"><i /><i /><i /><i /><span>Align label within guide</span></div>
        </div>
        <div className="camera-controls">
          <button className="shutter" data-testid="camera-capture-button" onClick={capture}><Camera /></button>
          <button className="camera-upload" data-testid="camera-upload-button" onClick={() => input.current?.click()}><Upload size={16} /> Use a photo instead</button>
          <input ref={input} hidden type="file" accept="image/*" onChange={pickFile} />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="subbar">
        <button data-testid="scan-back-button" onClick={() => go('home')}><ArrowLeft /> Back</button>
        <span className="mode-pill">{mode === 'FOOD' ? 'Food scan' : 'Medicine scan'}</span>
      </header>
      <div className="scan-title">
        <span className={`option-icon ${mode === 'FOOD' ? 'food' : 'medicine'}`}>{mode === 'FOOD' ? <Sparkles /> : <ShieldCheck />}</span>
        <span className="kicker">{mode} SCAN MODE</span>
        <h1>What are you checking?</h1>
        <p>Capture a label or paste its text for a personalized safety report.</p>
      </div>
      <form className="form scan-form" onSubmit={analyze}>
        <label>PRODUCT NAME
          <input data-testid="scan-product-name-input" value={name} onChange={e => setName(e.target.value)} placeholder={mode === 'FOOD' ? 'e.g. Harvest Oat Granola' : 'e.g. Paracetamol 500 mg'} />
        </label>
        <button type="button" className="camera-cta" data-testid="open-camera-button" onClick={openCamera}>
          <Camera />
          <span><b>Open camera</b><small>Live capture with label guide</small></span>
          <ChevronRight />
        </button>
        {file && (
          <div className="capture-preview" data-testid="capture-preview">
            <img src={preview} alt="Captured label preview" />
            <div><b>Label ready</b><small>{file.name}</small></div>
            <button type="button" data-testid="retake-label-button" onClick={openCamera}>Retake</button>
            <button type="button" data-testid="crop-label-button" onClick={() => setCropping(true)}><Crop size={12} /> Crop</button>
          </div>
        )}
        <label className="dropzone">
          <input data-testid="scan-file-input" type="file" accept="image/*" onChange={pickFile} />
          <FileImage size={24} />
          <b>{file ? file.name : 'Upload a label photo'}</b>
          <small>JPG, PNG or WEBP</small>
        </label>
        <div className="or"><span>OR PASTE LABEL TEXT</span></div>
        <textarea data-testid="scan-text-input" value={text} onChange={e => setText(e.target.value)} placeholder={mode === 'FOOD' ? 'Ingredients: oats, sugar, sodium…' : 'Active ingredient, dosage, directions…'} rows="5" />
        {error && <p className="error" data-testid="scan-error">{error}</p>}
        <button className="button primary" data-testid="analyze-label-button" disabled={busy || (!file && !text.trim())}>{busy ? 'Analyzing label…' : 'Analyze label'} <Sparkles size={17} /></button>
      </form>
    </div>
  );
}

function Results({ result, go }) {
  const score = Number(result.safety_score || 0);
  const color = score >= 8 ? 'good' : score >= 5 ? 'warn' : 'bad';
  return (
    <div className="page">
      <header className="subbar"><button data-testid="results-back-button" onClick={() => go('home')}><ArrowLeft /> Back</button><span className="kicker">ANALYSIS REPORT</span></header>
      <section className="result-hero">
        <span className="kicker">{result.type} LABEL</span>
        <h1>{result.product_name}</h1>
        <div className={`score ${color}`} data-testid="safety-score"><strong>{score.toFixed(1)}</strong><span>/10<br />{result.overall_verdict}</span></div>
        <div className="meter"><i style={{ width: `${score * 10}%` }} /></div>
        <div className="meter-labels"><span>Needs care</span><span>Safer choice</span></div>
      </section>
      <section className="ai-summary" data-testid="ai-assessment">
        <Sparkles size={17} />
        <div><b>AI health assessment</b><p>{result.summary_ai}</p></div>
      </section>
      {result.profile_match?.length > 0 && (
        <div className="match-alert" data-testid="profile-match-alert">
          <ShieldCheck size={18} />
          <span><b>Profile match found</b><br />{result.profile_match.join(', ')} appears in this label.</span>
        </div>
      )}
      <section>
        <div className="section-head"><h2>Detailed breakdown</h2><span>{result.total_ingredients} items</span></div>
        <div className="ingredient-list">
          {result.ingredients?.map((item, i) => (
            <div className="ingredient" key={`${item.name}-${i}`} data-testid={`ingredient-result-${i}`}>
              <span className={`status ${item.risk_level === 'Safe' ? 'safe' : 'risk'}`}>{item.risk_level === 'Safe' ? <Check size={14} /> : <X size={14} />}</span>
              <div><b>{item.name}</b><p>{item.description}</p></div>
              <em>{item.risk_level}</em>
            </div>
          ))}
        </div>
      </section>
      {result.recommendations?.length > 0 && (
        <section className="recommendations" data-testid="recommendations">
          <div className="section-head"><h2>Personalised tips</h2><span>{result.recommendations.length}</span></div>
          <ul>{result.recommendations.map((rec, i) => <li key={i} data-testid={`recommendation-${i}`}><Check size={13} /> {rec}</li>)}</ul>
        </section>
      )}
      {result.medicine_notice && <p className="disclaimer" data-testid="medicine-disclaimer">{result.medicine_notice} This information is educational and does not replace professional advice.</p>}
      <button className="button primary" data-testid="save-result-button" onClick={() => go('history')}>View saved history <Clock3 size={17} /></button>
    </div>
  );
}

function Profile({ profile, setProfile, user, logout }) {
  const [draft, setDraft] = useState(profile);
  const [entry, setEntry] = useState({});
  const [saved, setSaved] = useState(false);
  function add(key) {
    if (!entry[key]?.trim()) return;
    setDraft({ ...draft, [key]: [...draft[key], entry[key].trim()] });
    setEntry({ ...entry, [key]: '' });
  }
  async function save() {
    await request('/api/profile', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft) });
    setProfile(draft); setSaved(true); setTimeout(() => setSaved(false), 1800);
  }
  return (
    <div className="page">
      <header className="subbar"><span /><span className="kicker">PROFILE SETTINGS</span></header>
      <section className="profile-head">
        <div className="avatar large">{(user.name || 'I')[0]}</div>
        <div><h1>My health profile</h1><p>Profile active · Health shield enabled</p></div>
      </section>
      <section className="profile-section">
        <h2>Personal details</h2>
        <label>NAME<input data-testid="profile-name-input" value={user.name} readOnly /></label>
        <label>AGE<input data-testid="profile-age-input" value={draft.age} onChange={e => setDraft({ ...draft, age: e.target.value })} placeholder="Your age" /></label>
      </section>
      {tagGroups.map(([key, title, placeholder]) => (
        <section className="profile-section" key={key}>
          <h2>{title}</h2>
          <div className="tag-list">{draft[key].map(tag => <span key={tag} data-testid={`profile-tag-${key}`}>{tag}<button data-testid={`remove-${key}-${tag}`} onClick={() => setDraft({ ...draft, [key]: draft[key].filter(x => x !== tag) })}><X size={12} /></button></span>)}</div>
          <div className="add-row"><input data-testid={`profile-${key}-input`} value={entry[key] || ''} onChange={e => setEntry({ ...entry, [key]: e.target.value })} placeholder={placeholder} /><button data-testid={`profile-${key}-add-button`} onClick={() => add(key)}><Plus size={16} /> Add</button></div>
        </section>
      ))}
      {saved && <p className="saved" data-testid="profile-saved-message"><Check size={15} /> Changes saved</p>}
      <button className="button primary" data-testid="save-profile-button" onClick={save}>Save changes <Check size={17} /></button>
      <button className="logout" data-testid="logout-button" onClick={logout}><LogOut size={16} /> Log out</button>
    </div>
  );
}

function History({ go, history, clear }) {
  const [query, setQuery] = useState('');
  const [confirm, setConfirm] = useState(false);
  const items = history.filter(x => (x.product_name || '').toLowerCase().includes(query.toLowerCase()));
  return (
    <div className="page">
      <header className="subbar"><h1>Scan history</h1><button className="danger-link" data-testid="delete-history-button" onClick={() => setConfirm(true)}><Trash2 size={15} /> Delete all</button></header>
      <input className="search" data-testid="history-search-input" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search past scans…" />
      {items.length ? (
        <div className="history-list">
          {items.map((item, i) => (
            <button key={item.id || i} data-testid={`history-item-${i}`} onClick={() => go('results', item)}>
              <span className="history-icon">{item.type === 'MEDICINE' ? <ShieldCheck /> : <Sparkles />}</span>
              <span><b>{item.product_name}</b><small>{item.type} · {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Just now'}</small></span>
              <strong>{Number(item.safety_score).toFixed(1)}<small>/10</small></strong>
            </button>
          ))}
        </div>
      ) : (
        <div className="empty">
          <HistoryIcon size={30} />
          <h2>No scans yet</h2>
          <p>Your scanned food and medicines will appear here.</p>
          <button className="button primary" data-testid="empty-history-scan-button" onClick={() => go('scan')}>Start a scan</button>
        </div>
      )}
      {confirm && (
        <div className="modal" data-testid="delete-history-modal">
          <div>
            <button className="modal-close" data-testid="close-delete-modal-button" onClick={() => setConfirm(false)}><X /></button>
            <Trash2 />
            <h2>Delete all scan history?</h2>
            <p>This action cannot be undone.</p>
            <div>
              <button className="button" data-testid="cancel-delete-button" onClick={() => setConfirm(false)}>Cancel</button>
              <button className="button danger" data-testid="confirm-delete-button" onClick={() => { clear(); setConfirm(false); }}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('home');
  const [mode, setMode] = useState('FOOD');
  const [result, setResult] = useState(null);
  const [profile, setProfile] = useState(initialProfile);
  const [history, setHistory] = useState([]);
  useEffect(() => {
    if (!localStorage.getItem('ingrelens_token')) return;
    Promise.all([request('/api/auth/me'), request('/api/profile'), request('/api/history')])
      .then(([u, p, h]) => { setUser(u); setProfile({ ...initialProfile, ...(p || {}) }); setHistory(h || []); })
      .catch(() => localStorage.removeItem('ingrelens_token'));
  }, []);
  function go(next, data) { if (data) setResult(data); setPage(next); }
  function startScan(next) { setMode(next); setPage('scan'); }
  function logout() { localStorage.removeItem('ingrelens_token'); setUser(null); }
  if (!user) return <Auth onDone={setUser} />;
  return (
    <div className="app-shell">
      {page === 'home' && <HomePage user={user} go={go} startScan={startScan} profile={profile} />}
      {page === 'scan' && <ScanPage mode={mode} go={go} onResult={data => { setResult(data); setHistory([data, ...history]); setPage('results'); }} />}
      {page === 'results' && result && <Results result={result} go={go} />}
      {page === 'history' && <History go={go} history={history} clear={async () => { await request('/api/history', { method: 'DELETE' }); setHistory([]); }} />}
      {page === 'profile' && <Profile profile={profile} setProfile={setProfile} user={user} logout={logout} />}
      {['home', 'history', 'profile'].includes(page) && <Nav page={page} go={go} />}
    </div>
  );
}
