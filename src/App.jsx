import React, { useState } from 'react';
import { 
  ArrowLeft, ArrowRight, Aperture, Camera, Check, Clock, Home, ImagePlus, LogOut,
  Upload, ShieldCheck, Sparkles, Sliders, Search, RefreshCw, User, X
} from 'lucide-react';
import { analyzeIngredients } from './lib/api';

function ReferenceNav({ active, onChange }) {
  const items = [['home', 'Home', Home], ['scan', 'Scan', Camera], ['profile', 'Profile', User], ['history', 'History', Clock]];
  return <nav className="bottom-nav">{items.map(([id, label, Icon]) => <button key={id} className={`nav-item ${active === id ? 'active' : ''}`} onClick={() => onChange(id)}><Icon size={22} /><span>{label}</span></button>)}</nav>;
}

function ReferenceAuth({ signUp, onSubmit, onSwitch }) {
  const [name, setName] = useState('');
  return <div className="auth-container"><div className="auth-header"><img src="/assets/Your_paragraph_text-removebg-preview.png" alt="IngreLens Logo" className="h-11 w-auto" /><h1>{signUp ? 'Build your health shield.' : 'Your health, in focus.'}</h1><p>{signUp ? 'Personalized insights start with you.' : 'Understand what goes into every product.'}</p></div><form className="auth-form" onSubmit={(event) => { event.preventDefault(); onSubmit(name || 'Anusha'); }}><div className="form-group">{signUp && <><label>Your name</label><input className="input-underline" required value={name} onChange={(event) => setName(event.target.value)} /></>}<label>Email address</label><input className="input-underline" type="email" required placeholder="you@example.com" /><label>Password</label><input className="input-underline" type="password" required /></div><button className="btn-primary">{signUp ? 'Get started' : 'Log in'} <ArrowRight size={18} /></button></form><div className="auth-actions"><span className="text-muted">{signUp ? 'Already have an account?' : 'New to IngreLens?'}</span><button className="btn-secondary" type="button" onClick={onSwitch}>{signUp ? 'Log in' : 'Create an account'} <ArrowRight size={16} /></button></div></div>;
}

function ReferenceHome({ name, onScan, onChange }) {
  return <div className="screen"><div className="home-greeting"><div><div className="eyebrow">Personal Shield Active</div><h1>Hello, {name}</h1></div><button className="avatar-badge" onClick={() => onChange('profile')}>{name[0]}</button></div><div className="news-carousel-container"><div className="news-heading"><h2>Health News &amp; AI Insights</h2><span><Sparkles size={14} /> Tailored to your profile</span></div><div className="news-carousel"><article className="news-card"><div className="news-card-image news-image-one" /><div className="news-card-body"><span className="eyebrow">AI Insight</span><div className="news-card-title">Hidden Sodium: Decoding Labels for Diabetic &amp; Hypertensive Care</div><button className="read-more">Read More <ArrowRight size={15} /></button></div></article><article className="news-card"><div className="news-card-image news-image-two" /><div className="news-card-body"><span className="eyebrow">Nutrition</span><div className="news-card-title">Spotting Ultra-Processed Foods: 5 Red Flag Ingredients to Avoid</div><button className="read-more">Read More <ArrowRight size={15} /></button></div></article></div></div><div className="page-header"><h1>Quick Scan</h1></div><div className="quick-scan-grid"><button className="scan-action-card" onClick={() => onScan('MEDICINE')}><span className="scan-card-icon medicine"><ShieldCheck /></span><span>Medicine</span><small>Check expiry &amp; safety</small></button><button className="scan-action-card" onClick={() => onScan('FOOD')}><span className="scan-card-icon food"><Sparkles /></span><span>Food &amp; ingredients</span><small>Know what you eat</small></button></div><div className="page-header"><h1>Recent Activity</h1><button className="btn-secondary" onClick={() => onChange('history')}>View history <ArrowRight size={15} /></button></div><div className="activity-item"><div className="activity-info"><div className="activity-icon bg-green"><Check size={18} /></div><div className="activity-details"><h4>Your health shield is ready</h4><p>Scan a product to get started</p></div></div><span className="score-tag green">New</span></div></div>;
}

