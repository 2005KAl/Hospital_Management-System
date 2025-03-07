from app import app, db, Patient, Admission, Department, Doctor, AdmissionType

def check_active_admissions():
    with app.app_context():
        try:
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
            print("=" * 100)
            for admission, patient, dept, doctor, adm_type in active_admissions:
                print(f"Patient: {patient.patientname}")
                print(f"Department: {dept.deptname}")
                print(f"Doctor: {doctor.doctorname}")
                print(f"Type: {adm_type.admissiontypename}")
                print(f"Condition: {admission.condition}")
                print(f"Admitted: {admission.admissiondate}")
                print(f"Fee: ${admission.fee:,.2f}")
                print("-" * 100)
            
            print(f"\nTotal active patients: {len(active_admissions)}")
            
            # Department-wise breakdown
            print("\nDepartment-wise Active Patients:")
            print("=" * 50)
            dept_stats = (
                db.session.query(
                    Department.deptname,
                    db.func.count(Admission.admissionid).label('active_count')
                )
                .join(Admission, Department.deptid == Admission.department)
                .filter(Admission.dischargedate == None)
                .group_by(Department.deptname)
                .all()
            )
            
            for dept_name, count in dept_stats:
                print(f"{dept_name}: {count} patients")

        except Exception as e:
            print(f"Error checking active admissions: {str(e)}")

if __name__ == '__main__':
    check_active_admissions() 