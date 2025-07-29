#!/usr/bin/env python3
"""
Al Kabous AI - Comprehensive Backend Testing
اختبار شامل لخادم تحليل الذهب - الكابوس الذهبي
"""
import requests
import sys
import json
import time
import base64
from datetime import datetime
from typing import Dict, Any, Optional

class AlKabousAITester:
    """Comprehensive tester for Al Kabous AI Gold Analysis backend"""
    
    def __init__(self, base_url: str = "https://bae3be57-e4e6-4bb1-8d14-596456a3856b.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test configuration
        self.timeout = 60  # Increased for AI analysis
        self.expected_gold_price_range = (3200, 3400)  # Around $3310
        
        print(f"🚀 Initializing Al Kabous AI Backend Tester")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"⏰ Request timeout: {self.timeout}s")
        print(f"💰 Expected gold price range: ${self.expected_gold_price_range[0]}-${self.expected_gold_price_range[1]}")
        print("=" * 60)

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        print(f"{status} | {name}")
        if details:
            print(f"     └─ {details}")
        if not success and response_data:
            print(f"     └─ Response: {response_data}")
        print()

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200) -> tuple[bool, Any]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                return False, f"Unsupported method: {method}"
            
            # Check status code
            if response.status_code != expected_status:
                return False, {
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "response_text": response.text[:500]
                }
            
            # Try to parse JSON
            try:
                return True, response.json()
            except json.JSONDecodeError:
                return True, response.text
                
        except requests.exceptions.Timeout:
            return False, f"Request timeout after {self.timeout}s"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - backend may be down"
        except Exception as e:
            return False, f"Request error: {str(e)}"

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        print("🔍 Testing Health Endpoint...")
        
        success, response = self.make_request('GET', '/api/health')
        
        if not success:
            self.log_test("Health Check", False, "Request failed", response)
            return False
        
        # Validate response structure for current API
        required_fields = ['status', 'api_running', 'timestamp']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            self.log_test("Health Check", False, f"Missing fields: {missing_fields}", response)
            return False
        
        # Check if status is healthy
        if response.get('status') != 'healthy':
            self.log_test("Health Check", False, f"Status not healthy: {response.get('status')}", response)
            return False
        
        api_status = "running" if response.get('api_running') else "stopped"
        self.log_test("Health Check", True, f"Status: {response.get('status')}, API: {api_status}")
        return True

    def test_gold_price_endpoint(self):
        """Test /api/gold-price endpoint - HIGH PRIORITY"""
        print("💰 Testing Gold Price Endpoint...")
        
        success, response = self.make_request('GET', '/api/gold-price')
        
        if not success:
            self.log_test("Gold Price API", False, "Request failed", response)
            return False
        
        # Validate response structure
        if not isinstance(response, dict):
            self.log_test("Gold Price API", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("Gold Price API", False, f"API returned error: {response.get('error')}", response)
            return False
        
        # Check price data
        price_data = response.get('price_data')
        if not price_data:
            self.log_test("Gold Price API", False, "No price data returned", response)
            return False
        
        # Validate price is in expected range (~$3310)
        price_usd = price_data.get('price_usd')
        if not price_usd:
            self.log_test("Gold Price API", False, "No USD price found", response)
            return False
        
        if not (self.expected_gold_price_range[0] <= price_usd <= self.expected_gold_price_range[1]):
            self.log_test("Gold Price Accuracy", False, 
                         f"Price ${price_usd} outside expected range ${self.expected_gold_price_range[0]}-${self.expected_gold_price_range[1]}", 
                         price_data)
            return False
        
        # Check Arabic formatted text
        formatted_text = response.get('formatted_text')
        if not formatted_text:
            self.log_test("Gold Price Arabic Format", False, "No Arabic formatted text", response)
            return False
        
        self.log_test("Gold Price API", True, 
                     f"Price: ${price_usd}, Source: {price_data.get('source')}, Change: {price_data.get('price_change_pct', 0):.2f}%")
        return True

    def test_analysis_types_endpoint(self):
        """Test /api/analysis-types endpoint"""
        print("📊 Testing Analysis Types Endpoint...")
        
        success, response = self.make_request('GET', '/api/analysis-types')
        
        if not success:
            self.log_test("Analysis Types", False, "Request failed", response)
            return False
        
        # Validate response structure
        if not isinstance(response, dict) or 'types' not in response:
            self.log_test("Analysis Types", False, "Invalid response structure", response)
            return False
        
        types = response['types']
        expected_types = ['quick', 'detailed', 'chart', 'news', 'forecast']
        
        available_types = [t.get('id') for t in types if isinstance(t, dict)]
        missing_types = [t for t in expected_types if t not in available_types]
        
        if missing_types:
            self.log_test("Analysis Types", False, f"Missing analysis types: {missing_types}", response)
            return False
        
        self.log_test("Analysis Types", True, f"Available types: {available_types}")
        return True

    def test_regular_analysis_endpoint(self):
        """Test /api/analyze endpoint with all analysis types - HIGH PRIORITY"""
        print("🧠 Testing Regular Analysis Endpoint...")
        
        analysis_types = ['quick', 'detailed', 'chart', 'news', 'forecast']
        all_passed = True
        
        for analysis_type in analysis_types:
            print(f"  Testing {analysis_type} analysis...")
            
            test_data = {
                "analysis_type": analysis_type,
                "user_question": f"تحليل {analysis_type} للذهب",
                "additional_context": "اختبار من النظام"
            }
            
            start_time = time.time()
            success, response = self.make_request('POST', '/api/analyze', test_data)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            if not success:
                self.log_test(f"Analysis - {analysis_type}", False, "Request failed", response)
                all_passed = False
                continue
            
            # Validate response structure
            if not isinstance(response, dict):
                self.log_test(f"Analysis - {analysis_type}", False, "Invalid response format", response)
                all_passed = False
                continue
            
            if not response.get('success'):
                self.log_test(f"Analysis - {analysis_type}", False, 
                             f"Analysis failed: {response.get('error')}", response)
                all_passed = False
                continue
            
            # Check analysis content
            analysis_content = response.get('analysis')
            if not analysis_content or len(analysis_content) < 50:
                self.log_test(f"Analysis - {analysis_type}", False, 
                             "Analysis content too short or missing", response)
                all_passed = False
                continue
            
            # Check if analysis contains Arabic text
            if not any(ord(char) > 127 for char in analysis_content):
                self.log_test(f"Analysis - {analysis_type}", False, 
                             "Analysis doesn't contain Arabic text", response)
                all_passed = False
                continue
            
            self.log_test(f"Analysis - {analysis_type}", True, 
                         f"Response time: {response_time:.0f}ms, Content length: {len(analysis_content)} chars")
        
        return all_passed

    def create_test_chart_image(self):
        """Create a simple test chart image in base64 format"""
        # Create a simple 200x200 white image with some basic chart-like elements
        from PIL import Image, ImageDraw
        
        # Create a white image
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some basic chart elements
        # Draw axes
        draw.line([(20, 180), (180, 180)], fill='black', width=2)  # X-axis
        draw.line([(20, 20), (20, 180)], fill='black', width=2)   # Y-axis
        
        # Draw a simple price line
        points = [(20, 150), (50, 120), (80, 100), (110, 80), (140, 90), (170, 70)]
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill='blue', width=2)
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str

    def test_chart_analysis_endpoint(self):
        """Test /api/analyze-chart endpoint - HIGH PRIORITY"""
        print("📈 Testing Chart Analysis Endpoint...")
        
        try:
            # Create test chart image
            test_image = self.create_test_chart_image()
            
            test_data = {
                "image_data": test_image,
                "currency_pair": "XAU/USD",
                "timeframe": "H1",
                "analysis_notes": "اختبار تحليل الشارت من النظام"
            }
            
            start_time = time.time()
            success, response = self.make_request('POST', '/api/analyze-chart', test_data)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            if not success:
                self.log_test("Chart Analysis", False, "Request failed", response)
                return False
            
            # Validate response structure
            if not isinstance(response, dict):
                self.log_test("Chart Analysis", False, "Invalid response format", response)
                return False
            
            if not response.get('success'):
                self.log_test("Chart Analysis", False, 
                             f"Chart analysis failed: {response.get('error')}", response)
                return False
            
            # Check analysis content
            analysis_content = response.get('analysis')
            if not analysis_content or len(analysis_content) < 100:
                self.log_test("Chart Analysis", False, 
                             "Analysis content too short or missing", response)
                return False
            
            # Check image info
            image_info = response.get('image_info')
            if not image_info:
                self.log_test("Chart Analysis - Image Info", False, 
                             "No image info returned", response)
                return False
            
            # Validate image info structure
            expected_info_fields = ['width', 'height', 'format', 'size_kb']
            missing_info = [field for field in expected_info_fields if field not in image_info]
            
            if missing_info:
                self.log_test("Chart Analysis - Image Info", False, 
                             f"Missing image info fields: {missing_info}", image_info)
                return False
            
            # Check if analysis contains Arabic text
            if not any(ord(char) > 127 for char in analysis_content):
                self.log_test("Chart Analysis - Arabic Content", False, 
                             "Analysis doesn't contain Arabic text", response)
                return False
            
            self.log_test("Chart Analysis", True, 
                         f"Response time: {response_time:.0f}ms, Content length: {len(analysis_content)} chars, "
                         f"Image: {image_info['width']}x{image_info['height']} {image_info['format']}")
            return True
            
        except Exception as e:
            self.log_test("Chart Analysis", False, f"Test setup error: {str(e)}")
            return False

    def test_api_status_endpoint(self):
        """Test /api/api-status endpoint"""
        print("🔧 Testing API Status Endpoint...")
        
        success, response = self.make_request('GET', '/api/api-status')
        
        if not success:
            self.log_test("API Status", False, "Request failed", response)
            return False
        
        # Validate response structure
        if not isinstance(response, dict):
            self.log_test("API Status", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("API Status", False, f"API status check failed: {response.get('error')}", response)
            return False
        
        status_data = response.get('status', {})
        
        # Check for gold APIs status
        gold_apis = status_data.get('gold_apis')
        claude_ai = status_data.get('claude_ai')
        
        details = []
        if gold_apis:
            details.append(f"Gold APIs: {len(gold_apis) if isinstance(gold_apis, list) else 'available'}")
        if claude_ai:
            details.append(f"Claude AI: available")
        
        self.log_test("API Status", True, f"External services: {', '.join(details) if details else 'basic info'}")
        return True

    def test_performance_and_response_times(self):
        """Test API performance and response times"""
        print("⏱️ Testing Performance and Response Times...")
        
        endpoints = [
            ('/api/health', 'GET', None),
            ('/api/gold-price', 'GET', None),
            ('/api/analysis-types', 'GET', None),
        ]
        
        response_times = {}
        all_passed = True
        
        for endpoint, method, data in endpoints:
            start_time = time.time()
            success, response = self.make_request(method, endpoint, data)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times[endpoint] = response_time
            
            # Performance thresholds
            if endpoint == '/api/health':
                threshold = 2000  # 2 seconds for health
            elif endpoint == '/api/gold-price':
                threshold = 10000  # 10 seconds for gold price
            else:
                threshold = 5000  # 5 seconds for others
            
            if success and response_time < threshold:
                self.log_test(f"Performance {endpoint}", True, f"{response_time:.0f}ms")
            else:
                self.log_test(f"Performance {endpoint}", False, 
                             f"Slow response: {response_time:.0f}ms (threshold: {threshold}ms)")
                all_passed = False
        
        if response_times:
            avg_response_time = sum(response_times.values()) / len(response_times)
            self.log_test("Average Response Time", True, f"{avg_response_time:.0f}ms")
        
        return all_passed

    def test_error_handling(self):
        """Test error handling"""
        print("🚫 Testing Error Handling...")
        
        # Test invalid analysis type
        invalid_analysis_data = {
            "analysis_type": "invalid_type",
            "user_question": "test"
        }
        
        success, response = self.make_request('POST', '/api/analyze', invalid_analysis_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            self.log_test("Error Handling - Invalid Analysis Type", True, 
                         f"Correctly handled invalid analysis type: {response.get('error')}")
        else:
            self.log_test("Error Handling - Invalid Analysis Type", False, 
                         "Should reject invalid analysis type", response)
        
        # Test invalid chart data
        invalid_chart_data = {
            "image_data": "invalid_base64_data",
            "currency_pair": "XAU/USD"
        }
        
        success, response = self.make_request('POST', '/api/analyze-chart', invalid_chart_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            self.log_test("Error Handling - Invalid Chart Data", True, 
                         f"Correctly handled invalid chart data: {response.get('error')}")
        else:
            self.log_test("Error Handling - Invalid Chart Data", False, 
                         "Should reject invalid chart data", response)
        
        return True

    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting Al Kabous AI Backend Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core API Tests (High Priority)
        self.test_health_endpoint()
        self.test_gold_price_endpoint()  # HIGH PRIORITY
        self.test_chart_analysis_endpoint()  # HIGH PRIORITY  
        self.test_regular_analysis_endpoint()  # HIGH PRIORITY
        
        # Supporting API Tests
        self.test_analysis_types_endpoint()
        self.test_api_status_endpoint()
        
        # Performance and Error Tests
        self.test_performance_and_response_times()
        self.test_error_handling()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        print("\n🎯 RECOMMENDATIONS:")
        
        if self.tests_passed == self.tests_run:
            print("  ✅ All tests passed! Backend is working correctly.")
        else:
            print("  ⚠️ Some tests failed. Check the details above.")
            
        # Specific recommendations based on results
        gold_price_passed = any(r['test'] == 'Gold Price API' and r['success'] for r in self.test_results)
        chart_analysis_passed = any(r['test'] == 'Chart Analysis' and r['success'] for r in self.test_results)
        regular_analysis_passed = any('Analysis -' in r['test'] and r['success'] for r in self.test_results)
        
        if not gold_price_passed:
            print("  💰 Gold price API issues - check gold price providers and API keys")
        
        if not chart_analysis_passed:
            print("  📈 Chart analysis issues - check Claude AI integration and image processing")
        
        if not regular_analysis_passed:
            print("  🧠 Analysis issues - check Claude AI API key and prompts")
        
        print("\n📊 Detailed results saved in test_results list")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = AlKabousAITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())