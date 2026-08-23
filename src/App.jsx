import React, { useEffect, useState } from 'react'
import {
  House,
  User,
  Clock,
  Pill,
  Utensils,
  ChevronRight,
  Check,
  X,
  Pencil,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Search,
  Aperture,
  AlertTriangle,
  CalendarDays,
  ShieldAlert,
  PackageCheck,
  Info,
  Stethoscope
} from 'lucide-react'
import scanReference from '../assets/Gemini_Generated_Image_oedrlaoedrlaoedr.png'
import logoImage from '../assets/Your_paragraph_text-removebg-preview.png'

const USERS_STORAGE_KEY = 'ingrelens-users-v1'
const CURRENT_USER_STORAGE_KEY = 'ingrelens-current-user-v1'

function loadUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function saveUsers(users) {
  localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users))
}

function createUserId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function getExpiryStatus(expiryDate) {
  if (!expiryDate) return { label: 'Expiry date could not be detected', tone: 'yellow' }
  const today = new Date()
  const expiry = new Date(`${expiryDate}T23:59:59`)
  if (Number.isNaN(expiry.getTime())) return { label: 'Expiry date could not be detected', tone: 'yellow' }
  const daysUntilExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24))
  if (daysUntilExpiry < 0) return { label: 'Expired', tone: 'red' }
  if (daysUntilExpiry <= 90) return { label: 'Expires soon', tone: 'yellow' }
  return { label: 'Not expired', tone: 'green' }
}

function Avatar({ name, image, size = 'default' }) {
  return (
    <div className={`avatar-badge ${size === 'large' ? 'w-14 h-14 text-xl' : ''}`}>
      {image ? <img src={image} alt={`${name || 'User'} profile`} className="h-full w-full rounded-full object-cover" /> : (name || 'User').trim().charAt(0).toUpperCase()}
    </div>
  )
}

// --- IngreLens Official Transparent Image Logo Component ---
function IngreLensLogo({ size = 170, className = "" }) {
  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <img
        src={logoImage}
        alt="IngreLens Logo"
        style={{ width: size, height: 'auto', objectFit: 'contain' }}
        className="drop-shadow-sm"
      />
    </div>
  )
}

// --- Brand Logo Header Component ---
function Brand({ compact = false }) {
  return (
    <div className="flex items-center gap-2">
      <img
        src={logoImage}
        alt="IngreLens Logo"
        className={compact ? "h-8 w-auto object-contain" : "h-11 w-auto object-contain"}
      />
    </div>
  )
}

