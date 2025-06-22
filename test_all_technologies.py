#!/usr/bin/env python3
"""
Test script to verify all technologies are working correctly
"""

import requests
import json
import asyncio
import aiohttp
import websockets
from zeep import Client
import time
import sys


class TechnologyTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.async_url = "http://localhost:8080"
        self.soap_url = "http://localhost:5000/soap"
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

        except Exception as e:
            self.print_result("Flask Basic", False, str(e))

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
                self.print_result("RESTful - Technology Overview", True,
                                  f"Found {len(data.get('technologies', {}))} technologies")
            else:
                self.print_result("RESTful - Technology Overview", False)

        except Exception as e:
            self.print_result("RESTful API", False, str(e))

    def test_potion_api(self):
        """Test Flask-Potion API"""
        self.print_header("FLASK-POTION API")

        try:
            # Test Potion users endpoint
            response = requests.get(f"{self.base_url}/users")
            self.print_result("Potion - Users Endpoint", response.status_code == 200)

            # Test Potion posts endpoint
            response = requests.get(f"{self.base_url}/posts")
            self.print_result("Potion - Posts Endpoint", response.status_code == 200)

            # Test search functionality
            response = requests.get(f"{self.base_url}/search/posts?q=Flask")
            self.print_result("Potion - Search Posts", response.status_code == 200)

            # Test statistics
            response = requests.get(f"{self.base_url}/stats/overview")
            self.print_result("Potion - Statistics", response.status_code == 200)

        except Exception as e:
            self.print_result("Potion API", False, str(e))

    def test_soap_service(self):
        """Test SOAP service"""
        self.print_header("SOAP SERVICE")

        try:
            # Test WSDL
            response = requests.get(f"{self.soap_url}?wsdl")
            self.print_result("SOAP - WSDL Available", response.status_code == 200)

            # Test SOAP client
            try:
                client = Client(f"{self.soap_url}?wsdl")

                # Test authentication
                result = client.service.authenticate_user('admin', '123456')
                self.print_result("SOAP - Authentication",
                                  "successful" in result.lower())

                # Test get all users
                users = client.service.get_all_users()
                self.print_result("SOAP - Get All Users",
                                  len(users) > 0 if users else False)

                # Test get statistics
                stats = client.service.get_statistics()
                self.print_result("SOAP - Get Statistics",
                                  "Statistics" in stats if stats else False)

            except Exception as soap_e:
                self.print_result("SOAP - Client Operations", False, str(soap_e))

        except Exception as e:
            self.print_result("SOAP Service", False, str(e))

    async def test_async_service(self):
        """Test aiohttp async service"""
        self.print_header("AIOHTTP ASYNC SERVICE")

        try:
            async with aiohttp.ClientSession() as session:
                # Test health check
                async with session.get(f"{self.async_url}/async/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.print_result("Async - Health Check", True,
                                          f"Status: {data.get('status')}")
                    else:
                        self.print_result("Async - Health Check", False)

                # Test async posts
                async with session.get(f"{self.async_url}/async/posts") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.print_result("Async - Posts Endpoint", True,
                                          f"Got {data.get('total', 0)} posts")
                    else:
                        self.print_result("Async - Posts Endpoint", False)

                # Test analytics
                async with session.get(f"{self.async_url}/async/analytics") as resp:
                    self.print_result("Async - Analytics", resp.status == 200)

                # Test batch processing
                test_data = {"items": ["test1", "test2", "test3"]}
                async with session.post(f"{self.async_url}/async/batch",
                                        json=test_data) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.print_result("Async - Batch Processing", True,
                                          f"Processed {data.get('total_processed', 0)} items")
                    else:
                        self.print_result("Async - Batch Processing", False)

        except Exception as e:
            self.print_result("Async Service", False, str(e))

    def test_websocket(self):
        """Test WebSocket functionality"""
        self.print_header("WEBSOCKET")

        try:
            import websockets

            async def test_ws():
                try:
                    uri = f"ws://localhost:8080/async/ws"
                    async with websockets.connect(uri) as websocket:
                        # Send test message
                        test_msg = {"message": "test", "type": "ping"}
                        await websocket.send(json.dumps(test_msg))

                        # Receive response
                        response = await websocket.recv()
                        data = json.loads(response)

                        return data.get('type') == 'echo'

                except Exception as e:
                    return False

            # Run WebSocket test
            result = asyncio.run(test_ws())
            self.print_result("WebSocket - Echo Test", result)

        except ImportError:
            self.print_result("WebSocket", False, "websockets library not installed")
        except Exception as e:
            self.print_result("WebSocket", False, str(e))

    def test_jwt_authentication(self):
        """Test JWT authentication"""
        self.print_header("JWT AUTHENTICATION")

        try:
            # Test login
            login_data = {
                "username": "admin",
                "password": "123456"
            }

            response = requests.post(f"{self.base_url}/api/auth/login",
                                     json=login_data)

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')

                if token:
                    self.print_result("JWT - Login", True, "Token received")

                    # Test protected endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    protected_response = requests.post(f"{self.base_url}/api/posts",
                                                       headers=headers,
                                                       json={
                                                           "title": "Test JWT Post",
                                                           "content": "Testing JWT authentication"
                                                       })

                    self.print_result("JWT - Protected Endpoint",
                                      protected_response.status_code == 201)
                else:
                    self.print_result("JWT - Login", False, "No token received")
            else:
                self.print_result("JWT - Login", False, f"Status: {response.status_code}")

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
            # This is indirect - if we can fetch data, migrations worked
            response = requests.get(f"{self.base_url}/api/posts")
            self.print_result("Flask-Migrate", response.status_code == 200)

        except Exception as e:
            self.print_result("Database Technologies", False, str(e))

    def run_all_tests(self):
        """Run all technology tests"""
        print("FLASK CRUD APP - TECHNOLOGY VERIFICATION")
        print("Testing all required technologies for MVP...")

        # Wait for services to be ready
        print("\nWaiting for services to be ready...")
        time.sleep(2)

        # Run all tests
        self.test_flask_basic()
        self.test_restful_api()
        self.test_potion_api()
        self.test_soap_service()

        # Run async tests
        asyncio.run(self.test_async_service())

        self.test_websocket()
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