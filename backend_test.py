import requests
import sys
import json
from datetime import datetime
import time

class AILearningPlatformTester:
    def __init__(self, base_url="https://genaiforyouth.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"Status: {response.status_code}, Response: {json.dumps(response_data, indent=2)[:200]}..."
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}..."
            else:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}..."

            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            details = f"Request timed out after {timeout} seconds"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"Error: {str(e)}"
            self.log_test(name, False, details)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_get_models(self):
        """Test getting available AI models"""
        success, response = self.run_test(
            "Get Available Models",
            "GET", 
            "models",
            200
        )
        
        if success and 'models' in response:
            models = response['models']
            expected_models = ['gpt-5', 'claude-4-sonnet-20250514', 'gemini-2.5-pro']
            found_models = [model['name'] for model in models]
            
            all_models_present = all(model in found_models for model in expected_models)
            if all_models_present:
                self.log_test("All Expected Models Present", True, f"Found models: {found_models}")
            else:
                missing = [m for m in expected_models if m not in found_models]
                self.log_test("All Expected Models Present", False, f"Missing models: {missing}")
        
        return success, response

    def test_create_session(self):
        """Test creating a new chat session"""
        session_data = {
            "session_name": f"Test Session - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        success, response = self.run_test(
            "Create Chat Session",
            "POST",
            "chat/session",
            200,
            data=session_data
        )
        
        if success and 'id' in response:
            self.session_id = response['id']
            self.log_test("Session ID Retrieved", True, f"Session ID: {self.session_id}")
        else:
            self.log_test("Session ID Retrieved", False, "No session ID in response")
        
        return success, response

    def test_send_message(self, message, model_provider="openai", model_name="gpt-5"):
        """Test sending a chat message"""
        if not self.session_id:
            self.log_test("Send Message - No Session", False, "No session ID available")
            return False, {}
        
        message_data = {
            "session_id": self.session_id,
            "message": message,
            "model_provider": model_provider,
            "model_name": model_name
        }
        
        success, response = self.run_test(
            f"Send Message ({model_provider}/{model_name})",
            "POST",
            "chat/message",
            200,
            data=message_data,
            timeout=60  # Longer timeout for LLM responses
        )
        
        if success:
            # Check if response has expected fields
            expected_fields = ['id', 'session_id', 'message', 'response', 'model_provider', 'model_name', 'is_safe']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                self.log_test("Message Response Structure", True, f"All fields present")
                
                # Check if response is kid-friendly
                if response.get('is_safe', False):
                    self.log_test("Safety Check", True, "Content marked as safe")
                else:
                    self.log_test("Safety Check", False, "Content marked as unsafe")
                    
            else:
                self.log_test("Message Response Structure", False, f"Missing fields: {missing_fields}")
        
        return success, response

    def test_get_messages(self):
        """Test retrieving chat messages for a session"""
        if not self.session_id:
            self.log_test("Get Messages - No Session", False, "No session ID available")
            return False, {}
        
        return self.run_test(
            "Get Chat Messages",
            "GET",
            f"chat/messages/{self.session_id}",
            200
        )

    def test_get_sessions(self):
        """Test retrieving all chat sessions"""
        return self.run_test(
            "Get Chat Sessions",
            "GET",
            "chat/sessions",
            200
        )

    def test_safety_filtering(self):
        """Test safety filtering with inappropriate content"""
        if not self.session_id:
            # Create a session first
            self.test_create_session()
        
        # Test with potentially unsafe content
        unsafe_message = "Tell me about violence and weapons"
        
        success, response = self.test_send_message(unsafe_message)
        
        if success:
            # Check if safety filtering worked
            response_text = response.get('response', '').lower()
            if 'fun' in response_text or 'games' in response_text or 'robots' in response_text:
                self.log_test("Safety Filtering Active", True, "Unsafe content was filtered and redirected")
            else:
                self.log_test("Safety Filtering Active", False, f"Response may contain unsafe content: {response_text[:100]}...")

    def test_kid_friendly_language(self):
        """Test kid-friendly language simplification"""
        if not self.session_id:
            self.test_create_session()
        
        # Test with complex AI terminology
        complex_message = "Explain artificial intelligence and machine learning algorithms"
        
        success, response = self.test_send_message(complex_message)
        
        if success:
            response_text = response.get('response', '').lower()
            # Check for simplified language
            kid_friendly_terms = ['smart computer', 'computer brain', 'how computers learn', 'computer instructions']
            
            if any(term in response_text for term in kid_friendly_terms):
                self.log_test("Kid-Friendly Language", True, "Complex terms were simplified")
            else:
                self.log_test("Kid-Friendly Language", False, f"Response may be too complex: {response_text[:100]}...")

    def test_multiple_models(self):
        """Test different AI models"""
        if not self.session_id:
            self.test_create_session()
        
        models_to_test = [
            ("openai", "gpt-5"),
            ("anthropic", "claude-4-sonnet-20250514"),
            ("gemini", "gemini-2.5-pro")
        ]
        
        test_message = "What is AI?"
        
        for provider, model in models_to_test:
            success, response = self.test_send_message(test_message, provider, model)
            if success:
                self.log_test(f"Model {provider}/{model} Working", True, "Model responded successfully")
            else:
                self.log_test(f"Model {provider}/{model} Working", False, "Model failed to respond")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting AI Learning Platform Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        self.test_root_endpoint()
        self.test_get_models()
        
        # Session management tests
        self.test_create_session()
        self.test_get_sessions()
        
        # Basic messaging test
        self.test_send_message("Hello! What is AI?")
        self.test_get_messages()
        
        # Safety and kid-friendly tests
        self.test_safety_filtering()
        self.test_kid_friendly_language()
        
        # Multiple model tests
        self.test_multiple_models()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            return 1

def main():
    tester = AILearningPlatformTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())