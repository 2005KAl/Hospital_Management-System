from app import app, db, Admin, Doctor

def add_doctors():
    with app.app_context():
        try:
            # Clear existing data
            Doctor.query.delete()
            Admin.query.delete()
            db.session.commit()
            
            # Add admin users first
            admins = [
                Admin(loginid='admin', passid='admin123'),
                Admin(loginid='dr.smith', passid='doctor123'),
                Admin(loginid='dr.jones', passid='doctor456'),
                Admin(loginid='dr.patel', passid='doctor789'),
                Admin(loginid='dr.chen', passid='doctor101')
            ]
            
            for admin in admins:
                db.session.add(admin)
            db.session.commit()
            print("Added admin users")
            
            # Add doctors
            doctors = [
                Doctor(username='dr.smith', doctorname='Dr. John Smith', email='smith@hospital.com'),
                Doctor(username='dr.jones', doctorname='Dr. Sarah Jones', email='jones@hospital.com'),
                Doctor(username='dr.patel', doctorname='Dr. Raj Patel', email='patel@hospital.com'),
                Doctor(username='dr.chen', doctorname='Dr. Li Chen', email='chen@hospital.com')
            ]
            
            for doctor in doctors:
                db.session.add(doctor)
            db.session.commit()
            print("Added doctors")
            
            # Print current doctors
            doctors = Doctor.query.all()
            print("\nCurrent Doctors:")
            print("=" * 50)
            for doctor in doctors:
                print(f"Username: {doctor.username}")
                print(f"Name: {doctor.doctorname}")
                print(f"Email: {doctor.email}")
                print("-" * 50)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_doctors() 