// --- Global Persistent Bottom Navigation ---
function BottomNav({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: House },
    { id: 'scan', label: 'Scan', icon: Aperture },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'history', label: 'History', icon: Clock }
  ]

  return (
    <nav className="bottom-nav">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = activeTab === item.id
        return (
          <button
            key={item.id}
            className={`nav-item ${isActive ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <Icon size={22} strokeWidth={isActive ? 2.5 : 1.8} />
            <span>{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

// --- Forgot Password Modal/Screen ---
function ForgotPasswordModal({ onClose }) {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [resetError, setResetError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    setResetError('')

    try {
      const response = await fetch('http://localhost:8000/users/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password: 'dummy' }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to send password reset email.')
      }

      setSubmitted(true)
    } catch (err) {
      setResetError(err.message || 'Failed to send password reset email. Please ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl text-center relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
        >
          <X size={20} />
        </button>

        <IngreLensLogo size={100} className="mb-2" />
        <h2 className="text-xl font-bold text-gray-900 mb-1">Reset Password</h2>

        {submitted ? (
          <div className="my-4 space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-[#00C853]">
              <Check size={28} />
            </div>
            <p className="text-sm font-medium text-gray-800">
              Password reset email sent to <strong>{email}</strong>!
            </p>
            <p className="text-xs text-gray-500">
              Please check your email inbox and spam folder for instructions to reset your password.
            </p>
            <button
              onClick={onClose}
              className="btn-primary w-full mt-4"
            >
              Back to Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-left mt-4">
            <p className="text-xs text-gray-500 text-center">
              Enter your registered email address to receive a password reset link.
            </p>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                className="input-underline"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                required
              />
            </div>
            {resetError && (
              <p className="text-xs text-red-500 text-center">{resetError}</p>
            )}
            <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset Link'} <ArrowRight size={18} />
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

// --- Login Screen (/auth - Login Mode) ---
function LoginScreen({ onLogin, onGoToSignUp, error }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showForgotPassword, setShowForgotPassword] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    onLogin(email.trim().toLowerCase(), password)
  }

  return (
    <div className="auth-container">
      {showForgotPassword && (
        <ForgotPasswordModal onClose={() => setShowForgotPassword(false)} />
      )}

      <div className="auth-header">
        {/* Transparent Image Logo */}
        <IngreLensLogo size={190} />
        <h1 className="mt-2 text-2xl font-extrabold text-[#212121]">Welcome to IngreLens</h1>
        <p className="text-sm text-[#666666]">Log in to access your personal health shield</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            className="input-underline"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            required
          />
        </div>

        <div className="form-group">
          <div className="flex justify-between items-center">
            <label>Password</label>
            <button
              type="button"
              onClick={() => setShowForgotPassword(true)}
              className="text-xs font-semibold text-[#00C853] hover:underline mb-1"
            >
              Forgot Password?
            </button>
          </div>
          <input
            type="password"
            className="input-underline"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />
        </div>

        <button type="submit" className="btn-primary mt-2">
          Log In <ArrowRight size={18} />
        </button>
        {error && <p className="text-xs text-[#D32F2F] text-center">{error}</p>}
      </form>

      <div className="auth-actions text-center pb-4">
        <button className="btn-secondary" onClick={onGoToSignUp}>
          Don't have an account? <strong className="ml-1 text-[#00C853]">Sign Up</strong>
        </button>
      </div>
    </div>
  )
}

// --- Sign Up Screen (/auth - Sign Up Mode) ---
function SignUpScreen({ onSignUpSuccess, onGoToLogin, error }) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationError, setValidationError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match. Please ensure both passwords are identical.')
      return
    }
    setValidationError('')
    onSignUpSuccess({ email: email.trim().toLowerCase(), password, name: fullName.trim() })
  }

  return (
    <div className="auth-container">
      <div className="auth-header">
        {/* Transparent Image Logo */}
        <IngreLensLogo size={170} />
        <h1 className="mt-2 text-2xl font-extrabold text-[#212121]">Create Account</h1>
        <p className="text-sm text-[#666666]">Start analyzing food & medicine labels today</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full Name</label>
          <input
            type="text"
            className="input-underline"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="e.g. Sarah Mwangi"
            required
          />
        </div>

        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            className="input-underline"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            required
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            className="input-underline"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              if (validationError) setValidationError('')
            }}
            placeholder="Create password"
            required
          />
        </div>

        <div className="form-group">
          <label>Confirm Password</label>
          <input
            type="password"
            className="input-underline"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value)
              if (validationError) setValidationError('')
            }}
            placeholder="Confirm password"
            required
          />
        </div>

        <button type="submit" className="btn-primary mt-2">
          Sign Up <ArrowRight size={18} />
        </button>
        {password && confirmPassword && password !== confirmPassword && (
          <p className="text-xs font-semibold text-[#D32F2F] text-center mt-1">
            ⚠️ Passwords do not match
          </p>
        )}
        {validationError && (
          <p className="text-xs font-semibold text-[#D32F2F] text-center mt-1">{validationError}</p>
        )}
        {error && <p className="text-xs text-[#D32F2F] text-center mt-1">{error}</p>}
      </form>

      <div className="auth-actions text-center pb-4">
        <button className="btn-secondary" onClick={onGoToLogin}>
          Already have an account? <strong className="ml-1 text-[#00C853]">Log In</strong>
        </button>
      </div>
    </div>
  )
}

// --- Home Screen (/home) ---
function HomeScreen({ userName, recentScans = [], setActiveTab, openModal, setScanMode, setViewResult }) {
  const articles = [
    {
      id: 1,
      title: 'Hidden Sodium: Decoding Labels for Diabetic & Hypertensive Care',
      category: 'AI Insight',
      image: 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80',
    },
    {
      id: 2,
      title: 'Spotting Ultra-Processed Foods: 5 Red Flag Ingredients to Avoid',
      category: 'Nutrition',
      image: 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=600&q=80',
    },
    {
      id: 3,
      title: 'Medicine Authenticity Guide: Batch Verification & Expiry Shield',
      category: 'Pharma Safety',
      image: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=600&q=80',
    }
  ]

  const firstName = (userName || 'User').trim().split(' ')[0]

  return (
    <div className="screen">
      {/* Header */}
      <div className="home-greeting">
        <div>
          <div className="eyebrow">Personal Shield Active</div>
          <h1>Hello, {firstName}</h1>
        </div>
        <div className="avatar-badge" onClick={() => setActiveTab('profile')}>
          {firstName.charAt(0).toUpperCase()}
        </div>
      </div>

      {/* Health News Hub Carousel */}
      <div className="news-carousel-container">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-[#212121]">Health News & AI Insights</h2>
          <span className="text-xs text-[#00C853] font-semibold flex items-center gap-1">
            <Sparkles size={14} /> Tailored to your profile
          </span>
        </div>
        <div className="news-carousel">
          {articles.map((art) => (
            <div key={art.id} className="news-card">
              <img src={art.image} alt={art.title} className="news-card-image" />
              <div className="news-card-body">
                <span className="eyebrow">{art.category}</span>
                <div className="news-card-title">{art.title}</div>
                <button className="btn-secondary text-xs">
                  Read More <ChevronRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Scan Action Cards */}
      <div className="mb-6">
        <h2 className="text-base font-bold text-[#212121] mb-3">Quick Scan</h2>
        <div className="quick-scan-grid">
          <div
            className="scan-action-card"
            onClick={() => {
              setScanMode('MEDICINE')
              openModal()
            }}
          >
            <div className="scan-card-icon medicine">
              <Pill size={26} />
            </div>
            <span>Scan Medicine</span>
            <span className="text-xs text-[#666666]">Check authenticity & safety</span>
          </div>

          <div
            className="scan-action-card"
            onClick={() => {
              setScanMode('FOOD')
              openModal()
            }}
          >
            <div className="scan-card-icon food">
              <Utensils size={26} />
            </div>
            <span>Scan Food</span>
            <span className="text-xs text-[#666666]">Evaluate ingredients & risk</span>
          </div>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="recent-activity-section">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-[#212121]">Recent Scans</h2>
          <button
            className="text-xs font-semibold text-[#00C853]"
            onClick={() => setActiveTab('history')}
          >
            See All
          </button>
        </div>
        {recentScans.length === 0 ? (
          <p className="text-xs text-[#888888] italic py-2">No recent scans yet.</p>
        ) : (
          <div className="activity-list">
            {recentScans.map((item) => (
            <div
              key={item.id}
              className="activity-item"
              onClick={() => {
                setViewResult(item)
                setActiveTab('results')
              }}
            >
              <div className="activity-info">
                <div
                  className={`activity-icon ${
                    item.type === 'Food' ? 'bg-[#FFF3E0] text-[#F57C00]' : 'bg-[#E8F5E9] text-[#00C853]'
                  }`}
                >
                  {item.type === 'Food' ? <Utensils size={18} /> : <Pill size={18} />}
                </div>
                <div className="activity-details">
                  <h4>{item.name}</h4>
                  <p>{item.type} • {item.date}</p>
                </div>
              </div>
              <div
                className={`score-tag ${
                  item.score >= 8 ? 'green' : item.score >= 4 ? 'yellow' : 'red'
                }`}
              >
                {item.score}/10
              </div>
            </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// --- Scan Mode Selection Modal ---
function ScanModeModal({ isOpen, onClose, selectedMode, setSelectedMode, onContinue }) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>What would you like to scan?</h3>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-gray-800">
            <X size={20} />
          </button>
        </div>

        <p className="text-sm text-[#666666] mb-4">
          Select the label type to apply specialized AI health rules.
        </p>

        <div className="toggle-options">
          <button
            className={`toggle-btn ${selectedMode === 'FOOD' ? 'active' : ''}`}
            onClick={() => setSelectedMode('FOOD')}
          >
            <Utensils size={28} />
            <span>Food</span>
          </button>

          <button
            className={`toggle-btn ${selectedMode === 'MEDICINE' ? 'active' : ''}`}
            onClick={() => setSelectedMode('MEDICINE')}
          >
            <Pill size={28} />
            <span>Medicine</span>
          </button>
        </div>

        <button className="btn-primary" onClick={onContinue}>
          Continue <ArrowRight size={18} />
        </button>
      </div>
    </div>
  )
}

// --- Live Camera & Scanning View (/scan) ---
function LiveCameraView({ mode, onScanComplete, onBack }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleCapture = () => {
    setIsAnalyzing(true)
    setTimeout(() => {
      setIsAnalyzing(false)
      onScanComplete()
    }, 2000)
  }

  return (
    <div className="camera-container">
      {/* Top Controls */}
      <div className="camera-header">
        <button onClick={onBack} className="p-2 bg-white/10 rounded-full text-white">
          <ArrowLeft size={20} />
        </button>
        <div className="mode-badge">{mode} SCAN MODE</div>
        <div className="w-8" />
      </div>

      {/* Viewfinder */}
      <div className="camera-viewfinder">
        <div
          className="w-full h-full absolute inset-0 opacity-40 bg-cover bg-center"
          style={{ backgroundImage: `url(${scanReference})` }}
        />

        <div className="viewfinder-guide z-10">
          <div className="bracket-corner top-left"></div>
          <div className="bracket-corner top-right"></div>
          <div className="bracket-corner bottom-left"></div>
          <div className="bracket-corner bottom-right"></div>
          <div className="guide-text">Align label within guide.</div>
        </div>
      </div>

      {/* Bottom Shutter Controls */}
      <div className="camera-controls">
        <p className="text-xs text-gray-300">Tap shutter to capture & evaluate ingredients</p>
        <button className="shutter-btn" onClick={handleCapture} title="Capture Label">
          <Aperture size={36} className="text-[#00C853]" />
        </button>
      </div>

      {/* Animated Analyzing Loading Spinner */}
      {isAnalyzing && (
        <div className="loading-overlay">
          <div className="pulse-spinner"></div>
          <div className="text-lg font-bold text-white">Analyzing label...</div>
          <div className="text-xs text-gray-300">Evaluating health score against your profile</div>
        </div>
      )}
    </div>
  )
}

// --- Scan Results Screen (/results) ---
function ScanResultsScreen({ item, mode, userProfile, onBack, onSave }) {
  const defaultFoodResult = {
    modeName: 'Food Example',
    itemName: 'Harvest Oat Granola',
    score: 9,
    summary: 'Excellent choice for your health goals. Low sodium content & gluten-free certified.',
    ingredients: [
      { name: 'Whole Grain Oats', tag: 'Safe', isSafe: true },
      { name: 'Almonds', tag: 'Safe', isSafe: true },
      { name: 'Sea Salt', tag: 'Low Sodium', isSafe: true },
      { name: 'Natural Honey', tag: 'Safe', isSafe: true },
      { name: 'High Fructose Corn Syrup', tag: 'High Risk', isSafe: false }
    ]
  }

  const defaultMedicineResult = {
    modeName: 'Medicine Example',
    itemName: 'Paracetamol 500 mg',
    score: 9,
    summary: 'Commonly used for temporary relief of pain and fever when taken as directed.',
    activeIngredient: 'Paracetamol (acetaminophen)',
    strength: '500 mg per tablet',
    category: 'Analgesic and antipyretic',
    uses: 'Temporary relief of mild to moderate pain and fever.',
    manufacturer: 'Demo Pharmaceuticals Ltd.',
    dosageForm: 'Tablet',
    route: 'Oral',
    manufacturingDate: '2025-01-15',
    expiryDate: '2027-12-31',
    batchNumber: 'PCM5-250115',
    packaging: 'Name, strength, batch, and dates detected on the demo label.',
    barcodeStatus: 'Not available in demo scan',
    verificationStatus: 'Verification information available',
    verificationNote: 'Demo verification — authenticity could not be independently confirmed.',
    informationAvailable: true,
    dosage: 'Adults and children 12 years and over: 1–2 tablets every 4–6 hours as needed. Do not exceed the dose stated on the package.',
    warnings: 'Do not take with other medicines containing paracetamol. Ask a doctor or pharmacist before use if you have liver disease, drink alcohol regularly, or are taking other medicines.',
    contraindications: 'Do not use if allergic to paracetamol or any listed ingredient. Check with a healthcare professional if you have severe liver problems.',
    allergyIngredients: ['paracetamol'],
    interactions: 'May interact with other products containing paracetamol and some medicines that affect the liver. Interaction information is limited in this demo.',
    sideEffects: 'Nausea, stomach discomfort, or skin rash may occur. Stop use and seek medical help for signs of an allergic reaction or unusual skin changes.',
    seriousWarnings: 'Seek medical attention for trouble breathing, swelling of the face or throat, severe rash, or signs of an overdose.',
    storage: 'Store in a cool, dry place below 25°C, away from direct sunlight and out of the reach of children.',
    prescription: 'Usually available without a prescription, but local requirements may vary.'
  }

  const resultData = item
    ? item.type === 'Medicine'
      ? {
          ...defaultMedicineResult,
          modeName: 'Medicine Analysis',
          itemName: item.name,
          score: item.score
        }
      : {
        modeName: `${item.type} Analysis`,
        itemName: item.name,
        score: item.score,
        summary: item.score >= 8 ? 'Great fit for your health profile!' : 'Contains ingredients flagging high risk.',
        ingredients: defaultFoodResult.ingredients
      }
    : mode === 'MEDICINE'
      ? defaultMedicineResult
    : defaultFoodResult

  const pointerPositionPercent = Math.min(Math.max((resultData.score / 10) * 100, 5), 95)
  const isMedicineResult = mode === 'MEDICINE'
  const expiryStatus = isMedicineResult ? getExpiryStatus(resultData.expiryDate) : null
  const profileAllergies = userProfile?.allergies || []
  const profileConditions = userProfile?.conditions || []
  const currentMedicines = userProfile?.currentMedicines || []
  const allergyAlert = isMedicineResult && profileAllergies.some((allergy) =>
    resultData.allergyIngredients?.some((ingredient) => ingredient.includes(allergy.toLowerCase()))
  )
  const interactionAlert = isMedicineResult && currentMedicines.some((medicine) =>
    /paracetamol|acetaminophen/i.test(medicine)
  )
  const conditionAlert = isMedicineResult && profileConditions.some((condition) =>
    /liver|kidney/i.test(condition)
  )

  return (
    <div className="screen">
      <div className="page-header">
        <button onClick={onBack} className="p-1">
          <ArrowLeft size={20} />
        </button>
        <h1>Scan Results: {resultData.modeName}</h1>
        <div className="w-6" />
      </div>

      {/* Item Title & Summary */}
      <div className="mb-4">
        <h2 className="text-xl font-extrabold text-[#212121]">{resultData.itemName}</h2>
        <p className="text-xs text-[#666666] mt-1">{resultData.summary}</p>
      </div>

      {/* Health Score Card */}
      <div className="score-card">
        <div className="eyebrow">Health Score</div>
        <div className="score-display">
          {resultData.score}
          <span>/10</span>
        </div>

        {/* Continuous Horizontal Gradient Safety Bar */}
        <div className="safety-gradient-bar-container">
          <div className="safety-gradient-bar" />
          <div
            className="score-pointer"
            style={{ left: `${pointerPositionPercent}%` }}
            title={`Score: ${resultData.score}`}
          />
        </div>
        <div className="safety-labels">
          <span style={{ color: '#D32F2F' }}>0–3 High Risk</span>
          <span style={{ color: '#FBC02D' }}>4–7 Moderate</span>
          <span style={{ color: '#388E3C' }}>8–10 Safe</span>
        </div>
      </div>

      {mode === 'MEDICINE' ? (
        <div>
          <div className={`p-4 rounded-2xl border mb-4 ${expiryStatus.tone === 'red' ? 'bg-[#FFEBEE] border-[#FFCDD2]' : expiryStatus.tone === 'yellow' ? 'bg-[#FFFDE7] border-[#FFF1A8]' : 'bg-[#E8F5E9] border-[#C8E6C9]'}`}>
            <div className="flex items-center gap-2 font-bold text-sm">
              {expiryStatus.tone === 'green' ? <CalendarDays size={18} className="text-[#388E3C]" /> : <AlertTriangle size={18} className="text-[#D32F2F]" />}
              <span>Expiry & Safety: {expiryStatus.label}</span>
            </div>
            <p className="text-xs mt-2 text-[#666666]">
              {expiryStatus.tone === 'red' ? 'Do not use this medicine. Check with a pharmacist or healthcare professional.' : expiryStatus.tone === 'yellow' ? 'Verify the expiry date on the physical packaging before use.' : 'Expiry status is based on the demo package date.'}
            </p>
          </div>

          <div className="mb-4 space-y-2">
            <h3 className="text-sm font-bold text-[#212121]">Safety Alerts</h3>
            {allergyAlert && <div className="p-3 rounded-xl bg-[#FFEBEE] border border-[#FFCDD2] text-xs"><strong>Allergy Alert</strong><p className="mt-1">This medicine may contain an ingredient you have listed as an allergy. Verify the ingredients and consult a healthcare professional.</p></div>}
            {interactionAlert && <div className="p-3 rounded-xl bg-[#FFFDE7] border border-[#FFF1A8] text-xs"><strong>Possible medicine interaction</strong><p className="mt-1">This medicine may duplicate {currentMedicines.find((medicine) => /paracetamol|acetaminophen/i.test(medicine))}. Consult a doctor or pharmacist before taking them together.</p></div>}
            {conditionAlert && <div className="p-3 rounded-xl bg-[#FFFDE7] border border-[#FFF1A8] text-xs"><strong>Possible condition-related risk</strong><p className="mt-1">This medicine may require additional caution with a listed liver or kidney condition. Verify with a doctor or pharmacist.</p></div>}
            {!allergyAlert && !interactionAlert && !conditionAlert && <div className="p-3 rounded-xl bg-[#F4FAF5] border border-[#E8ECE9] text-xs text-[#666666]">No personalized alert was identified from the optional information provided. Interaction and contraindication information is not complete; verify with a pharmacist.</div>}
          </div>

          <div className="p-4 rounded-2xl bg-[#FFFDE7] border border-[#FFF1A8] mb-4">
            <div className="flex items-center gap-2 font-bold text-sm"><ShieldAlert size={18} className="text-[#F57C00]" /> Verification information available</div>
            <p className="text-xs text-[#666666] mt-2">{resultData.verificationNote}</p>
            <p className="text-xs text-[#666666] mt-1">Verify suspicious medicines with a pharmacist, manufacturer, or official medicine-verification service.</p>
          </div>

          <h3 className="text-sm font-bold text-[#212121] mb-3">Medicine Information</h3>
          <div className="ingredient-list-container border border-[#E8ECE9] rounded-2xl overflow-hidden">
            {[
              ['Active Ingredient', resultData.activeIngredient],
              ['Strength / Dosage', resultData.strength],
              ['Category', resultData.category],
              ['Common Uses', resultData.uses],
              ['Manufacturer', resultData.manufacturer],
              ['Dosage Form', resultData.dosageForm],
              ['Route', resultData.route],
              ['Typical Dosage', resultData.dosage],
              ['Manufacturing Date', resultData.manufacturingDate],
              ['Expiry Date', resultData.expiryDate],
              ['Batch / Lot', resultData.batchNumber],
              ['Prescription', resultData.prescription]
            ].map(([label, value]) => (
              <div key={label} className="ingredient-item items-start">
                <div>
                  <div className="eyebrow mb-1">{label}</div>
                  <p className="text-sm text-[#212121] leading-relaxed">{value}</p>
                </div>
              </div>
            ))}
          </div>
          <h3 className="text-sm font-bold text-[#212121] mt-5 mb-3">Medicine Verification</h3>
          <div className="ingredient-list-container border border-[#E8ECE9] rounded-2xl overflow-hidden">
            {[
              ['Medicine Detected', resultData.itemName],
              ['Packaging / Label', resultData.packaging],
              ['Barcode / QR Code', resultData.barcodeStatus],
              ['Available Status', resultData.verificationStatus]
            ].map(([label, value]) => <div key={label} className="ingredient-item items-start"><div><div className="eyebrow mb-1">{label}</div><p className="text-sm text-[#212121]">{value}</p></div></div>)}
          </div>

          <h3 className="text-sm font-bold text-[#212121] mt-5 mb-3">Safety Information</h3>
          <div className="ingredient-list-container border border-[#E8ECE9] rounded-2xl overflow-hidden">
            {[
              ['Warnings', resultData.warnings],
              ['Contraindications', resultData.contraindications],
              ['Common Side Effects', resultData.sideEffects],
              ['Storage', resultData.storage],
              ['Interactions', resultData.interactions]
            ].map(([label, value]) => <div key={label} className="ingredient-item items-start"><div><div className="eyebrow mb-1">{label}</div><p className="text-sm text-[#212121] leading-relaxed">{value || 'Information unavailable — please check the medicine packaging or consult a pharmacist.'}</p></div></div>)}
          </div>

          <div className="p-4 rounded-2xl bg-[#F4FAF5] border border-[#E8ECE9] mt-5">
            <h3 className="text-sm font-bold text-[#212121] mb-3">Before Taking This Medicine</h3>
            {['Check the medicine name and strength', 'Check the expiry date', 'Check that the packaging is intact', 'Check the batch/lot information', 'Check for signs of tampering', 'Make sure it was prescribed/recommended for you when appropriate', 'Check allergies and important interactions', 'Follow dosage instructions from the packaging or healthcare professional'].map((check) => <p key={check} className="text-xs text-[#212121] mb-2"><PackageCheck size={14} className="inline mr-2 text-[#388E3C]" />{check}</p>)}
          </div>
          <div className="p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] mt-4">
            <div className="flex items-center gap-2 font-bold text-sm"><Stethoscope size={18} className="text-[#D32F2F]" /> Serious warning signs</div>
            <p className="text-xs text-[#666666] mt-2">{resultData.seriousWarnings}</p>
          </div>
          <p className="text-xs text-[#666666] mt-4"><Info size={14} className="inline mr-1" />Demo information only. This scan cannot confirm that a medicine is safe or genuine.</p>
          <p className="text-xs text-[#666666] mt-2">This information is for informational purposes only and does not replace advice from a doctor or pharmacist. Always verify the medicine, expiry date, dosage, and packaging before use.</p>
        </div>
      ) : (
        <div>
          <h3 className="text-sm font-bold text-[#212121] mb-3">Detailed Ingredient Breakdown</h3>
          <div className="ingredient-list-container border border-[#E8ECE9] rounded-2xl overflow-hidden">
            {resultData.ingredients.map((ing, idx) => (
              <div key={idx} className="ingredient-item">
                <div className="ingredient-left">
                  <div className={`status-badge-icon ${ing.isSafe ? 'safe' : 'risk'}`}>
                    {ing.isSafe ? <Check size={16} /> : <X size={16} />}
                  </div>
                  <span className="font-semibold text-sm text-[#212121]">{ing.name}</span>
                </div>
                <span className={`risk-tag-badge ${ing.isSafe ? 'safe' : 'risk'}`}>
                  {ing.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn-primary mt-6" onClick={onSave}>
        Save to History <Check size={18} />
      </button>
    </div>
  )
}

// --- Profile Screen (/profile) ---
function ProfileScreen({ profileData, onSaveProfile, onLogout }) {
  const [profile, setProfile] = useState({
    name: profileData.name || '',
    age: profileData.age || '',
    image: profileData.image || '',
    goals: profileData.goals || [],
    allergies: profileData.allergies || [],
    conditions: profileData.conditions || [],
    currentMedicines: profileData.currentMedicines || []
  })

  const [editingSection, setEditingSection] = useState(null)
  const [inputValue, setInputValue] = useState('')
  const [editName, setEditName] = useState(profileData.name || '')
  const [editAge, setEditAge] = useState(profileData.age || '')
  const [editImage, setEditImage] = useState(profileData.image || '')
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    setProfile((current) => ({ ...current, ...profileData }))
    setEditName(profileData.name || '')
    setEditAge(profileData.age || '')
    setEditImage(profileData.image || '')
  }, [profileData])

  const handleImageChange = (event) => {
    const file = event.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setFeedback('Please choose an image file.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => setEditImage(reader.result)
    reader.readAsDataURL(file)
  }

  const handleProfileSave = () => {
    const age = Number(editAge)
    if (!editName.trim()) return setFeedback('Please enter your name.')
    if (!Number.isInteger(age) || age < 1 || age > 120) return setFeedback('Please enter an age between 1 and 120.')
    onSaveProfile({ name: editName.trim(), age, image: editImage, goals: profile.goals, allergies: profile.allergies, conditions: profile.conditions, currentMedicines: profile.currentMedicines })
    setFeedback('Profile saved.')
  }

  const handleAddTag = (section) => {
    if (!inputValue.trim()) return
    if (section === 'goals') {
      setProfile((prev) => ({ ...prev, goals: [...prev.goals, inputValue.trim()] }))
    } else if (section === 'allergies') {
      setProfile((prev) => ({ ...prev, allergies: [...prev.allergies, inputValue.trim()] }))
    } else if (section === 'conditions') {
      setProfile((prev) => ({ ...prev, conditions: [...prev.conditions, inputValue.trim()] }))
    } else if (section === 'currentMedicines') {
      setProfile((prev) => ({ ...prev, currentMedicines: [...prev.currentMedicines, inputValue.trim()] }))
    }
    setInputValue('')
    setEditingSection(null)
  }

  const handleRemoveTag = (section, indexToRemove) => {
    if (section === 'goals') {
      setProfile((prev) => ({ ...prev, goals: prev.goals.filter((_, idx) => idx !== indexToRemove) }))
    } else if (section === 'allergies') {
      setProfile((prev) => ({ ...prev, allergies: prev.allergies.filter((_, idx) => idx !== indexToRemove) }))
    } else if (section === 'conditions') {
      setProfile((prev) => ({ ...prev, conditions: prev.conditions.filter((_, idx) => idx !== indexToRemove) }))
    } else if (section === 'currentMedicines') {
      setProfile((prev) => ({ ...prev, currentMedicines: prev.currentMedicines.filter((_, idx) => idx !== indexToRemove) }))
    }
  }

  return (
    <div className="screen">
      <div className="page-header">
        <h1>My Health Profile</h1>
        <ShieldCheck className="text-[#00C853]" size={24} />
      </div>

      {/* Header Avatar Info */}
      <div className="flex items-center gap-4 p-4 bg-[#F4FAF5] rounded-2xl border border-[#E8ECE9] mb-6">
        <Avatar name={profile.name} image={profile.image} size="large" />
        <div>
          <h2 className="text-lg font-bold text-[#212121]">{profile.name}</h2>
          <p className="text-xs text-[#666666]">Profile active • Health shield enabled</p>
        </div>
      </div>

      {/* Section 1: Personal Details */}
      <div className="profile-section-card">
        <div className="profile-section-header">
          <h3>Personal Details</h3>
          <Pencil size={18} className="text-[#00C853]" />
        </div>
        <div className="form-group mb-4">
          <label>Name</label>
          <input className="input-underline" value={editName} onChange={(e) => setEditName(e.target.value)} />
        </div>
        <div className="form-group mb-4">
          <label>Age</label>
          <input className="input-underline" type="number" min="1" max="120" value={editAge} onChange={(e) => setEditAge(e.target.value)} />
        </div>
        <div className="flex items-center gap-3 mb-4">
          <Avatar name={editName} image={editImage} />
          <label className="btn-secondary cursor-pointer">
            Change photo
            <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
          </label>
          {editImage && <button className="btn-secondary text-[#D32F2F]" onClick={() => setEditImage('')}>Remove</button>}
        </div>
        <button className="btn-primary mb-3" onClick={handleProfileSave}>Save Changes <Check size={18} /></button>
        {feedback && <p className={`text-xs mb-3 ${feedback === 'Profile saved.' ? 'text-[#388E3C]' : 'text-[#D32F2F]'}`}>{feedback}</p>}
        <div className="text-sm space-y-2 text-[#212121]">
          <div className="flex justify-between border-b border-gray-100 pb-2">
            <span className="text-[#666666]">Full Name:</span>
            <span className="font-semibold">{profile.name}</span>
          </div>
          <div className="flex justify-between pt-1">
            <span className="text-[#666666]">Age:</span>
            <span className="font-semibold">{profile.age ? `${profile.age} years` : 'Not specified'}</span>
          </div>
        </div>
      </div>

      {/* Section 2: Health Goals */}
      <div className="profile-section-card">
        <div className="profile-section-header">
          <h3>Health Goals</h3>
          <button
            onClick={() => setEditingSection(editingSection === 'goals' ? null : 'goals')}
            className="p-1 text-[#00C853]"
          >
            <Pencil size={18} />
          </button>
        </div>
        {profile.goals.length === 0 ? (
          <p className="text-xs text-[#888888] italic py-1">No health goals added yet.</p>
        ) : (
          <div className="profile-chip-grid">
            {profile.goals.map((g, idx) => (
              <span key={idx} className="profile-chip bg-[#E8F5E9] text-[#00C853] border-0 flex items-center gap-1">
                {g}
                <button
                  type="button"
                  className="hover:opacity-70 ml-1 cursor-pointer"
                  onClick={() => handleRemoveTag('goals', idx)}
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}
        {editingSection === 'goals' && (
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              className="border p-2 rounded-lg text-xs flex-1"
              placeholder="Add new goal (e.g. Low Sodium)..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTag('goals')}
            />
            <button
              className="bg-[#00C853] text-white px-3 py-1 rounded-lg text-xs font-bold"
              onClick={() => handleAddTag('goals')}
            >
              Add
            </button>
          </div>
        )}
      </div>

      {/* Section 3: Allergies & Conditions */}
      <div className="profile-section-card">
        <div className="profile-section-header">
          <h3>Allergies & Conditions</h3>
          <button
            onClick={() => setEditingSection(editingSection === 'allergies' ? null : 'allergies')}
            className="p-1 text-[#00C853]"
          >
            <Pencil size={18} />
          </button>
        </div>
        {profile.allergies.length === 0 ? (
          <p className="text-xs text-[#888888] italic py-1">No allergies or conditions added yet.</p>
        ) : (
          <div className="profile-chip-grid">
            {profile.allergies.map((a, idx) => (
              <span key={idx} className="profile-chip bg-[#FFEBEE] text-[#D32F2F] border-0 flex items-center gap-1">
                {a}
                <button
                  type="button"
                  className="hover:opacity-70 ml-1 cursor-pointer"
                  onClick={() => handleRemoveTag('allergies', idx)}
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}
        {editingSection === 'allergies' && (
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              className="border p-2 rounded-lg text-xs flex-1"
              placeholder="Add allergy/condition (e.g. Peanuts)..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTag('allergies')}
            />
            <button
              className="bg-[#D32F2F] text-white px-3 py-1 rounded-lg text-xs font-bold"
              onClick={() => handleAddTag('allergies')}
            >
              Add
            </button>
          </div>
        )}
      </div>

      <div className="profile-section-card">
        <div className="profile-section-header">
          <h3>Health Information <span className="text-xs font-normal text-[#888888]">(Optional)</span></h3>
        </div>
        <p className="text-xs text-[#666666] mb-3">Add information to highlight possible medicine risks. You can remove it at any time.</p>
        {[
          ['conditions', 'Medical conditions', 'e.g. liver problems'],
          ['currentMedicines', 'Current medicines', 'e.g. Warfarin']
        ].map(([section, label, placeholder]) => (
          <div key={section} className="mb-4">
            <div className="text-xs font-bold text-[#212121] mb-2">{label}</div>
            <div className="profile-chip-grid">
              {(profile[section] || []).map((value, idx) => (
                <span key={`${value}-${idx}`} className="profile-chip bg-[#FFFDE7] text-[#8A6500] border-0 flex items-center gap-1">
                  {value}
                  <button type="button" className="hover:opacity-70 ml-1" onClick={() => handleRemoveTag(section, idx)}><X size={12} /></button>
                </span>
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              <input type="text" className="border p-2 rounded-lg text-xs flex-1" placeholder={placeholder} value={editingSection === section ? inputValue : ''} onChange={(e) => { setEditingSection(section); setInputValue(e.target.value) }} onKeyDown={(e) => e.key === 'Enter' && handleAddTag(section)} />
              <button className="bg-[#00C853] text-white px-3 py-1 rounded-lg text-xs font-bold" onClick={() => handleAddTag(section)}>Add</button>
            </div>
          </div>
        ))}
      </div>

      <button className="btn-secondary text-[#D32F2F] w-full justify-center mt-4" onClick={onLogout}>Log Out</button>
    </div>
  )
}

// --- History Screen (/history) ---
function HistoryScreen({ historyItems, onSelectResult, onDeleteHistory, error }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)

  const filteredHistory = historyItems.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="screen">
      <div className="page-header">
        <h1>Scan History</h1>
        <Clock className="text-[#00C853]" size={20} />
      </div>

      {/* Search Input */}
      <div className="relative mb-4">
        <input
          type="text"
          placeholder="Search past scans..."
          className="w-full pl-9 pr-4 py-2.5 bg-[#F9F9F9] border border-[#E8ECE9] rounded-xl text-xs focus:outline-none focus:border-[#00C853]"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Search size={16} className="absolute left-3 top-3 text-gray-400" />
      </div>

      {historyItems.length > 0 && (
        <button className="btn-secondary text-[#D32F2F] mb-4" onClick={() => setIsConfirmOpen(true)}>
          Delete History <X size={16} />
        </button>
      )}

      {filteredHistory.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="mx-auto text-[#00C853] mb-3" size={32} />
          <h2 className="text-lg font-bold text-[#212121]">No scans yet</h2>
          <p className="text-xs text-[#666666] mt-1">Your scanned food and medicines will appear here.</p>
        </div>
      ) : (
        <div className="activity-list">
          {filteredHistory.map((item) => (
          <div
            key={item.id}
            className="activity-item"
            onClick={() => onSelectResult(item)}
          >
            <div className="activity-info">
              <div
                className={`activity-icon ${
                  item.type === 'Food' ? 'bg-[#FFF3E0] text-[#F57C00]' : 'bg-[#E8F5E9] text-[#00C853]'
                }`}
              >
                {item.type === 'Food' ? <Utensils size={18} /> : <Pill size={18} />}
              </div>
              <div className="activity-details">
                <h4>{item.name}</h4>
                <p>{item.type} • {item.date}</p>
              </div>
            </div>
            <div
              className={`score-tag ${
                item.score >= 8 ? 'green' : item.score >= 4 ? 'yellow' : 'red'
              }`}
            >
              {item.score}/10
            </div>
          </div>
          ))}
        </div>
      )}
      {error && <p className="text-xs text-[#D32F2F] mt-3">{error}</p>}
      {isConfirmOpen && (
        <div className="modal-overlay" onClick={() => setIsConfirmOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Delete all scan history?</h3>
              <button className="p-1 text-gray-500" onClick={() => setIsConfirmOpen(false)}><X size={20} /></button>
            </div>
            <p className="text-sm text-[#666666] mb-5">This action cannot be undone.</p>
            <div className="flex gap-3">
              <button className="btn-secondary flex-1 justify-center" onClick={() => setIsConfirmOpen(false)}>Cancel</button>
              <button className="btn-primary flex-1" onClick={() => { onDeleteHistory(); setIsConfirmOpen(false) }}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ProfileCompletionModal({ initialName, onSave, onClose }) {
  const [name, setName] = useState(initialName || '')
  const [age, setAge] = useState('')
  const [image, setImage] = useState('')
  const [error, setError] = useState('')

  const handleImageChange = (event) => {
    const file = event.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) return setError('Please choose an image file.')
    const reader = new FileReader()
    reader.onload = () => setImage(reader.result)
    reader.readAsDataURL(file)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const numericAge = Number(age)
    if (!name.trim()) return setError('Please enter your name.')
    if (!Number.isInteger(numericAge) || numericAge < 1 || numericAge > 120) {
      return setError('Please enter an age between 1 and 120.')
    }
    onSave({ name: name.trim(), age: numericAge, image })
  }

  return (
    <div className="modal-overlay">
      <form className="modal-content" onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Complete your profile</h3>
          {onClose && <button type="button" onClick={onClose} className="p-1 text-gray-500"><X size={20} /></button>}
        </div>
        <p className="text-sm text-[#666666] mb-4">Add the basics to personalize your health shield.</p>
        <div className="form-group mb-4">
          <label>Name</label>
          <input className="input-underline" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
        </div>
        <div className="form-group mb-4">
          <label>Age</label>
          <input className="input-underline" type="number" min="1" max="120" value={age} onChange={(e) => setAge(e.target.value)} />
        </div>
        <div className="flex items-center gap-3 mb-4">
          <Avatar name={name} image={image} />
          <label className="btn-secondary cursor-pointer">
            Add photo
            <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
          </label>
          {image && <button type="button" className="btn-secondary text-[#D32F2F]" onClick={() => setImage('')}>Remove</button>}
        </div>
        {error && <p className="text-xs text-[#D32F2F] mb-3">{error}</p>}
        <button type="submit" className="btn-primary">Save & Continue <ArrowRight size={18} /></button>
      </form>
    </div>
  )
}

// --- Main App Component ---
export default function App() {
  const [currentScreen, setCurrentScreen] = useState(() => localStorage.getItem(CURRENT_USER_STORAGE_KEY) ? 'home' : 'login') // login, signup, home, scan, results, profile, history
  const [selectedScanMode, setSelectedScanMode] = useState('FOOD') // FOOD or MEDICINE
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedResultItem, setSelectedResultItem] = useState(null)
  const [users, setUsers] = useState(loadUsers)
  const [currentUserId, setCurrentUserId] = useState(() => localStorage.getItem(CURRENT_USER_STORAGE_KEY))
  const [authError, setAuthError] = useState('')
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [historyError, setHistoryError] = useState('')

  const currentUser = users.find((user) => user.id === currentUserId)

  const updateUsers = (nextUsers) => {
    setUsers(nextUsers)
    saveUsers(nextUsers)
  }

  const updateCurrentUser = (changes) => {
    updateUsers(users.map((user) => user.id === currentUserId ? { ...user, ...changes } : user))
  }

  const handleLogin = (email, password) => {
    const user = users.find((candidate) => candidate.email === email && candidate.password === password)
    if (!user) return setAuthError('No matching account found. Please check your details or sign up.')
    setAuthError('')
    setCurrentUserId(user.id)
    localStorage.setItem(CURRENT_USER_STORAGE_KEY, user.id)
    setCurrentScreen('home')
  }

  const handleSignUpSuccess = ({ email, password, name }) => {
    if (users.some((user) => user.email === email)) return setAuthError('An account with this email already exists.')
    const newUser = { id: createUserId(), email, password, name: name || '', age: '', image: '', goals: [], allergies: [], conditions: [], currentMedicines: [], history: [] }
    const nextUsers = [...users, newUser]
    updateUsers(nextUsers)
    setCurrentUserId(newUser.id)
    localStorage.setItem(CURRENT_USER_STORAGE_KEY, newUser.id)
    setAuthError('')
    setCurrentScreen('home')
    setProfileModalOpen(true)
  }

  const handleContinueFromModal = () => {
    setIsModalOpen(false)
    setCurrentScreen('scan')
  }

  const handleScanComplete = () => {
    setSelectedResultItem(null)
    setCurrentScreen('results')
  }

  const handleSaveScan = () => {
    if (!currentUser) return
    const scan = {
      id: createUserId(),
      name: selectedScanMode === 'MEDICINE' ? 'Paracetamol 500 mg' : 'Harvest Oat Granola',
      type: selectedScanMode === 'MEDICINE' ? 'Medicine' : 'Food',
      date: 'Just now',
      score: 9
    }
    updateCurrentUser({ history: [scan, ...(currentUser.history || [])] })
    setCurrentScreen('history')
  }

  const handleSaveProfile = (profile) => updateCurrentUser(profile)

  const handleDeleteHistory = () => {
    try {
      updateCurrentUser({ history: [] })
      setHistoryError('')
    } catch {
      setHistoryError('History could not be deleted. Please try again.')
    }
  }

  const handleLogout = () => {
    setCurrentUserId(null)
    localStorage.removeItem(CURRENT_USER_STORAGE_KEY)
    setSelectedResultItem(null)
    setCurrentScreen('login')
  }

  return (
    <div className="app-container">
      {/* Active Screen View */}
      {currentScreen === 'login' && (
        <LoginScreen
          onLogin={handleLogin}
          onGoToSignUp={() => setCurrentScreen('signup')}
          error={authError}
        />
      )}

      {currentScreen === 'signup' && (
        <SignUpScreen
          onSignUpSuccess={handleSignUpSuccess}
          onGoToLogin={() => setCurrentScreen('login')}
          error={authError}
        />
      )}

      {currentScreen === 'home' && (
        <HomeScreen
          userName={currentUser?.name || 'User'}
          recentScans={(currentUser?.history || []).slice(0, 3)}
          setActiveTab={(tab) => setCurrentScreen(tab)}
          openModal={() => setIsModalOpen(true)}
          setScanMode={setSelectedScanMode}
          setViewResult={(item) => setSelectedResultItem(item)}
        />
      )}

      {currentScreen === 'scan' && (
        <LiveCameraView
          mode={selectedScanMode}
          onScanComplete={handleScanComplete}
          onBack={() => setCurrentScreen('home')}
        />
      )}

      {currentScreen === 'results' && (
        <ScanResultsScreen
          item={selectedResultItem}
          mode={selectedScanMode}
          userProfile={currentUser}
          onBack={() => setCurrentScreen('home')}
          onSave={handleSaveScan}
        />
      )}

      {currentScreen === 'profile' && (
        <ProfileScreen
          profileData={currentUser || { name: '', age: '', image: '' }}
          onSaveProfile={handleSaveProfile}
          onLogout={handleLogout}
        />
      )}

      {currentScreen === 'history' && (
        <HistoryScreen
          historyItems={currentUser?.history || []}
          onSelectResult={(item) => {
            setSelectedResultItem(item)
            setSelectedScanMode(item.type === 'Medicine' ? 'MEDICINE' : 'FOOD')
            setCurrentScreen('results')
          }}
          onDeleteHistory={handleDeleteHistory}
          error={historyError}
        />
      )}

      {/* Global Bottom Navigation (Visible on Main Screens) */}
      {['home', 'results', 'profile', 'history'].includes(currentScreen) && (
        <BottomNav
          activeTab={currentScreen}
          setActiveTab={(tab) => {
            if (tab === 'scan') {
              setIsModalOpen(true)
              return
            }
            setCurrentScreen(tab)
          }}
        />
      )}

      {/* Scan Mode Selection Modal */}
      <ScanModeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        selectedMode={selectedScanMode}
        setSelectedMode={setSelectedScanMode}
        onContinue={handleContinueFromModal}
      />
      {profileModalOpen && (
        <ProfileCompletionModal
          initialName={currentUser?.name}
          onSave={(profile) => {
            handleSaveProfile(profile)
            setProfileModalOpen(false)
          }}
        />
      )}
    </div>
  )
}
