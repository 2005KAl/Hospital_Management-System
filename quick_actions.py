from app import app, db, Patient, Admission, Department, Doctor, AdmissionType
from datetime import datetime

def quick_admit_patient(patient_name, department_name, doctor_username, condition, fee):
    """
    Quick action to admit a patient by name and department name instead of IDs.
    """
    with app.app_context():
        try:
            # Find department by name
            department = Department.query.filter_by(deptname=department_name).first()
            if not department:
                raise ValueError(f"Department '{department_name}' not found")

            # Find doctor by username
            doctor = Doctor.query.get(doctor_username)
            if not doctor:
                raise ValueError(f"Doctor with username '{doctor_username}' not found")

            # Create new patient if doesn't exist
            patient = Patient.query.filter_by(patientname=patient_name).first()
            if not patient:
                patient = Patient(patientname=patient_name, condition=condition)
                db.session.add(patient)
                db.session.commit()

            # Create new admission
            new_admission = Admission(
                patient=patient.patientid,
                department=department.deptid,
                admissiontype=11,  # Default to Emergency
                administrator=doctor_username,
                condition=condition,
                admissiondate=datetime.utcnow(),
                dischargedate=None,
                fee=fee
            )

            db.session.add(new_admission)
            db.session.commit()

            print("\nQuick Admission Successful:")
            print("=" * 80)
            print(f"Patient: {patient.patientname}")
            print(f"Department: {department.deptname}")
            print(f"Doctor: {doctor.doctorname}")
            print(f"Condition: {condition}")
            print(f"Fee: ${fee:,.2f}")
            print("=" * 80)

            return new_admission

        except Exception as e:
            print(f"Error in quick admission: {str(e)}")
            db.session.rollback()
            return None

def quick_discharge_patient(patient_name):
    """
    Quick action to discharge a patient by name.
    """
    with app.app_context():
        try:
            # Find patient
            patient = Patient.query.filter_by(patientname=patient_name).first()
            if not patient:
                raise ValueError(f"Patient '{patient_name}' not found")

            # Find active admission
            active_admission = Admission.query.filter_by(
                patient=patient.patientid,
                dischargedate=None
            ).first()

            if not active_admission:
                raise ValueError(f"No active admission found for patient '{patient_name}'")

            # Update discharge date
            active_admission.dischargedate = datetime.utcnow()
            db.session.commit()

            print("\nQuick Discharge Successful:")
            print("=" * 80)
            print(f"Patient: {patient.patientname}")
            print(f"Discharge Date: {active_admission.dischargedate}")
            print("=" * 80)

            return active_admission

        except Exception as e:
            print(f"Error in quick discharge: {str(e)}")
            db.session.rollback()
            return None

def quick_check_patient_status(patient_name):
    """
    Quick action to check patient's current status.
    """
    with app.app_context():
        try:
            # Find patient
            patient = Patient.query.filter_by(patientname=patient_name).first()
            if not patient:
                raise ValueError(f"Patient '{patient_name}' not found")

            # Get active admission
            active_admission = Admission.query.filter_by(
                patient=patient.patientid,
                dischargedate=None
            ).first()

            if active_admission:
                department = Department.query.get(active_admission.department)
                doctor = Doctor.query.get(active_admission.administrator)
                admission_type = AdmissionType.query.get(active_admission.admissiontype)

                print("\nPatient Status:")
                print("=" * 80)
                print(f"Patient: {patient.patientname}")
                print(f"Status: Currently Admitted")
                print(f"Department: {department.deptname}")
                print(f"Doctor: {doctor.doctorname}")
                print(f"Admission Type: {admission_type.admissiontypename}")
                print(f"Condition: {active_admission.condition}")
                print(f"Admitted: {active_admission.admissiondate}")
                print(f"Fee: ${active_admission.fee:,.2f}")
            else:
                print(f"\nPatient '{patient_name}' is not currently admitted.")

            print("=" * 80)

        except Exception as e:
            print(f"Error checking patient status: {str(e)}")

def quick_list_active_patients():
    """
    Quick action to list all currently admitted patients.
    """
    with app.app_context():
        try:
            active_admissions = (
                db.session.query(Admission, Patient, Department, Doctor)
                .join(Patient, Admission.patient == Patient.patientid)
                .join(Department, Admission.department == Department.deptid)
                .join(Doctor, Admission.administrator == Doctor.username)
                .filter(Admission.dischargedate == None)
                .all()
            )

            print("\nCurrently Admitted Patients:")
            print("=" * 100)
            for admission, patient, dept, doctor in active_admissions:
                print(f"Patient: {patient.patientname}")
                print(f"Department: {dept.deptname}")
                print(f"Doctor: {doctor.doctorname}")
                print(f"Condition: {admission.condition}")
                print(f"Admitted: {admission.admissiondate}")
                print(f"Fee: ${admission.fee:,.2f}")
                print("-" * 100)

            print(f"\nTotal active patients: {len(active_admissions)}")
            print("=" * 100)

        except Exception as e:
            print(f"Error listing active patients: {str(e)}")

if __name__ == '__main__':
    while True:
        print("\nQuick Actions Menu:")
        print("1. Quick Admit Patient")
        print("2. Quick Discharge Patient")
        print("3. Check Patient Status")
        print("4. List Active Patients")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            patient_name = input("Enter patient name: ")
            department_name = input("Enter department name: ")
            doctor_username = input("Enter doctor username: ")
            condition = input("Enter patient condition: ")
            fee = float(input("Enter admission fee: "))
            
            quick_admit_patient(patient_name, department_name, doctor_username, condition, fee)
            
        elif choice == '2':
            patient_name = input("Enter patient name to discharge: ")
            quick_discharge_patient(patient_name)
            
        elif choice == '3':
            patient_name = input("Enter patient name to check status: ")
            quick_check_patient_status(patient_name)
            
        elif choice == '4':
            quick_list_active_patients()
            
        elif choice == '5':
            print("Exiting Quick Actions...")
            break
            
        else:
            print("Invalid choice. Please try again.") 