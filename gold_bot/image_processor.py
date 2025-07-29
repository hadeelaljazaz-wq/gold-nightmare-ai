"""
Al Kabous AI - Advanced Image Processing with OCR
معالجة متقدمة للصور مع قراءة النصوص من الشارت
"""

import cv2
import numpy as np
import pytesseract
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import base64
import io
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ChartImageProcessor:
    """معالج الصور المتقدم لتحليل الشارتات"""
    
    def __init__(self):
        # Initialize EasyOCR reader
        try:
            self.ocr_reader = easyocr.Reader(['en', 'ar'], gpu=False)
            logger.info("✅ EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ EasyOCR initialization failed: {e}")
            self.ocr_reader = None
        
        # Price extraction patterns
        self.price_patterns = [
            r'\b\d{1,5}(?:\.\d{1,5})\b',  # 2451.23, 1234.5
            r'\b\d{1,5}(?:,\d{3})*(?:\.\d{1,5})?\b',  # 2,451.23
            r'\$\s*\d{1,5}(?:,\d{3})*(?:\.\d{1,5})?\b',  # $2,451.23
            r'XAU[:/]\s*\d{1,5}(?:\.\d{1,5})\b',  # XAU: 2451.23
            r'GOLD[:/]\s*\d{1,5}(?:\.\d{1,5})\b',  # GOLD: 2451.23
        ]
        
        self.timeframe_patterns = [
            r'\b(?:M|H|D|W|MN)\d*\b',  # M1, M5, H1, H4, D1, W1, MN1
            r'\b\d+\s*(?:min|hour|day|week|month)s?\b',  # 1 hour, 15 min
            r'\b(?:1|5|15|30)m\b',  # 1m, 5m, 15m, 30m
            r'\b(?:1|4|12|24)h\b',  # 1h, 4h, 12h, 24h
        ]
        
        # Currency pair patterns
        self.pair_patterns = [
            r'\b(?:XAU|GOLD)/USD\b',
            r'\b(?:EUR|GBP|USD|JPY|AUD|CAD|CHF|NZD)/(?:USD|EUR|JPY|GBP)\b',
            r'\bGOLD\b',
            r'\bXAUUSD\b',
        ]

    async def process_chart_image(self, image_data: bytes) -> Dict[str, Any]:
        """معالجة شاملة لصورة الشارت مع استخراج المعلومات"""
        try:
            # تحويل البيانات لصورة PIL
            image = Image.open(io.BytesIO(image_data))
            
            # معالجة متوازية للمهام المختلفة
            with ThreadPoolExecutor(max_workers=4) as executor:
                # استخراج النصوص
                texts_task = executor.submit(self._extract_texts, image)
                
                # تحليل الألوان والشموع
                colors_task = executor.submit(self._analyze_chart_colors, image)
                
                # استخراج الأرقام والأسعار
                prices_task = executor.submit(self._extract_prices_advanced, image)
                
                # تحليل الأنماط البصرية
                patterns_task = executor.submit(self._detect_chart_patterns, image)
                
                # انتظار النتائج
                texts_info = texts_task.result()
                colors_info = colors_task.result()
                prices_info = prices_task.result()
                patterns_info = patterns_task.result()
            
            # دمج جميع المعلومات
            analysis_result = {
                "image_info": {
                    "width": image.width,
                    "height": image.height,
                    "format": image.format,
                    "mode": image.mode
                },
                "text_extraction": texts_info,
                "price_analysis": prices_info,
                "visual_analysis": {
                    "colors": colors_info,
                    "patterns": patterns_info
                },
                "trading_context": self._build_trading_context(texts_info, prices_info, colors_info)
            }
            
            logger.info("✅ Chart image processed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error processing chart image: {e}")
            return {"error": str(e)}

    def _extract_texts(self, image: Image.Image) -> Dict[str, Any]:
        """استخراج النصوص من الصورة باستخدام OCR متعدد"""
        try:
            texts_info = {
                "all_texts": [],
                "prices": [],
                "timeframes": [],
                "currency_pairs": [],
                "indicators": []
            }
            
            # تحسين جودة الصورة لـ OCR
            enhanced_image = self._enhance_for_ocr(image)
            
            # EasyOCR extraction
            if self.ocr_reader:
                try:
                    easy_results = self.ocr_reader.readtext(np.array(enhanced_image))
                    for result in easy_results:
                        text = result[1].strip()
                        confidence = result[2]
                        
                        if confidence > 0.5:  # عتبة الثقة
                            texts_info["all_texts"].append({
                                "text": text,
                                "confidence": confidence,
                                "method": "easyocr"
                            })
                            
                            # تصنيف النصوص
                            self._classify_text(text, texts_info)
                            
                except Exception as e:
                    logger.warning(f"⚠️ EasyOCR failed: {e}")
            
            # Tesseract OCR as backup
            try:
                # تحويل لـ OpenCV
                cv_image = cv2.cvtColor(np.array(enhanced_image), cv2.COLOR_RGB2BGR)
                tessearct_text = pytesseract.image_to_string(cv_image, config='--oem 3 --psm 6')
                
                for line in tessearct_text.split('\n'):
                    line = line.strip()
                    if line and len(line) > 2:
                        texts_info["all_texts"].append({
                            "text": line,
                            "confidence": 0.8,  # افتراضي لـ Tesseract
                            "method": "tesseract"
                        })
                        self._classify_text(line, texts_info)
                        
            except Exception as e:
                logger.warning(f"⚠️ Tesseract failed: {e}")
            
            return texts_info
            
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return {"error": str(e)}

    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """تحسين الصورة لـ OCR بشكل أفضل"""
        try:
            # تحويل لـ RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # تكبير الصورة
            width, height = image.size
            image = image.resize((width * 2, height * 2), Image.LANCZOS)
            
            # تحسين التباين والسطوع
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # شحذ الصورة
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Image enhancement failed: {e}")
            return image

    def _classify_text(self, text: str, texts_info: Dict[str, Any]):
        """تصنيف النصوص المستخرجة"""
        text_upper = text.upper()
        
        # البحث عن الأسعار
        for pattern in self.price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # تنظيف الرقم
                clean_price = re.sub(r'[^\d.]', '', match)
                try:
                    price_value = float(clean_price)
                    if 1000 <= price_value <= 5000:  # نطاق أسعار الذهب المعقول
                        texts_info["prices"].append({
                            "value": price_value,
                            "original": match,
                            "context": text
                        })
                except ValueError:
                    continue
        
        # البحث عن الإطارات الزمنية
        for pattern in self.timeframe_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                texts_info["timeframes"].append({
                    "timeframe": match,
                    "context": text
                })
        
        # البحث عن أزواج العملات
        for pattern in self.pair_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                texts_info["currency_pairs"].append({
                    "pair": match,
                    "context": text
                })
        
        # البحث عن المؤشرات الفنية
        indicators = ['RSI', 'MACD', 'MA', 'EMA', 'SMA', 'BB', 'STOCH', 'ADX', 'CCI']
        for indicator in indicators:
            if indicator in text_upper:
                texts_info["indicators"].append({
                    "indicator": indicator,
                    "context": text
                })

    def _extract_prices_advanced(self, image: Image.Image) -> Dict[str, Any]:
        """استخراج متقدم للأسعار من الشارت"""
        try:
            prices_info = {
                "detected_prices": [],
                "current_price_estimate": None,
                "high_low_estimates": {},
                "axis_analysis": {}
            }
            
            # تحويل لـ OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # البحث عن النصوص في محاور الأسعار (عادة على الجانب الأيمن)
            height, width = gray.shape
            
            # منطقة المحور الأيمن (آخر 15% من العرض)
            right_axis = gray[:, int(width * 0.85):]
            
            # تحسين المحور لـ OCR
            right_axis = cv2.bilateralFilter(right_axis, 9, 75, 75)
            _, right_axis = cv2.threshold(right_axis, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # استخراج النصوص من المحور
            axis_text = pytesseract.image_to_string(right_axis, config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,')
            
            # البحث عن الأسعار في نص المحور
            for line in axis_text.split('\n'):
                line = line.strip()
                if line:
                    # تنظيف وتحويل الأرقام
                    clean_line = re.sub(r'[^\d.]', '', line)
                    try:
                        if clean_line:
                            price = float(clean_line)
                            if 1000 <= price <= 5000:  # نطاق الذهب
                                prices_info["detected_prices"].append(price)
                    except ValueError:
                        continue
            
            # تحليل الأسعار المكتشفة
            if prices_info["detected_prices"]:
                prices = sorted(prices_info["detected_prices"])
                prices_info["high_low_estimates"] = {
                    "highest": max(prices),
                    "lowest": min(prices),
                    "range": max(prices) - min(prices)
                }
                # تقدير السعر الحالي (قد يكون في المنتصف)
                prices_info["current_price_estimate"] = prices[len(prices) // 2]
            
            return prices_info
            
        except Exception as e:
            logger.error(f"❌ Advanced price extraction failed: {e}")
            return {"error": str(e)}

    def _analyze_chart_colors(self, image: Image.Image) -> Dict[str, Any]:
        """تحليل ألوان الشارت لفهم حالة السوق"""
        try:
            colors_info = {
                "dominant_colors": [],
                "candlestick_analysis": {},
                "trend_indicators": {}
            }
            
            # تحويل لـ numpy array
            img_array = np.array(image)
            
            # تحليل الألوان السائدة
            pixels = img_array.reshape(-1, 3)
            
            # البحث عن الألوان الخضراء والحمراء (صعود/هبوط)
            green_pixels = np.sum((pixels[:, 1] > pixels[:, 0]) & (pixels[:, 1] > pixels[:, 2]))
            red_pixels = np.sum((pixels[:, 0] > pixels[:, 1]) & (pixels[:, 0] > pixels[:, 2]))
            
            total_pixels = len(pixels)
            
            colors_info["candlestick_analysis"] = {
                "green_percentage": (green_pixels / total_pixels) * 100,
                "red_percentage": (red_pixels / total_pixels) * 100,
                "trend_indication": "bullish" if green_pixels > red_pixels else "bearish"
            }
            
            return colors_info
            
        except Exception as e:
            logger.error(f"❌ Color analysis failed: {e}")
            return {"error": str(e)}

    def _detect_chart_patterns(self, image: Image.Image) -> Dict[str, Any]:
        """كشف الأنماط الفنية في الشارت"""
        try:
            patterns_info = {
                "detected_patterns": [],
                "support_resistance": [],
                "trend_lines": []
            }
            
            # تحويل لـ OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # كشف الخطوط (خطوط الاتجاه، الدعم والمقاومة)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            if lines is not None:
                # تحليل الخطوط
                horizontal_lines = 0
                ascending_lines = 0
                descending_lines = 0
                
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # حساب الميل
                    if x2 != x1:
                        slope = abs((y2 - y1) / (x2 - x1))
                        if slope < 0.1:  # خط أفقي تقريباً
                            horizontal_lines += 1
                        elif (y2 - y1) / (x2 - x1) > 0.1:  # خط صاعد
                            ascending_lines += 1
                        elif (y2 - y1) / (x2 - x1) < -0.1:  # خط هابط
                            descending_lines += 1
                
                patterns_info["trend_lines"] = {
                    "horizontal": horizontal_lines,
                    "ascending": ascending_lines,
                    "descending": descending_lines,
                    "trend_direction": self._determine_trend(ascending_lines, descending_lines)
                }
            
            return patterns_info
            
        except Exception as e:
            logger.error(f"❌ Pattern detection failed: {e}")
            return {"error": str(e)}

    def _determine_trend(self, ascending: int, descending: int) -> str:
        """تحديد اتجاه الترند"""
        if ascending > descending * 1.5:
            return "صاعد قوي"
        elif ascending > descending:
            return "صاعد"
        elif descending > ascending * 1.5:
            return "هابط قوي"
        elif descending > ascending:
            return "هابط"
        else:
            return "جانبي"

    def _build_trading_context(self, texts_info: Dict, prices_info: Dict, colors_info: Dict) -> Dict[str, Any]:
        """بناء السياق التداولي من المعلومات المستخرجة"""
        try:
            context = {
                "extracted_data_summary": "",
                "confidence_score": 0.0,
                "trading_signals": []
            }
            
            # تجميع المعلومات
            summary_parts = []
            confidence_factors = []
            
            # معلومات الأسعار
            if prices_info.get("detected_prices"):
                prices = prices_info["detected_prices"]
                summary_parts.append(f"أسعار مكتشفة: {len(prices)} سعر")
                if prices_info.get("current_price_estimate"):
                    summary_parts.append(f"السعر المقدر: ${prices_info['current_price_estimate']:.2f}")
                confidence_factors.append(0.3)
            
            # معلومات النصوص
            if texts_info.get("currency_pairs"):
                pairs = [pair["pair"] for pair in texts_info["currency_pairs"]]
                summary_parts.append(f"أزواج العملات: {', '.join(set(pairs))}")
                confidence_factors.append(0.2)
            
            if texts_info.get("timeframes"):
                timeframes = [tf["timeframe"] for tf in texts_info["timeframes"]]
                summary_parts.append(f"الإطارات الزمنية: {', '.join(set(timeframes))}")
                confidence_factors.append(0.1)
            
            # تحليل الألوان
            if colors_info.get("candlestick_analysis"):
                trend = colors_info["candlestick_analysis"]["trend_indication"]
                summary_parts.append(f"اتجاه الألوان: {trend}")
                confidence_factors.append(0.2)
            
            # حساب نتيجة الثقة
            context["confidence_score"] = sum(confidence_factors)
            context["extracted_data_summary"] = ". ".join(summary_parts)
            
            # إشارات التداول
            if colors_info.get("candlestick_analysis", {}).get("green_percentage", 0) > 60:
                context["trading_signals"].append("إشارة صعود قوية من تحليل الألوان")
            elif colors_info.get("candlestick_analysis", {}).get("red_percentage", 0) > 60:
                context["trading_signals"].append("إشارة هبوط قوية من تحليل الألوان")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Context building failed: {e}")
            return {"error": str(e)}


# إنشاء مثيل مشترك
chart_processor = ChartImageProcessor()