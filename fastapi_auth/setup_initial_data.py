"""
Setup script to create initial data in the database
Run this once to create schools, departments, and an admin user
"""
from fastapi_auth.app.database import SessionLocal, engine
from fastapi_auth.app.models import Base, User, School, Department
from fastapi_auth.app.utils import get_password_hash
import uuid

def init_db():
    """Initialize database with sample data"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@school.com").first()
        if admin:
            print("⚠️  Admin user already exists. Skipping initialization.")
            return
        
        print("🚀 Initializing database with sample data...")
        
        # 1. Create Admin User
        admin_user = User(
            email="admin@school.com",
            password_hash=get_password_hash("admin123"),
            role=1,  # Admin role
            name="System Admin",
            phone_number="1234567890"
        )
        db.add(admin_user)
        print("✅ Created admin user: admin@school.com (password: admin123)")
        
        # 2. Create Sample Schools
        schools = [
            School(school_name="School of Engineering", school_dean="Dr. John Smith"),
            School(school_name="School of Computer Science", school_dean="Dr. Jane Doe"),
            School(school_name="School of Business", school_dean="Dr. Mike Johnson"),
        ]
        db.add_all(schools)
        db.flush()  # Get school IDs
        print(f"✅ Created {len(schools)} schools")
        
        # 3. Create Sample Departments
        departments = [
            # Engineering School Departments
            Department(department_name="Computer Engineering", hod="Prof. A", school_id=schools[0].school_id),
            Department(department_name="Mechanical Engineering", hod="Prof. B", school_id=schools[0].school_id),
            Department(department_name="Civil Engineering", hod="Prof. C", school_id=schools[0].school_id),
            
            # Computer Science School Departments
            Department(department_name="Software Engineering", hod="Prof. D", school_id=schools[1].school_id),
            Department(department_name="Data Science", hod="Prof. E", school_id=schools[1].school_id),
            Department(department_name="Artificial Intelligence", hod="Prof. F", school_id=schools[1].school_id),
            
            # Business School Departments
            Department(department_name="Business Administration", hod="Prof. G", school_id=schools[2].school_id),
            Department(department_name="Finance", hod="Prof. H", school_id=schools[2].school_id),
            Department(department_name="Marketing", hod="Prof. I", school_id=schools[2].school_id),
        ]
        db.add_all(departments)
        db.flush()
        print(f"✅ Created {len(departments)} departments")
        
        db.commit()
        print("\n" + "="*60)
        print("🎉 Database initialization complete!")
        print("="*60)
        print("\n📋 Summary:")
        print(f"   • Admin Email: admin@school.com")
        print(f"   • Admin Password: admin123")
        print(f"   • Schools Created: {len(schools)}")
        print(f"   • Departments Created: {len(departments)}")
        print("\n📝 School IDs:")
        for school in schools:
            print(f"   • {school.school_name} (ID: {school.school_id})")
        print("\n📝 Department IDs:")
        for dept in departments:
            print(f"   • {dept.department_name} (ID: {dept.department_id}, School ID: {dept.school_id})")
        print("\n🔐 Next Steps:")
        print("   1. Start the server: python run.py")
        print("   2. Login as admin to get a Bearer token")
        print("   3. Use the token to add teachers and students")
        print("="*60 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
