#!/usr/bin/env python3
"""
Gold Nightmare Bot - Comprehensive Backend Testing
اختبار شامل لخادم Gold Nightmare Bot
"""
import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class GoldNightmareBotTester:
    """Comprehensive tester for Gold Nightmare Bot backend"""
    
    def __init__(self, base_url: str = "https://bae3be57-e4e6-4bb1-8d14-596456a3856b.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test configuration
        self.timeout = 30
        self.master_user_id = "590918137"
        
        print(f"🚀 Initializing Gold Nightmare Bot Tester")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"⏰ Request timeout: {self.timeout}s")
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
        
        # Validate response structure
        required_fields = ['status', 'bot_running', 'timestamp']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            self.log_test("Health Check", False, f"Missing fields: {missing_fields}", response)
            return False
        
        # Check if status is healthy
        if response.get('status') != 'healthy':
            self.log_test("Health Check", False, f"Status not healthy: {response.get('status')}", response)
            return False
        
        bot_status = "running" if response.get('bot_running') else "stopped"
        self.log_test("Health Check", True, f"Status: {response.get('status')}, Bot: {bot_status}")
        return True

    def test_bot_stats_endpoint(self):
        """Test /api/bot/stats endpoint"""
        print("📊 Testing Bot Stats Endpoint...")
        
        success, response = self.make_request('GET', '/api/bot/stats')
        
        if not success:
            self.log_test("Bot Stats", False, "Request failed", response)
            return False
        
        # Check for error response
        if isinstance(response, dict) and 'detail' in response:
            if 'Bot not initialized' in response['detail']:
                self.log_test("Bot Stats", False, "Bot not initialized", response)
                return False
        
        # Validate stats structure (if bot is running)
        expected_fields = ['bot_name', 'running', 'uptime_hours', 'total_users', 'active_users']
        
        if isinstance(response, dict):
            available_fields = [field for field in expected_fields if field in response]
            self.log_test("Bot Stats", True, f"Available fields: {available_fields}", 
                         {k: v for k, v in response.items() if k in expected_fields})
        else:
            self.log_test("Bot Stats", False, "Invalid response format", response)
            return False
        
        return True

    def test_broadcast_endpoint(self):
        """Test /api/bot/broadcast endpoint"""
        print("📢 Testing Broadcast Endpoint...")
        
        # Test without authentication (should fail)
        test_data = {
            "message": "Test broadcast message",
            "admin_id": "invalid_id"
        }
        
        success, response = self.make_request('POST', '/api/bot/broadcast', test_data, expected_status=403)
        
        if success:
            self.log_test("Broadcast - Unauthorized", True, "Correctly rejected unauthorized request")
        else:
            self.log_test("Broadcast - Unauthorized", False, "Should reject unauthorized request", response)
        
        # Test with correct admin ID but potentially no bot
        test_data_admin = {
            "message": "Test broadcast from admin",
            "admin_id": self.master_user_id
        }
        
        success, response = self.make_request('POST', '/api/bot/broadcast', test_data_admin, expected_status=503)
        
        if success or (isinstance(response, dict) and 'Bot not initialized' in str(response)):
            self.log_test("Broadcast - Admin Auth", True, "Admin authentication working")
        else:
            self.log_test("Broadcast - Admin Auth", False, "Admin authentication issue", response)
        
        return True

    def test_cors_headers(self):
        """Test CORS configuration"""
        print("🌐 Testing CORS Headers...")
        
        try:
            response = requests.options(f"{self.base_url}/api/health", timeout=self.timeout)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            has_cors = any(cors_headers.values())
            
            if has_cors:
                self.log_test("CORS Configuration", True, f"CORS headers present: {cors_headers}")
            else:
                self.log_test("CORS Configuration", False, "No CORS headers found")
            
            return has_cors
            
        except Exception as e:
            self.log_test("CORS Configuration", False, f"CORS test failed: {e}")
            return False

    def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        print("🚫 Testing Error Handling...")
        
        # Test non-existent endpoint
        success, response = self.make_request('GET', '/api/nonexistent', expected_status=404)
        
        if success:
            self.log_test("404 Error Handling", True, "Correctly returns 404 for invalid endpoint")
        else:
            # Some frameworks return different status codes, check if it's a reasonable error
            if isinstance(response, dict) and response.get('actual_status') in [404, 405, 422]:
                self.log_test("404 Error Handling", True, f"Returns {response.get('actual_status')} for invalid endpoint")
            else:
                self.log_test("404 Error Handling", False, "Invalid endpoint handling issue", response)
        
        # Test malformed JSON
        try:
            url = f"{self.base_url}/api/bot/broadcast"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data="invalid json", headers=headers, timeout=self.timeout)
            
            if response.status_code in [400, 422]:
                self.log_test("JSON Error Handling", True, f"Correctly handles malformed JSON (status: {response.status_code})")
            else:
                self.log_test("JSON Error Handling", False, f"Unexpected status for malformed JSON: {response.status_code}")
                
        except Exception as e:
            self.log_test("JSON Error Handling", False, f"JSON error test failed: {e}")
        
        return True

    def test_response_times(self):
        """Test API response times"""
        print("⏱️ Testing Response Times...")
        
        endpoints = ['/api/health', '/api/bot/stats']
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            success, response = self.make_request('GET', endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            response_times[endpoint] = response_time
            
            if success and response_time < 5000:  # Less than 5 seconds
                self.log_test(f"Response Time {endpoint}", True, f"{response_time:.2f}ms")
            else:
                self.log_test(f"Response Time {endpoint}", False, f"Slow response: {response_time:.2f}ms")
        
        avg_response_time = sum(response_times.values()) / len(response_times)
        self.log_test("Average Response Time", True, f"{avg_response_time:.2f}ms")
        
        return True

    def test_api_prefix_routing(self):
        """Test that API routes require /api prefix"""
        print("🛣️ Testing API Prefix Routing...")
        
        # Test without /api prefix (should fail or redirect)
        success, response = self.make_request('GET', '/health', expected_status=404)
        
        if success:
            self.log_test("API Prefix Routing", True, "Correctly requires /api prefix")
        else:
            # Check if it's redirected or returns different status
            if isinstance(response, dict) and response.get('actual_status') in [301, 302, 404]:
                self.log_test("API Prefix Routing", True, f"API prefix enforced (status: {response.get('actual_status')})")
            else:
                self.log_test("API Prefix Routing", False, "API prefix routing issue", response)
        
        return True

    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting Gold Nightmare Bot Backend Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core API Tests
        self.test_health_endpoint()
        self.test_bot_stats_endpoint()
        self.test_broadcast_endpoint()
        
        # Infrastructure Tests
        self.test_cors_headers()
        self.test_error_handling()
        self.test_response_times()
        self.test_api_prefix_routing()
        
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
        health_passed = any(r['test'] == 'Health Check' and r['success'] for r in self.test_results)
        stats_passed = any(r['test'] == 'Bot Stats' and r['success'] for r in self.test_results)
        
        if not health_passed:
            print("  🔧 Health endpoint issues - check if backend server is running")
        
        if not stats_passed:
            print("  🤖 Bot stats issues - check if Telegram bot is properly initialized")
            print("  📋 Verify environment variables: TELEGRAM_BOT_TOKEN, CLAUDE_API_KEY, etc.")
        
        print("\n📊 Detailed results saved in test_results list")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = GoldNightmareBotTester()
    
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