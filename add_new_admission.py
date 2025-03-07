from app import app, db, Patient, Admission, Department, Doctor, AdmissionType
from datetime import datetime

def add_new_admission(patient_id, department_id, admission_type_id, doctor_username, condition, fee):
    """
    Add a new admission to the hospital system.
    
    Args:
        patient_id (int): ID of the patient
        department_id (int): ID of the department
        admission_type_id (int): ID of the admission type
        doctor_username (str): Username of the doctor
        condition (str): Patient's condition
        fee (float): Admission fee
    """
    with app.app_context():
        try:
            # Validate patient exists
            patient = Patient.query.get(patient_id)
            if not patient:
                raise ValueError(f"Patient with ID {patient_id} not found")

            # Validate department exists
            department = Department.query.get(department_id)
            if not department:
                raise ValueError(f"Department with ID {department_id} not found")

            # Validate admission type exists
            admission_type = AdmissionType.query.get(admission_type_id)
            if not admission_type:
                raise ValueError(f"Admission type with ID {admission_type_id} not found")

            # Validate doctor exists
            doctor = Doctor.query.get(doctor_username)
            if not doctor:
                raise ValueError(f"Doctor with username {doctor_username} not found")

            # Create new admission
            new_admission = Admission(
                patient=patient_id,
                department=department_id,
                admissiontype=admission_type_id,
                administrator=doctor_username,
                condition=condition,
                admissiondate=datetime.utcnow(),
                dischargedate=None,
                fee=fee
            )

            # Add to database
            db.session.add(new_admission)
            db.session.commit()

            # Print confirmation
            print("\nNew Admission Added Successfully:")
            print("=" * 80)
            print(f"Patient: {patient.patientname}")
            print(f"Department: {department.deptname}")
            print(f"Doctor: {doctor.doctorname}")
            print(f"Type: {admission_type.admissiontypename}")
            print(f"Condition: {condition}")
            print(f"Admission Date: {new_admission.admissiondate}")
            print(f"Fee: ${fee:,.2f}")
            print("=" * 80)

            return new_admission

        except Exception as e:
            print(f"Error adding new admission: {str(e)}")
            db.session.rollback()
            return None

def print_available_options():
    """Print available options for adding a new admission"""
    print("\nAvailable Options:")
    print("=" * 80)
    
    # Print departments
    print("\nDepartments:")
    departments = Department.query.all()
    for dept in departments:
        print(f"{dept.deptid}: {dept.deptname}")
    
    # Print admission types
    print("\nAdmission Types:")
    types = AdmissionType.query.all()
    for t in types:
        print(f"{t.admissiontypeid}: {t.admissiontypename}")
    
    # Print doctors
    print("\nDoctors:")
    doctors = Doctor.query.all()
    for doc in doctors:
        print(f"{doc.username}: {doc.doctorname}")
    
    print("=" * 80)

if __name__ == '__main__':
    # Print available options
    print_available_options()
    
    # Get user input
    try:
        patient_id = int(input("\nEnter patient ID: "))
        department_id = int(input("Enter department ID: "))
        admission_type_id = int(input("Enter admission type ID: "))
        doctor_username = input("Enter doctor username: ")
        condition = input("Enter patient condition: ")
        fee = float(input("Enter admission fee: "))
        
        # Add new admission
        add_new_admission(
            patient_id=patient_id,
            department_id=department_id,
            admission_type_id=admission_type_id,
            doctor_username=doctor_username,
            condition=condition,
            fee=fee
        )
        
    except ValueError as e:
        print(f"Error: Please enter valid values. {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

    # Example usage of quick actions
    print("\nExample usage of quick actions:")
    print("=" * 80)
    print("Enter patient name: John Doe")
    print("Enter department name: Cardiology")
    print("Enter doctor username: dr.smith")
    print("Enter patient condition: Chest pain")
    print("Enter admission fee: 3000")
    print("Enter patient name to check status: John Doe") 