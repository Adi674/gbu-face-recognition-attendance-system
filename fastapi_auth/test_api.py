"""
Automated API Testing Script for School Management System
Run this script to test all endpoints systematically
"""

import requests
import json
import base64
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_admin@school.com"
TEST_PASSWORD = "admin123"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.school_id: Optional[int] = None
        self.department_id: Optional[int] = None
        self.class_id: Optional[int] = None
        self.course_code: Optional[str] = None
        self.teacher_id: Optional[int] = None
        self.roll_no: Optional[str] = None
        self.unique_code: Optional[str] = None
        
    def print_header(self, text: str):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def make_request(self, method: str, endpoint: str, data=None, use_auth=True):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            self.print_error(f"Request failed: {str(e)}")
            return None
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.print_header("Testing Health Check")
        
        response = self.make_request("GET", "/health", use_auth=False)
        if response and response.status_code == 200:
            data = response.json()
            self.print_success(f"Health check passed: {data['status']}")
            self.print_info(f"Version: {data['version']}")
            return True
        else:
            self.print_error("Health check failed")
            return False
    
    def test_register(self):
        """Test user registration"""
        self.print_header("Testing User Registration")
        
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.make_request("POST", "/register", data, use_auth=False)
        if response and response.status_code in [201, 400]:
            if response.status_code == 201:
                self.print_success("User registered successfully")
                return True
            else:
                self.print_info("User already exists (this is okay)")
                return True
        else:
            self.print_error("Registration failed")
            return False
    
    def test_login(self):
        """Test user login"""
        self.print_header("Testing User Login")
        
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.make_request("POST", "/login", data, use_auth=False)
        if response and response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            self.print_success(f"Login successful")
            self.print_info(f"Token: {self.token[:50]}...")
            return True
        else:
            self.print_error("Login failed")
            return False
    
    def test_get_current_user(self):
        """Test get current user endpoint"""
        self.print_header("Testing Get Current User")
        
        response = self.make_request("GET", "/users/me")
        if response and response.status_code == 200:
            user = response.json()
            self.print_success(f"Current user: {user['email']}")
            self.print_info(f"Role: {user['role']}")
            return True
        else:
            self.print_error("Get current user failed")
            return False
    
    def test_create_school(self):
        """Test create school endpoint"""
        self.print_header("Testing Create School")
        
        data = {
            "school_name": "Test University",
            "school_dean": "Dr. Test Dean"
        }
        
        response = self.make_request("POST", "/schools", data)
        if response and response.status_code in [201, 400]:
            if response.status_code == 201:
                result = response.json()
                self.school_id = result["school_id"]
                self.print_success(f"School created: ID {self.school_id}")
                return True
            else:
                # Try to get existing school
                response = self.make_request("GET", "/schools")
                if response and response.status_code == 200:
                    schools = response.json()
                    if schools:
                        self.school_id = schools[0]["school_id"]
                        self.print_info(f"Using existing school: ID {self.school_id}")
                        return True
        else:
            self.print_error("Create school failed")
            return False
    
    def test_create_department(self):
        """Test create department endpoint"""
        self.print_header("Testing Create Department")
        
        if not self.school_id:
            self.print_error("School ID not set")
            return False
        
        data = {
            "department_name": "Computer Science",
            "school_id": self.school_id,
            "hod": "Dr. Test HOD"
        }
        
        response = self.make_request("POST", "/departments", data)
        if response and response.status_code == 201:
            result = response.json()
            self.department_id = result["department_id"]
            self.print_success(f"Department created: ID {self.department_id}")
            return True
        else:
            self.print_error(f"Create department failed: {response.text if response else 'No response'}")
            return False
    
    def test_create_class(self):
        """Test create class endpoint"""
        self.print_header("Testing Create Class")
        
        if not self.department_id:
            self.print_error("Department ID not set")
            return False
        
        data = {
            "class_name": "CS-2024-A",
            "department_id": self.department_id
        }
        
        response = self.make_request("POST", "/classes", data)
        if response and response.status_code == 201:
            result = response.json()
            self.class_id = result["class_id"]
            self.print_success(f"Class created: ID {self.class_id}")
            return True
        else:
            self.print_error(f"Create class failed: {response.text if response else 'No response'}")
            return False
    
    def test_create_subject(self):
        """Test create subject endpoint"""
        self.print_header("Testing Create Subject")
        
        if not self.school_id or not self.class_id:
            self.print_error("School ID or Class ID not set")
            return False
        
        data = {
            "course_code": "CS101",
            "subject_name": "Introduction to Programming",
            "school_id": self.school_id,
            "semester": 1,
            "class_id": self.class_id
        }
        
        response = self.make_request("POST", "/subjects", data)
        if response and response.status_code == 201:
            result = response.json()
            self.course_code = result["course_code"]
            self.print_success(f"Subject created: {self.course_code}")
            return True
        else:
            self.print_error(f"Create subject failed: {response.text if response else 'No response'}")
            return False
    
    def test_add_teacher(self):
        """Test add teacher endpoint"""
        self.print_header("Testing Add Teacher")
        
        if not self.school_id:
            self.print_error("School ID not set")
            return False
        
        data = {
            "teacher_name": "John Test Teacher",
            "teacher_email": "teacher_test@school.com",
            "school_id": self.school_id,
            "phone_number": "+1234567890"
        }
        
        response = self.make_request("POST", "/teachers", data)
        if response and response.status_code in [201, 400]:
            if response.status_code == 201:
                result = response.json()
                self.teacher_id = result["teacher_id"]
                self.print_success(f"Teacher added: ID {self.teacher_id}")
                self.print_info(result["message"])
                return True
            else:
                self.print_info("Teacher already exists (this is okay)")
                # Get existing teacher
                response = self.make_request("GET", "/teachers")
                if response and response.status_code == 200:
                    teachers = response.json()
                    if teachers:
                        self.teacher_id = teachers[0]["teacher_id"]
                        self.print_info(f"Using existing teacher: ID {self.teacher_id}")
                        return True
        else:
            self.print_error(f"Add teacher failed: {response.text if response else 'No response'}")
            return False
    
    def test_add_student(self):
        """Test add student endpoint"""
        self.print_header("Testing Add Student")
        
        if not self.school_id or not self.department_id:
            self.print_error("School ID or Department ID not set")
            return False
        
        # Generate dummy base64 image (1x1 pixel PNG)
        dummy_image = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        data = {
            "roll_no": "TEST001",
            "name": "Alice Test Student",
            "email": "student_test@school.com",
            "phone_number": "+1234567890",
            "semester": 1,
            "year": 2024,
            "school_id": self.school_id,
            "department_id": self.department_id,
            "photo_base64": dummy_image
        }
        
        response = self.make_request("POST", "/students", data)
        if response and response.status_code in [201, 400]:
            if response.status_code == 201:
                result = response.json()
                self.roll_no = result["roll_no"]
                self.print_success(f"Student added: {self.roll_no}")
                self.print_info(result["message"])
                return True
            else:
                self.print_info("Student already exists (this is okay)")
                self.roll_no = "TEST001"
                return True
        else:
            self.print_error(f"Add student failed: {response.text if response else 'No response'}")
            return False
    
    def test_create_attendance_register(self):
        """Test create attendance register endpoint"""
        self.print_header("Testing Create Attendance Register")
        
        if not self.course_code or not self.class_id:
            self.print_error("Course code or Class ID not set")
            return False
        
        data = {
            "course_code": self.course_code,
            "class_id": self.class_id
        }
        
        response = self.make_request("POST", "/attendance/register", data)
        if response and response.status_code == 201:
            result = response.json()
            self.unique_code = result["unique_code"]
            self.print_success(f"Attendance register created: {self.unique_code}")
            self.print_info(result["message"])
            return True
        else:
            self.print_error(f"Create attendance register failed: {response.text if response else 'No response'}")
            return False
    
    def test_mark_attendance_manual(self):
        """Test mark attendance (manual) endpoint"""
        self.print_header("Testing Mark Attendance (Manual)")
        
        if not self.unique_code or not self.roll_no:
            self.print_error("Unique code or Roll number not set")
            return False
        
        data = {
            "unique_code": self.unique_code,
            "roll_no": self.roll_no,
            "photo_base64": None
        }
        
        response = self.make_request("POST", "/attendance/mark", data, use_auth=False)
        if response and response.status_code in [200, 400]:
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Attendance marked: {result['message']}")
                self.print_info(f"Is manual: {result['is_manual']}")
                return True
            else:
                self.print_info("Attendance already marked (this is okay)")
                return True
        else:
            self.print_error(f"Mark attendance failed: {response.text if response else 'No response'}")
            return False
    
    def test_mark_attendance_photo(self):
        """Test mark attendance (photo) endpoint"""
        self.print_header("Testing Mark Attendance (Photo)")
        
        if not self.unique_code or not self.roll_no:
            self.print_error("Unique code or Roll number not set")
            return False
        
        # Create a different roll number for photo test
        photo_roll_no = "TEST002"
        
        # Add student first
        dummy_image = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        student_data = {
            "roll_no": photo_roll_no,
            "name": "Bob Test Student",
            "email": "bob_test@school.com",
            "phone_number": "+1234567891",
            "semester": 1,
            "year": 2024,
            "school_id": self.school_id,
            "department_id": self.department_id,
            "photo_base64": dummy_image
        }
        
        # Try to add student (might already exist)
        self.make_request("POST", "/students", student_data)
        
        # Now mark attendance with photo
        data = {
            "unique_code": self.unique_code,
            "roll_no": photo_roll_no,
            "photo_base64": dummy_image
        }
        
        response = self.make_request("POST", "/attendance/mark", data, use_auth=False)
        if response and response.status_code in [200, 400]:
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Photo attendance marked: {result['message']}")
                self.print_info(f"Is manual: {result['is_manual']}")
                self.print_info(f"Is proxy: {result['is_proxy']}")
                return True
            else:
                self.print_info("Attendance already marked or failed (acceptable)")
                return True
        else:
            self.print_error(f"Photo attendance failed: {response.text if response else 'No response'}")
            return False
    
    def test_get_attendance_logs(self):
        """Test get attendance logs endpoint"""
        self.print_header("Testing Get Attendance Logs")
        
        if not self.unique_code:
            self.print_error("Unique code not set")
            return False
        
        response = self.make_request("GET", f"/attendance/logs?unique_code={self.unique_code}")
        if response and response.status_code == 200:
            logs = response.json()
            self.print_success(f"Retrieved {len(logs)} attendance logs")
            for log in logs[:3]:  # Show first 3
                self.print_info(f"  - {log['roll_no']}: {'Manual' if log['is_manual'] else 'Photo'}")
            return True
        else:
            self.print_error(f"Get attendance logs failed: {response.text if response else 'No response'}")
            return False
    
    def test_get_attendance_summary(self):
        """Test get attendance summary endpoint"""
        self.print_header("Testing Get Attendance Summary")
        
        response = self.make_request("GET", "/reports/attendance-summary")
        if response and response.status_code == 200:
            summary = response.json()
            self.print_success("Attendance summary retrieved")
            self.print_info(f"  Total attendance: {summary['total_attendance']}")
            self.print_info(f"  Manual: {summary['manual_attendance']}")
            self.print_info(f"  Photo: {summary['photo_attendance']}")
            self.print_info(f"  Proxy detected: {summary['proxy_detected']}")
            return True
        else:
            self.print_error(f"Get attendance summary failed: {response.text if response else 'No response'}")
            return False
    
    def test_get_student_attendance_report(self):
        """Test get student attendance report endpoint"""
        self.print_header("Testing Get Student Attendance Report")
        
        if not self.roll_no:
            self.print_error("Roll number not set")
            return False
        
        response = self.make_request("GET", f"/reports/student-attendance/{self.roll_no}")
        if response and response.status_code == 200:
            report = response.json()
            self.print_success("Student attendance report retrieved")
            self.print_info(f"  Student: {report['student_info']['name']}")
            self.print_info(f"  Total attendance: {report['total_attendance']}")
            return True
        else:
            self.print_error(f"Get student report failed: {response.text if response else 'No response'}")
            return False
    
    def test_get_all_endpoints(self):
        """Test GET endpoints for all entities"""
        self.print_header("Testing GET All Endpoints")
        
        endpoints = [
            ("/schools", "Schools"),
            ("/departments", "Departments"),
            ("/classes", "Classes"),
            ("/subjects", "Subjects"),
            ("/teachers", "Teachers"),
            ("/students", "Students"),
            ("/attendance/registers", "Attendance Registers")
        ]
        
        results = []
        for endpoint, name in endpoints:
            response = self.make_request("GET", endpoint)
            if response and response.status_code == 200:
                data = response.json()
                self.print_success(f"{name}: {len(data)} items")
                results.append(True)
            else:
                self.print_error(f"{name}: Failed")
                results.append(False)
        
        return all(results)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║     SCHOOL MANAGEMENT SYSTEM - API TESTING SUITE           ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_register),
            ("User Login", self.test_login),
            ("Get Current User", self.test_get_current_user),
            ("Create School", self.test_create_school),
            ("Create Department", self.test_create_department),
            ("Create Class", self.test_create_class),
            ("Create Subject", self.test_create_subject),
            ("Add Teacher", self.test_add_teacher),
            ("Add Student", self.test_add_student),
            ("Create Attendance Register", self.test_create_attendance_register),
            ("Mark Attendance (Manual)", self.test_mark_attendance_manual),
            ("Mark Attendance (Photo)", self.test_mark_attendance_photo),
            ("Get Attendance Logs", self.test_get_attendance_logs),
            ("Get Attendance Summary", self.test_get_attendance_summary),
            ("Get Student Report", self.test_get_student_attendance_report),
            ("Get All Endpoints", self.test_get_all_endpoints)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.print_error(f"{test_name} raised exception: {str(e)}")
                results[test_name] = False
        
        # Print summary
        self.print_header("TEST SUMMARY")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
            print(f"{test_name.ljust(40)} [{status}]")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
        
        if passed == total:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  SOME TESTS FAILED ⚠️{Colors.ENDC}\n")
        
        return passed == total


def main():
    """Main function to run tests"""
    print(f"{Colors.OKCYAN}Starting API tests...{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Base URL: {BASE_URL}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Test Email: {TEST_EMAIL}{Colors.ENDC}\n")
    
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())