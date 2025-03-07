from app import app, db, Patient, Admission, Department, Doctor, AdmissionType
from datetime import datetime, timedelta

def add_admissions():
    with app.app_context():
        try:
            # Clear existing admissions
            Admission.query.delete()
            db.session.commit()
            
            # Get current time
            current_time = datetime.utcnow()
            
            # Create some active admissions
            admissions = [
                Admission(
                    patient=1,  # James Wilson
                    department=6,  # Cardiology
                    admissiontype=11,  # Emergency (ID from current DB)
                    administrator='dr.smith',
                    condition='Critical hypertension, requires monitoring',
                    admissiondate=current_time - timedelta(days=2),
                    fee=2500.00
                ),
                Admission(
                    patient=2,  # Maria Garcia
                    department=7,  # Orthopedics
                    admissiontype=12,  # Planned Surgery (ID from current DB)
                    administrator='dr.jones',
                    condition='Pre-op for femur surgery',
                    admissiondate=current_time - timedelta(days=1),
                    fee=4500.00
                ),
                Admission(
                    patient=5,  # Emily Brown
                    department=10,  # Emergency
                    admissiontype=11,  # Emergency (ID from current DB)
                    administrator='dr.patel',
                    condition='Acute appendicitis',
                    admissiondate=current_time - timedelta(hours=6),
                    fee=3500.00
                ),
                Admission(
                    patient=9,  # Sofia Martinez
                    department=13,  # Obstetrics & Gynecology
                    admissiontype=15,  # Maternity (ID from current DB)
                    administrator='dr.jones',
                    condition='Active labor',
                    admissiondate=current_time - timedelta(hours=3),
                    fee=4000.00
                ),
                Admission(
                    patient=10,  # William Turner
                    department=6,  # Cardiology
                    admissiontype=14,  # Intensive Care (ID from current DB)
                    administrator='dr.smith',
                    condition='Severe cardiac arrhythmia',
                    admissiondate=current_time - timedelta(days=3),
                    fee=5500.00
                )
            ]
            
            # Add all admissions
            for admission in admissions:
                db.session.add(admission)
            
            db.session.commit()
            print("Successfully added active admissions")
            
            # Print current active admissions
            active_admissions = (
                db.session.query(
                    Admission, Patient, Department, Doctor, AdmissionType
                )
                .join(Patient, Admission.patient == Patient.patientid)
                .join(Department, Admission.department == Department.deptid)
                .join(Doctor, Admission.administrator == Doctor.username)
                .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
                .filter(Admission.dischargedate == None)
                .all()
            )
            
            print("\nCurrent Active Admissions:")
            print("=" * 80)
            for admission, patient, dept, doctor, adm_type in active_admissions:
                print(f"Patient: {patient.patientname}")
                print(f"Department: {dept.deptname}")
                print(f"Doctor: {doctor.doctorname}")
                print(f"Type: {adm_type.admissiontypename}")
                print(f"Condition: {admission.condition}")
                print(f"Admitted: {admission.admissiondate}")
                print(f"Fee: ${admission.fee:,.2f}")
                print("-" * 80)
            
            print(f"\nTotal active patients: {len(active_admissions)}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_admissions() 