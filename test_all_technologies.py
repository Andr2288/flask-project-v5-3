#!/usr/bin/env python3
"""
Test script to verify all technologies are working correctly
Updated to include Flask-Admin testing
"""

import requests
import json
import asyncio
import aiohttp
import time
import sys


class TechnologyTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.async_url = "http://localhost:8080"
        self.results = {}

    def print_header(self, title):
        print(f"\n{'=' * 60}")
        print(f"TESTING: {title}")
        print(f"{'=' * 60}")

    def print_result(self, test_name, success, message=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        self.results[test_name] = success

    def test_flask_basic(self):
        """Test basic Flask functionality"""
        self.print_header("FLASK BASIC")

        try:
            response = requests.get(f"{self.base_url}/")
            self.print_result("Flask Home Page", response.status_code == 200)

            response = requests.get(f"{self.base_url}/posts")
            self.print_result("Flask Posts Page", response.status_code == 200)

            response = requests.get(f"{self.base_url}/map")
            self.print_result("Folium Map Integration", response.status_code == 200)

            response = requests.get(f"{self.base_url}/websocket")
            self.print_result("Flask-SocketIO Test Page", response.status_code == 200)

        except Exception as e:
            self.print_result("Flask Basic", False, str(e))

    def test_flask_admin(self):
        """Test Flask-Admin functionality"""
        self.print_header("FLASK-ADMIN")

        try:
            # Test admin panel redirect (should redirect to login for non-authenticated users)
            response = requests.get(f"{self.base_url}/admin", allow_redirects=False)
            self.print_result("Admin Panel Access Control",
                              response.status_code in [302, 403],
                              "Correctly redirects unauthenticated users")

            # Test admin routes existence
            admin_routes = [
                "/admin/user/",
                "/admin/post/",
                "/admin/comment/"
            ]

            for route in admin_routes:
                response = requests.get(f"{self.base_url}{route}", allow_redirects=False)
                route_name = route.replace("/admin/", "").replace("/", "").title()
                self.print_result(f"Admin {route_name} Route",
                                  response.status_code in [302, 403],
                                  f"Route exists and protected")

        except Exception as e:
            self.print_result("Flask-Admin", False, str(e))

    def test_admin_with_auth(self):
        """Test Flask-Admin with authentication"""
        self.print_header("FLASK-ADMIN WITH AUTH")

        try:
            # Create a session to maintain cookies
            session = requests.Session()

            # Login as admin
            login_data = {
                'username': 'admin',
                'password': '123456',
                'csrf_token': self.get_csrf_token(session)
            }

            # Get login page first to get CSRF token
            login_page = session.get(f"{self.base_url}/login")
            if login_page.status_code == 200:
                # Try to extract CSRF token from the page
                # This is a simplified approach - in real testing you'd parse the HTML
                login_response = session.post(f"{self.base_url}/login",
                                              data={'username': 'admin', 'password': '123456'},
                                              allow_redirects=False)

                if login_response.status_code == 302:  # Redirect after successful login
                    self.print_result("Admin Login", True, "Successfully logged in")

                    # Test admin dashboard access
                    admin_response = session.get(f"{self.base_url}/admin")
                    self.print_result("Admin Dashboard Access",
                                      admin_response.status_code == 200,
                                      "Can access admin dashboard")

                    # Test admin model views
                    user_admin = session.get(f"{self.base_url}/admin/user/")
                    self.print_result("Admin User Management",
                                      user_admin.status_code == 200,
                                      "Can access user management")

                    post_admin = session.get(f"{self.base_url}/admin/post/")
                    self.print_result("Admin Post Management",
                                      post_admin.status_code == 200,
                                      "Can access post management")

                else:
                    self.print_result("Admin Login", False, "Login failed")
            else:
                self.print_result("Admin Login Page", False, "Cannot access login page")

        except Exception as e:
            self.print_result("Admin Authentication", False, str(e))

    def get_csrf_token(self, session):
        """Helper to get CSRF token (simplified)"""
        try:
            response = session.get(f"{self.base_url}/login")
            # In a real implementation, you'd parse the HTML to extract the CSRF token
            return "dummy_token"  # Placeholder
        except:
            return "dummy_token"

    def test_restful_api(self):
        """Test Flask-RESTful API"""
        self.print_header("FLASK-RESTFUL API")

        try:
            # Test GET users
            response = requests.get(f"{self.base_url}/api/users")
            self.print_result("RESTful - Get Users", response.status_code == 200)

            # Test GET posts
            response = requests.get(f"{self.base_url}/api/posts")
            self.print_result("RESTful - Get Posts", response.status_code == 200)

            # Test technology overview
            response = requests.get(f"{self.base_url}/api/test/technologies")
            if response.status_code == 200:
                data = response.json()
                technologies = data.get('technologies', {})
                endpoints = data.get('endpoints', {})

                # Check if Flask-Admin is mentioned
                admin_mentioned = 'Flask-Admin' in technologies
                admin_endpoints = 'Admin Panel (Flask-Admin)' in endpoints

                self.print_result("RESTful - Technology Overview", True,
                                  f"Found {len(technologies)} technologies")
                self.print_result("RESTful - Admin Integration",
                                  admin_mentioned and admin_endpoints,
                                  "Flask-Admin properly integrated")
            else:
                self.print_result("RESTful - Technology Overview", False)

        except Exception as e:
            self.print_result("RESTful API", False, str(e))

    async def test_async_service(self):
        """Test aiohttp async service"""
        self.print_header("AIOHTTP ASYNC SERVICE")

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test health check
                try:
                    async with session.get(f"{self.async_url}/async/health") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.print_result("Async - Health Check", True,
                                              f"Status: {data.get('status')}")
                        else:
                            self.print_result("Async - Health Check", False,
                                              f"Status: {resp.status}")
                except Exception as e:
                    self.print_result("Async - Health Check", False,
                                      f"Connection failed: {str(e)}")

                # Test async posts
                try:
                    async with session.get(f"{self.async_url}/async/posts") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.print_result("Async - Posts Endpoint", True,
                                              f"Got {data.get('total', 0)} posts")
                        else:
                            self.print_result("Async - Posts Endpoint", False,
                                              f"Status: {resp.status}")
                except Exception as e:
                    self.print_result("Async - Posts Endpoint", False,
                                      f"Connection failed: {str(e)}")

        except Exception as e:
            self.print_result("Async Service", False, f"Service unavailable: {str(e)}")

    def test_flask_socketio(self):
        """Test Flask-SocketIO functionality"""
        self.print_header("FLASK-SOCKETIO")

        try:
            import socketio

            sio = socketio.SimpleClient()

            try:
                sio.connect(f"{self.base_url}")
                self.print_result("Flask-SocketIO - Connection", True, "Connected successfully")

                # Test ping
                sio.emit('ping')
                event = sio.receive(timeout=5)
                if event[0] == 'pong':
                    self.print_result("Flask-SocketIO - Ping/Pong", True, "Pong received")
                else:
                    self.print_result("Flask-SocketIO - Ping/Pong", False, f"Unexpected event: {event[0]}")

                sio.disconnect()

            except Exception as e:
                self.print_result("Flask-SocketIO - Connection", False, f"Connection failed: {str(e)}")

        except ImportError:
            self.print_result("Flask-SocketIO", False, "python-socketio library not installed")
        except Exception as e:
            self.print_result("Flask-SocketIO", False, str(e))

    def test_jwt_authentication(self):
        """Test JWT authentication"""
        self.print_header("JWT AUTHENTICATION")

        try:
            login_data = {
                "username": "admin",
                "password": "123456"
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(f"{self.base_url}/api/auth/login",
                                     json=login_data,
                                     headers=headers)

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')

                if token:
                    self.print_result("JWT - Login", True, "Token received")

                    # Test protected endpoint
                    auth_headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    protected_response = requests.post(f"{self.base_url}/api/posts",
                                                       headers=auth_headers,
                                                       json={
                                                           "title": "Test JWT Post",
                                                           "content": "Testing JWT authentication"
                                                       })

                    self.print_result("JWT - Protected Endpoint",
                                      protected_response.status_code == 201,
                                      f"Status: {protected_response.status_code}")
                else:
                    self.print_result("JWT - Login", False, "No token in response")
            else:
                self.print_result("JWT - Login", False,
                                  f"Status: {response.status_code}")

        except Exception as e:
            self.print_result("JWT Authentication", False, str(e))

    def test_database_technologies(self):
        """Test database-related technologies"""
        self.print_header("DATABASE TECHNOLOGIES")

        try:
            # Test SQLAlchemy through API
            response = requests.get(f"{self.base_url}/api/users")
            if response.status_code == 200:
                users = response.json()
                self.print_result("SQLAlchemy - Data Access", True,
                                  f"Found {len(users)} users")
            else:
                self.print_result("SQLAlchemy - Data Access", False)

            # Test migrations (check if tables exist)
            response = requests.get(f"{self.base_url}/api/posts")
            self.print_result("Flask-Migrate", response.status_code == 200)

        except Exception as e:
            self.print_result("Database Technologies", False, str(e))

    def run_all_tests(self):
        """Run all technology tests"""
        print("FLASK CRUD APP - COMPLETE TECHNOLOGY VERIFICATION")
        print("Testing all essential technologies including Flask-Admin...")

        # Wait for services to be ready
        print("\nWaiting for services to be ready...")
        time.sleep(3)

        # Run all tests
        self.test_flask_basic()
        self.test_flask_admin()
        self.test_admin_with_auth()
        self.test_restful_api()

        # Run async tests
        asyncio.run(self.test_async_service())

        self.test_flask_socketio()
        self.test_jwt_authentication()
        self.test_database_technologies()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for test_name, result in self.results.items():
                if not result:
                    print(f"  ❌ {test_name}")

        print(f"\n{'=' * 60}")
        if failed_tests == 0:
            print("🎉 ALL TECHNOLOGIES WORKING CORRECTLY!")
            print("✓ Flask-Admin successfully integrated!")
        elif failed_tests <= 2:
            print("😊 MOST TECHNOLOGIES WORKING CORRECTLY!")
        else:
            print(f"⚠️  {failed_tests} TECHNOLOGIES NEED ATTENTION")
        print(f"{'=' * 60}")


def main():
    """Main function"""
    tester = TechnologyTester()

    # Check if services are running
    try:
        requests.get("http://localhost:5000/", timeout=5)
    except:
        print("❌ Flask app not running on localhost:5000")
        print("Please start the main application first: python main.py")
        sys.exit(1)

    tester.run_all_tests()


if __name__ == "__main__":
    main()