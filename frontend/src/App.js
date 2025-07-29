import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, analyze, results, contact, chart-analysis
  const [goldPrice, setGoldPrice] = useState(null);
  const [loading, setLoading] = useState(false);
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
  const [quickQuestions] = useState([
    "تحليل الذهب الحالي",
    "ما هي توقعات الذهب للأسبوع القادم؟",
    "هل الوقت مناسب لشراء الذهب؟", 
    "تحليل فني للذهب",
    "تأثير التضخم على أسعار الذهب"
  ]);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchGoldPrice();
  }, []);

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
    const actualQuestion = question || userQuestion;
    const actualType = analysisType || selectedAnalysisType;
    
    if (!actualQuestion.trim()) {
      console.error('No question provided for analysis');
      return;
    }

    setAnalysisLoading(true);
    setCurrentView('results');
    
    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_type: actualType,
          user_question: actualQuestion,
          additional_context: actualQuestion
        })
      });
      
      const data = await response.json();
      setAnalysisResult(data);
      
    } catch (err) {
      console.error('Error analyzing:', err);
      setAnalysisResult({
        success: false,
        error: 'حدث خطأ في التحليل'
      });
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Forex Analysis Function
  const handleForexAnalysis = async (pair) => {
    setSelectedForexPair(pair);
    setForexAnalysisLoading(true);
    setCurrentView('results');
    
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
    setCurrentView('results');
    
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
            مدرسة الكابوس الذهبية - تحليل الذهب والعملات الذكي
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-8">

        
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

        {/* Contact Info & Channels */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center">
            <span className="gold-text mr-2">🔗</span>
            قنوات التوصيات والتواصل
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Telegram Channels */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-purple-200 flex items-center">
                <span className="text-blue-400 mr-2">📱</span>
                قنوات التليجرام
              </h3>
              <div className="space-y-3">
                <a 
                  href="https://t.me/odai_xauusdt" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">📊</span>
                  <div>
                    <p className="font-medium royal-text">قناة التوصيات</p>
                    <p className="text-sm text-purple-200">توصيات الذهب والعملات</p>
                  </div>
                </a>
                <a 
                  href="https://t.me/odai_xau_usd" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">💬</span>
                  <div>
                    <p className="font-medium royal-text">قناة المناقشات</p>
                    <p className="text-sm text-purple-200">نقاش وتحليل الأسواق</p>
                  </div>
                </a>
              </div>
            </div>

            {/* Personal Contact */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-purple-200 flex items-center">
                <span className="gold-text mr-2">👤</span>
                التواصل الشخصي
              </h3>
              <div className="space-y-3">
                <a 
                  href="https://wa.me/962786275654" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">💬</span>
                  <div>
                    <p className="font-medium royal-text">واتساب</p>
                    <p className="text-sm price-high">962786275654</p>
                  </div>
                </a>
                <a 
                  href="https://t.me/Odai_xau" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">📱</span>
                  <div>
                    <p className="font-medium royal-text">تليجرام شخصي</p>
                    <p className="text-sm text-blue-300">@Odai_xau</p>
                  </div>
                </a>
                <a 
                  href="https://www.instagram.com/odai_xau?igsh=MWtrOXNleGlnY3k1aQ==" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">📷</span>
                  <div>
                    <p className="font-medium royal-text">انستغرام</p>
                    <p className="text-sm text-pink-300">@odai_xau</p>
                  </div>
                </a>
                <a 
                  href="https://www.facebook.com/odaiaboamera" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="contact-link"
                >
                  <span className="text-2xl mr-3">📘</span>
                  <div>
                    <p className="font-medium royal-text">فيسبوك</p>
                    <p className="text-sm text-blue-300">عدي أبو عامرة</p>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
        {/* Quick Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center">
            <span className="gold-text mr-2">⚡</span>
            تحليل فوري للذهب
          </h2>
          <p className="text-purple-200 mb-6">اضغط على نوع التحليل للحصول على تحليل فوري</p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <button 
              onClick={() => handleAnalyze('quick', 'تحليل سريع للذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📉</div>
              سريع
            </button>
            
            <button 
              onClick={() => handleAnalyze('chart', 'التحليل الفني للذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📊</div>
              فني
            </button>
            
            <button 
              onClick={() => handleAnalyze('news', 'أخبار الذهب وتأثيرها على السوق')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📰</div>
              أخبار
            </button>
            
            <button 
              onClick={() => handleAnalyze('forecast', 'توقعات الذهب المستقبلية')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📈</div>
              توقعات
            </button>
            
            <button 
              onClick={() => handleAnalyze('detailed', 'تحليل مفصل وشامل للذهب')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📋</div>
              مفصل
            </button>
          </div>
        </div>

        {/* Currency Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center">
            <span className="gold-text mr-2">💱</span>
            تحليل العملات
          </h2>
          <p className="text-purple-200 mb-6">تحليل العملات الرئيسية في السوق</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => handleAnalyze('detailed', 'تحليل زوج EUR/USD')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇪🇺</div>
              EUR/USD
            </button>
            
            <button 
              onClick={() => handleAnalyze('detailed', 'تحليل زوج USD/JPY')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇯🇵</div>
              USD/JPY
            </button>
            
            <button 
              onClick={() => handleAnalyze('detailed', 'تحليل زوج GBP/USD')}
              className="analysis-button font-semibold transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇬🇧</div>
              GBP/USD
            </button>
          </div>
        </div>

        {/* Chart Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold royal-text mb-6 flex items-center">
            <span className="gold-text mr-2">📊</span>
            تحليل الشارت بالصورة
          </h2>
          <p className="text-purple-200 mb-6">ارفع صورة الشارت واحصل على تحليل فني احترافي مدعوم بالذكاء الاصطناعي</p>
          
          <div className="text-center">
            <button
              onClick={() => setCurrentView('chart-analysis')}
              className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
            >
              <span className="mr-2">📷</span>
              تحليل الشارت بالصورة
            </button>
          </div>
        </div>

        {/* Custom Analysis Button */}
        <div className="text-center">
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => setCurrentView('analyze')}
              className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
            >
              <span className="mr-2">🎯</span>
              طلب تحليل مخصص
            </button>
            <button
              onClick={() => setCurrentView('contact')}
              className="royal-button px-8 py-4 text-lg font-bold shadow-xl"
            >
              <span className="mr-2">📞</span>
              التواصل معنا
            </button>
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
          
          {/* Handle both regular analysis and chart analysis */}
          {analysisLoading || chartAnalysisLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-green-400 border-t-transparent mx-auto mb-6"></div>
              <p className="text-white text-lg">جاري إجراء التحليل الذكي...</p>
              <p className="text-purple-300 text-sm mt-2">قد يستغرق هذا بعض الوقت</p>
            </div>
          ) : (analysisResult || chartAnalysisResult) ? (
            // Show results
            (() => {
              const result = analysisResult || chartAnalysisResult;
              return result.success ? (
                <div className="space-y-4">
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
                      <div className="text-white whitespace-pre-line leading-relaxed">
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
                } else {
                  setCurrentView('analyze');
                  setAnalysisResult(null);
                }
              }}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
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
              التواصل المباشر
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

  return (
    <div className="App">
      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'analyze' && renderAnalyzeView()}
      {currentView === 'results' && renderResultsView()}
      {currentView === 'contact' && renderContactView()}
      {currentView === 'chart-analysis' && renderChartAnalysisView()}
    </div>
  );
}

export default App;