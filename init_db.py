import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import logging
from app import db, Patient, Department, AdmissionType, Admin, Doctor, Admission, app
from datetime import datetime, timedelta
from sqlalchemy import inspect

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the database and create required tables"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Extract connection parameters from DATABASE_URL
    db_params = DATABASE_URL.replace('postgresql://', '')
    user_pass, host_db = db_params.split('@')
    user, password = user_pass.split(':')
    host_port, db_name = host_db.split('/')
    host = host_port.split(':')[0]
    port = host_port.split(':')[1] if ':' in host_port else '5432'

    try:
        # First, connect to PostgreSQL server without specifying a database
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cursor.fetchone():
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
        
        # Close connection to postgres database
        cursor.close()
        conn.close()

        # Connect to the newly created database
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        create_tables_sql = """
        -- Drop existing tables if they exist
        DROP TABLE IF EXISTS Admission CASCADE;
        DROP TABLE IF EXISTS Patient CASCADE;
        DROP TABLE IF EXISTS AdmissionType CASCADE;
        DROP TABLE IF EXISTS Department CASCADE;
        DROP TABLE IF EXISTS Doctordetails CASCADE;
        DROP TABLE IF EXISTS Admini CASCADE;

        -- Create tables
        CREATE TABLE Admini (
            Loginid VARCHAR(50) PRIMARY KEY,
            passid VARCHAR(50) NOT NULL
        );

        CREATE TABLE Doctordetails (
            UserName VARCHAR(50) PRIMARY KEY REFERENCES Admini(Loginid),
            DoctorName VARCHAR(100) NOT NULL,
            Email VARCHAR(100)
        );

        CREATE TABLE Department (
            DeptId SERIAL PRIMARY KEY,
            DeptName VARCHAR(100) UNIQUE NOT NULL
        );

        CREATE TABLE AdmissionType (
            AdmissionTypeID SERIAL PRIMARY KEY,
            AdmissionTypeName VARCHAR(50) UNIQUE NOT NULL
        );

        CREATE TABLE Patient (
            PatientId SERIAL PRIMARY KEY,
            PatientName VARCHAR(100) NOT NULL,
            Condition TEXT
        );

        CREATE TABLE Admission (
            AdmissionID SERIAL PRIMARY KEY,
            AdmissionType INTEGER REFERENCES AdmissionType(AdmissionTypeID),
            Department INTEGER REFERENCES Department(DeptId),
            Patient INTEGER REFERENCES Patient(PatientId),
            Administrator VARCHAR(50) REFERENCES Doctordetails(UserName),
            Condition TEXT,
            AdmissionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            DischargeDate TIMESTAMP,
            Fee DECIMAL(10,2)
        );

        -- Insert admin users
        INSERT INTO Admini (Loginid, passid) VALUES
            ('admin', 'admin123'),
            ('dr.smith', 'doctor123'),
            ('dr.jones', 'doctor456'),
            ('dr.patel', 'doctor789'),
            ('dr.chen', 'doctor101')
        ON CONFLICT (Loginid) DO NOTHING;

        -- Insert doctors
        INSERT INTO Doctordetails (UserName, DoctorName, Email) VALUES
            ('dr.smith', 'Dr. John Smith', 'smith@hospital.com'),
            ('dr.jones', 'Dr. Sarah Jones', 'jones@hospital.com'),
            ('dr.patel', 'Dr. Raj Patel', 'patel@hospital.com'),
            ('dr.chen', 'Dr. Li Chen', 'chen@hospital.com')
        ON CONFLICT (UserName) DO NOTHING;

        -- Insert departments
        INSERT INTO Department (DeptName) VALUES
            ('Cardiology'),
            ('Orthopedics'),
            ('Pediatrics'),
            ('Neurology'),
            ('Emergency'),
            ('Internal Medicine'),
            ('Surgery'),
            ('Obstetrics & Gynecology'),
            ('Psychiatry'),
            ('Oncology')
        ON CONFLICT (DeptName) DO NOTHING;

        -- Insert admission types
        INSERT INTO AdmissionType (AdmissionTypeName) VALUES
            ('Emergency'),
            ('Planned Surgery'),
            ('Regular Checkup'),
            ('Intensive Care'),
            ('Maternity'),
            ('Observation')
        ON CONFLICT (AdmissionTypeName) DO NOTHING;

        -- Insert patients
        INSERT INTO Patient (PatientName, Condition) VALUES
            ('James Wilson', 'Hypertension and mild chest pain'),
            ('Maria Garcia', 'Fractured right femur'),
            ('Sarah Johnson', 'Type 2 Diabetes'),
            ('Michael Chang', 'Post-surgery recovery'),
            ('Emily Brown', 'Acute appendicitis'),
            ('Robert Taylor', 'Chronic back pain'),
            ('Lisa Anderson', 'Migraine and vertigo'),
            ('David Miller', 'Pneumonia'),
            ('Sofia Martinez', 'Pregnancy - third trimester'),
            ('William Turner', 'Cardiac arrhythmia'),
            ('Emma Davis', 'Depression and anxiety'),
            ('Thomas Wright', 'Lung cancer - Stage 2'),
            ('Linda Kim', 'Rheumatoid arthritis'),
            ('Richard Lee', 'Stroke recovery'),
            ('Patricia Moore', 'High-risk pregnancy')
        ON CONFLICT (PatientId) DO NOTHING;

        -- Insert admissions (including both active and past admissions)
        INSERT INTO Admission (AdmissionType, Department, Patient, Administrator, Condition, AdmissionDate, DischargeDate, Fee) VALUES
            -- Active admissions
            (1, 1, 1, 'dr.smith', 'Admitted for chest pain evaluation', CURRENT_TIMESTAMP - INTERVAL '2 days', NULL, 1500.00),
            (2, 2, 2, 'dr.jones', 'Scheduled for femur surgery', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL, 3500.00),
            (1, 5, 5, 'dr.patel', 'Emergency appendectomy required', CURRENT_TIMESTAMP - INTERVAL '12 hours', NULL, 2500.00),
            (4, 1, 10, 'dr.smith', 'Cardiac monitoring', CURRENT_TIMESTAMP - INTERVAL '3 days', NULL, 2800.00),
            (5, 8, 15, 'dr.jones', 'Pre-eclampsia monitoring', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL, 3200.00),

            -- Past/discharged admissions
            (3, 6, 3, 'dr.chen', 'Diabetes monitoring and medication adjustment', CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP - INTERVAL '28 days', 800.00),
            (2, 2, 4, 'dr.jones', 'Knee replacement surgery', CURRENT_TIMESTAMP - INTERVAL '15 days', CURRENT_TIMESTAMP - INTERVAL '10 days', 4500.00),
            (3, 4, 7, 'dr.smith', 'Severe migraine evaluation', CURRENT_TIMESTAMP - INTERVAL '45 days', CURRENT_TIMESTAMP - INTERVAL '44 days', 1200.00),
            (1, 5, 8, 'dr.patel', 'Severe pneumonia treatment', CURRENT_TIMESTAMP - INTERVAL '20 days', CURRENT_TIMESTAMP - INTERVAL '15 days', 3800.00),
            (2, 7, 12, 'dr.chen', 'Tumor removal surgery', CURRENT_TIMESTAMP - INTERVAL '60 days', CURRENT_TIMESTAMP - INTERVAL '52 days', 6500.00),
            (3, 9, 11, 'dr.jones', 'Mental health evaluation', CURRENT_TIMESTAMP - INTERVAL '10 days', CURRENT_TIMESTAMP - INTERVAL '9 days', 900.00),
            (6, 3, 9, 'dr.patel', 'Routine pregnancy checkup', CURRENT_TIMESTAMP - INTERVAL '25 days', CURRENT_TIMESTAMP - INTERVAL '25 days', 400.00)
        ON CONFLICT (AdmissionID) DO NOTHING;
        """
        
        cursor.execute(create_tables_sql)
        conn.commit()
        logger.info("Tables created and sample data inserted successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Create tables
    db.create_all()

    # Add sample departments
    departments = [
        Department(dept_id=1, dept_name='Cardiology'),
        Department(dept_id=2, dept_name='Orthopedics'),
        Department(dept_id=3, dept_name='Pediatrics'),
        Department(dept_id=4, dept_name='Neurology'),
        Department(dept_id=5, dept_name='Emergency'),
        Department(dept_id=6, dept_name='Internal Medicine')
    ]

    # Add sample admission types
    admission_types = [
        AdmissionType(admission_type_id=1, admission_type_name='Emergency'),
        AdmissionType(admission_type_id=2, admission_type_name='Planned Surgery'),
        AdmissionType(admission_type_id=3, admission_type_name='Regular Checkup'),
        AdmissionType(admission_type_id=4, admission_type_name='Intensive Care')
    ]

    # Add admin and doctors
    admin = Admin(loginid='admin', passid='admin123')
    doctors = [
        Doctor(username='dr.smith', doctor_name='Dr. John Smith', email='smith@hospital.com'),
        Doctor(username='dr.jones', doctor_name='Dr. Sarah Jones', email='jones@hospital.com'),
        Doctor(username='dr.patel', doctor_name='Dr. Raj Patel', email='patel@hospital.com'),
        Doctor(username='dr.chen', doctor_name='Dr. Li Chen', email='chen@hospital.com')
    ]

    # Add sample patients
    patients = [
        Patient(
            patient_id=1,
            patient_name='James Wilson',
            condition='Hypertension and mild chest pain'
        ),
        Patient(
            patient_id=2,
            patient_name='Maria Garcia',
            condition='Fractured right femur'
        ),
        Patient(
            patient_id=3,
            patient_name='Sarah Johnson',
            condition='Type 2 Diabetes'
        ),
        Patient(
            patient_id=4,
            patient_name='Michael Chang',
            condition='Post-surgery recovery'
        ),
        Patient(
            patient_id=5,
            patient_name='Emily Brown',
            condition='Acute appendicitis'
        ),
        Patient(
            patient_id=6,
            patient_name='Robert Taylor',
            condition='Chronic back pain'
        ),
        Patient(
            patient_id=7,
            patient_name='Lisa Anderson',
            condition='Migraine and vertigo'
        ),
        Patient(
            patient_id=8,
            patient_name='David Miller',
            condition='Pneumonia'
        ),
        Patient(
            patient_id=9,
            patient_name='Sofia Martinez',
            condition='Pregnancy - third trimester'
        ),
        Patient(
            patient_id=10,
            patient_name='William Turner',
            condition='Cardiac arrhythmia'
        )
    ]

    # Add sample admissions
    current_time = datetime.utcnow()
    admissions = [
        # Active admissions
        Admission(
            patient=1,
            department=1,  # Cardiology
            admission_type=1,  # Emergency
            administrator='dr.smith',
            condition='Admitted for chest pain evaluation',
            admission_date=current_time - timedelta(days=2),
            fee=1500.00
        ),
        Admission(
            patient=2,
            department=2,  # Orthopedics
            admission_type=2,  # Planned Surgery
            administrator='dr.jones',
            condition='Scheduled for femur surgery',
            admission_date=current_time - timedelta(days=1),
            fee=3500.00
        ),
        Admission(
            patient=5,
            department=5,  # Emergency
            admission_type=1,  # Emergency
            administrator='dr.patel',
            condition='Emergency appendectomy required',
            admission_date=current_time - timedelta(hours=12),
            fee=2500.00
        ),
        
        # Past/discharged admissions
        Admission(
            patient=3,
            department=6,  # Internal Medicine
            admission_type=3,  # Regular Checkup
            administrator='dr.chen',
            condition='Diabetes monitoring and medication adjustment',
            admission_date=current_time - timedelta(days=30),
            discharge_date=current_time - timedelta(days=28),
            fee=800.00
        ),
        Admission(
            patient=4,
            department=2,  # Orthopedics
            admission_type=2,  # Planned Surgery
            administrator='dr.jones',
            condition='Knee replacement surgery',
            admission_date=current_time - timedelta(days=15),
            discharge_date=current_time - timedelta(days=10),
            fee=4500.00
        ),
        Admission(
            patient=7,
            department=4,  # Neurology
            admission_type=3,  # Regular Checkup
            administrator='dr.smith',
            condition='Severe migraine evaluation',
            admission_date=current_time - timedelta(days=45),
            discharge_date=current_time - timedelta(days=44),
            fee=1200.00
        )
    ]

    # Add all records to database
    try:
        # Add departments
        for dept in departments:
            db.session.add(dept)
        
        # Add admission types
        for admission_type in admission_types:
            db.session.add(admission_type)
        
        # Add admin and doctors
        db.session.add(admin)
        for doctor in doctors:
            db.session.add(doctor)
        
        # Add patients
        for patient in patients:
            db.session.add(patient)
        
        # Add admissions
        for admission in admissions:
            db.session.add(admission)
        
        # Commit all changes
        db.session.commit()
        print("Sample data added successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"Error adding sample data: {str(e)}")

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if tables exist
        inspector = inspect(db.engine)
        print("Tables in database:", inspector.get_table_names())
        
        # Add sample data only if tables are empty
        if not Admin.query.first():
            # Insert Admin Users
            admins = [
                Admin(loginid='admin', passid='admin123'),
                Admin(loginid='dr.smith', passid='doctor123'),
                Admin(loginid='dr.jones', passid='doctor456'),
                Admin(loginid='dr.patel', passid='doctor789'),
                Admin(loginid='dr.chen', passid='doctor101')
            ]
            db.session.add_all(admins)
            db.session.commit()
            print("Added admin users")

        if not Doctor.query.first():
            # Insert Doctors
            doctors = [
                Doctor(username='dr.smith', doctorname='Dr. John Smith', email='smith@hospital.com'),
                Doctor(username='dr.jones', doctorname='Dr. Sarah Jones', email='jones@hospital.com'),
                Doctor(username='dr.patel', doctorname='Dr. Raj Patel', email='patel@hospital.com'),
                Doctor(username='dr.chen', doctorname='Dr. Li Chen', email='chen@hospital.com')
            ]
            db.session.add_all(doctors)
            db.session.commit()
            print("Added doctors")

        if not Department.query.first():
            # Insert Departments
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
            db.session.add_all(departments)
            db.session.commit()
            print("Added departments")

        if not AdmissionType.query.first():
            # Insert Admission Types
            admission_types = [
                AdmissionType(admissiontypename='Emergency'),
                AdmissionType(admissiontypename='Planned Surgery'),
                AdmissionType(admissiontypename='Regular Checkup'),
                AdmissionType(admissiontypename='Intensive Care'),
                AdmissionType(admissiontypename='Maternity'),
                AdmissionType(admissiontypename='Observation')
            ]
            db.session.add_all(admission_types)
            db.session.commit()
            print("Added admission types")

        if not Patient.query.first():
            # Insert Patients
            patients = [
                Patient(patientname='James Wilson', condition='Hypertension and mild chest pain'),
                Patient(patientname='Maria Garcia', condition='Fractured right femur'),
                Patient(patientname='Sarah Johnson', condition='Type 2 Diabetes'),
                Patient(patientname='Michael Chang', condition='Post-surgery recovery'),
                Patient(patientname='Emily Brown', condition='Acute appendicitis'),
                Patient(patientname='Robert Taylor', condition='Chronic back pain'),
                Patient(patientname='Lisa Anderson', condition='Migraine and vertigo'),
                Patient(patientname='David Miller', condition='Pneumonia'),
                Patient(patientname='Sofia Martinez', condition='Pregnancy - third trimester'),
                Patient(patientname='William Turner', condition='Cardiac arrhythmia'),
                Patient(patientname='Emma Davis', condition='Depression and anxiety'),
                Patient(patientname='Thomas Wright', condition='Lung cancer - Stage 2'),
                Patient(patientname='Linda Kim', condition='Rheumatoid arthritis'),
                Patient(patientname='Richard Lee', condition='Stroke recovery'),
                Patient(patientname='Patricia Moore', condition='High-risk pregnancy')
            ]
            db.session.add_all(patients)
            db.session.commit()
            print("Added patients")

        # Print counts
        print(f"\nCurrent database status:")
        print(f"Admins: {Admin.query.count()}")
        print(f"Doctors: {Doctor.query.count()}")
        print(f"Departments: {Department.query.count()}")
        print(f"Admission Types: {AdmissionType.query.count()}")
        print(f"Patients: {Patient.query.count()}")

if __name__ == "__main__":
    init_db() 