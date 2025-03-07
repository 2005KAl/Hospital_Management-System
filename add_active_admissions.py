from app import app, db, Patient, Admission, Department, AdmissionType, Doctor
from datetime import datetime, timedelta

def add_active_admissions():
    with app.app_context():
        try:
            # Add active admissions
            current_time = datetime.utcnow()
            active_admissions = [
                # Emergency cases
                {
                    'patient_id': 1,  # James Wilson
                    'department_id': 1,  # Cardiology
                    'admission_type_id': 1,  # Emergency
                    'administrator': 'dr.smith',
                    'condition': 'Critical hypertension, requires constant monitoring',
                    'admission_date': current_time - timedelta(days=2),
                    'fee': 2500.00
                },
                {
                    'patient_id': 2,  # Maria Garcia
                    'department_id': 2,  # Orthopedics
                    'admission_type_id': 2,  # Planned Surgery
                    'administrator': 'dr.jones',
                    'condition': 'Scheduled for femur surgery tomorrow',
                    'admission_date': current_time - timedelta(days=1),
                    'fee': 4500.00
                },
                {
                    'patient_id': 5,  # Emily Brown
                    'department_id': 7,  # Surgery
                    'admission_type_id': 1,  # Emergency
                    'administrator': 'dr.patel',
                    'condition': 'Acute appendicitis, prepped for emergency surgery',
                    'admission_date': current_time - timedelta(hours=6),
                    'fee': 3500.00
                },
                {
                    'patient_id': 9,  # Sofia Martinez
                    'department_id': 8,  # Obstetrics & Gynecology
                    'admission_type_id': 5,  # Maternity
                    'administrator': 'dr.jones',
                    'condition': 'Active labor, contractions 5 minutes apart',
                    'admission_date': current_time - timedelta(hours=3),
                    'fee': 4000.00
                },
                {
                    'patient_id': 10,  # William Turner
                    'department_id': 1,  # Cardiology
                    'admission_type_id': 4,  # Intensive Care
                    'administrator': 'dr.smith',
                    'condition': 'Severe cardiac arrhythmia, ICU monitoring',
                    'admission_date': current_time - timedelta(days=3),
                    'fee': 5500.00
                },
                {
                    'patient_id': 12,  # Thomas Wright
                    'department_id': 10,  # Oncology
                    'admission_type_id': 2,  # Planned Surgery
                    'administrator': 'dr.chen',
                    'condition': 'Admitted for scheduled tumor removal surgery',
                    'admission_date': current_time - timedelta(days=1),
                    'fee': 6500.00
                },
                {
                    'patient_id': 15,  # Patricia Moore
                    'department_id': 8,  # Obstetrics & Gynecology
                    'admission_type_id': 4,  # Intensive Care
                    'administrator': 'dr.jones',
                    'condition': 'High-risk pregnancy with complications',
                    'admission_date': current_time - timedelta(days=4),
                    'fee': 4800.00
                }
            ]

            # First, set all existing admissions as discharged
            Admission.query.update({'dischargedate': current_time - timedelta(days=1)})
            
            # Add new active admissions
            for admission_data in active_admissions:
                admission = Admission(
                    patient=admission_data['patient_id'],
                    department=admission_data['department_id'],
                    admissiontype=admission_data['admission_type_id'],
                    administrator=admission_data['administrator'],
                    condition=admission_data['condition'],
                    admissiondate=admission_data['admission_date'],
                    dischargedate=None,
                    fee=admission_data['fee']
                )
                db.session.add(admission)
            
            db.session.commit()
            
            # Print current active admissions
            active_admissions = Admission.query.filter_by(dischargedate=None).all()
            print("\nCurrent Active Admissions:")
            print("=" * 80)
            for admission in active_admissions:
                patient = Patient.query.get(admission.patient)
                department = Department.query.get(admission.department)
                doctor = Doctor.query.get(admission.administrator)
                admission_type = AdmissionType.query.get(admission.admissiontype)
                
                print(f"Patient: {patient.patientname}")
                print(f"Department: {department.deptname}")
                print(f"Doctor: {doctor.doctorname}")
                print(f"Type: {admission_type.admissiontypename}")
                print(f"Condition: {admission.condition}")
                print(f"Admitted: {admission.admissiondate}")
                print(f"Fee: ${admission.fee:,.2f}")
                print("-" * 80)
            
            print(f"\nTotal active patients: {len(active_admissions)}")
            
        except Exception as e:
            print(f"Error adding active admissions: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_active_admissions() 