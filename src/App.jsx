import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Aperture, ArrowLeft, Camera, Check, ChevronLeft, ChevronRight, Clock3, Crop, ExternalLink, FileImage, History as HistoryIcon, Home, ImagePlus, LogOut, Plus, RotateCcw, ScanBarcode, ShieldCheck, Sparkles, Trash2, Upload, UserRound, X } from 'lucide-react';
import BarcodeScanner from './components/BarcodeScanner';
import { auth, request, submitScan } from './lib/api';

const initialProfile = { goals: ['Low sodium'], allergies: [], conditions: [], medicines: [], age: '', avatar: '' };
const tagGroups = [
  ['goals', 'Health goals', 'Add a goal, e.g. Low Sodium'],
  ['allergies', 'Allergies & conditions', 'Add allergy or condition'],
  ['medicines', 'Current medicines', 'Add a medicine'],
];

const NEWS_ARTICLES = [
  { kicker: 'AI INSIGHT', title: 'Hidden sodium: decoding food labels for everyday care', photo: 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=600&q=80', href: 'https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/sodium/sodium-and-salt' },
  { kicker: 'NUTRITION', title: 'Spotting ultra-processed foods in seconds', photo: 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80', href: 'https://www.hsph.harvard.edu/nutritionsource/processed-foods/' },
  { kicker: 'MEDICINE', title: 'Reading prescription labels the right way', photo: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=600&q=80', href: 'https://www.fda.gov/drugs/drug-information-consumers/understanding-over-counter-medicines' },
  { kicker: 'ALLERGIES', title: 'The 9 major food allergens now on every U.S. label', photo: 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=600&q=80', href: 'https://www.fda.gov/food/food-labeling-nutrition/food-allergies' },
  { kicker: 'INTERACTIONS', title: 'Grapefruit, greens & meds — what to eat with care', photo: 'https://images.unsplash.com/photo-1615486364155-6f9f10b6a1f8?auto=format&fit=crop&w=600&q=80', href: 'https://www.mayoclinic.org/healthy-lifestyle/consumer-health/expert-answers/food-and-nutrition/faq-20058586' },
  { kicker: 'SUGAR', title: 'Added sugar vs. natural sugar — how to tell them apart', photo: 'https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80', href: 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet' },
];

function Brand() {
  return (
    <div className="brand" data-testid="brand-mark">
      <span className="brand-icon"><Aperture size={21} /></span>
      <b>Ingre<span>Lens</span></b>
    </div>
  );
}

function Avatar({ user, profile, size = 'sm', ...rest }) {
  const initial = (user?.name || 'I').trim()[0]?.toUpperCase() || 'I';
  const src = profile?.avatar;
  const cls = size === 'lg' ? 'avatar large' : 'avatar';
  if (src) return <button className={`${cls} has-photo`} {...rest}><img src={src} alt="Profile" /></button>;
  return <button className={cls} {...rest}>{initial}</button>;
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

function NewsCarousel() {
  const trackRef = useRef(null);
  const [index, setIndex] = useState(0);
  function scrollTo(i) {
    const track = trackRef.current; if (!track) return;
    const card = track.children[i]; if (!card) return;
    track.scrollTo({ left: card.offsetLeft - track.offsetLeft, behavior: 'smooth' });
    setIndex(i);
  }
  function onScroll() {
    const track = trackRef.current; if (!track) return;
    const nearest = Array.from(track.children).findIndex(c => c.offsetLeft - track.offsetLeft >= track.scrollLeft - 8);
    if (nearest >= 0 && nearest !== index) setIndex(nearest);
  }
  return (
    <section className="news-section">
      <div className="section-head">
        <h2>Health news & AI insights</h2>
        <span><Sparkles size={14} /> Tailored to you</span>
      </div>
      <div className="news-track" ref={trackRef} onScroll={onScroll} data-testid="news-carousel">
        {NEWS_ARTICLES.map((article, i) => (
          <a
            key={article.href}
            className="news-slide"
            href={article.href}
            target="_blank"
            rel="noopener noreferrer"
            data-testid={`news-slide-${i}`}
          >
            <div className="news-photo" style={{ backgroundImage: `url(${article.photo})` }} />
            <div className="news-body">
              <span className="kicker">{article.kicker}</span>
              <h3>{article.title}</h3>
              <span className="news-cta" data-testid={`news-cta-${i}`}>Read article <ExternalLink size={12} /></span>
            </div>
          </a>
        ))}
      </div>
      <div className="news-controls">
        <button data-testid="news-prev-button" onClick={() => scrollTo(Math.max(0, index - 1))} aria-label="Previous article"><ChevronLeft size={16} /></button>
        <div className="news-dots" data-testid="news-dots">
          {NEWS_ARTICLES.map((_, i) => (
            <button key={i} className={i === index ? 'active' : ''} data-testid={`news-dot-${i}`} onClick={() => scrollTo(i)} aria-label={`Go to article ${i + 1}`} />
          ))}
        </div>
        <button data-testid="news-next-button" onClick={() => scrollTo(Math.min(NEWS_ARTICLES.length - 1, index + 1))} aria-label="Next article"><ChevronRight size={16} /></button>
      </div>
    </section>
  );
}

function HomePage({ user, go, startScan, profile }) {
  return (
    <div className="page">
      <header className="topbar">
        <Brand />
        <Avatar user={user} profile={profile} data-testid="home-profile-button" onClick={() => go('profile')} />
      </header>
      <section className="welcome">
        <span className="kicker">● PERSONAL SHIELD ACTIVE</span>
        <h1>Hello, {user.name || 'there'}</h1>
        <p>Make your next choice with a little more clarity.</p>
      </section>
      <NewsCarousel />
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
  const [layout, setLayout] = useState({ w: 320, h: 240 });
  const [box, setBox] = useState({ x: 0.1, y: 0.2, w: 0.8, h: 0.6 });
  const drag = useRef(null);
  function onImageLoad() {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    setLayout({ w: rect.width, h: rect.height });
  }
  function pointer(e) { const t = e.touches ? e.touches[0] : e; return { x: t.clientX, y: t.clientY }; }
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
        <div className="crop-box" style={{ left: `${box.x * 100}%`, top: `${box.y * 100}%`, width: `${box.w * 100}%`, height: `${box.h * 100}%` }} onMouseDown={start('move')} onTouchStart={start('move')} data-testid="crop-box">
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
  const [barcode, setBarcode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [cropping, setCropping] = useState(false);
  const [scanningBarcode, setScanningBarcode] = useState(false);
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
  async function onBarcodeDetected(code) {
    setScanningBarcode(false);
    setBarcode(code);
    setNotice(`Barcode ${code} captured — looking it up…`);
    try {
      const info = await request(`/api/barcode/${encodeURIComponent(code)}?mode=${encodeURIComponent(mode)}`);
      if (info.product_name && !name) setName(info.product_name);
      if (info.ingredients_text) setText(t => (t ? t : info.ingredients_text));
      setNotice(`Found "${info.product_name}" via ${info.source === 'openfoodfacts' ? 'Open Food Facts' : 'OpenFDA'}. Tap Analyze to get your personal report.`);
    } catch (err) {
      setNotice('');
      setError(err.message || "We couldn't find that barcode. Try scanning the label instead.");
    }
  }
  async function analyze(e) {
    e.preventDefault();
    if (!file && !text.trim() && !barcode) return;
    setBusy(true); setError(''); setNotice('');
    try {
      onResult(await submitScan({ file, text, productName: name || (mode === 'FOOD' ? 'Food label' : 'Medicine label'), mode, barcode }));
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  if (scanningBarcode) {
    return <BarcodeScanner onDetected={onBarcodeDetected} onCancel={() => setScanningBarcode(false)} />;
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
        <p>Capture a label, scan the barcode, or paste the text — we'll compare it with your profile.</p>
      </div>
      <form className="form scan-form" onSubmit={analyze}>
        <label>PRODUCT NAME
          <input data-testid="scan-product-name-input" value={name} onChange={e => setName(e.target.value)} placeholder={mode === 'FOOD' ? 'e.g. Harvest Oat Granola' : 'e.g. Paracetamol 500 mg'} />
        </label>
        <div className="scan-inputs">
          <button type="button" className="camera-cta" data-testid="open-camera-button" onClick={openCamera}>
            <Camera />
            <span><b>Open camera</b><small>Capture label for OCR</small></span>
            <ChevronRight />
          </button>
          <button type="button" className="camera-cta" data-testid="open-barcode-button" onClick={() => { setError(''); setScanningBarcode(true); }}>
            <ScanBarcode />
            <span><b>Scan barcode</b><small>Auto-fill from open catalog</small></span>
            <ChevronRight />
          </button>
        </div>
        {barcode && (
          <div className="barcode-chip" data-testid="barcode-chip">
            <ScanBarcode size={13} /> {barcode}
            <button type="button" onClick={() => { setBarcode(''); setNotice(''); }} data-testid="barcode-clear-button"><X size={11} /></button>
          </div>
        )}
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
        <div className="or"><span>OR PASTE / EDIT LABEL TEXT</span></div>
        <textarea data-testid="scan-text-input" value={text} onChange={e => setText(e.target.value)} placeholder={mode === 'FOOD' ? 'Ingredients: oats, sugar, sodium…' : 'Active ingredient, dosage, directions…'} rows="5" />
        {notice && <p className="notice" data-testid="scan-notice">{notice}</p>}
        {error && <p className="error" data-testid="scan-error">{error}</p>}
        <button className="button primary" data-testid="analyze-label-button" disabled={busy || (!file && !text.trim() && !barcode)}>{busy ? 'Analyzing label…' : 'Analyze label'} <Sparkles size={17} /></button>
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
        {result.barcode?.image_url && <img className="result-photo" src={result.barcode.image_url} alt={result.product_name} data-testid="result-photo" />}
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
      {result.extracted_text && (
        <details className="extracted-text" data-testid="extracted-text-panel">
          <summary>View extracted label text</summary>
          <pre data-testid="extracted-text">{result.extracted_text}</pre>
        </details>
      )}
      {result.medicine_notice && <p className="disclaimer" data-testid="medicine-disclaimer">{result.medicine_notice} This information is educational and does not replace professional advice.</p>}
      <button className="button primary" data-testid="save-result-button" onClick={() => go('history')}>View saved history <Clock3 size={17} /></button>
    </div>
  );
}

function resizeAvatar(file) {
  return new Promise((resolve, reject) => {
    if (!file) return reject(new Error('No file selected'));
    if (!file.type.startsWith('image/')) return reject(new Error('Please pick an image file'));
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const size = 320;
        const canvas = document.createElement('canvas');
        canvas.width = size; canvas.height = size;
        const ctx = canvas.getContext('2d');
        const min = Math.min(img.width, img.height);
        const sx = (img.width - min) / 2;
        const sy = (img.height - min) / 2;
        ctx.drawImage(img, sx, sy, min, min, 0, 0, size, size);
        resolve(canvas.toDataURL('image/jpeg', 0.85));
      };
      img.onerror = () => reject(new Error('Could not read the image'));
      img.src = reader.result;
    };
    reader.onerror = () => reject(new Error('Could not read the file'));
    reader.readAsDataURL(file);
  });
}

function Profile({ profile, setProfile, user, logout }) {
  const [draft, setDraft] = useState(profile);
  const [entry, setEntry] = useState({});
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef(null);
  useEffect(() => { setDraft(profile); }, [profile]);
  function add(key) {
    if (!entry[key]?.trim()) return;
    setDraft({ ...draft, [key]: [...draft[key], entry[key].trim()] });
    setEntry({ ...entry, [key]: '' });
  }
  async function pickAvatar(e) {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file) return;
    try {
      const dataUrl = await resizeAvatar(file);
      setDraft(d => ({ ...d, avatar: dataUrl }));
      setError('');
    } catch (err) { setError(err.message); }
  }
  async function save() {
    setError('');
    try {
      await request('/api/profile', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft) });
      setProfile(draft); setSaved(true); setTimeout(() => setSaved(false), 1800);
    } catch (err) { setError(err.message); }
  }
  return (
    <div className="page">
      <header className="subbar"><span /><span className="kicker">PROFILE SETTINGS</span></header>
      <section className="profile-head">
        <div className="avatar large avatar-editable">
          {draft.avatar ? <img src={draft.avatar} alt="Profile" data-testid="profile-avatar-preview" /> : (user.name || 'I')[0]}
          <button type="button" className="avatar-edit" data-testid="upload-avatar-button" onClick={() => fileRef.current?.click()} aria-label="Change profile photo"><ImagePlus size={14} /></button>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={pickAvatar} data-testid="avatar-file-input" />
        </div>
        <div>
          <h1>My health profile</h1>
          <p>Profile active · Health shield enabled</p>
          {draft.avatar && <button type="button" className="avatar-remove" data-testid="remove-avatar-button" onClick={() => setDraft({ ...draft, avatar: '' })}>Remove photo</button>}
        </div>
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
      {error && <p className="error" data-testid="profile-error">{error}</p>}
      {saved && <p className="saved" data-testid="profile-saved-message"><Check size={15} /> Changes saved</p>}
      <button className="button primary" data-testid="save-profile-button" onClick={save}>Save changes <Check size={17} /></button>
      <button className="logout" data-testid="logout-button" onClick={logout}><LogOut size={16} /> Log out</button>
    </div>
  );
}

function History({ go, history, clear }) {
  const [query, setQuery] = useState('');
  const [confirm, setConfirm] = useState(false);
  const items = useMemo(() => history.filter(x => (x.product_name || '').toLowerCase().includes(query.toLowerCase())), [history, query]);
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
