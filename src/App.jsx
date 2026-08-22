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
  Aperture
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

// --- Login Screen (/auth - Login Mode) ---
function LoginScreen({ onLogin, onGoToSignUp, error }) {
  const [email, setEmail] = useState('sarah@example.com')
  const [password, setPassword] = useState('••••••••')

  const handleSubmit = (e) => {
    e.preventDefault()
    onLogin(email.trim().toLowerCase(), password)
  }

  return (
    <div className="auth-container">
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
            placeholder="Enter your email"
            required
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            className="input-underline"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
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

  const handleSubmit = (e) => {
    e.preventDefault()
    if (password !== confirmPassword) return
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
            placeholder="sarah@example.com"
            required
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            className="input-underline"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm password"
            required
          />
        </div>

        <button type="submit" className="btn-primary mt-2">
          Sign Up <ArrowRight size={18} />
        </button>
        {password && confirmPassword && password !== confirmPassword && (
          <p className="text-xs text-[#D32F2F] text-center">Passwords do not match.</p>
        )}
        {error && <p className="text-xs text-[#D32F2F] text-center">{error}</p>}
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
function ScanResultsScreen({ item, mode, onBack, onSave }) {
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
    strength: '500 mg per tablet',
    category: 'Analgesic and antipyretic',
    uses: 'Temporary relief of mild to moderate pain and fever.',
    dosage: 'Adults and children 12 years and over: 1–2 tablets every 4–6 hours as needed. Do not exceed the dose stated on the package.',
    warnings: 'Do not take with other medicines containing paracetamol. Ask a doctor or pharmacist before use if you have liver disease, drink alcohol regularly, or are taking other medicines.',
    sideEffects: 'Nausea, stomach discomfort, or skin rash may occur. Stop use and seek medical help for signs of an allergic reaction or unusual skin changes.',
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
          <h3 className="text-sm font-bold text-[#212121] mb-3">Medicine Information</h3>
          <div className="ingredient-list-container border border-[#E8ECE9] rounded-2xl overflow-hidden">
            {[
              ['Strength / Dosage', resultData.strength],
              ['Category', resultData.category],
              ['Common Uses', resultData.uses],
              ['Typical Dosage', resultData.dosage],
              ['Warnings & Precautions', resultData.warnings],
              ['Common Side Effects', resultData.sideEffects],
              ['Storage', resultData.storage],
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
          <p className="text-xs text-[#666666] mt-3">
            Demo information only. Follow your doctor&apos;s or pharmacist&apos;s advice and the instructions on the actual medicine packaging.
          </p>
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
    goals: [],
    allergies: []
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
    onSaveProfile({ name: editName.trim(), age, image: editImage })
    setFeedback('Profile saved.')
  }

  const handleAddTag = (section) => {
    if (!inputValue.trim()) return
    if (section === 'goals') {
      setProfile((prev) => ({ ...prev, goals: [...prev.goals, inputValue.trim()] }))
    } else if (section === 'allergies') {
      setProfile((prev) => ({ ...prev, allergies: [...prev.allergies, inputValue.trim()] }))
    }
    setInputValue('')
    setEditingSection(null)
  }

  const handleRemoveTag = (section, indexToRemove) => {
    if (section === 'goals') {
      setProfile((prev) => ({ ...prev, goals: prev.goals.filter((_, idx) => idx !== indexToRemove) }))
    } else if (section === 'allergies') {
      setProfile((prev) => ({ ...prev, allergies: prev.allergies.filter((_, idx) => idx !== indexToRemove) }))
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
    const newUser = { id: createUserId(), email, password, name: name || '', age: '', image: '', history: [] }
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
