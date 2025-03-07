from app import app, db, AdmissionType

def add_admission_types():
    with app.app_context():
        try:
            # Clear existing admission types
            AdmissionType.query.delete()
            db.session.commit()
            
            # Add admission types
            types = [
                AdmissionType(admissiontypename='Emergency'),
                AdmissionType(admissiontypename='Planned Surgery'),
                AdmissionType(admissiontypename='Regular Checkup'),
                AdmissionType(admissiontypename='Intensive Care'),
                AdmissionType(admissiontypename='Maternity'),
                AdmissionType(admissiontypename='Observation')
            ]
            
            for admission_type in types:
                db.session.add(admission_type)
            db.session.commit()
            print("Added admission types")
            
            # Print current admission types
            types = AdmissionType.query.all()
            print("\nCurrent Admission Types:")
            print("=" * 50)
            for t in types:
                print(f"ID: {t.admissiontypeid}")
                print(f"Name: {t.admissiontypename}")
                print("-" * 50)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_admission_types() 