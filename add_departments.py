from app import app, db, Department

def add_departments():
    with app.app_context():
        try:
            # Clear existing departments
            Department.query.delete()
            db.session.commit()
            
            # Add departments
            departments = [
                Department(deptname='Cardiology'),
                Department(deptname='Orthopedics'),
                Department(deptname='Pediatrics'),
                Department(deptname='Neurology'),
                Department(deptname='Emergency'),
                Department(deptname='Internal Medicine'),
                Department(deptname='Surgery'),
                Department(deptname='Obstetrics & Gynecology'),
                Department(deptname='Psychiatry'),
                Department(deptname='Oncology')
            ]
            
            for dept in departments:
                db.session.add(dept)
            db.session.commit()
            print("Added departments")
            
            # Print current departments
            departments = Department.query.all()
            print("\nCurrent Departments:")
            print("=" * 50)
            for dept in departments:
                print(f"ID: {dept.deptid}")
                print(f"Name: {dept.deptname}")
                print("-" * 50)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_departments() 