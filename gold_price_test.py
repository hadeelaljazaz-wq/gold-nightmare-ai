#!/usr/bin/env python3
"""
Simple Gold Price System Test
"""
import subprocess
import json
import time

def run_curl_test(endpoint, description):
    """Run curl test and parse JSON response"""
    print(f"\n🔍 Testing {description}...")
    
    try:
        # Run curl command
        result = subprocess.run([
            'curl', '-s', '-w', '\\n%{http_code}',
            f'http://localhost:8001{endpoint}'
        ], capture_output=True, text=True, timeout=10)
        
        # Split response and status code
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            response_text = '\n'.join(lines[:-1])
            status_code = lines[-1]
        else:
            response_text = result.stdout.strip()
            status_code = "unknown"
        
        print(f"Status Code: {status_code}")
        
        if status_code == "200":
            try:
                # Try to parse JSON
                data = json.loads(response_text)
                return True, data
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response_text[:100]}...")
                return False, response_text
        else:
            print(f"❌ HTTP Error {status_code}: {response_text[:100]}...")
            return False, {"error": f"HTTP {status_code}", "response": response_text}
            
    except subprocess.TimeoutExpired:
        print("❌ Request timeout")
        return False, {"error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, {"error": str(e)}

def test_gold_price_system():
    """Test the gold price system comprehensively"""
    print("🏆 GOLD PRICE SYSTEM COMPREHENSIVE TEST")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    tests_total += 1
    success, data = run_curl_test("/api/health", "Health Endpoint")
    if success and data.get("status") == "healthy":
        print("✅ Health check passed")
        tests_passed += 1
    else:
        print("❌ Health check failed")
    
    # Test 2: Gold Price API
    tests_total += 1
    success, data = run_curl_test("/api/gold-price", "Gold Price API")
    if success and data.get("success"):
        price_data = data.get("price_data", {})
        price_usd = price_data.get("price_usd", 0)
        source = price_data.get("source", "unknown")
        formatted_text = data.get("formatted_text", "")
        
        print(f"✅ Gold Price API working:")
        print(f"   💰 Price: ${price_usd:.2f}")
        print(f"   📡 Source: {source}")
        print(f"   📝 Arabic text: {'Yes' if any(ord(c) > 127 for c in formatted_text) else 'No'}")
        
        # Validate price range
        if 1000 <= price_usd <= 5000:
            print(f"   ✅ Price in reasonable range")
            tests_passed += 1
        else:
            print(f"   ❌ Price outside reasonable range: ${price_usd}")
    else:
        print("❌ Gold Price API failed")
    
    # Test 3: Cache System (multiple requests)
    tests_total += 1
    print(f"\n🔍 Testing Cache System (15-minute cache)...")
    
    # First request
    start_time = time.time()
    success1, data1 = run_curl_test("/api/gold-price", "First Request")
    end_time1 = time.time()
    
    if success1 and data1.get("success"):
        price1 = data1.get("price_data", {}).get("price_usd", 0)
        response_time1 = (end_time1 - start_time) * 1000
        
        # Second request immediately
        start_time = time.time()
        success2, data2 = run_curl_test("/api/gold-price", "Second Request (Cache)")
        end_time2 = time.time()
        
        if success2 and data2.get("success"):
            price2 = data2.get("price_data", {}).get("price_usd", 0)
            response_time2 = (end_time2 - start_time) * 1000
            
            if price1 == price2:
                print(f"✅ Cache system working:")
                print(f"   ⏱️ First request: {response_time1:.0f}ms")
                print(f"   ⏱️ Second request: {response_time2:.0f}ms")
                print(f"   💰 Same price: ${price1:.2f}")
                tests_passed += 1
            else:
                print(f"❌ Cache system may not be working (different prices)")
        else:
            print("❌ Second request failed")
    else:
        print("❌ First request failed")
    
    # Test 4: API Status
    tests_total += 1
    success, data = run_curl_test("/api/api-status", "API Status")
    if success and data.get("success"):
        status_info = data.get("status", {})
        gold_apis = status_info.get("gold_apis", {})
        claude_ai = status_info.get("claude_ai", {})
        
        print(f"✅ API Status working:")
        print(f"   🏆 Gold APIs: {len(gold_apis) if isinstance(gold_apis, dict) else 'available'}")
        print(f"   🤖 Claude AI: {'available' if claude_ai else 'not available'}")
        tests_passed += 1
    else:
        print("❌ API Status failed")
    
    # Test 5: Analysis Types
    tests_total += 1
    success, data = run_curl_test("/api/analysis-types", "Analysis Types")
    if success and isinstance(data, dict) and "types" in data:
        types = data["types"]
        type_ids = [t.get("id") for t in types if isinstance(t, dict)]
        expected_types = ["quick", "detailed", "chart", "news", "forecast"]
        
        if all(t in type_ids for t in expected_types):
            print(f"✅ Analysis Types working: {type_ids}")
            tests_passed += 1
        else:
            print(f"❌ Missing analysis types: {set(expected_types) - set(type_ids)}")
    else:
        print("❌ Analysis Types failed")
    
    # Test 6: Admin Login
    tests_total += 1
    print(f"\n🔍 Testing Admin Login...")
    
    try:
        # Create JSON payload for admin login
        login_data = '{"username": "admin", "password": "GOLD_NIGHTMARE_205"}'
        
        result = subprocess.run([
            'curl', '-s', '-w', '\\n%{http_code}',
            '-H', 'Content-Type: application/json',
            '-d', login_data,
            'http://localhost:8001/api/admin/login'
        ], capture_output=True, text=True, timeout=10)
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            response_text = '\n'.join(lines[:-1])
            status_code = lines[-1]
            
            if status_code == "200":
                data = json.loads(response_text)
                if data.get("success") and data.get("token"):
                    print(f"✅ Admin Login working: {data.get('token')[:20]}...")
                    tests_passed += 1
                else:
                    print(f"❌ Admin Login failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Admin Login HTTP error: {status_code}")
        else:
            print("❌ Admin Login request failed")
            
    except Exception as e:
        print(f"❌ Admin Login error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 GOLD PRICE SYSTEM TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🏆 ALL TESTS PASSED - Gold Price System is fully functional!")
        return True
    elif tests_passed >= tests_total * 0.8:
        print("✅ MOSTLY WORKING - Gold Price System is functional with minor issues")
        return True
    else:
        print("❌ SIGNIFICANT ISSUES - Gold Price System needs attention")
        return False

if __name__ == "__main__":
    test_gold_price_system()