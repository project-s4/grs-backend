"""
Script to seed the database with dummy data including:
- Multiple departments
- Users for each department
- Regular citizens
- Admin users
- Sample complaints

Run with: python seed_db.py

Note: Make sure the backend server is configured with the correct DATABASE_URL.
Set DATABASE_URL environment variable if using a different database than the default.
Example: DATABASE_URL="postgresql://user:password@localhost:5432/dbname" python seed_db.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, DATABASE_URL
from app.models.models import User, Department, Complaint, UserRole, ComplaintStatus
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import uuid
import random

print(f"Connecting to database: {DATABASE_URL}")
print()

# Department data
DEPARTMENTS = [
    {"code": "PW", "name": "Public Works", "parent_id": None},
    {"code": "HD", "name": "Health Department", "parent_id": None},
    {"code": "ED", "name": "Education Department", "parent_id": None},
    {"code": "TD", "name": "Transport Department", "parent_id": None},
    {"code": "RD", "name": "Revenue Department", "parent_id": None},
    {"code": "PD", "name": "Police Department", "parent_id": None},
    {"code": "FD", "name": "Fire Department", "parent_id": None},
    {"code": "ENV", "name": "Environment Department", "parent_id": None},
    {"code": "PW-SUB", "name": "Public Works - Roads", "parent_code": "PW"},
    {"code": "HD-SUB", "name": "Health Department - Clinics", "parent_code": "HD"},
]

# Sample citizen users
CITIZEN_USERS = [
    {"name": "Rajesh Kumar", "phone": "9876543210", "email": "rajesh@example.com", "password": "rajesh123"},
    {"name": "Priya Sharma", "phone": "9876543211", "email": "priya@example.com", "password": "priya123"},
    {"name": "Amit Patel", "phone": "9876543212", "email": "amit@example.com", "password": "amit123"},
    {"name": "Deepika Nair", "phone": "9876543213", "email": "deepika@example.com", "password": "deepika123"},
    {"name": "Ravi Menon", "phone": "9876543214", "email": "ravi@example.com", "password": "ravi123"},
    {"name": "Kavita Desai", "phone": "9876543215", "email": "kavita@example.com", "password": "kavita123"},
    {"name": "Nikhil Joshi", "phone": "9876543216", "email": "nikhil@example.com", "password": "nikhil123"},
    {"name": "Sneha Rao", "phone": "9876543217", "email": "sneha@example.com", "password": "sneha123"},
]

# Admin users
ADMIN_USERS = [
    {"name": "Admin User", "phone": "9999999999", "email": "admin@example.com", "password": "admin123"},
    {"name": "Super Admin", "phone": "9999999998", "email": "superadmin@example.com", "password": "superadmin123"},
]

# Sample complaints
SAMPLE_COMPLAINTS = [
    {
        "title": "Potholes on Main Street",
        "description": "There are several large potholes on Main Street near the intersection. They are causing damage to vehicles and posing a safety hazard.",
        "category": "Road Maintenance",
        "subcategory": "Potholes",
        "language": "en",
    },
    {
        "title": "Damaged Streetlights",
        "description": "Streetlights on Park Avenue have been non-functional for two weeks. The area becomes very dark at night.",
        "category": "Public Works",
        "subcategory": "Streetlights",
        "language": "en",
    },
    {
        "title": "Garbage Not Being Collected",
        "description": "Garbage collection has not been done in my neighborhood for over a week. The bins are overflowing.",
        "category": "Waste Management",
        "subcategory": "Collection",
        "language": "en",
    },
    {
        "title": "Water Supply Issue",
        "description": "Water supply is inconsistent in my area. Water comes only twice a day and the pressure is very low.",
        "category": "Water Supply",
        "subcategory": "Supply Issues",
        "language": "en",
    },
    {
        "title": "Clinic Appointment Delay",
        "description": "I have been waiting for over 3 months for my follow-up appointment at the local clinic.",
        "category": "Healthcare",
        "subcategory": "Appointments",
        "language": "en",
    },
    {
        "title": "School Infrastructure",
        "description": "The school building has leaking roofs and damaged classrooms. Students are being taught in temporary arrangements.",
        "category": "Education",
        "subcategory": "Infrastructure",
        "language": "en",
    },
    {
        "title": "Bus Service Frequency",
        "description": "Bus service to our area is very infrequent. Only one bus comes every 2 hours during peak times.",
        "category": "Transport",
        "subcategory": "Bus Service",
        "language": "en",
    },
    {
        "title": "Traffic Violations",
        "description": "People regularly park on the footpath blocking pedestrian access. No action is being taken.",
        "category": "Traffic",
        "subcategory": "Parking Violations",
        "language": "en",
    },
    {
        "title": "Noise Pollution",
        "description": "Construction work nearby continues late into the night causing disturbance to residents.",
        "category": "Environment",
        "subcategory": "Noise",
        "language": "en",
    },
    {
        "title": "Fire Safety Equipment",
        "description": "The fire hydrant in our building complex is non-functional. This is a critical safety issue.",
        "category": "Fire Safety",
        "subcategory": "Equipment",
        "language": "en",
    },
]

def get_department_code(db, code):
    """Get department by code"""
    dept = db.query(Department).filter(Department.code == code).first()
    return dept.id if dept else None

def generate_reference_no(index):
    """Generate a unique reference number"""
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    return f"GRS{date_str}{str(index).zfill(4)}"

def seed_database():
    db = SessionLocal()
    try:
        print("Starting database seeding...\n")
        
        # 1. Seed Departments
        print("1. Seeding Departments...")
        departments_map = {}
        for dept_data in DEPARTMENTS:
            existing_dept = db.query(Department).filter(Department.code == dept_data["code"]).first()
            if existing_dept:
                print(f"   ✓ Department '{dept_data['name']}' already exists")
                departments_map[dept_data["code"]] = existing_dept
            else:
                parent_id = None
                if "parent_code" in dept_data:
                    parent_dept = departments_map.get(dept_data["parent_code"])
                    parent_id = parent_dept.id if parent_dept else None
                elif dept_data.get("parent_id") is not None:
                    # This would need to be implemented based on your needs
                    pass
                
                dept = Department(
                    code=dept_data["code"],
                    name=dept_data["name"],
                    parent_department_id=parent_id,
                    escalation_policy={
                        "auto_escalate_after_days": 7,
                        "escalation_levels": ["dept_head", "commissioner"]
                    }
                )
                db.add(dept)
                db.flush()
                departments_map[dept_data["code"]] = dept
                print(f"   ✓ Created department: {dept_data['name']} ({dept_data['code']})")
        
        db.commit()
        print()
        
        # 2. Seed Citizen Users
        print("2. Seeding Citizen Users...")
        citizen_ids = []
        for user_data in CITIZEN_USERS:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"   ✓ User '{user_data['name']}' already exists")
                citizen_ids.append(existing_user)
            else:
                user = User(
                    name=user_data["name"],
                    phone=user_data["phone"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=UserRole.citizen
                )
                db.add(user)
                db.flush()
                citizen_ids.append(user)
                print(f"   ✓ Created citizen user: {user_data['name']} ({user_data['email']})")
        
        db.commit()
        print()
        
        # 3. Seed Department Users
        print("3. Seeding Department Users...")
        dept_user_ids = []
        department_users = [
            {"name": "John Public Works", "email": "john.publicworks@dept.gov", "phone": "+91-9876500001", "password": "dept123", "dept_code": "PW"},
            {"name": "Sarah Health Dept", "email": "sarah.health@dept.gov", "phone": "+91-9876500002", "password": "dept123", "dept_code": "HD"},
            {"name": "Mike Education", "email": "mike.education@dept.gov", "phone": "+91-9876500003", "password": "dept123", "dept_code": "ED"},
            {"name": "Lisa Transport", "email": "lisa.transport@dept.gov", "phone": "+91-9876500004", "password": "dept123", "dept_code": "TD"},
            {"name": "David Revenue", "email": "david.revenue@dept.gov", "phone": "+91-9876500005", "password": "dept123", "dept_code": "RD"},
            {"name": "Emma Police", "email": "emma.police@dept.gov", "phone": "+91-9876500006", "password": "dept123", "dept_code": "PD"},
            {"name": "Tom Fire Dept", "email": "tom.fire@dept.gov", "phone": "+91-9876500007", "password": "dept123", "dept_code": "FD"},
            {"name": "Anna Environment", "email": "anna.env@dept.gov", "phone": "+91-9876500008", "password": "dept123", "dept_code": "ENV"},
        ]
        
        for user_data in department_users:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"   ✓ Department user '{user_data['name']}' already exists")
                dept_user_ids.append(existing_user)
            else:
                dept_id = get_department_code(db, user_data["dept_code"])
                user = User(
                    name=user_data["name"],
                    phone=user_data["phone"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=UserRole.department,
                    department_id=dept_id
                )
                db.add(user)
                db.flush()
                dept_user_ids.append(user)
                print(f"   ✓ Created department user: {user_data['name']} ({user_data['email']}) - {user_data['dept_code']}")
        
        db.commit()
        print()
        
        # 4. Seed Admin Users
        print("4. Seeding Admin Users...")
        admin_ids = []
        for user_data in ADMIN_USERS:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"   ✓ Admin user '{user_data['name']}' already exists")
                admin_ids.append(existing_user)
            else:
                user = User(
                    name=user_data["name"],
                    phone=user_data["phone"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=UserRole.admin
                )
                db.add(user)
                db.flush()
                admin_ids.append(user)
                print(f"   ✓ Created admin user: {user_data['name']} ({user_data['email']})")
        
        db.commit()
        print()
        
        # 5. Seed Complaints
        print("5. Seeding Complaints...")
        complaint_count = db.query(Complaint).count()
        new_complaints = 0
        
        for i, complaint_data in enumerate(SAMPLE_COMPLAINTS):
            # Distribute complaints across departments
            dept_codes = ["PW", "HD", "ED", "TD", "RD", "PD", "FD", "ENV"]
            dept_code = dept_codes[i % len(dept_codes)]
            dept_id = get_department_code(db, dept_code)
            
            # Get a random citizen user
            citizen_user = citizen_ids[i % len(citizen_ids)]
            
            # Get a department user for assignment (if available)
            assigned_user = dept_user_ids[i % len(dept_user_ids)] if dept_user_ids else None
            
            # Random status distribution
            statuses = [ComplaintStatus.new, ComplaintStatus.triaged, ComplaintStatus.in_progress, ComplaintStatus.resolved]
            status = statuses[i % len(statuses)]
            
            complaint = Complaint(
                reference_no=generate_reference_no(complaint_count + i + 1),
                user_id=citizen_user.id,
                title=complaint_data["title"],
                description=complaint_data["description"],
                category=complaint_data["category"],
                subcategory=complaint_data["subcategory"],
                language=complaint_data["language"],
                department_id=dept_id,
                status=status,
                assigned_to=assigned_user.id if assigned_user else None,
                source="web",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(complaint)
            new_complaints += 1
            print(f"   ✓ Created complaint #{complaint.reference_no}: {complaint_data['title']} -> {dept_code}")
        
        db.commit()
        print()
        
        print("="*60)
        print("Database seeding completed successfully! ✓")
        print("="*60)
        print(f"\nSummary:")
        print(f"  • Departments created: {len(departments_map)}")
        print(f"  • Citizen users created: {len(citizen_ids)}")
        print(f"  • Department users created: {len(dept_user_ids)}")
        print(f"  • Admin users created: {len(admin_ids)}")
        print(f"  • New complaints created: {new_complaints}")
        print("\n" + "="*60)
        print("\nTest Login Credentials:")
        print("\nCitizens:")
        for user_data in CITIZEN_USERS[:3]:
            print(f"  Email: {user_data['email']} | Password: {user_data['password']}")
        print("\nDepartment Users:")
        for user_data in department_users[:3]:
            print(f"  Email: {user_data['email']} | Password: {user_data['password']}")
        print("\nAdmin:")
        print(f"  Email: {ADMIN_USERS[0]['email']} | Password: {ADMIN_USERS[0]['password']}")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\nError seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

