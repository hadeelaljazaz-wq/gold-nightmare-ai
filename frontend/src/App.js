import React, { useState, useEffect } from 'react';
import './App.css';
import './i18n'; // Initialize i18n
import { useTranslation } from 'react-i18next';

function App() {
  const { t, i18n } = useTranslation();
  const API_URL = process.env.REACT_APP_BACKEND_URL;

  // Navigation and UI States
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, analyze, results, contact, chart-analysis, admin, login, register
  const [loading, setLoading] = useState(false);
  
  // Authentication States
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  
  // Login Form States
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginShowPassword, setLoginShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  
  // Register Form States
  const [registerFormData, setRegisterFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    firstName: '',
    lastName: ''
  });
  const [registerShowPassword, setRegisterShowPassword] = useState(false);
  const [registerError, setRegisterError] = useState('');
  
  // Language State
  const [currentLanguage, setCurrentLanguage] = useState('ar');
  
  // Gold Price States
  const [goldPrice, setGoldPrice] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('quick');
  const [userQuestion, setUserQuestion] = useState('');
  
  // Chart Analysis States
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [currencyPair, setCurrencyPair] = useState('XAU/USD');
  const [timeframe, setTimeframe] = useState('H1');
  const [analysisNotes, setAnalysisNotes] = useState('');
  const [chartAnalysisResult, setChartAnalysisResult] = useState(null);
  const [chartAnalysisLoading, setChartAnalysisLoading] = useState(false);
  
  // Forex Analysis States
  const [forexPrices, setForexPrices] = useState({});
  const [forexAnalysisResult, setForexAnalysisResult] = useState(null);
  const [forexAnalysisLoading, setForexAnalysisLoading] = useState(false);
  const [selectedForexPair, setSelectedForexPair] = useState('');
  
  // Admin Panel States
  const [adminAuthenticated, setAdminAuthenticated] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminData, setAdminData] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminLogs, setAdminLogs] = useState([]);
  const [adminCurrentPage, setAdminCurrentPage] = useState(1);
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  
  const [quickQuestions] = useState([
    "تحليل الذهب الحالي",
    "ما هي توقعات الذهب للأسبوع القادم؟",
    "هل الوقت مناسب لشراء الذهب؟", 
    "تحليل فني للذهب",
    "تأثير التضخم على أسعار الذهب"
  ]);

  useEffect(() => {
    fetchGoldPrice();
    checkAuthStatus(); // Check if user is logged in
  }, []);

  // Reset form states when changing views
  useEffect(() => {
    if (currentView === 'login') {
      setLoginEmail('');
      setLoginPassword('');
      setLoginShowPassword(false);
      setLoginError('');
    } else if (currentView === 'register') {
      setRegisterFormData({
        email: '',
        password: '',
        confirmPassword: '',
        username: '',
        firstName: '',
        lastName: ''
      });
      setRegisterShowPassword(false);
      setRegisterError('');
    }
  }, [currentView]);

  // Authentication Functions
  const checkAuthStatus = () => {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setCurrentUser(user);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('currentUser');
      }
    }
  };

  const handleLogin = async (email, password) => {
    setAuthLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();
      
      if (data.success) {
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        setCurrentView('dashboard');
        return { success: true, message: data.message };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: t('errors.network') };
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (email, password, userData = {}) => {
    setAuthLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          username: userData.username,
          first_name: userData.firstName,
          last_name: userData.lastName
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        setCurrentView('dashboard');
        return { success: true, message: data.message };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: t('errors.network') };
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('currentUser');
    setCurrentView('dashboard');
  };

  // Language Functions
  const toggleLanguage = () => {
    const newLang = currentLanguage === 'ar' ? 'en' : 'ar';
    setCurrentLanguage(newLang);
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  // Gold Price Functions

  const fetchGoldPrice = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/gold-price`);
      const data = await response.json();
      if (data.success) {
        setGoldPrice(data.price_data);
      }
    } catch (err) {
      console.error('Error fetching gold price:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (analysisType = null, question = null) => {
    // Check if user is authenticated
    if (!isAuthenticated || !currentUser) {
      alert(t('auth.messages.loginRequired', 'يجب تسجيل الدخول للحصول على التحليل'));
      setCurrentView('login');
      return;
    }

    const actualQuestion = question || userQuestion;
    const actualType = analysisType || selectedAnalysisType;
    
    if (!actualQuestion.trim()) {
      console.error('No question provided for analysis');
      return;
    }

    // Set the selected analysis type for display
    setSelectedAnalysisType(actualType);
    setUserQuestion(actualQuestion);
    
    setAnalysisLoading(true);
    setCurrentView('results');
    
    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_type: actualType,
          user_question: actualQuestion,
          user_id: currentUser.user_id, // Include user ID
          additional_context: actualQuestion
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setAnalysisResult(data);
        // Update remaining analyses count
        if (currentUser) {
          const updatedUser = { ...currentUser, daily_analyses_remaining: currentUser.daily_analyses_remaining - 1 };
          setCurrentUser(updatedUser);
          localStorage.setItem('currentUser', JSON.stringify(updatedUser));
        }
      } else {
        setAnalysisResult(data);
      }
      
    } catch (err) {
      console.error('Error analyzing:', err);
      setAnalysisResult({
        success: false,
        error: t('errors.network', 'حدث خطأ في التحليل')
      });
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Forex Analysis Function
  const handleForexAnalysis = async (pair) => {
    setSelectedForexPair(pair);
    setForexAnalysisLoading(true);
    setCurrentView('forex-results');
    
    try {
      const response = await fetch(`${API_URL}/api/analyze-forex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pair: pair,
          analysis_type: 'detailed',
          additional_context: `تحليل شامل لزوج العملة ${pair}`
        })
      });
      
      const data = await response.json();
      setForexAnalysisResult(data);
      
    } catch (err) {
      console.error('Error analyzing forex:', err);
      setForexAnalysisResult({
        success: false,
        error: 'حدث خطأ في تحليل العملة'
      });
    } finally {
      setForexAnalysisLoading(false);
    }
  };

  const handleQuickQuestion = (question) => {
    setUserQuestion(question);
  };

  // Admin Panel Functions
  const handleAdminLogin = async () => {
    if (!adminUsername || !adminPassword) {
      alert('يرجى إدخال اسم المستخدم وكلمة المرور');
      return;
    }

    setAdminLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: adminUsername,
          password: adminPassword
        })
      });

      const data = await response.json();
      if (data.success) {
        setAdminAuthenticated(true);
        await fetchAdminDashboard();
        await fetchAdminUsers();
      } else {
        alert(data.error || 'فشل في تسجيل الدخول');
      }
    } catch (error) {
      console.error('Admin login error:', error);
      alert('خطأ في الاتصال بالخادم');
    } finally {
      setAdminLoading(false);
    }
  };

  const fetchAdminDashboard = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/dashboard`);
      const data = await response.json();
      if (data.success) {
        setAdminData(data.data);
      }
    } catch (error) {
      console.error('Fetch admin dashboard error:', error);
    }
  };

  const fetchAdminUsers = async (page = 1) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users?page=${page}&per_page=20`);
      const data = await response.json();
      if (data.success) {
        setAdminUsers(data.data.users);
        setAdminCurrentPage(page);
      }
    } catch (error) {
      console.error('Fetch admin users error:', error);
    }
  };

  const fetchAdminLogs = async (page = 1, userId = null) => {
    try {
      let url = `${API_URL}/api/admin/analysis-logs?page=${page}&per_page=50`;
      if (userId) {
        url += `&user_id=${userId}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        setAdminLogs(data.data.logs);
      }
    } catch (error) {
      console.error('Fetch admin logs error:', error);
    }
  };

  const toggleUserStatus = async (userId) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users/toggle-status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          admin_id: 'admin'
        })
      });

      const data = await response.json();
      if (data.success) {
        // Refresh users list
        await fetchAdminUsers(adminCurrentPage);
        alert(data.data.message);
      } else {
        alert(data.error || 'فشل في تغيير حالة المستخدم');
      }
    } catch (error) {
      console.error('Toggle user status error:', error);
      alert('خطأ في الاتصال بالخادم');
    }
  };

  const updateUserTier = async (userId, newTier) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users/update-tier`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          new_tier: newTier,
          admin_id: 'admin'
        })
      });

      const data = await response.json();
      if (data.success) {
        // Refresh users list
        await fetchAdminUsers(adminCurrentPage);
        alert(data.data.message);
      } else {
        alert(data.error || 'فشل في تحديث نوع الاشتراك');
      }
    } catch (error) {
      console.error('Update user tier error:', error);
      alert('خطأ في الاتصال بالخادم');
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('حجم الصورة كبير جداً. يرجى اختيار صورة أصغر من 10 ميجابايت.');
        return;
      }
      
      setSelectedImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(file);
    } else {
      alert('يرجى اختيار ملف صورة صحيح (JPG, PNG, etc.)');
    }
  };

  const handleChartAnalysis = async () => {
    if (!selectedImage) {
      alert('يرجى اختيار صورة الشارت أولاً');
      return;
    }

    setChartAnalysisLoading(true);
    setCurrentView('chart-analysis');
    
    try {
      // Convert image to base64
      const reader = new FileReader();
      reader.readAsDataURL(selectedImage);
      
      reader.onload = async () => {
        try {
          const response = await fetch(`${API_URL}/api/analyze-chart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_data: reader.result,
              currency_pair: currencyPair,
              timeframe: timeframe,
              analysis_notes: analysisNotes
            })
          });
          
          const data = await response.json();
          setChartAnalysisResult(data);
          
        } catch (err) {
          console.error('Error analyzing chart:', err);
          setChartAnalysisResult({
            success: false,
            error: 'حدث خطأ في تحليل الشارت'
          });
        } finally {
          setChartAnalysisLoading(false);
        }
      };
      
      reader.onerror = () => {
        setChartAnalysisResult({
          success: false,
          error: 'فشل في قراءة الصورة'
        });
        setChartAnalysisLoading(false);
      };
      
    } catch (err) {
      console.error('Error processing image:', err);
      setChartAnalysisResult({
        success: false,
        error: 'حدث خطأ في معالجة الصورة'
      });
      setChartAnalysisLoading(false);
    }
  };

  // Authentication Views
  const renderLoginView = () => {
    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!loginEmail || !loginPassword) {
        setLoginError('البريد الإلكتروني وكلمة المرور مطلوبان');
        return;
      }

      const result = await handleLogin(loginEmail, loginPassword);
      if (!result.success) {
        setLoginError(result.error);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex items-center justify-center p-4">
        <div className="glass-card p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              تسجيل الدخول
            </h1>
            <p className="text-purple-200">أدخل بياناتك للوصول لحسابك</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {loginError && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-red-300">
                {loginError}
              </div>
            )}

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                البريد الإلكتروني
              </label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full px-4 py-3 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
                placeholder="example@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  type={loginShowPassword ? "text" : "password"}
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors pr-12"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setLoginShowPassword(!loginShowPassword)}
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-gold transition-colors"
                >
                  {loginShowPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={authLoading}
              className="w-full royal-button py-3 font-semibold text-lg"
            >
              {authLoading ? 'جاري التحميل...' : 'تسجيل الدخول'}
            </button>
          </form>

          <div className="text-center mt-6 space-y-4">
            <p className="text-purple-300">
              ليس لديك حساب؟{' '}
              <button
                onClick={() => setCurrentView('register')}
                className="text-gold hover:text-yellow-300 font-medium transition-colors"
              >
                إنشاء حساب جديد
              </button>
            </p>
            
            <button
              onClick={() => setCurrentView('dashboard')}
              className="text-purple-400 hover:text-purple-200 transition-colors"
            >
              العودة
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderRegisterView = () => {
    const handleInputChange = (field, value) => {
      setRegisterFormData(prev => ({ ...prev, [field]: value }));
    };

    const validateForm = () => {
      if (!registerFormData.email || !registerFormData.password) {
        return 'البريد الإلكتروني وكلمة المرور مطلوبان';
      }
      
      if (registerFormData.password !== registerFormData.confirmPassword) {
        return 'كلمات المرور غير متطابقة';
      }

      if (registerFormData.password.length < 6) {
        return 'كلمة المرور يجب أن تكون 6 أحرف على الأقل';
      }

      return null;
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      const validationError = validateForm();
      if (validationError) {
        setRegisterError(validationError);
        return;
      }

      const result = await handleRegister(
        registerFormData.email, 
        registerFormData.password,
        {
          username: registerFormData.username,
          firstName: registerFormData.firstName,
          lastName: registerFormData.lastName
        }
      );
      
      if (!result.success) {
        setRegisterError(result.error);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex items-center justify-center p-4">
        <div className="glass-card p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              إنشاء حساب جديد
            </h1>
            <p className="text-purple-200">انضم إلينا واحصل على تحليلات الذهب المجانية</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {registerError && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-red-300">
                {registerError}
              </div>
            )}

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                البريد الإلكتروني *
              </label>
              <input
                type="email"
                value={registerFormData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full px-4 py-3 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
                placeholder="example@email.com"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-purple-200 text-sm font-medium mb-2">
                  الاسم الأول
                </label>
                <input
                  type="text"
                  value={registerFormData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className="w-full px-4 py-2 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label className="block text-purple-200 text-sm font-medium mb-2">
                  اسم العائلة
                </label>
                <input
                  type="text"
                  value={registerFormData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className="w-full px-4 py-2 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                اسم المستخدم
              </label>
              <input
                type="text"
                value={registerFormData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className="w-full px-4 py-2 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                كلمة المرور *
              </label>
              <div className="relative">
                <input
                  type={registerShowPassword ? "text" : "password"}
                  value={registerFormData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="w-full px-4 py-3 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors pr-12"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setRegisterShowPassword(!registerShowPassword)}
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-gold transition-colors"
                >
                  {registerShowPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                تأكيد كلمة المرور *
              </label>
              <input
                type="password"
                value={registerFormData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                className="w-full px-4 py-3 bg-black/20 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={authLoading}
              className="w-full royal-button py-3 font-semibold text-lg mt-6"
            >
              {authLoading ? 'جاري التحميل...' : 'إنشاء الحساب'}
            </button>
          </form>

          <div className="text-center mt-6 space-y-4">
            <p className="text-purple-300">
              لديك حساب بالفعل؟{' '}
              <button
                onClick={() => setCurrentView('login')}
                className="text-gold hover:text-yellow-300 font-medium transition-colors"
              >
                تسجيل الدخول
              </button>
            </p>
            
            <button
              onClick={() => setCurrentView('dashboard')}
              className="text-purple-400 hover:text-purple-200 transition-colors"
            >
              العودة
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderDashboard = () => (
    <div className="min-h-screen royal-text" style={{
      background: 'linear-gradient(135deg, #0A0F2C, #3C1E70, #8C00FF)',
      fontFamily: "'Cairo', sans-serif"
    }}>
      
      {/* Header */}
      <div className="text-center py-8">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold royal-text mb-4 flex items-center justify-center">
            <span className="gold-text mr-3">🏆</span>
            al_kabous ai
          </h1>
          <p className="text-purple-200 text-lg">
            {currentLanguage === 'ar' ? 'مدرسة الكابوس الذهبية - تحليل الذهب والعملات الذكي' : 'Gold Nightmare School - Smart Gold & Currency Analysis'}
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-8">

        {/* Welcome Section for Non-Authenticated Users */}
        {!isAuthenticated && (
          <div className="text-center mb-12">
            {/* Welcome Message */}
            <div className="glass-card p-8 mb-8">
              <div className="text-6xl mb-6">🔐</div>
              <h2 className="text-3xl font-bold text-white mb-4">
                {currentLanguage === 'ar' ? 'مرحباً بك في al_kabous ai' : 'Welcome to al_kabous ai'}
              </h2>
              <p className="text-purple-200 text-lg mb-8 leading-relaxed">
                {currentLanguage === 'ar' ? 
                  'منصة متخصصة في تحليل الذهب والعملات باستخدام الذكاء الاصطناعي. سجل دخولك أو أنشئ حساب مجاني للبدء.' :
                  'Specialized platform for gold and currency analysis using artificial intelligence. Log in or create a free account to get started.'}
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
                <button
                  onClick={() => setCurrentView('register')}
                  className="royal-button px-8 py-4 font-semibold text-lg"
                >
                  📝 {currentLanguage === 'ar' ? 'إنشاء حساب مجاني' : 'Create Free Account'}
                </button>
                <button
                  onClick={() => setCurrentView('login')}
                  className="px-8 py-4 bg-blue-600/20 border border-blue-500/30 rounded-lg text-blue-300 hover:bg-blue-600/30 transition-all font-semibold text-lg"
                >
                  🔐 {currentLanguage === 'ar' ? 'تسجيل الدخول' : 'Login'}
                </button>
              </div>
            </div>

            {/* Features Preview */}
            <div className="glass-card p-8 mb-8">
              <h3 className="text-2xl font-bold text-white mb-6 flex items-center justify-center">
                <span className="gold-text mr-3">✨</span>
                {currentLanguage === 'ar' ? 'ميزات المنصة' : 'Platform Features'}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-black/20 border border-purple-500/30 rounded-lg">
                  <div className="text-4xl mb-4">📊</div>
                  <h4 className="text-lg font-bold text-white mb-2">
                    {currentLanguage === 'ar' ? 'تحليل ذكي للذهب' : 'Smart Gold Analysis'}
                  </h4>
                  <p className="text-purple-200 text-sm">
                    {currentLanguage === 'ar' ? 'تحليلات احترافية مدعومة بالذكاء الاصطناعي' : 'Professional AI-powered analysis'}
                  </p>
                </div>
                
                <div className="text-center p-6 bg-black/20 border border-purple-500/30 rounded-lg">
                  <div className="text-4xl mb-4">💱</div>
                  <h4 className="text-lg font-bold text-white mb-2">
                    {currentLanguage === 'ar' ? 'تحليل العملات' : 'Currency Analysis'}
                  </h4>
                  <p className="text-purple-200 text-sm">
                    {currentLanguage === 'ar' ? 'تحليل أزواج العملات الرئيسية' : 'Major currency pairs analysis'}
                  </p>
                </div>
                
                <div className="text-center p-6 bg-black/20 border border-purple-500/30 rounded-lg">
                  <div className="text-4xl mb-4">📈</div>
                  <h4 className="text-lg font-bold text-white mb-2">
                    {currentLanguage === 'ar' ? 'تحليل الشارت' : 'Chart Analysis'}
                  </h4>
                  <p className="text-purple-200 text-sm">
                    {currentLanguage === 'ar' ? 'تحليل الشارت بالصور باستخدام الذكاء الاصطناعي' : 'AI-powered image chart analysis'}
                  </p>
                </div>
              </div>
            </div>

            {/* Subscription Tiers Preview */}
            <div className="glass-card p-8">
              <h3 className="text-2xl font-bold text-white mb-6 flex items-center justify-center">
                <span className="gold-text mr-3">💎</span>
                {currentLanguage === 'ar' ? 'باقات الاشتراك' : 'Subscription Plans'}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-gray-900/30 border border-gray-500/30 rounded-lg">
                  <div className="text-3xl mb-2">🆓</div>
                  <h4 className="text-lg font-bold text-gray-300 mb-2">
                    {currentLanguage === 'ar' ? 'أساسي' : 'Basic'}
                  </h4>
                  <p className="text-lg font-bold text-gray-400 mb-4">
                    {currentLanguage === 'ar' ? 'مجاني' : 'Free'}
                  </p>
                  <ul className="text-sm text-gray-300 text-left space-y-1">
                    <li>✓ {currentLanguage === 'ar' ? 'تحليل واحد يومياً' : '1 analysis per day'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'تحليل أساسي للذهب' : 'Basic gold analysis'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'دعم عبر البريد' : 'Email support'}</li>
                  </ul>
                </div>
                
                <div className="text-center p-6 bg-blue-900/30 border border-blue-500/50 rounded-lg relative">
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold">
                      {currentLanguage === 'ar' ? 'الأكثر شعبية' : 'Most Popular'}
                    </span>
                  </div>
                  <div className="text-3xl mb-2">⭐</div>
                  <h4 className="text-lg font-bold text-blue-300 mb-2">
                    {currentLanguage === 'ar' ? 'مميز' : 'Premium'}
                  </h4>
                  <p className="text-lg font-bold text-blue-400 mb-4">$19/{currentLanguage === 'ar' ? 'شهر' : 'month'}</p>
                  <ul className="text-sm text-blue-200 text-left space-y-1">
                    <li>✓ {currentLanguage === 'ar' ? '5 تحليلات يومياً' : '5 analyses per day'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'حفظ سجل التحليلات' : 'Analysis history'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'تحليلات متقدمة' : 'Advanced analysis'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'الرسوم البيانية المتقدمة' : 'Advanced charts'}</li>
                  </ul>
                </div>
                
                <div className="text-center p-6 bg-yellow-900/30 border border-yellow-500/50 rounded-lg">
                  <div className="text-3xl mb-2">👑</div>
                  <h4 className="text-lg font-bold text-yellow-300 mb-2">VIP</h4>
                  <p className="text-lg font-bold text-yellow-400 mb-4">$49/{currentLanguage === 'ar' ? 'شهر' : 'month'}</p>
                  <ul className="text-sm text-yellow-200 text-left space-y-1">
                    <li>✓ {currentLanguage === 'ar' ? 'تحليلات غير محدودة' : 'Unlimited analyses'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'دعم أولوية' : 'Priority support'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'تحليل صوتي' : 'Voice analysis'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'مؤشرات مخصصة' : 'Custom indicators'}</li>
                    <li>✓ {currentLanguage === 'ar' ? 'جميع الميزات' : 'All features'}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Authenticated Users - Redirect to Analysis Dashboard */}
        {isAuthenticated && (
          <div className="text-center">
            <div className="glass-card p-8">
              <div className="text-6xl mb-6">🎉</div>
              <h2 className="text-3xl font-bold text-white mb-4">
                {currentLanguage === 'ar' ? `مرحباً ${currentUser?.email?.split('@')[0] || 'مستخدم'}!` : `Welcome ${currentUser?.email?.split('@')[0] || 'User'}!`}
              </h2>
              <p className="text-purple-200 text-lg mb-8">
                {currentLanguage === 'ar' ? 'تم تسجيل الدخول بنجاح. انتقل إلى لوحة التحليل للبدء.' : 'Successfully logged in. Go to analysis dashboard to get started.'}
              </p>
              
              <button
                onClick={() => setCurrentView('analysis-dashboard')}
                className="royal-button px-8 py-4 font-semibold text-lg"
              >
                📊 {currentLanguage === 'ar' ? 'انتقل إلى لوحة التحليل' : 'Go to Analysis Dashboard'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalysisDashboard = () => (
    <div className="min-h-screen royal-text" style={{
      background: 'linear-gradient(135deg, #0A0F2C, #3C1E70, #8C00FF)',
      fontFamily: "'Cairo', sans-serif"
    }}>
      
      {/* Header */}
      <div className="text-center py-8">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold royal-text mb-4 flex items-center justify-center">
            <span className="gold-text mr-3">🏆</span>
            al_kabous ai
          </h1>
          <p className="text-purple-200 text-lg">
            {currentLanguage === 'ar' ? 'مدرسة الكابوس الذهبية - تحليل الذهب والعملات الذكي' : 'Gold Nightmare School - Smart Gold & Currency Analysis'}
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-8">

        {/* User Subscription Info */}
        {isAuthenticated && currentUser && (
          <div className="glass-card p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center">
                <span className="text-blue-400 mr-3">👤</span>
                {t('dashboard.welcome')}, {currentUser.email?.split('@')[0] || 'مستخدم'}
              </h2>
              <div className="text-sm text-purple-300">
                ID: {currentUser.user_id}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="bg-black/20 border border-purple-500/30 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-2">{t('dashboard.subscription.current')}</p>
                <p className={`text-2xl font-bold ${
                  currentUser.tier === 'basic' ? 'text-gray-400' :
                  currentUser.tier === 'premium' ? 'text-blue-400' : 'text-yellow-400'
                }`}>
                  {currentUser.tier === 'basic' ? t('subscription.tiers.basic.name') :
                   currentUser.tier === 'premium' ? t('subscription.tiers.premium.name') :
                   t('subscription.tiers.vip.name')}
                </p>
              </div>
              
              <div className="bg-black/20 border border-purple-500/30 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-2">{t('dashboard.subscription.analysesRemaining')}</p>
                <p className="text-2xl font-bold text-green-400">
                  {currentUser.daily_analyses_remaining === -1 ? 
                    t('dashboard.subscription.unlimited') : 
                    currentUser.daily_analyses_remaining || 0}
                </p>
              </div>
              
              <div className="bg-black/20 border border-purple-500/30 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-2">إجمالي التحليلات</p>
                <p className="text-2xl font-bold text-purple-400">
                  {currentUser.total_analyses || 0}
                </p>
              </div>
            </div>

            {/* Upgrade message for basic users */}
            {currentUser.tier === 'basic' && currentUser.daily_analyses_remaining === 0 && (
              <div className="mt-4 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded-lg text-center">
                <p className="text-yellow-300 font-medium">
                  ⚠️ تم استنفاد حد التحليلات اليومية
                </p>
                <p className="text-yellow-200 text-sm mt-2">
                  تواصل مع الإدارة لترقية اشتراكك والحصول على المزيد من التحليلات
                </p>
              </div>
            )}
          </div>
        )}

        {/* Current Gold Price */}
        {goldPrice && (
          <div className="glass-card p-6 mb-8">
            <h2 className="text-2xl font-bold royal-text mb-6 flex items-center justify-center">
              <span className="gold-text mr-3">💰</span>
              السعر الحالي للذهب
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-purple-300 text-sm">السعر الحالي</p>
                <p className="text-3xl font-bold gold-text">${goldPrice.price_usd?.toFixed(2) || '---'}</p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">التغيير اليومي</p>
                <p className={`text-2xl font-bold ${goldPrice.price_change >= 0 ? 'price-high' : 'price-low'}`}>
                  {goldPrice.price_change >= 0 ? '+' : ''}{goldPrice.price_change?.toFixed(2) || '---'}
                </p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">أعلى سعر</p>
                <p className="text-2xl font-bold price-high">${goldPrice.high_24h?.toFixed(2) || '---'}</p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">أقل سعر</p>
                <p className="text-2xl font-bold price-low">${goldPrice.low_24h?.toFixed(2) || '---'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Gold Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center justify-center">
            <span className="gold-text mr-3">📊</span>
            تحليل الذهب الاحترافي
          </h2>
          
          <p className="text-center text-purple-200 mb-8">
            احصل على تحليلات احترافية للذهب مدعومة بالذكاء الاصطناعي - تحليلات فنية وأساسية وتوقعات دقيقة
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <button 
              onClick={() => handleAnalyze('quick', 'تحليل سريع للذهب الحالي')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">⚡</div>
              سريع
            </button>
            
            <button 
              onClick={() => handleAnalyze('technical', 'تحليل فني مفصل للذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📈</div>
              فني
            </button>
            
            <button 
              onClick={() => handleAnalyze('news', 'تحليل آخر أخبار الذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📰</div>
              أخبار
            </button>
            
            <button 
              onClick={() => handleAnalyze('forecast', 'توقعات الذهب المستقبلية')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🔮</div>
              توقعات
            </button>
            
            <button 
              onClick={() => handleAnalyze('detailed', 'تحليل شامل ومفصل للذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📋</div>
              مفصل
            </button>
          </div>

          {/* Custom Analysis Section */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-4 flex items-center justify-center">
              <span className="text-purple-400 mr-3">🎯</span>
              تحليل مخصص
            </h3>
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                value={userQuestion}
                onChange={(e) => setUserQuestion(e.target.value)}
                placeholder="اكتب سؤالك حول الذهب هنا..."
                className="flex-1 px-4 py-3 bg-black/30 border border-purple-500/50 rounded-lg text-white placeholder-purple-300 focus:border-gold focus:outline-none transition-colors"
              />
              <button
                onClick={() => setCurrentView('analyze')}
                disabled={!userQuestion.trim()}
                className="px-6 py-3 royal-button font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                طلب تحليل مخصص
              </button>
            </div>
          </div>
        </div>

        {/* Chart Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center justify-center">
            <span className="gold-text mr-3">📊</span>
            تحليل الشارت بالصورة
          </h2>
          
          <p className="text-center text-purple-200 mb-8">
            ارفع صورة الشارت واحصل على تحليل فني احترافي مدعوم بالذكاء الاصطناعي
          </p>
          
          <div className="text-center">
            <button
              onClick={() => setCurrentView('chart-analysis')}
              className="royal-button px-8 py-4 font-semibold text-lg"
            >
              📷 رفع الشارت والتحليل
            </button>
          </div>
        </div>

        {/* Forex Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center justify-center">
            <span className="gold-text mr-2">💱</span>
            تحليل العملات
          </h2>
          
          <p className="text-center text-purple-200 mb-8">
            تحليل العملات الرئيسية في السوق العالمي بتقنية الذكاء الاصطناعي
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => handleForexAnalysis('EUR/USD')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇪🇺</div>
              EUR/USD
            </button>
            
            <button 
              onClick={() => handleForexAnalysis('USD/JPY')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇯🇵</div>
              USD/JPY
            </button>
            
            <button 
              onClick={() => handleForexAnalysis('GBP/USD')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇬🇧</div>
              GBP/USD
            </button>
          </div>
        </div>

        {/* Quick Questions */}
        <div className="glass-card p-6">
          <h3 className="text-2xl font-bold royal-text mb-6 flex items-center justify-center">
            <span className="gold-text mr-3">❓</span>
            أسئلة سريعة
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuickQuestion(question)}
                className="text-right p-4 bg-gradient-to-r from-purple-700/30 to-blue-700/30 border border-purple-500/30 rounded-lg text-purple-200 hover:bg-gradient-to-r hover:from-purple-700/50 hover:to-blue-700/50 transition-all transform hover:scale-105 font-medium"
              >
                💭 {question}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalyzeView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-2xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-purple-400 mr-3">🎯</span>
            طلب التحليل
          </h1>
          <p className="text-purple-200">اكتب سؤالك أو اختر من الأسئلة الجاهزة</p>
        </div>

        <div className="glass-card p-6 mb-6">
          
          {/* Analysis Type Selector */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-4">نوع التحليل:</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { id: 'quick', name: 'سريع', icon: '⚡' },
                { id: 'detailed', name: 'مفصل', icon: '📊' },
                { id: 'chart', name: 'فني', icon: '📈' },
                { id: 'news', name: 'أخبار', icon: '📰' },
                { id: 'forecast', name: 'توقعات', icon: '🔮' }
              ].map(type => (
                <button
                  key={type.id}
                  onClick={() => setSelectedAnalysisType(type.id)}
                  className={`p-3 rounded-lg font-medium transition-all ${
                    selectedAnalysisType === type.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-purple-800/50 text-purple-200 hover:bg-purple-700/50'
                  }`}
                >
                  <div className="text-lg mb-1">{type.icon}</div>
                  {type.name}
                </button>
              ))}
            </div>
          </div>

          {/* Question Input */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-4">اكتب سؤالك:</h3>
            <textarea
              value={userQuestion}
              onChange={(e) => setUserQuestion(e.target.value)}
              placeholder="مثال: ما رأيك في اتجاه الذهب خلال الأسبوع القادم؟"
              className="w-full h-32 p-4 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-purple-400 resize-none"
            />
          </div>

          {/* Quick Questions */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-4">أسئلة سريعة:</h3>
            <div className="space-y-2">
              {quickQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => setUserQuestion(question)}
                  className="w-full p-3 text-right bg-purple-800/30 hover:bg-purple-700/50 border border-purple-600/30 rounded-lg text-purple-200 transition-all"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => setCurrentView('dashboard')}
              className="flex-1 py-3 px-6 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
            >
              العودة
            </button>
            <button
              onClick={() => handleAnalyze(selectedAnalysisType, userQuestion)}
              disabled={!userQuestion.trim()}
              className="flex-1 py-3 px-6 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 disabled:from-gray-500 disabled:to-gray-600 text-white rounded-lg font-bold transition-all disabled:cursor-not-allowed"
            >
              <span className="mr-2">📊</span>
              تحليل الذهب
            </button>
          </div>

        </div>

      </div>
    </div>
  );

  const renderChartAnalysisView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-orange-400 mr-3">📊</span>
            تحليل الشارت الاحترافي
          </h1>
          <p className="text-purple-200">ارفع صورة الشارت واحصل على تحليل فني شامل مدعوم بالذكاء الاصطناعي</p>
        </div>

        <div className="glass-card p-6 mb-6">
          
          {/* Image Upload Section */}
          <div className="mb-8">
            <h3 className="text-white font-semibold mb-4 flex items-center">
              <span className="text-orange-400 mr-2">📷</span>
              ارفع صورة الشارت
            </h3>
            
            <div className="border-2 border-dashed border-orange-400/50 rounded-xl p-8 text-center bg-gradient-to-br from-orange-900/20 to-red-900/20">
              {imagePreview ? (
                <div className="space-y-4">
                  <img 
                    src={imagePreview} 
                    alt="Chart preview" 
                    className="max-w-full max-h-96 mx-auto rounded-lg shadow-lg"
                  />
                  <div className="text-green-400 font-medium">
                    ✅ تم تحميل الصورة بنجاح
                  </div>
                  <button
                    onClick={() => {
                      setSelectedImage(null);
                      setImagePreview(null);
                      document.getElementById('chart-upload').value = '';
                    }}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                  >
                    🗑️ حذف الصورة
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-6xl mb-4">📊</div>
                  <p className="text-white text-lg font-medium">اضغط لرفع الشارت أو اسحب الملف هنا</p>
                  <p className="text-purple-300 text-sm">PNG, JPG, JPEG (أقل من 10 ميجابايت)</p>
                  <input
                    id="chart-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                  <button
                    onClick={() => document.getElementById('chart-upload').click()}
                    className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white rounded-lg font-medium transition-all transform hover:scale-105"
                  >
                    📁 اختيار ملف
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Quick Analysis Buttons */}
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-4 flex items-center">
              <span className="text-yellow-400 mr-2">⚡</span>
              تحليل سريع
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button
                onClick={() => {
                  setCurrencyPair('XAU/USD');
                  setTimeframe('H1');
                  setAnalysisNotes('تحليل سريع للذهب');
                }}
                className="p-3 bg-gradient-to-r from-yellow-600/80 to-orange-600/80 hover:from-yellow-500/80 hover:to-orange-500/80 text-white rounded-lg font-medium transition-all"
              >
                🥇 XAU/USD
              </button>
              <button
                onClick={() => {
                  setCurrencyPair('EUR/USD');
                  setTimeframe('H1');
                  setAnalysisNotes('تحليل سريع لليورو');
                }}
                className="p-3 bg-gradient-to-r from-blue-600/80 to-cyan-600/80 hover:from-blue-500/80 hover:to-cyan-500/80 text-white rounded-lg font-medium transition-all"
              >
                🇪🇺 EUR/USD
              </button>
              <button
                onClick={() => {
                  setCurrencyPair('GBP/USD');
                  setTimeframe('H1');
                  setAnalysisNotes('تحليل سريع للجنيه');
                }}
                className="p-3 bg-gradient-to-r from-purple-600/80 to-indigo-600/80 hover:from-purple-500/80 hover:to-indigo-500/80 text-white rounded-lg font-medium transition-all"
              >
                🇬🇧 GBP/USD
              </button>
              <button
                onClick={() => {
                  setCurrencyPair('USD/JPY');
                  setTimeframe('H1');
                  setAnalysisNotes('تحليل سريع للين');
                }}
                className="p-3 bg-gradient-to-r from-red-600/80 to-pink-600/80 hover:from-red-500/80 hover:to-pink-500/80 text-white rounded-lg font-medium transition-all"
              >
                🇯🇵 USD/JPY
              </button>
            </div>
          </div>

          {/* Detailed Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            
            {/* Currency Pair */}
            <div>
              <label className="block text-white font-semibold mb-2">
                <span className="text-green-400 mr-2">💱</span>
                زوج العملة
              </label>
              <input
                type="text"
                value={currencyPair}
                onChange={(e) => setCurrencyPair(e.target.value)}
                placeholder="مثال: XAU/USD"
                className="w-full p-3 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-orange-400"
              />
            </div>

            {/* Timeframe */}
            <div>
              <label className="block text-white font-semibold mb-2">
                <span className="text-blue-400 mr-2">⏰</span>
                الإطار الزمني
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full p-3 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white focus:outline-none focus:border-orange-400"
              >
                <option value="M1">دقيقة واحدة (M1)</option>
                <option value="M5">5 دقائق (M5)</option>
                <option value="M15">15 دقيقة (M15)</option>
                <option value="M30">30 دقيقة (M30)</option>
                <option value="H1">ساعة (H1)</option>
                <option value="H4">4 ساعات (H4)</option>
                <option value="D1">يومي (D1)</option>
                <option value="W1">أسبوعي (W1)</option>
                <option value="MN1">شهري (MN1)</option>
              </select>
            </div>
          </div>

          {/* Analysis Notes */}
          <div className="mb-6">
            <label className="block text-white font-semibold mb-2">
              <span className="text-pink-400 mr-2">📝</span>
              ملاحظات إضافية للتحليل
            </label>
            <textarea
              value={analysisNotes}
              onChange={(e) => setAnalysisNotes(e.target.value)}
              placeholder="أضف أي ملاحظات أو أسئلة خاصة حول الشارت..."
              rows="3"
              className="w-full p-3 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-orange-400 resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => setCurrentView('dashboard')}
              className="flex-1 py-3 px-6 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
            >
              العودة
            </button>
            <button
              onClick={handleChartAnalysis}
              disabled={!selectedImage}
              className="flex-2 py-3 px-8 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 disabled:from-gray-500 disabled:to-gray-600 text-white rounded-lg font-bold transition-all disabled:cursor-not-allowed transform hover:scale-105"
            >
              <span className="mr-2">🚀</span>
              تحليل الشارت الآن
            </button>
          </div>

        </div>

      </div>
    </div>
  );

  const renderResultsView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-yellow-400 mr-3">🏆</span>
            تحليل al_kabous ai
          </h1>
          <p className="text-purple-200">تحليل ذكي ومتقدم للأسواق المالية</p>
          <button 
            onClick={fetchGoldPrice}
            className="mt-4 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg transition-colors text-sm"
          >
            🔄 تحديث السعر
          </button>
        </div>

        {/* Current Price Display */}
        {goldPrice && (
          <div className="glass-card p-6 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-purple-300 text-sm">السعر الحالي</p>
                <p className="text-3xl font-bold text-white">${goldPrice.price_usd?.toFixed(2) || '---'}</p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">التغيير اليومي</p>
                <p className={`text-2xl font-bold ${goldPrice.price_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {goldPrice.price_change >= 0 ? '+' : ''}{goldPrice.price_change?.toFixed(2) || '---'}
                </p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">أعلى سعر</p>
                <p className="text-2xl font-bold text-green-400">${goldPrice.high_24h?.toFixed(2) || '---'}</p>
              </div>
              <div>
                <p className="text-purple-300 text-sm">أقل سعر</p>
                <p className="text-2xl font-bold text-red-400">${goldPrice.low_24h?.toFixed(2) || '---'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        <div className="glass-card p-6 mb-6">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="text-green-400 mr-3">🎯</span>
            نتائج التحليل
          </h2>
          <p className="text-purple-200 mb-6">تحليل ذكي مدعوم بالذكاء الاصطناعي مع التوصيات</p>
          
          {/* Handle both regular analysis and chart analysis and forex analysis */}
          {analysisLoading || chartAnalysisLoading || forexAnalysisLoading ? (
            <div className="text-center py-12">
              <div className="royal-loading mx-auto mb-6"></div>
              <p className="royal-text text-lg">جاري إجراء التحليل الذكي...</p>
              <p className="text-purple-300 text-sm mt-2">قد يستغرق هذا بعض الوقت</p>
            </div>
          ) : (analysisResult || chartAnalysisResult || forexAnalysisResult) ? (
            // Show results
            (() => {
              const result = analysisResult || chartAnalysisResult || forexAnalysisResult;
              return result.success ? (
                <div className="space-y-4">
                  {/* Show forex price info if it's forex analysis */}
                  {forexAnalysisResult && forexAnalysisResult.forex_price && (
                    <div className="glass-card p-6 mb-4">
                      <h4 className="gold-text font-medium mb-4 flex items-center">
                        <span className="mr-2">💱</span>
                        معلومات السعر - {forexAnalysisResult.forex_price.pair}
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div>
                          <p className="text-purple-300 text-sm">السعر الحالي</p>
                          <p className="text-xl font-bold gold-text">{forexAnalysisResult.forex_price.price_usd?.toFixed(4)}</p>
                        </div>
                        <div>
                          <p className="text-purple-300 text-sm">التغيير</p>
                          <p className={`text-xl font-bold ${forexAnalysisResult.forex_price.price_change >= 0 ? 'price-high' : 'price-low'}`}>
                            {forexAnalysisResult.forex_price.price_change >= 0 ? '+' : ''}{forexAnalysisResult.forex_price.price_change?.toFixed(4)}
                          </p>
                        </div>
                        <div>
                          <p className="text-purple-300 text-sm">أعلى سعر</p>
                          <p className="text-xl font-bold price-high">{forexAnalysisResult.forex_price.high_24h?.toFixed(4)}</p>
                        </div>
                        <div>
                          <p className="text-purple-300 text-sm">أقل سعر</p>
                          <p className="text-xl font-bold price-low">{forexAnalysisResult.forex_price.low_24h?.toFixed(4)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Show image info if it's chart analysis */}
                  {chartAnalysisResult && chartAnalysisResult.image_info && (
                    <div className="bg-blue-900/30 rounded-lg p-4 border border-blue-500/30 mb-4">
                      <h4 className="text-blue-300 font-medium mb-2">📊 معلومات الصورة:</h4>
                      <div className="text-sm text-blue-200">
                        <p>الأبعاد: {chartAnalysisResult.image_info.width} × {chartAnalysisResult.image_info.height}</p>
                        <p>الحجم: {chartAnalysisResult.image_info.size_kb.toFixed(1)} كيلوبايت</p>
                        <p>النوع: {chartAnalysisResult.image_info.format}</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="bg-purple-800/30 rounded-lg p-6 border border-purple-600/30">
                    <div className="prose prose-invert max-w-none">
                      <div className="royal-text whitespace-pre-line leading-relaxed">
                        {result.analysis}
                      </div>
                    </div>
                  </div>
                  
                  {result.processing_time && (
                    <div className="text-center text-purple-300 text-sm">
                      ⏱️ وقت المعالجة: {result.processing_time.toFixed(2)} ثانية
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-6xl mb-4">⚠️</div>
                  <p className="text-red-300 text-lg">حدث خطأ في التحليل</p>
                  <p className="text-purple-300 text-sm mt-2">
                    {result.error || 'خطأ غير معروف'}
                  </p>
                </div>
              );
            })()
          ) : (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">⚠️</div>
              <p className="text-yellow-300 text-lg">لا يوجد تحليل بعد</p>
              <p className="text-purple-300 text-sm mt-2">قم بطلب تحليل للحصول على النتائج</p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="text-center space-y-4">
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => {
                // Reset states and go back to appropriate view
                if (chartAnalysisResult) {
                  setCurrentView('chart-analysis');
                  setChartAnalysisResult(null);
                } else if (forexAnalysisResult) {
                  setCurrentView('dashboard');
                  setForexAnalysisResult(null);
                } else {
                  setCurrentView('analyze');
                  setAnalysisResult(null);
                }
              }}
              className="royal-button px-6 py-3 font-medium"
            >
              طلب تحليل جديد
            </button>
            <button
              onClick={() => setCurrentView('dashboard')}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
            >
              العودة للرئيسية
            </button>
          </div>
        </div>

      </div>
    </div>
  );

  const renderContactView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-green-400 mr-3">📞</span>
            التواصل مع al_kabous ai
          </h1>
          <p className="text-purple-200">مدرسة الكابوس الذهبية - جميع وسائل التواصل والقنوات</p>
        </div>

        {/* Contact Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          
          {/* Personal Contact Card */}
          <div className="glass-card p-6">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="text-green-400 mr-3">👤</span>
              Personal Contact
            </h2>
            <div className="space-y-4">
              <a 
                href="https://wa.me/962786275654" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-green-600/20 border border-green-500/30 rounded-lg text-purple-200 hover:bg-green-600/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">💬</span>
                <div>
                  <p className="font-bold text-white text-lg">واتساب</p>
                  <p className="text-green-300">962786275654</p>
                  <p className="text-sm">للاستفسارات الشخصية</p>
                </div>
              </a>
              
              <a 
                href="https://t.me/Odai_xau" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-blue-600/20 border border-blue-500/30 rounded-lg text-purple-200 hover:bg-blue-600/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">📱</span>
                <div>
                  <p className="font-bold text-white text-lg">تليجرام شخصي</p>
                  <p className="text-blue-300">@Odai_xau</p>
                  <p className="text-sm">للتواصل المباشر</p>
                </div>
              </a>
              
              <a 
                href="https://www.instagram.com/odai_xau?igsh=MWtrOXNleGlnY3k1aQ==" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-pink-600/20 border border-pink-500/30 rounded-lg text-purple-200 hover:bg-pink-600/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">📷</span>
                <div>
                  <p className="font-bold text-white text-lg">انستغرام</p>
                  <p className="text-pink-300">@odai_xau</p>
                  <p className="text-sm">أحدث المنشورات</p>
                </div>
              </a>
              
              <a 
                href="https://www.facebook.com/odaiaboamera" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-blue-800/20 border border-blue-700/30 rounded-lg text-purple-200 hover:bg-blue-800/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">📘</span>
                <div>
                  <p className="font-bold text-white text-lg">فيسبوك</p>
                  <p className="text-blue-300">عدي أبو عامرة</p>
                  <p className="text-sm">متابعة أخبار السوق</p>
                </div>
              </a>
            </div>
          </div>

          {/* Channels Card */}
          <div className="glass-card p-6">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="text-blue-400 mr-3">📡</span>
              القنوات الرسمية
            </h2>
            <div className="space-y-4">
              <a 
                href="https://t.me/odai_xauusdt" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-yellow-600/20 border border-yellow-500/30 rounded-lg text-purple-200 hover:bg-yellow-600/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">📊</span>
                <div>
                  <p className="font-bold text-white text-lg">قناة التوصيات</p>
                  <p className="text-yellow-300">@odai_xauusdt</p>
                  <p className="text-sm">توصيات الذهب والعملات اليومية</p>
                </div>
              </a>
              
              <a 
                href="https://t.me/odai_xau_usd" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center p-4 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-200 hover:bg-purple-600/30 transition-all transform hover:scale-105"
              >
                <span className="text-3xl mr-4">💬</span>
                <div>
                  <p className="font-bold text-white text-lg">قناة المناقشات</p>
                  <p className="text-purple-300">@odai_xau_usd</p>
                  <p className="text-sm">نقاش وتحليل الأسواق مع المتابعين</p>
                </div>
              </a>
            </div>
          </div>
        </div>

        {/* About Section */}
        <div className="glass-card p-6 mb-6 text-center">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-yellow-400 mr-3">🏆</span>
            مدرسة الكابوس الذهبية
          </h2>
          <p className="text-purple-200 text-lg leading-relaxed mb-4">
            خبرة أكثر من 20 سنة في تحليل الأسواق المالية، متخصصون في تحليل الذهب والعملات الأجنبية
          </p>
          <p className="text-purple-300">
            نقدم تحليلات دقيقة ومدروسة لمساعدة المتداولين على اتخاذ قرارات صحيحة في الأسواق
          </p>
        </div>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={() => setCurrentView('dashboard')}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-medium transition-all transform hover:scale-105"
          >
            <span className="mr-2">🏠</span>
            العودة للرئيسية
          </button>
        </div>

      </div>
    </div>
  );

  const renderAdminView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-red-400 mr-3">🔧</span>
            لوحة التحكم الإدارية
          </h1>
          <p className="text-purple-200">إدارة النظام والمستخدمين</p>
        </div>

        {!adminAuthenticated ? (
          /* Login Form */
          <div className="max-w-md mx-auto">
            <div className="glass-card p-6">
              <h2 className="text-2xl font-bold text-white mb-6 text-center flex items-center justify-center">
                <span className="text-yellow-400 mr-3">🔐</span>
                تسجيل الدخول
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-white font-medium mb-2">اسم المستخدم</label>
                  <input
                    type="text"
                    value={adminUsername}
                    onChange={(e) => setAdminUsername(e.target.value)}
                    className="w-full p-3 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-red-400"
                    placeholder="أدخل اسم المستخدم"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-medium mb-2">كلمة المرور</label>
                  <input
                    type="password"
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    className="w-full p-3 bg-purple-800/30 border border-purple-600/50 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-red-400"
                    placeholder="أدخل كلمة المرور"
                  />
                </div>
                
                <div className="flex gap-4">
                  <button
                    onClick={() => setCurrentView('dashboard')}
                    className="flex-1 py-3 px-6 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
                  >
                    العودة
                  </button>
                  <button
                    onClick={handleAdminLogin}
                    disabled={adminLoading || !adminUsername || !adminPassword}
                    className="flex-1 py-3 px-6 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 disabled:from-gray-500 disabled:to-gray-600 text-white rounded-lg font-bold transition-all disabled:cursor-not-allowed"
                  >
                    {adminLoading ? (
                      <span className="flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        جاري التحقق...
                      </span>
                    ) : (
                      <>
                        <span className="mr-2">🔓</span>
                        دخول
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Admin Dashboard */
          <div className="space-y-6">
            
            {/* Dashboard Stats */}
            {adminData && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="glass-card p-6 text-center">
                  <div className="text-3xl mb-2">👥</div>
                  <div className="text-2xl font-bold text-white">{adminData.total_users || 0}</div>
                  <div className="text-purple-300">إجمالي المستخدمين</div>
                </div>
                
                <div className="glass-card p-6 text-center">
                  <div className="text-3xl mb-2">✅</div>
                  <div className="text-2xl font-bold text-green-400">{adminData.active_users || 0}</div>
                  <div className="text-purple-300">المستخدمين النشطين</div>
                </div>
                
                <div className="glass-card p-6 text-center">
                  <div className="text-3xl mb-2">📊</div>
                  <div className="text-2xl font-bold text-blue-400">{adminData.total_analyses || 0}</div>
                  <div className="text-purple-300">إجمالي التحليلات</div>
                </div>
                
                <div className="glass-card p-6 text-center">
                  <div className="text-3xl mb-2">📈</div>
                  <div className="text-2xl font-bold text-yellow-400">{adminData.analyses_today || 0}</div>
                  <div className="text-purple-300">تحليلات اليوم</div>
                </div>
              </div>
            )}

            {/* Users Management */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <span className="text-blue-400 mr-3">👥</span>
                  إدارة المستخدمين
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => fetchAdminUsers(adminCurrentPage)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    🔄 تحديث
                  </button>
                  <button
                    onClick={() => fetchAdminLogs()}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    📋 السجلات
                  </button>
                </div>
              </div>
              
              {adminUsers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-white">
                    <thead>
                      <tr className="border-b border-purple-600/50">
                        <th className="text-right p-3">المستخدم</th>
                        <th className="text-right p-3">نوع الاشتراك</th>
                        <th className="text-right p-3">الحالة</th>
                        <th className="text-right p-3">التحليلات</th>
                        <th className="text-right p-3">تاريخ التسجيل</th>
                        <th className="text-center p-3">الإجراءات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminUsers.map((user, index) => (
                        <tr key={user.user_id || index} className="border-b border-purple-600/30 hover:bg-purple-800/20">
                          <td className="p-3">
                            <div>
                              <div className="font-medium">{user.user_id}</div>
                              <div className="text-sm text-purple-300">{user.ip_address}</div>
                            </div>
                          </td>
                          <td className="p-3">
                            <select
                              value={user.user_tier || 'free'}
                              onChange={(e) => updateUserTier(user.user_id, e.target.value)}
                              className="bg-purple-800/50 border border-purple-600/50 rounded px-2 py-1 text-white text-sm"
                            >
                              <option value="free">مجاني</option>
                              <option value="premium">مميز</option>
                              <option value="vip">VIP</option>
                            </select>
                          </td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              user.is_active ? 'bg-green-600/30 text-green-300' : 'bg-red-600/30 text-red-300'
                            }`}>
                              {user.is_active ? 'نشط' : 'معطل'}
                            </span>
                          </td>
                          <td className="p-3 text-center">{user.analysis_count || 0}</td>
                          <td className="p-3 text-sm text-purple-300">
                            {user.created_at ? new Date(user.created_at).toLocaleDateString('ar-SA') : 'غير محدد'}
                          </td>
                          <td className="p-3 text-center">
                            <button
                              onClick={() => toggleUserStatus(user.user_id)}
                              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                user.is_active 
                                  ? 'bg-red-600/30 text-red-300 hover:bg-red-600/50' 
                                  : 'bg-green-600/30 text-green-300 hover:bg-green-600/50'
                              }`}
                            >
                              {user.is_active ? 'إيقاف' : 'تفعيل'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-purple-300">
                  <div className="text-4xl mb-4">👥</div>
                  <p>لا توجد بيانات مستخدمين</p>
                  <button
                    onClick={() => fetchAdminUsers()}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    تحديث البيانات
                  </button>
                </div>
              )}
            </div>

            {/* Analysis Logs */}
            {adminLogs.length > 0 && (
              <div className="glass-card p-6">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                  <span className="text-green-400 mr-3">📋</span>
                  سجل التحليلات
                </h2>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-white text-sm">
                    <thead>
                      <tr className="border-b border-purple-600/50">
                        <th className="text-right p-3">المستخدم</th>
                        <th className="text-right p-3">نوع التحليل</th>
                        <th className="text-right p-3">السؤال</th>
                        <th className="text-right p-3">الوقت</th>
                        <th className="text-center p-3">النتيجة</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminLogs.slice(0, 10).map((log, index) => (
                        <tr key={log.id || index} className="border-b border-purple-600/30 hover:bg-purple-800/20">
                          <td className="p-3">{log.user_id}</td>
                          <td className="p-3">
                            <span className="px-2 py-1 bg-purple-600/30 rounded text-xs">
                              {log.analysis_type === 'quick' ? 'سريع' :
                               log.analysis_type === 'detailed' ? 'مفصل' :
                               log.analysis_type === 'chart' ? 'فني' :
                               log.analysis_type === 'news' ? 'أخبار' :
                               log.analysis_type === 'forecast' ? 'توقعات' : 'غير محدد'}
                            </span>
                          </td>
                          <td className="p-3 text-purple-300 max-w-xs truncate">
                            {log.question || 'لا توجد تفاصيل'}
                          </td>
                          <td className="p-3 text-purple-300">
                            {log.timestamp ? new Date(log.timestamp).toLocaleString('ar-SA') : 'غير محدد'}
                          </td>
                          <td className="p-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              log.success ? 'bg-green-600/30 text-green-300' : 'bg-red-600/30 text-red-300'
                            }`}>
                              {log.success ? 'نجح' : 'فشل'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Logout Button */}
            <div className="text-center mt-8">
              <button
                onClick={() => {
                  setAdminAuthenticated(false);
                  setAdminData(null);
                  setAdminUsers([]);
                  setAdminLogs([]);
                  setAdminUsername('');
                  setAdminPassword('');
                  setCurrentView('dashboard');
                }}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                🚪 تسجيل خروج
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="App">
      <div className="header">
        <h1 className="app-title">al_kabous ai</h1>
        <div className="subtitle">مدرسة الكابوس الذهبية</div>
        
        <nav className="nav-menu">
          <button 
            onClick={() => setCurrentView('dashboard')}
            className={currentView === 'dashboard' ? 'active' : ''}
          >
            🏠 {t('header.nav.home')}
          </button>
          <button 
            onClick={() => setCurrentView('contact')}
            className={currentView === 'contact' ? 'active' : ''}
          >
            📞 {t('header.nav.contact')}
          </button>
          <button 
            onClick={() => setCurrentView('admin')}
            className={currentView === 'admin' ? 'active' : ''}
          >
            🔧 {t('header.nav.admin')}
          </button>
          
          {/* Language Toggle */}
          <button
            onClick={toggleLanguage}
            className="nav-language-btn"
          >
            {currentLanguage === 'ar' ? '🇺🇸 EN' : '🇸🇦 AR'}
          </button>
          
          {/* Authentication Buttons */}
          {isAuthenticated ? (
            <>
              <span className="nav-user-info">
                👤 {currentUser?.email?.split('@')[0] || 'مستخدم'}
              </span>
              <button 
                onClick={handleLogout}
                className="nav-logout-btn"
              >
                🚪 {t('header.nav.logout')}
              </button>
            </>
          ) : (
            <>
              <button 
                onClick={() => setCurrentView('login')}
                className={currentView === 'login' ? 'active' : ''}
              >
                🔐 {t('header.nav.login')}
              </button>
              <button 
                onClick={() => setCurrentView('register')}
                className={currentView === 'register' ? 'active' : ''}
              >
                📝 {t('header.nav.register')}
              </button>
            </>
          )}
        </nav>
      </div>

      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'analyze' && renderAnalyzeView()}
      {currentView === 'analysis-dashboard' && renderAnalysisDashboard()}
      {currentView === 'chart-analysis' && renderChartAnalysisView()}
      {currentView === 'contact' && renderContactView()}
      {currentView === 'admin' && renderAdminView()}
      {currentView === 'login' && renderLoginView()}
      {currentView === 'register' && renderRegisterView()}
      
      {currentView === 'results' && (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                <span className="text-red-400">💎</span> نتائج التحليل
              </h1>
              
              <div className="inline-block bg-black/20 backdrop-blur-sm border border-red-500/30 rounded-lg p-4 shadow-xl">
                <div className="text-2xl font-bold text-red-400 mb-2">
                  نوع التحليل: {selectedAnalysisType === 'quick' ? 'سريع ⚡' : 
                                 selectedAnalysisType === 'detailed' ? 'مفصل 📊' :
                                 selectedAnalysisType === 'chart' ? 'فني 📈' :
                                 selectedAnalysisType === 'news' ? 'أخبار 📰' : 'توقعات 🔮'}
                </div>
                {goldPrice && (
                  <div className="text-lg text-white">
                    السعر الحالي: <span className="text-yellow-400 font-bold">${goldPrice.price_usd}</span>
                    <span className={`ml-2 ${goldPrice.price_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({goldPrice.price_change >= 0 ? '+' : ''}{goldPrice.price_change_pct}%)
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="glass-card p-8 mb-8">
              <div className="analysis-content">
                {analysisLoading ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🔄</div>
                    <p className="text-white">جاري التحليل...</p>
                  </div>
                ) : analysisResult ? (
                  analysisResult.success ? (
                    <div className="text-white whitespace-pre-wrap">
                      {analysisResult.analysis}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-4">❌</div>
                      <p className="text-red-400">{analysisResult.error}</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">⏳</div>
                    <p className="text-white">لا توجد نتائج</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-center">
              <button
                onClick={() => setCurrentView('dashboard')}
                className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
              >
                العودة للرئيسية
              </button>
            </div>
          </div>
        </div>
      )}
      
      {currentView === 'chart-analysis' && (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                <span className="text-red-400">📊</span> نتائج تحليل الشارت
              </h1>
              
              <div className="inline-block bg-black/20 backdrop-blur-sm border border-red-500/30 rounded-lg p-4 shadow-xl">
                <div className="text-2xl font-bold text-red-400 mb-2">
                  تحليل الشارت المرفوع
                </div>
                <div className="text-lg text-white">
                  زوج العملة: <span className="text-yellow-400 font-bold">{currencyPair}</span>
                  <span className="mx-2">|</span>
                  الإطار الزمني: <span className="text-blue-400 font-bold">{timeframe}</span>
                </div>
              </div>
            </div>
            
            <div className="glass-card p-8 mb-8">
              <div className="analysis-content">
                {chartAnalysisLoading ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🔄</div>
                    <p className="text-white">جاري تحليل الشارت...</p>
                  </div>
                ) : chartAnalysisResult ? (
                  chartAnalysisResult.success ? (
                    <div className="text-white whitespace-pre-wrap">
                      {chartAnalysisResult.analysis}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-4">❌</div>
                      <p className="text-red-400">{chartAnalysisResult.error}</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">⏳</div>
                    <p className="text-white">لا توجد نتائج</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-center">
              <button
                onClick={() => setCurrentView('dashboard')}
                className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
              >
                العودة للرئيسية
              </button>
            </div>
          </div>
        </div>
      )}
      
      {currentView === 'forex-results' && (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                <span className="text-red-400">💱</span> نتائج تحليل العملات
              </h1>
              
              <div className="inline-block bg-black/20 backdrop-blur-sm border border-red-500/30 rounded-lg p-4 shadow-xl">
                <div className="text-2xl font-bold text-red-400 mb-2">
                  تحليل زوج العملة: {selectedForexPair}
                </div>
                {forexPrices[selectedForexPair] && (
                  <div className="text-lg text-white">
                    السعر الحالي: <span className="text-yellow-400 font-bold">{forexPrices[selectedForexPair].price_usd}</span>
                    <span className={`ml-2 ${forexPrices[selectedForexPair].price_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ({forexPrices[selectedForexPair].price_change >= 0 ? '+' : ''}{forexPrices[selectedForexPair].price_change_pct}%)
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="glass-card p-8 mb-8">
              <div className="analysis-content">
                {forexAnalysisLoading ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🔄</div>
                    <p className="text-white">جاري تحليل العملات...</p>
                  </div>
                ) : forexAnalysisResult ? (
                  forexAnalysisResult.success ? (
                    <div className="text-white whitespace-pre-wrap">
                      {forexAnalysisResult.analysis}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-4">❌</div>
                      <p className="text-red-400">{forexAnalysisResult.error}</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">⏳</div>
                    <p className="text-white">لا توجد نتائج</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-center">
              <button
                onClick={() => setCurrentView('dashboard')}
                className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
              >
                العودة للرئيسية
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;