from app import app, db, Patient

with app.app_context():
    try:
        total_patients = Patient.query.count()
        print(f'Total patients in database: {total_patients}')
        
        # List all patients
        patients = Patient.query.all()
        print('\nPatient list:')
        for patient in patients:
            print(f'ID: {patient.patientid}, Name: {patient.patientname}, Condition: {patient.condition}')
    except Exception as e:
        print(f'Error: {e}') 