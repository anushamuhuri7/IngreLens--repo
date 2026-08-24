import React, { useState } from 'react';
import { 
  Camera, Upload, ShieldCheck, Sparkles, Sliders, Search, RefreshCw 
} from 'lucide-react';
import { analyzeIngredients } from './lib/api';

export default function App() {
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