function ReferenceScan({ mode, onBack, onResult }) {
  const [text, setText] = useState(''); const [productName, setProductName] = useState(''); const [file, setFile] = useState(null); const [loading, setLoading] = useState(false);
  const submit = async (event) => { event.preventDefault(); if (!text && !file) return; setLoading(true); try { onResult(await analyzeIngredients({ text, file, productName, profile: { allergies: ['paraben', 'fragrance'], skin_type: 'Sensitive', is_pregnant: false } })); } catch (error) { window.alert(error.message); } finally { setLoading(false); } };
  return <div className="screen"><div className="page-header"><button className="btn-secondary" onClick={onBack}><ArrowLeft size={18} /> Back</button><span className="mode-badge">{mode}</span></div><div className="scan-intro"><span className="scan-card-icon medicine"><Aperture /></span><h1>What are you checking?</h1><p>Upload a label or paste the ingredients to get a personalized safety report.</p></div><form className="auth-form" onSubmit={submit}><input className="input-underline" placeholder="Product name" value={productName} onChange={(event) => setProductName(event.target.value)} /><label className="upload-box"><input type="file" accept="image/*" onChange={(event) => setFile(event.target.files?.[0] || null)} /><ImagePlus size={28} /><strong>{file ? file.name : 'Upload a label photo'}</strong><small>Tap to choose an image</small></label><textarea className="text-area" rows="6" placeholder="Or paste the ingredient list here..." value={text} onChange={(event) => setText(event.target.value)} /><button className="btn-primary" disabled={loading || (!text && !file)}>{loading ? 'Analyzing...' : 'Analyze product'} <Sparkles size={18} /></button></form></div>;
}

function ReferenceResults({ result, onBack, onSave }) {
  const score = Number(result.safety_score || 0); const safe = score >= 8; return <div className="screen"><div className="page-header"><button className="btn-secondary" onClick={onBack}><ArrowLeft size={18} /> Back</button><span className="eyebrow">Analysis report</span></div><div className="score-card"><h1>{result.product_name}</h1><div className={`score-display ${safe ? 'green' : 'red'}`}>{score.toFixed(1)}<span>/10</span></div><strong>{result.overall_verdict || 'Safety rating'}</strong><div className="safety-gradient-bar-container"><div className="safety-gradient-bar" /><div className="score-pointer" style={{ left: `${Math.max(0, Math.min(100, score * 10))}%` }} /></div><div className="safety-labels"><span>Needs care</span><span>Safer choice</span></div></div><div className="profile-section-card"><div className="profile-section-header"><h3><Sparkles size={16} /> AI health assessment</h3></div><p>{result.summary_ai}</p></div><div className="page-header"><h1>Ingredient breakdown</h1></div><div className="ingredient-list-container">{(result.ingredients || []).map((ingredient, index) => <div className="ingredient-item" key={`${ingredient.name}-${index}`}><div className="ingredient-left"><span className={`status-badge-icon ${ingredient.risk_level === 'Safe' ? 'safe' : 'risk'}`}>{ingredient.risk_level === 'Safe' ? <Check size={15} /> : <X size={15} />}</span><div><strong>{ingredient.name}</strong><p>{ingredient.description}</p></div></div><span className={`risk-tag-badge ${ingredient.risk_level === 'Safe' ? 'safe' : 'risk'}`}>{ingredient.risk_level}</span></div>)}</div><button className="btn-primary" onClick={onSave}>Save to history <Check size={18} /></button></div>;
}

