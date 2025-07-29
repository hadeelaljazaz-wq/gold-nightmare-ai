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
import requests
import json
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

    def optimize_chart_image(self, image_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        تحسين جودة الصورة قبل التحليل - تطبيق الحلول المتقدمة
        """
        try:
            # فتح الصورة
            img = Image.open(io.BytesIO(image_data))
            
            # تحويل لـ RGB إذا لزم الأمر
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            optimization_log = {
                "original_size": img.size,
                "steps_applied": []
            }
            
            # 1. زيادة الحجم والدقة (كما اقترحت)
            target_width, target_height = 1920, 1080
            if img.size[0] < target_width or img.size[1] < target_height:
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                optimization_log["steps_applied"].append("Resolution upscaling to 1920x1080")
            
            # 2. تحسين باستخدام OpenCV
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # زيادة الحدة والوضوح
            sharpening_kernel = np.array([[-1,-1,-1], 
                                        [-1, 9,-1], 
                                        [-1,-1,-1]])
            img_cv = cv2.filter2D(img_cv, -1, sharpening_kernel)
            optimization_log["steps_applied"].append("Sharpening filter applied")
            
            # 3. تحسين التباين باستخدام CLAHE
            lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            img_cv = cv2.merge([l,a,b])
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_LAB2BGR)
            optimization_log["steps_applied"].append("CLAHE contrast enhancement")
            
            # 4. تقليل الضوضاء مع الحفاظ على الحواف
            img_cv = cv2.bilateralFilter(img_cv, 9, 75, 75)
            optimization_log["steps_applied"].append("Bilateral noise reduction")
            
            # 5. تحسين إضافي للنصوص
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # تحسين التباين للنصوص
            clahe_text = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
            gray = clahe_text.apply(gray)
            
            # تحويل مرة أخرى للألوان
            img_cv = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            optimization_log["steps_applied"].append("Text clarity enhancement")
            
            # تحويل إلى PIL
            img_optimized = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            
            # حفظ كـ bytes عالية الجودة
            output_buffer = io.BytesIO()
            img_optimized.save(output_buffer, format='PNG', optimize=True, quality=95)
            optimized_data = output_buffer.getvalue()
            
            optimization_log["final_size"] = img_optimized.size
            optimization_log["size_improvement"] = f"{len(optimized_data) / len(image_data):.2f}x"
            
            logger.info(f"✅ Image optimized: {len(optimization_log['steps_applied'])} enhancements applied")
            
            return optimized_data, optimization_log
            
        except Exception as e:
            logger.error(f"❌ Image optimization failed: {e}")
            return image_data, {"error": str(e)}

    def extract_text_from_chart_advanced(self, image_data: bytes) -> Dict[str, Any]:
        """
        استخراج متقدم للنصوص مع تحسينات OCR
        """
        try:
            # تحسين الصورة أولاً
            optimized_data, optimization_log = self.optimize_chart_image(image_data)
            
            # فتح الصورة المحسنة
            img = Image.open(io.BytesIO(optimized_data))
            
            text_data = {
                "prices": [],
                "timestamps": [],
                "full_text": "",
                "confidence_scores": [],
                "optimization_applied": optimization_log,
                "extraction_methods": []
            }
            
            # الطريقة الأولى: EasyOCR المحسن
            if self.ocr_reader:
                try:
                    # تحسين إضافي لـ EasyOCR
                    img_for_easy = self._prepare_for_easyocr(img)
                    easy_results = self.ocr_reader.readtext(np.array(img_for_easy), detail=1)
                    
                    for (bbox, text, confidence) in easy_results:
                        if confidence > 0.6:  # عتبة ثقة أعلى
                            text_data["full_text"] += text + " "
                            text_data["confidence_scores"].append(confidence)
                            
                            # استخراج الأسعار
                            prices = re.findall(r'\b\d{1,5}(?:\.\d{1,5})?\b', text)
                            for price_str in prices:
                                try:
                                    price = float(price_str)
                                    if 1000 <= price <= 5000:
                                        text_data["prices"].append(price)
                                except ValueError:
                                    continue
                            
                            # استخراج الأوقات
                            times = re.findall(r'\d{1,2}:\d{2}', text)
                            text_data["timestamps"].extend(times)
                    
                    text_data["extraction_methods"].append("EasyOCR_Advanced")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Advanced EasyOCR failed: {e}")
            
            # الطريقة الثانية: Tesseract المحسن
            try:
                # تحسين خاص لـ Tesseract
                img_for_tess = self._prepare_for_tesseract(img)
                cv_img = cv2.cvtColor(np.array(img_for_tess), cv2.COLOR_RGB2BGR)
                
                # إعدادات متعددة لـ Tesseract
                configs = [
                    '--oem 3 --psm 6',  # للنصوص العامة
                    '--oem 3 --psm 8',  # للكلمات المفردة
                    '--oem 3 --psm 13',  # للنصوص في خط واحد
                    '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,:$'  # للأرقام فقط
                ]
                
                for config in configs:
                    try:
                        tessearct_text = pytesseract.image_to_string(cv_img, config=config)
                        if tessearct_text.strip():
                            text_data["full_text"] += " " + tessearct_text
                            
                            # استخراج إضافي للأسعار من Tesseract
                            prices = re.findall(r'\b\d{1,5}(?:\.\d{1,5})?\b', tessearct_text)
                            for price_str in prices:
                                try:
                                    price = float(price_str)
                                    if 1000 <= price <= 5000:
                                        text_data["prices"].append(price)
                                except ValueError:
                                    continue
                    
                    except Exception as e:
                        continue
                
                text_data["extraction_methods"].append("Tesseract_Multi_Config")
                
            except Exception as e:
                logger.warning(f"⚠️ Advanced Tesseract failed: {e}")
            
            # تنظيف وتلخيص البيانات
            text_data["prices"] = list(set(text_data["prices"]))  # إزالة المكررات
            text_data["timestamps"] = list(set(text_data["timestamps"]))
            text_data["full_text"] = text_data["full_text"].strip()
            text_data["average_confidence"] = np.mean(text_data["confidence_scores"]) if text_data["confidence_scores"] else 0.0
            
            logger.info(f"✅ Advanced text extraction: {len(text_data['prices'])} prices, {len(text_data['timestamps'])} timestamps")
            
            return text_data
            
        except Exception as e:
            logger.error(f"❌ Advanced text extraction failed: {e}")
            return {"error": str(e)}

    def _prepare_for_easyocr(self, image: Image.Image) -> Image.Image:
        """تحضير الصورة لـ EasyOCR بشكل محسن"""
        try:
            # تحويل لمقياس الرمادي للنصوص
            gray_img = image.convert('L')
            
            # تحسين التباين للنصوص
            enhancer = ImageEnhance.Contrast(gray_img)
            enhanced = enhancer.enhance(2.0)
            
            # تحويل مرة أخرى للألوان (EasyOCR يفضل RGB)
            rgb_img = enhanced.convert('RGB')
            
            return rgb_img
            
        except Exception as e:
            logger.error(f"❌ EasyOCR preparation failed: {e}")
            return image

    def _prepare_for_tesseract(self, image: Image.Image) -> Image.Image:
        """تحضير الصورة لـ Tesseract بشكل محسن"""
        try:
            # تحويل لـ OpenCV
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # تطبيق threshold للحصول على نص أسود على خلفية بيضاء
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # تنظيف الضوضاء
            kernel = np.ones((1,1), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # تحويل مرة أخرى لـ PIL
            result_img = Image.fromarray(thresh).convert('RGB')
            
            return result_img
            
        except Exception as e:
            logger.error(f"❌ Tesseract preparation failed: {e}")
            return image

    def chart_to_data_context(self, image_data: bytes, user_context: Optional[str] = None) -> str:
        """
        تحويل الشارت إلى بيانات منسقة مع السياق
        """
        try:
            # استخراج البيانات المتقدمة
            text_data = self.extract_text_from_chart_advanced(image_data)
            
            # بناء السياق الشامل
            context_parts = []
            
            # معلومات الشارت الأساسية
            context_parts.append("=== تحليل شامل للشارت ===")
            
            # الأسعار المستخرجة
            if text_data.get("prices"):
                prices = sorted(text_data["prices"])
                context_parts.append(f"الأسعار المكتشفة: {prices}")
                context_parts.append(f"أعلى سعر مرئي: ${max(prices):.2f}")
                context_parts.append(f"أدنى سعر مرئي: ${min(prices):.2f}")
                context_parts.append(f"نطاق الأسعار: ${max(prices) - min(prices):.2f}")
            
            # الأوقات المستخرجة
            if text_data.get("timestamps"):
                context_parts.append(f"الأوقات المكتشفة: {text_data['timestamps']}")
            
            # النصوص الكاملة
            if text_data.get("full_text"):
                context_parts.append(f"النصوص المستخرجة: {text_data['full_text'][:200]}...")
            
            # معلومات الثقة
            if text_data.get("average_confidence"):
                context_parts.append(f"مستوى الثقة في استخراج البيانات: {text_data['average_confidence']:.2f}")
            
            # السياق المقدم من المستخدم
            if user_context:
                context_parts.append(f"السياق المقدم من المستخدم: {user_context}")
            
            # تعليمات للتحليل
            context_parts.extend([
                "",
                "=== تعليمات التحليل ===",
                "1. استخدم البيانات المستخرجة أعلاه مع الصورة المرفقة",
                "2. اربط الأسعار المستخرجة بالحركة المرئية في الشارت",
                "3. حلل الاتجاهات بناءً على البيانات الرقمية والبصرية",
                "4. قدم توصيات محددة بناءً على التحليل الشامل",
                "5. إذا كانت البيانات المستخرجة غير واضحة، ركز على التحليل البصري"
            ])
            
            formatted_context = "\n".join(context_parts)
            
            logger.info("✅ Chart context built successfully")
            return formatted_context
            
        except Exception as e:
            logger.error(f"❌ Chart context building failed: {e}")
            return f"خطأ في بناء سياق الشارت: {str(e)}"

    def get_ohlc_data_simulation(self, symbol: str = 'XAUUSD', timeframe: str = '4h') -> Dict[str, Any]:
        """
        محاكاة بيانات OHLC للشارت (يمكن ربطها بـ APIs حقيقية لاحقاً)
        """
        try:
            # بيانات تجريبية محاكية (في التطبيق الحقيقي، استخدم API)
            sample_data = [
                {"time": "2024-01-30 08:00", "open": 2650.45, "high": 2658.30, "low": 2648.20, "close": 2655.80},
                {"time": "2024-01-30 12:00", "open": 2655.80, "high": 2662.15, "low": 2652.40, "close": 2659.70},
                {"time": "2024-01-30 16:00", "open": 2659.70, "high": 2665.90, "low": 2657.30, "close": 2661.25},
                {"time": "2024-01-30 20:00", "open": 2661.25, "high": 2668.45, "low": 2659.80, "close": 2665.15},
                {"time": "2024-01-31 00:00", "open": 2665.15, "high": 2670.30, "low": 2663.70, "close": 2668.90},
            ]
            
            # تنسيق البيانات
            formatted_data = f"بيانات {symbol} - الإطار الزمني {timeframe}:\n"
            formatted_data += "الوقت | فتح | أعلى | أدنى | إغلاق\n"
            formatted_data += "-" * 50 + "\n"
            
            for candle in sample_data:
                formatted_data += f"{candle['time']} | {candle['open']:.2f} | {candle['high']:.2f} | {candle['low']:.2f} | {candle['close']:.2f}\n"
            
            # حساب إحصائيات
            prices = [candle['close'] for candle in sample_data]
            stats = {
                "current_price": prices[-1],
                "highest": max([candle['high'] for candle in sample_data]),
                "lowest": min([candle['low'] for candle in sample_data]),
                "average": sum(prices) / len(prices),
                "volatility": max(prices) - min(prices)
            }
            
            formatted_data += f"\nإحصائيات:\n"
            formatted_data += f"السعر الحالي: ${stats['current_price']:.2f}\n"
            formatted_data += f"أعلى سعر: ${stats['highest']:.2f}\n"
            formatted_data += f"أدنى سعر: ${stats['lowest']:.2f}\n"
            formatted_data += f"المتوسط: ${stats['average']:.2f}\n"
            formatted_data += f"التقلبات: ${stats['volatility']:.2f}\n"
            
            return {
                "raw_data": sample_data,
                "formatted_text": formatted_data,
                "statistics": stats,
                "symbol": symbol,
                "timeframe": timeframe
            }
            
        except Exception as e:
            logger.error(f"❌ OHLC data simulation failed: {e}")
            return {"error": str(e)}

    def analyze_chart_intelligently(self, image_data: bytes, user_context: Optional[str] = None) -> Dict[str, Any]:
        """
        تحليل ذكي شامل للشارت - النهج المختلط المقترح
        """
        try:
            analysis_result = {
                "optimization_log": {},
                "text_extraction": {},
                "ohlc_simulation": {},
                "comprehensive_prompt": "",
                "optimized_image_data": None,
                "confidence_score": 0.0
            }
            
            logger.info("🔍 Starting intelligent chart analysis...")
            
            # 1. تحسين الصورة
            optimized_data, optimization_log = self.optimize_chart_image(image_data)
            analysis_result["optimization_log"] = optimization_log
            analysis_result["optimized_image_data"] = optimized_data
            
            # 2. استخراج النصوص المتقدم
            text_data = self.extract_text_from_chart_advanced(optimized_data)
            analysis_result["text_extraction"] = text_data
            
            # 3. محاكاة بيانات OHLC
            ohlc_data = self.get_ohlc_data_simulation()
            analysis_result["ohlc_simulation"] = ohlc_data
            
            # 4. بناء السياق الشامل
            chart_context = self.chart_to_data_context(optimized_data, user_context)
            
            # 5. بناء الـ Prompt الشامل
            comprehensive_prompt = f"""
تحليل شامل ومتقدم لشارت الذهب - نهج مختلط ذكي

=== البيانات المستخرجة من الصورة ===
{chart_context}

=== بيانات OHLC المحاكية ===
{ohlc_data.get('formatted_text', 'غير متوفر')}

=== تحسينات الصورة المطبقة ===
الخطوات المطبقة: {', '.join(optimization_log.get('steps_applied', []))}
الثقة في استخراج النصوص: {text_data.get('average_confidence', 0):.2f}

=== السياق الإضافي ===
{user_context or 'لا يوجد سياق إضافي مقدم من المستخدم'}

=== المطلوب ===
بناءً على:
1. الصورة المحسنة المرفقة
2. البيانات النصية المستخرجة أعلاه  
3. بيانات OHLC المحاكية
4. السياق المقدم

قدم تحليلاً فنياً شاملاً يتضمن:
- تحليل الاتجاه العام
- مستويات الدعم والمقاومة المحددة
- توقعات قصيرة ومتوسطة المدى
- نقاط الدخول والخروج المقترحة
- إدارة المخاطر
- توصيات تداول محددة مع الأسباب

ملاحظة: إذا كانت البيانات المستخرجة غير دقيقة، اعتمد بشكل أكبر على التحليل البصري للصورة المحسنة.
            """.strip()
            
            analysis_result["comprehensive_prompt"] = comprehensive_prompt
            
            # حساب درجة الثقة الإجمالية
            confidence_factors = []
            
            if optimization_log.get("steps_applied"):
                confidence_factors.append(0.2)  # تحسين الصورة
            
            if text_data.get("prices"):
                confidence_factors.append(0.3)  # استخراج الأسعار
            
            if text_data.get("average_confidence", 0) > 0.7:
                confidence_factors.append(0.2)  # جودة OCR
            
            if ohlc_data.get("raw_data"):
                confidence_factors.append(0.3)  # بيانات إضافية
            
            analysis_result["confidence_score"] = sum(confidence_factors)
            
            logger.info(f"✅ Intelligent analysis complete. Confidence: {analysis_result['confidence_score']:.2f}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Intelligent chart analysis failed: {e}")
            return {"error": str(e)}

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