import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, analyze, results
  const [goldPrice, setGoldPrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('quick');
  const [userQuestion, setUserQuestion] = useState('');
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

  const handleAnalyze = async () => {
    if (!userQuestion.trim() && selectedAnalysisType === 'quick') {
      return;
    }

    setAnalysisLoading(true);
    setCurrentView('results');
    
    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_type: selectedAnalysisType,
          user_question: userQuestion,
          additional_context: userQuestion
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

  const renderDashboard = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900">
      
      {/* Header */}
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-yellow-400 mr-3">🏆</span>
            al_kabous ai
          </h1>
          <p className="text-purple-200 text-lg">
            مدرسة الكابوس الذهبية - تحليل الذهب والعملات الذكي
          </p>
        </div>

        {/* Live Gold Price Chart */}
        <div className="glass-card p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <span className="text-yellow-400 mr-2">💰</span>
              سعر الذهب الحالي
            </h2>
            <button 
              onClick={fetchGoldPrice}
              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm font-medium"
            >
              تحديث السعر
            </button>
          </div>
          
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-400 border-t-transparent mx-auto mb-4"></div>
              <p className="text-purple-200">جاري تحميل الأسعار...</p>
            </div>
          ) : goldPrice ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-purple-300 text-sm mb-1">السعر الحالي</p>
                <p className="text-2xl font-bold text-white">${goldPrice.price_usd?.toFixed(2) || '---'}</p>
              </div>
              <div className="text-center">
                <p className="text-purple-300 text-sm mb-1">التغيير اليومي</p>
                <p className={`text-xl font-semibold ${goldPrice.price_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {goldPrice.price_change >= 0 ? '+' : ''}{goldPrice.price_change?.toFixed(2) || '---'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-purple-300 text-sm mb-1">أعلى سعر</p>
                <p className="text-xl font-semibold text-green-400">${goldPrice.high_24h?.toFixed(2) || '---'}</p>
              </div>
              <div className="text-center">
                <p className="text-purple-300 text-sm mb-1">أقل سعر</p>
                <p className="text-xl font-semibold text-red-400">${goldPrice.low_24h?.toFixed(2) || '---'}</p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-red-300">لا يوجد بيانات متاحة</p>
            </div>
          )}
        </div>

        {/* Contact Info & Channels */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="text-green-400 mr-2">🔗</span>
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
                  className="flex items-center p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg text-purple-200 hover:bg-blue-600/30 transition-all"
                >
                  <span className="text-2xl mr-3">📊</span>
                  <div>
                    <p className="font-medium text-white">قناة التوصيات</p>
                    <p className="text-sm">توصيات الذهب والعملات</p>
                  </div>
                </a>
                <a 
                  href="https://t.me/odai_xau_usd" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg text-purple-200 hover:bg-blue-600/30 transition-all"
                >
                  <span className="text-2xl mr-3">💬</span>
                  <div>
                    <p className="font-medium text-white">قناة المناقشات</p>
                    <p className="text-sm">نقاش وتحليل الأسواق</p>
                  </div>
                </a>
              </div>
            </div>

            {/* Personal Contact */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-purple-200 flex items-center">
                <span className="text-green-400 mr-2">👤</span>
                التواصل الشخصي
              </h3>
              <div className="space-y-3">
                <a 
                  href="https://wa.me/962786275654" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center p-3 bg-green-600/20 border border-green-500/30 rounded-lg text-purple-200 hover:bg-green-600/30 transition-all"
                >
                  <span className="text-2xl mr-3">💬</span>
                  <div>
                    <p className="font-medium text-white">واتساب</p>
                    <p className="text-sm">962786275654</p>
                  </div>
                </a>
                <a 
                  href="https://t.me/Odai_xau" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg text-purple-200 hover:bg-blue-600/30 transition-all"
                >
                  <span className="text-2xl mr-3">📱</span>
                  <div>
                    <p className="font-medium text-white">تليجرام شخصي</p>
                    <p className="text-sm">@Odai_xau</p>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
        {/* Quick Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="text-purple-400 mr-2">⚡</span>
            تحليل فوري للذهب
          </h2>
          <p className="text-purple-200 mb-6">اضغط على نوع التحليل للحصول على تحليل فوري</p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <button 
              onClick={() => { 
                setSelectedAnalysisType('quick'); 
                setUserQuestion('تحليل سريع للذهب'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white p-4 rounded-xl font-semibold hover:from-yellow-600 hover:to-orange-600 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📉</div>
              سريع
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('chart'); 
                setUserQuestion('التحليل الفني للذهب'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-4 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📊</div>
              فني
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('news'); 
                setUserQuestion('أخبار الذهب وتأثيرها على السوق'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-green-500 to-teal-500 text-white p-4 rounded-xl font-semibold hover:from-green-600 hover:to-teal-600 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📰</div>
              أخبار
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('forecast'); 
                setUserQuestion('توقعات الذهب المستقبلية'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-pink-500 to-red-500 text-white p-4 rounded-xl font-semibold hover:from-pink-600 hover:to-red-600 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📈</div>
              توقعات
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('detailed'); 
                setUserQuestion('تحليل مفصل وشامل للذهب'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-4 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-600 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">📋</div>
              مفصل
            </button>
          </div>
        </div>

        {/* Currency Analysis Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="text-blue-400 mr-2">💱</span>
            تحليل العملات
          </h2>
          <p className="text-purple-200 mb-6">تحليل العملات الرئيسية في السوق</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => { 
                setSelectedAnalysisType('detailed'); 
                setUserQuestion('تحليل زوج EUR/USD'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-4 rounded-xl font-semibold hover:from-blue-700 hover:to-cyan-700 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇪🇺</div>
              EUR/USD
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('detailed'); 
                setUserQuestion('تحليل زوج USD/JPY'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-red-600 to-pink-600 text-white p-4 rounded-xl font-semibold hover:from-red-700 hover:to-pink-700 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇯🇵</div>
              USD/JPY
            </button>
            
            <button 
              onClick={() => { 
                setSelectedAnalysisType('detailed'); 
                setUserQuestion('تحليل زوج GBP/USD'); 
                handleAnalyze(); 
              }}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all transform hover:scale-105"
            >
              <div className="text-2xl mb-2">🇬🇧</div>
              GBP/USD
            </button>
          </div>
        </div>

        {/* Custom Analysis Button */}
        <div className="text-center">
          <button
            onClick={() => setCurrentView('analyze')}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:from-purple-700 hover:to-indigo-700 transition-all transform hover:scale-105 shadow-xl"
          >
            <span className="mr-2">🎯</span>
            طلب التحليل
          </button>
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
              onClick={handleAnalyze}
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

  const renderResultsView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center">
            <span className="text-yellow-400 mr-3">💰</span>
            تحليل الذهب
          </h1>
          <p className="text-purple-200">تحليل ذكي ومتقدم لأسعار الذهب</p>
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
          
          {analysisLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-green-400 border-t-transparent mx-auto mb-6"></div>
              <p className="text-white text-lg">جاري إجراء التحليل الذكي...</p>
              <p className="text-purple-300 text-sm mt-2">قد يستغرق هذا بعض الوقت</p>
            </div>
          ) : analysisResult ? (
            analysisResult.success ? (
              <div className="space-y-4">
                <div className="bg-purple-800/30 rounded-lg p-6 border border-purple-600/30">
                  <div className="prose prose-invert max-w-none">
                    <div className="text-white whitespace-pre-line leading-relaxed">
                      {analysisResult.analysis}
                    </div>
                  </div>
                </div>
                
                {analysisResult.processing_time && (
                  <div className="text-center text-purple-300 text-sm">
                    ⏱️ وقت المعالجة: {analysisResult.processing_time.toFixed(2)} ثانية
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">⚠️</div>
                <p className="text-red-300 text-lg">لا يوجد تحليل بعد</p>
                <p className="text-purple-300 text-sm mt-2">
                  {analysisResult.error || '"اكتب سؤالك واضغط على "تحليل الذهب'}
                </p>
              </div>
            )
          ) : (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">⚠️</div>
              <p className="text-yellow-300 text-lg">لا يوجد تحليل بعد</p>
              <p className="text-purple-300 text-sm mt-2">ارفع دليلاً بيانياً واضغط على "تحليل الذهب"</p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="text-center space-y-4">
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => setCurrentView('analyze')}
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

  return (
    <div className="App">
      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'analyze' && renderAnalyzeView()}
      {currentView === 'results' && renderResultsView()}
    </div>
  );
}

export default App;