function ReferenceApp() {
  const [screen, setScreen] = useState('login'); const [name, setName] = useState('Anusha'); const [mode, setMode] = useState('FOOD'); const [result, setResult] = useState(null); const [history, setHistory] = useState([]);
  const completeLogin = (value) => { setName(value); setScreen('home'); }; const save = () => { if (result && !history.includes(result)) setHistory([result, ...history]); setScreen('history'); };
  if (screen === 'login') return <div className="app-container"><ReferenceAuth onSubmit={completeLogin} onSwitch={() => setScreen('signup')} /></div>;
  if (screen === 'signup') return <div className="app-container"><ReferenceAuth signUp onSubmit={completeLogin} onSwitch={() => setScreen('login')} /></div>;
  return <div className="app-container">{screen === 'home' && <ReferenceHome name={name} onScan={(value) => { setMode(value); setScreen('scan'); }} onChange={setScreen} />}{screen === 'scan' && <ReferenceScan mode={mode} onBack={() => setScreen('home')} onResult={(value) => { setResult(value); setScreen('results'); }} />}{screen === 'results' && result && <ReferenceResults result={result} onBack={() => setScreen('home')} onSave={save} />}{screen === 'history' && <div className="screen"><div className="page-header"><h1>Scan history</h1><Clock /></div>{history.length ? history.map((item, index) => <button className="activity-item" key={index} onClick={() => { setResult(item); setScreen('results'); }}><span>{item.product_name}</span><span className="score-tag green">{Number(item.safety_score).toFixed(1)}/10</span></button>) : <div className="empty-state"><Clock size={32} /><h2>No scans yet</h2><p>Your saved scans will appear here.</p></div>}</div>}{screen === 'profile' && <div className="screen"><div className="page-header"><h1>My profile</h1><User /></div><div className="profile-hero"><div className="avatar-badge large">{name[0]}</div><h2>Your health shield</h2><p>Personalize every scan around your needs.</p></div><div className="profile-section-card"><h3>Allergies & sensitivities</h3><div className="profile-chip-grid"><span className="profile-chip">paraben</span><span className="profile-chip">fragrance</span></div></div><button className="btn-secondary logout" onClick={() => setScreen('login')}><LogOut size={16} /> Log out</button></div>}{['home', 'profile', 'history'].includes(screen) && <ReferenceNav active={screen} onChange={setScreen} />}</div>;
}

