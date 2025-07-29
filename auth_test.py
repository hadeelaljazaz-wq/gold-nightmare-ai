#!/usr/bin/env python3
"""
Al Kabous AI - Authentication & Subscription System Testing
اختبار نظام المصادقة والاشتراكات - الكابوس الذهبي
"""
import requests
import sys
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, Any, Optional

class AlKabousAuthTester:
    """Comprehensive tester for Al Kabous AI Authentication & Subscription System"""
    
    def __init__(self, base_url: str = "https://33206162-97aa-4ab2-bf61-8029b938fa88.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test configuration
        self.timeout = 30
        
        # Test user data
        self.test_users = []
        
        print(f"🚀 Initializing Al Kabous AI Authentication System Tester")
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

    def generate_test_user_data(self):
        """Generate realistic test user data"""
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return {
            "email": f"ahmed.hassan{random_suffix}@gmail.com",
            "password": "Ahmed123456",
            "username": f"ahmed_hassan_{random_suffix}",
            "first_name": "أحمد",
            "last_name": "حسن"
        }

    def test_user_registration(self):
        """Test user registration endpoint - HIGH PRIORITY"""
        print("👤 Testing User Registration...")
        
        # Test valid registration
        user_data = self.generate_test_user_data()
        
        success, response = self.make_request('POST', '/api/auth/register', user_data)
        
        if not success:
            self.log_test("User Registration - Valid Data", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("User Registration - Valid Data", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("User Registration - Valid Data", False, 
                         f"Registration failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        user_info = response.get('user', {})
        required_fields = ['user_id', 'email', 'tier', 'daily_analyses_remaining']
        missing_fields = [field for field in required_fields if field not in user_info]
        
        if missing_fields:
            self.log_test("User Registration - Response Structure", False, 
                         f"Missing fields: {missing_fields}", user_info)
            return False
        
        # Store test user for later tests
        test_user = {
            "user_id": user_info['user_id'],
            "email": user_data['email'],
            "password": user_data['password'],
            "tier": user_info['tier'],
            "daily_analyses_remaining": user_info['daily_analyses_remaining']
        }
        self.test_users.append(test_user)
        
        self.log_test("User Registration - Valid Data", True, 
                     f"User registered: ID={user_info['user_id']}, Email={user_info['email']}, "
                     f"Tier={user_info['tier']}, Daily limit={user_info['daily_analyses_remaining']}")
        
        # Test duplicate email registration
        success, response = self.make_request('POST', '/api/auth/register', user_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("User Registration - Duplicate Email", True, 
                         f"Correctly rejected duplicate email. Arabic error: {has_arabic}")
        else:
            self.log_test("User Registration - Duplicate Email", False, 
                         "Should reject duplicate email", response)
        
        # Test invalid email format
        invalid_user_data = user_data.copy()
        invalid_user_data['email'] = "invalid-email-format"
        
        success, response = self.make_request('POST', '/api/auth/register', invalid_user_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("User Registration - Invalid Email", True, 
                         f"Correctly rejected invalid email. Arabic error: {has_arabic}")
        else:
            self.log_test("User Registration - Invalid Email", False, 
                         "Should reject invalid email format", response)
        
        # Test weak password
        weak_password_data = self.generate_test_user_data()
        weak_password_data['password'] = "123"
        
        success, response = self.make_request('POST', '/api/auth/register', weak_password_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("User Registration - Weak Password", True, 
                         f"Correctly rejected weak password. Arabic error: {has_arabic}")
        else:
            self.log_test("User Registration - Weak Password", False, 
                         "Should reject weak password", response)
        
        return True

    def test_user_login(self):
        """Test user login endpoint - HIGH PRIORITY"""
        print("🔐 Testing User Login...")
        
        if not self.test_users:
            self.log_test("User Login - Setup", False, "No test users available for login test")
            return False
        
        test_user = self.test_users[0]
        
        # Test valid login
        login_data = {
            "email": test_user['email'],
            "password": test_user['password']
        }
        
        success, response = self.make_request('POST', '/api/auth/login', login_data)
        
        if not success:
            self.log_test("User Login - Valid Credentials", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("User Login - Valid Credentials", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("User Login - Valid Credentials", False, 
                         f"Login failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        user_info = response.get('user', {})
        required_fields = ['user_id', 'email', 'tier', 'daily_analyses_remaining']
        missing_fields = [field for field in required_fields if field not in user_info]
        
        if missing_fields:
            self.log_test("User Login - Response Structure", False, 
                         f"Missing fields: {missing_fields}", user_info)
            return False
        
        # Verify user data matches registration
        if user_info['user_id'] != test_user['user_id']:
            self.log_test("User Login - Data Consistency", False, 
                         f"User ID mismatch: expected {test_user['user_id']}, got {user_info['user_id']}")
            return False
        
        self.log_test("User Login - Valid Credentials", True, 
                     f"Login successful: ID={user_info['user_id']}, Email={user_info['email']}, "
                     f"Tier={user_info['tier']}, Remaining={user_info['daily_analyses_remaining']}")
        
        # Test invalid password
        invalid_login_data = {
            "email": test_user['email'],
            "password": "wrong_password"
        }
        
        success, response = self.make_request('POST', '/api/auth/login', invalid_login_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("User Login - Invalid Password", True, 
                         f"Correctly rejected invalid password. Arabic error: {has_arabic}")
        else:
            self.log_test("User Login - Invalid Password", False, 
                         "Should reject invalid password", response)
        
        # Test non-existent email
        nonexistent_login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        success, response = self.make_request('POST', '/api/auth/login', nonexistent_login_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("User Login - Non-existent Email", True, 
                         f"Correctly rejected non-existent email. Arabic error: {has_arabic}")
        else:
            self.log_test("User Login - Non-existent Email", False, 
                         "Should reject non-existent email", response)
        
        return True

    def test_get_user_info(self):
        """Test get user info endpoint - HIGH PRIORITY"""
        print("ℹ️ Testing Get User Info...")
        
        if not self.test_users:
            self.log_test("Get User Info - Setup", False, "No test users available")
            return False
        
        test_user = self.test_users[0]
        user_id = test_user['user_id']
        
        success, response = self.make_request('GET', f'/api/auth/user/{user_id}')
        
        if not success:
            self.log_test("Get User Info - Valid User ID", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("Get User Info - Valid User ID", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("Get User Info - Valid User ID", False, 
                         f"Request failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        user_info = response.get('user', {})
        required_fields = ['user_id', 'email', 'tier', 'status', 'daily_analyses_remaining', 
                          'total_analyses', 'features', 'created_at']
        missing_fields = [field for field in required_fields if field not in user_info]
        
        if missing_fields:
            self.log_test("Get User Info - Response Structure", False, 
                         f"Missing fields: {missing_fields}", user_info)
            return False
        
        # Verify user data
        if user_info['user_id'] != user_id:
            self.log_test("Get User Info - Data Consistency", False, 
                         f"User ID mismatch: expected {user_id}, got {user_info['user_id']}")
            return False
        
        # Check features structure
        features = user_info.get('features', {})
        expected_feature_keys = ['daily_analyses', 'save_history', 'priority_support']
        missing_features = [key for key in expected_feature_keys if key not in features]
        
        if missing_features:
            self.log_test("Get User Info - Features Structure", False, 
                         f"Missing feature keys: {missing_features}", features)
            return False
        
        self.log_test("Get User Info - Valid User ID", True, 
                     f"User info retrieved: ID={user_info['user_id']}, Email={user_info['email']}, "
                     f"Tier={user_info['tier']}, Status={user_info['status']}, "
                     f"Daily limit={features['daily_analyses']}")
        
        # Test non-existent user ID
        success, response = self.make_request('GET', '/api/auth/user/99999')
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("Get User Info - Non-existent User", True, 
                         f"Correctly handled non-existent user. Arabic error: {has_arabic}")
        else:
            self.log_test("Get User Info - Non-existent User", False, 
                         "Should handle non-existent user properly", response)
        
        return True

    def test_check_analysis_permission(self):
        """Test check analysis permission endpoint - HIGH PRIORITY"""
        print("🔍 Testing Check Analysis Permission...")
        
        if not self.test_users:
            self.log_test("Check Analysis Permission - Setup", False, "No test users available")
            return False
        
        test_user = self.test_users[0]
        user_id = test_user['user_id']
        
        success, response = self.make_request('GET', f'/api/auth/check-analysis-permission/{user_id}')
        
        if not success:
            self.log_test("Check Analysis Permission - Valid User", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("Check Analysis Permission - Valid User", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("Check Analysis Permission - Valid User", False, 
                         f"Request failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        required_fields = ['can_analyze', 'message', 'remaining_analyses']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            self.log_test("Check Analysis Permission - Response Structure", False, 
                         f"Missing fields: {missing_fields}", response)
            return False
        
        can_analyze = response.get('can_analyze')
        remaining = response.get('remaining_analyses')
        message = response.get('message', '')
        
        # For a new user, they should be able to analyze
        if not can_analyze:
            self.log_test("Check Analysis Permission - New User", False, 
                         f"New user should be able to analyze. Message: {message}")
            return False
        
        # Basic tier should have 1 analysis remaining
        if remaining != 1:
            self.log_test("Check Analysis Permission - Basic Tier Limit", False, 
                         f"Basic tier should have 1 analysis remaining, got {remaining}")
            return False
        
        self.log_test("Check Analysis Permission - Valid User", True, 
                     f"Permission check successful: Can analyze={can_analyze}, "
                     f"Remaining={remaining}, Message='{message}'")
        
        # Test non-existent user
        success, response = self.make_request('GET', '/api/auth/check-analysis-permission/99999')
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("Check Analysis Permission - Non-existent User", True, 
                         f"Correctly handled non-existent user. Arabic error: {has_arabic}")
        else:
            self.log_test("Check Analysis Permission - Non-existent User", False, 
                         "Should handle non-existent user properly", response)
        
        return True

    def test_analysis_with_user_id(self):
        """Test analysis endpoint with user_id requirement - HIGH PRIORITY"""
        print("🧠 Testing Analysis with User ID...")
        
        if not self.test_users:
            self.log_test("Analysis with User ID - Setup", False, "No test users available")
            return False
        
        test_user = self.test_users[0]
        user_id = test_user['user_id']
        
        # Test analysis with valid user_id
        analysis_data = {
            "analysis_type": "quick",
            "user_question": "تحليل سريع للذهب - اختبار النظام",
            "user_id": user_id,
            "additional_context": "اختبار تحليل مع معرف المستخدم"
        }
        
        success, response = self.make_request('POST', '/api/analyze', analysis_data)
        
        if not success:
            self.log_test("Analysis with User ID - Valid Request", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("Analysis with User ID - Valid Request", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("Analysis with User ID - Valid Request", False, 
                         f"Analysis failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        required_fields = ['analysis', 'gold_price', 'processing_time']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            self.log_test("Analysis with User ID - Response Structure", False, 
                         f"Missing fields: {missing_fields}", response)
            return False
        
        analysis_content = response.get('analysis')
        if not analysis_content or len(analysis_content) < 50:
            self.log_test("Analysis with User ID - Content Quality", False, 
                         "Analysis content too short or missing")
            return False
        
        # Check if analysis contains Arabic text
        if not any(ord(char) > 127 for char in analysis_content):
            self.log_test("Analysis with User ID - Arabic Content", False, 
                         "Analysis doesn't contain Arabic text")
            return False
        
        processing_time = response.get('processing_time', 0)
        
        self.log_test("Analysis with User ID - Valid Request", True, 
                     f"Analysis successful: Content length={len(analysis_content)} chars, "
                     f"Processing time={processing_time:.2f}s")
        
        # Test analysis without user_id (should fail)
        analysis_data_no_user = {
            "analysis_type": "quick",
            "user_question": "تحليل بدون معرف مستخدم"
        }
        
        success, response = self.make_request('POST', '/api/analyze', analysis_data_no_user)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            self.log_test("Analysis with User ID - Missing User ID", True, 
                         f"Correctly rejected request without user_id: {error_msg}")
        else:
            self.log_test("Analysis with User ID - Missing User ID", False, 
                         "Should reject analysis request without user_id", response)
        
        # Test analysis with non-existent user_id
        analysis_data_invalid_user = {
            "analysis_type": "quick",
            "user_question": "تحليل مع معرف مستخدم غير موجود",
            "user_id": 99999
        }
        
        success, response = self.make_request('POST', '/api/analyze', analysis_data_invalid_user)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("Analysis with User ID - Invalid User ID", True, 
                         f"Correctly rejected invalid user_id. Arabic error: {has_arabic}")
        else:
            self.log_test("Analysis with User ID - Invalid User ID", False, 
                         "Should reject analysis with invalid user_id", response)
        
        return True

    def test_daily_limit_enforcement(self):
        """Test daily analysis limit enforcement - HIGH PRIORITY"""
        print("📊 Testing Daily Limit Enforcement...")
        
        if not self.test_users:
            self.log_test("Daily Limit - Setup", False, "No test users available")
            return False
        
        test_user = self.test_users[0]
        user_id = test_user['user_id']
        
        # Check initial permission (should be able to analyze)
        success, response = self.make_request('GET', f'/api/auth/check-analysis-permission/{user_id}')
        
        if not success or not response.get('success') or not response.get('can_analyze'):
            self.log_test("Daily Limit - Initial Check", False, 
                         "User should initially be able to analyze", response)
            return False
        
        initial_remaining = response.get('remaining_analyses', 0)
        
        # Perform analysis to consume the daily limit (Basic = 1 analysis)
        analysis_data = {
            "analysis_type": "quick",
            "user_question": "تحليل لاستنفاد الحد اليومي",
            "user_id": user_id
        }
        
        success, response = self.make_request('POST', '/api/analyze', analysis_data)
        
        if not success or not response.get('success'):
            self.log_test("Daily Limit - First Analysis", False, 
                         "First analysis should succeed", response)
            return False
        
        self.log_test("Daily Limit - First Analysis", True, 
                     f"First analysis successful, initial remaining: {initial_remaining}")
        
        # Check permission after first analysis (Basic tier should be exhausted)
        success, response = self.make_request('GET', f'/api/auth/check-analysis-permission/{user_id}')
        
        if not success or not response.get('success'):
            self.log_test("Daily Limit - Permission After First", False, 
                         "Permission check should succeed", response)
            return False
        
        can_analyze_after = response.get('can_analyze')
        remaining_after = response.get('remaining_analyses', 0)
        message_after = response.get('message', '')
        
        # For Basic tier (1 analysis), user should not be able to analyze after first analysis
        if can_analyze_after:
            self.log_test("Daily Limit - Basic Tier Exhaustion", False, 
                         f"Basic tier user should be exhausted after 1 analysis. "
                         f"Can analyze: {can_analyze_after}, Remaining: {remaining_after}")
            return False
        
        if remaining_after != 0:
            self.log_test("Daily Limit - Remaining Count", False, 
                         f"Remaining should be 0 after exhausting Basic tier, got {remaining_after}")
            return False
        
        # Check if error message is in Arabic
        has_arabic = any(ord(char) > 127 for char in message_after)
        
        self.log_test("Daily Limit - Basic Tier Exhaustion", True, 
                     f"Basic tier correctly exhausted: Can analyze={can_analyze_after}, "
                     f"Remaining={remaining_after}, Arabic message={has_arabic}")
        
        # Try to perform another analysis (should fail)
        success, response = self.make_request('POST', '/api/analyze', analysis_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("Daily Limit - Exceeded Limit", True, 
                         f"Correctly rejected analysis after limit exceeded. Arabic error: {has_arabic}")
        else:
            self.log_test("Daily Limit - Exceeded Limit", False, 
                         "Should reject analysis when daily limit is exceeded", response)
        
        return True

    def test_admin_subscription_update(self):
        """Test admin subscription update functionality - HIGH PRIORITY"""
        print("👑 Testing Admin Subscription Update...")
        
        if not self.test_users:
            self.log_test("Admin Subscription Update - Setup", False, "No test users available")
            return False
        
        test_user = self.test_users[0]
        user_id = test_user['user_id']
        
        # Update user to Premium tier
        update_data = {
            "user_id": user_id,
            "new_tier": "premium",
            "admin_id": "admin"
        }
        
        success, response = self.make_request('POST', '/api/admin/users/update-tier', update_data)
        
        if not success:
            self.log_test("Admin Subscription Update - Premium Upgrade", False, "Request failed", response)
            return False
        
        if not isinstance(response, dict):
            self.log_test("Admin Subscription Update - Premium Upgrade", False, "Invalid response format", response)
            return False
        
        if not response.get('success'):
            self.log_test("Admin Subscription Update - Premium Upgrade", False, 
                         f"Upgrade failed: {response.get('error')}", response)
            return False
        
        # Validate response structure
        data = response.get('data', {})
        required_fields = ['message', 'old_tier', 'new_tier', 'new_daily_limit']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("Admin Subscription Update - Response Structure", False, 
                         f"Missing fields: {missing_fields}", data)
            return False
        
        if data.get('old_tier') != 'basic' or data.get('new_tier') != 'premium':
            self.log_test("Admin Subscription Update - Tier Change", False, 
                         f"Tier change incorrect: {data.get('old_tier')} -> {data.get('new_tier')}")
            return False
        
        if data.get('new_daily_limit') != 5:
            self.log_test("Admin Subscription Update - Premium Limit", False, 
                         f"Premium tier should have 5 daily analyses, got {data.get('new_daily_limit')}")
            return False
        
        self.log_test("Admin Subscription Update - Premium Upgrade", True, 
                     f"Successfully upgraded to premium: {data.get('old_tier')} -> {data.get('new_tier')}, "
                     f"New limit: {data.get('new_daily_limit')}")
        
        # Verify the upgrade by checking user info
        success, response = self.make_request('GET', f'/api/auth/user/{user_id}')
        
        if success and response.get('success'):
            user_info = response.get('user', {})
            if user_info.get('tier') == 'premium':
                features = user_info.get('features', {})
                if features.get('daily_analyses') == 5:
                    self.log_test("Admin Subscription Update - Verification", True, 
                                 f"User tier successfully updated to premium with 5 daily analyses")
                else:
                    self.log_test("Admin Subscription Update - Verification", False, 
                                 f"Premium features not applied correctly: {features}")
            else:
                self.log_test("Admin Subscription Update - Verification", False, 
                             f"User tier not updated: {user_info.get('tier')}")
        else:
            self.log_test("Admin Subscription Update - Verification", False, 
                         "Could not verify tier update", response)
        
        # Test upgrade to VIP
        vip_update_data = {
            "user_id": user_id,
            "new_tier": "vip",
            "admin_id": "admin"
        }
        
        success, response = self.make_request('POST', '/api/admin/users/update-tier', vip_update_data)
        
        if success and response.get('success'):
            data = response.get('data', {})
            if data.get('new_tier') == 'vip' and data.get('new_daily_limit') == -1:
                self.log_test("Admin Subscription Update - VIP Upgrade", True, 
                             f"Successfully upgraded to VIP with unlimited analyses")
            else:
                self.log_test("Admin Subscription Update - VIP Upgrade", False, 
                             f"VIP upgrade data incorrect: {data}")
        else:
            self.log_test("Admin Subscription Update - VIP Upgrade", False, 
                         "VIP upgrade failed", response)
        
        # Test invalid tier
        invalid_update_data = {
            "user_id": user_id,
            "new_tier": "invalid_tier",
            "admin_id": "admin"
        }
        
        success, response = self.make_request('POST', '/api/admin/users/update-tier', invalid_update_data)
        
        if success and isinstance(response, dict) and not response.get('success'):
            error_msg = response.get('error', '')
            has_arabic = any(ord(char) > 127 for char in error_msg)
            self.log_test("Admin Subscription Update - Invalid Tier", True, 
                         f"Correctly rejected invalid tier. Arabic error: {has_arabic}")
        else:
            self.log_test("Admin Subscription Update - Invalid Tier", False, 
                         "Should reject invalid tier", response)
        
        return True

    def test_subscription_tiers(self):
        """Test different subscription tier behaviors - HIGH PRIORITY"""
        print("🎯 Testing Subscription Tiers...")
        
        # Create users for each tier
        tier_users = {}
        
        # Create Basic user (already have one)
        if self.test_users:
            tier_users['basic'] = self.test_users[0]
        
        # Create Premium user
        premium_user_data = self.generate_test_user_data()
        success, response = self.make_request('POST', '/api/auth/register', premium_user_data)
        
        if success and response.get('success'):
            user_info = response.get('user', {})
            premium_user = {
                "user_id": user_info['user_id'],
                "email": premium_user_data['email'],
                "password": premium_user_data['password'],
                "tier": "basic"  # Will upgrade to premium
            }
            
            # Upgrade to premium
            update_data = {
                "user_id": premium_user['user_id'],
                "new_tier": "premium",
                "admin_id": "admin"
            }
            
            success, response = self.make_request('POST', '/api/admin/users/update-tier', update_data)
            if success and response.get('success'):
                premium_user['tier'] = 'premium'
                tier_users['premium'] = premium_user
        
        # Create VIP user
        vip_user_data = self.generate_test_user_data()
        success, response = self.make_request('POST', '/api/auth/register', vip_user_data)
        
        if success and response.get('success'):
            user_info = response.get('user', {})
            vip_user = {
                "user_id": user_info['user_id'],
                "email": vip_user_data['email'],
                "password": vip_user_data['password'],
                "tier": "basic"  # Will upgrade to VIP
            }
            
            # Upgrade to VIP
            update_data = {
                "user_id": vip_user['user_id'],
                "new_tier": "vip",
                "admin_id": "admin"
            }
            
            success, response = self.make_request('POST', '/api/admin/users/update-tier', update_data)
            if success and response.get('success'):
                vip_user['tier'] = 'vip'
                tier_users['vip'] = vip_user
        
        # Test each tier's limits
        tier_limits = {
            'basic': 1,
            'premium': 5,
            'vip': -1  # Unlimited
        }
        
        all_passed = True
        
        for tier, expected_limit in tier_limits.items():
            if tier not in tier_users:
                self.log_test(f"Subscription Tiers - {tier.title()} Setup", False, 
                             f"Could not create {tier} user for testing")
                all_passed = False
                continue
            
            user = tier_users[tier]
            user_id = user['user_id']
            
            # Check permission
            success, response = self.make_request('GET', f'/api/auth/check-analysis-permission/{user_id}')
            
            if not success or not response.get('success'):
                self.log_test(f"Subscription Tiers - {tier.title()} Permission", False, 
                             "Permission check failed", response)
                all_passed = False
                continue
            
            remaining = response.get('remaining_analyses', 0)
            
            if expected_limit == -1:  # Unlimited
                if remaining != -1:
                    self.log_test(f"Subscription Tiers - {tier.title()} Limit", False, 
                                 f"VIP should have unlimited (-1), got {remaining}")
                    all_passed = False
                else:
                    self.log_test(f"Subscription Tiers - {tier.title()} Limit", True, 
                                 f"{tier.title()} tier has unlimited analyses")
            else:
                if remaining != expected_limit:
                    self.log_test(f"Subscription Tiers - {tier.title()} Limit", False, 
                                 f"{tier.title()} should have {expected_limit} analyses, got {remaining}")
                    all_passed = False
                else:
                    self.log_test(f"Subscription Tiers - {tier.title()} Limit", True, 
                                 f"{tier.title()} tier has {expected_limit} daily analyses")
        
        return all_passed

    def run_all_tests(self):
        """Run all authentication and subscription tests"""
        print("🧪 Starting Al Kabous AI Authentication & Subscription Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Authentication Tests (High Priority)
        self.test_user_registration()  # HIGH PRIORITY
        self.test_user_login()  # HIGH PRIORITY
        self.test_get_user_info()  # HIGH PRIORITY
        self.test_check_analysis_permission()  # HIGH PRIORITY
        
        # Analysis Integration Tests (High Priority)
        self.test_analysis_with_user_id()  # HIGH PRIORITY
        self.test_daily_limit_enforcement()  # HIGH PRIORITY
        
        # Admin & Subscription Tests (High Priority)
        self.test_admin_subscription_update()  # HIGH PRIORITY
        self.test_subscription_tiers()  # HIGH PRIORITY
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("=" * 60)
        print("📋 AUTHENTICATION & SUBSCRIPTION TEST SUMMARY")
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
            print("  ✅ All authentication and subscription tests passed!")
        else:
            print("  ⚠️ Some tests failed. Check the details above.")
            
        # Specific recommendations
        registration_passed = any('User Registration - Valid Data' in r['test'] and r['success'] for r in self.test_results)
        login_passed = any('User Login - Valid Credentials' in r['test'] and r['success'] for r in self.test_results)
        permission_passed = any('Check Analysis Permission - Valid User' in r['test'] and r['success'] for r in self.test_results)
        analysis_passed = any('Analysis with User ID - Valid Request' in r['test'] and r['success'] for r in self.test_results)
        limit_passed = any('Daily Limit - Basic Tier Exhaustion' in r['test'] and r['success'] for r in self.test_results)
        admin_passed = any('Admin Subscription Update - Premium Upgrade' in r['test'] and r['success'] for r in self.test_results)
        
        if not registration_passed:
            print("  👤 User registration issues - check auth_manager and database")
        
        if not login_passed:
            print("  🔐 User login issues - check password hashing and validation")
        
        if not permission_passed:
            print("  🔍 Permission checking issues - check user tier and daily limits")
        
        if not analysis_passed:
            print("  🧠 Analysis with user_id issues - check analysis endpoint integration")
        
        if not limit_passed:
            print("  📊 Daily limit enforcement issues - check tier limits and counting")
        
        if not admin_passed:
            print("  👑 Admin subscription updates issues - check admin endpoints and auth_manager")
        
        print(f"\n📊 Test users created: {len(self.test_users)}")
        for i, user in enumerate(self.test_users):
            print(f"  {i+1}. ID: {user['user_id']}, Email: {user['email']}, Tier: {user.get('tier', 'basic')}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = AlKabousAuthTester()
    
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