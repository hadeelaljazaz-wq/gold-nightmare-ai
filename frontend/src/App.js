import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [botStatus, setBotStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchBotStatus();
    fetchBotStats();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchBotStatus();
      fetchBotStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchBotStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      const data = await response.json();
      setBotStatus(data);
      setError(null);
    } catch (err) {
      setError('فشل في جلب حالة البوت');
      console.error('Error fetching bot status:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBotStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bot/stats`);
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching bot stats:', err);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('ar-SA');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-400 via-yellow-500 to-yellow-600 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-lg font-semibold">جاري تحميل البوت...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-400 via-yellow-500 to-yellow-600">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-4 shadow-text">
            🏆 Gold Nightmare Bot
          </h1>
          <p className="text-xl text-yellow-100 font-medium">
            بوت تحليل الذهب الاحترافي بالذكاء الاصطناعي
          </p>
          <div className="mt-6 inline-flex items-center px-6 py-3 bg-white/20 backdrop-blur rounded-full text-white">
            <span className={`w-3 h-3 rounded-full mr-3 ${botStatus?.bot_running ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
            <span className="font-semibold">
              {botStatus?.bot_running ? 'البوت يعمل بنجاح' : 'البوت متوقف'}
            </span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-8 mx-auto max-w-md">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
              <strong className="font-bold">خطأ!</strong>
              <span className="block sm:inline ml-2">{error}</span>
            </div>
          </div>
        )}

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          
          {/* Bot Status Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-white border border-white/20">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center mr-4">
                <span className="text-2xl">🤖</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold">حالة البوت</h3>
                <p className="text-yellow-100 text-sm">الحالة الحالية</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>الحالة:</span>
                <span className={`font-semibold ${botStatus?.bot_running ? 'text-green-300' : 'text-red-300'}`}>
                  {botStatus?.bot_running ? '✅ يعمل' : '❌ متوقف'}
                </span>
              </div>
              {botStatus?.timestamp && (
                <div className="flex justify-between">
                  <span>آخر فحص:</span>
                  <span className="text-yellow-100 text-sm">{formatTime(botStatus.timestamp)}</span>
                </div>
              )}
            </div>
          </div>

          {/* User Stats Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-white border border-white/20">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center mr-4">
                <span className="text-2xl">👥</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold">المستخدمين</h3>
                <p className="text-yellow-100 text-sm">إحصائيات المستخدمين</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>إجمالي المستخدمين:</span>
                <span className="font-semibold text-green-300">{stats?.total_users || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>المستخدمين النشطين:</span>
                <span className="font-semibold text-blue-300">{stats?.active_users || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>وقت التشغيل:</span>
                <span className="text-yellow-100 text-sm">{stats?.uptime_hours || 0} ساعة</span>
              </div>
            </div>
          </div>

          {/* Analysis Stats Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-white border border-white/20">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mr-4">
                <span className="text-2xl">📊</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold">التحليلات</h3>
                <p className="text-yellow-100 text-sm">إحصائيات التحليل</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>اليوم:</span>
                <span className="font-semibold text-purple-300">{stats?.analyses_today || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>الإجمالي:</span>
                <span className="font-semibold text-orange-300">{stats?.analyses_total || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-white border border-white/20 mb-8">
          <h2 className="text-2xl font-bold text-center mb-8">🎯 ميزات البوت</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">💰</span>
              </div>
              <h3 className="font-semibold mb-2">أسعار لحظية</h3>
              <p className="text-yellow-100 text-sm">أسعار الذهب المحدثة من مصادر متعددة</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🤖</span>
              </div>
              <h3 className="font-semibold mb-2">تحليل ذكي</h3>
              <p className="text-yellow-100 text-sm">تحليلات مدعومة بالذكاء الاصطناعي</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📈</span>
              </div>
              <h3 className="font-semibold mb-2">تحليل فني</h3>
              <p className="text-yellow-100 text-sm">تحليل المخططات والمؤشرات الفنية</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🔮</span>
              </div>
              <h3 className="font-semibold mb-2">التوقعات</h3>
              <p className="text-yellow-100 text-sm">توقعات السوق والتحليل المستقبلي</p>
            </div>
          </div>
        </div>

        {/* How to Use Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 text-white border border-white/20 mb-8">
          <h2 className="text-2xl font-bold text-center mb-6">🚀 كيفية الاستخدام</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">
                1
              </div>
              <h3 className="font-semibold mb-2">ابدأ المحادثة</h3>
              <p className="text-yellow-100 text-sm">ابحث عن البوت في تليجرام وأرسل /start</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">
                2
              </div>
              <h3 className="font-semibold mb-2">فعّل حسابك</h3>
              <p className="text-yellow-100 text-sm">استخدم كلمة المرور للحصول على الوصول الكامل</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">
                3
              </div>
              <h3 className="font-semibold mb-2">احصل على التحليل</h3>
              <p className="text-yellow-100 text-sm">اختر نوع التحليل المطلوب واستمتع بالخدمة</p>
            </div>
          </div>
        </div>

        {/* Contact Section */}
        <div className="text-center">
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-white border border-white/20 inline-block">
            <h3 className="text-xl font-bold mb-4">📞 للتواصل والدعم</h3>
            <p className="text-yellow-100 mb-4">
              للحصول على كلمة المرور أو للدعم الفني
            </p>
            <div className="space-y-2">
              <p className="text-sm">Gold Nightmare – عدي</p>
              <p className="text-sm text-yellow-200">بوت التحليل المالي الأول في المنطقة</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;