function LegacyApp() {
  const [inputText, setInputText] = useState('');
  const [productName, setProductName] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  // User Health Profile
  const [profile, setProfile] = useState({
    allergies: ['paraben', 'fragrance'],
    skin_type: 'Sensitive',
    is_pregnant: false,
  });
  const [allergyInput, setAllergyInput] = useState('');

  const handleScan = async (overrideFile = null) => {
    const targetFile = overrideFile || file;
    if (!inputText && !targetFile) return;

    setLoading(true);
    try {
      const data = await analyzeIngredients({
        text: inputText,
        file: targetFile,
        productName: productName || 'Product Scan',
        profile: profile,
      });
      setResult(data);
    } catch (err) {
      alert(err.message || 'Scan error occurred');
    } finally {
      setLoading(false);
    }
  };

  const addAllergy = () => {
    if (allergyInput.trim() && !profile.allergies.includes(allergyInput.trim().toLowerCase())) {
      setProfile({
        ...profile,
        allergies: [...profile.allergies, allergyInput.trim().toLowerCase()]
      });
      setAllergyInput('');
    }
  };

  const removeAllergy = (item) => {
    setProfile({
      ...profile,
      allergies: profile.allergies.filter(a => a !== item)
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-500/10 border border-emerald-500/30 p-2 rounded-xl text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
              IngreLens
            </span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>AI Safety Scanner (0-10 Scale)</span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Input & Health Profile Settings */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* User Allergy & Health Profile Settings */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2 mb-4">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Personal Health Profile
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">My Allergies & Sensitivities</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={allergyInput}
                    onChange={(e) => setAllergyInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
                    placeholder="e.g. gluten, paraben, peanut"
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    onClick={addAllergy}
                    className="bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold px-3 py-1.5 rounded-xl transition"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {profile.allergies.map((a) => (
                    <span key={a} className="inline-flex items-center gap-1 bg-red-500/10 text-red-400 border border-red-500/20 text-xs px-2.5 py-0.5 rounded-full">
                      {a}
                      <button onClick={() => removeAllergy(a)} className="hover:text-red-200">×</button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Skin / Health Type</label>
                  <select
                    value={profile.skin_type}
                    onChange={(e) => setProfile({ ...profile, skin_type: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200"
                  >
                    <option>Normal</option>
                    <option>Sensitive</option>
                    <option>Acne-Prone</option>
                    <option>Dry / Eczema</option>
                  </select>
                </div>

                <div className="flex items-end pb-1.5">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={profile.is_pregnant}
                      onChange={(e) => setProfile({ ...profile, is_pregnant: e.target.checked })}
                      className="rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-0"
                    />
                    <span>Pregnancy Safe</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Scanner / Text Input Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Camera className="w-4 h-4 text-emerald-400" />
              Scan or Paste Ingredients
            </h3>

            <input
              type="text"
              placeholder="Product Name (e.g. Daily Facial Cleanser)"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />

            <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-2xl p-4 text-center cursor-pointer transition relative bg-slate-950/40">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setFile(e.target.files[0]);
                  }
                }}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="w-6 h-6 text-slate-400 mx-auto mb-1.5" />
              <p className="text-xs font-medium text-slate-300">
                {file ? file.name : "Upload or snap ingredient label photo"}
              </p>
              <span className="text-[10px] text-slate-500">Auto-OCR Image Extraction</span>
            </div>

            <div className="relative">
              <textarea
                rows={4}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Or paste ingredients manually: Water, Niacinamide, Glycerin, Methylparaben..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs focus:outline-none focus:border-emerald-500 leading-relaxed font-mono"
              />
            </div>

            <button
              onClick={() => handleScan()}
              disabled={loading || (!inputText && !file)}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Analyzing Safety...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Product
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Scan Results */}
        <div className="lg:col-span-7">
          {result ? (
            <div className="space-y-6">
              
              {/* Scorecard Header (0 to 10 Scale) */}
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-xs uppercase font-bold tracking-widest text-emerald-400">Analysis Report</span>
                    <h2 className="text-2xl font-black text-slate-100 mt-0.5">{result.product_name}</h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Evaluated {result.total_ingredients} ingredients • {result.flagged_count} flagged risks
                    </p>
                  </div>

                  {/* Safety Score Meter: Scale 0 to 10 */}
                  <div className="flex items-center gap-3 bg-slate-950/80 border border-slate-800 px-4 py-2.5 rounded-2xl">
                    <div className={`text-3xl font-black ${
                      result.safety_score >= 8.0 ? 'text-emerald-400' :
                      result.safety_score >= 5.0 ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {Number(result.safety_score).toFixed(1)}
                      <span className="text-xs text-slate-500 font-normal"> / 10</span>
                    </div>
                    <div className="text-left">
                      <div className="text-[10px] text-slate-400 font-medium uppercase">Safety Rating</div>
                      <div className={`text-xs font-bold ${
                        result.safety_score >= 8.0 ? 'text-emerald-300' :
                        result.safety_score >= 5.0 ? 'text-amber-300' : 'text-red-300'
                      }`}>
                        {result.overall_verdict}
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Plain English Summary */}
                <div className="mt-5 p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/20 text-xs text-slate-300 leading-relaxed">
                  <div className="flex items-center gap-1.5 font-semibold text-emerald-400 mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Health Assessment
                  </div>
                  {result.summary_ai}
                </div>
              </div>

              {/* Ingredient Breakdown List */}
              <div className="space-y-3">
                <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Ingredient Breakdown
                </h4>
                {result.ingredients.map((ing, idx) => (
                  <div 
                    key={idx} 
                    className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row justify-between gap-3 hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200 text-sm">{ing.name}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          ing.risk_level === 'Safe' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          ing.risk_level === 'Caution' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          'bg-red-500/10 text-red-400 border-red-500/20'
                        }`}>
                          {ing.risk_level}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{ing.description}</p>
                      {ing.side_effects.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {ing.side_effects.map((eff, i) => (
                            <span key={i} className="text-[10px] bg-red-950/50 text-red-300 border border-red-800/40 px-2 py-0.5 rounded-md">
                              ⚠️ {eff}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="text-right sm:self-center shrink-0">
                      <span className="text-[10px] text-slate-500 block">Hazard Score</span>
                      <span className="text-sm font-bold text-slate-300">{ing.hazard_score} / 10</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[380px] bg-slate-900/40 border border-dashed border-slate-800 rounded-3xl flex flex-col items-center justify-center p-8 text-center">
              <Search className="w-12 h-12 text-slate-700 mb-3" />
              <h3 className="text-base font-semibold text-slate-300">No Active Scan</h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Upload a picture of an ingredient label or paste the ingredient list to receive a toxicity rating and personal allergy report.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default ReferenceApp;