from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import case, func, text
from datetime import datetime, timedelta
import logging
import traceback
import os
import psycopg2
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
app.config['SECRET_KEY'] = 'your-actual-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:kalai123@localhost:5432/hospital'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class Admin(UserMixin, db.Model):
    __tablename__ = 'admini'
    loginid = db.Column(db.String(50), primary_key=True)
    passid = db.Column(db.String(50), nullable=False)

    def get_id(self):
        return str(self.loginid)  # PostgreSQL needs string IDs

class Doctor(db.Model):
    __tablename__ = 'doctordetails'
    username = db.Column(db.String(50), db.ForeignKey('admini.loginid'), primary_key=True)
    doctorname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))

class Department(db.Model):
    __tablename__ = 'department'
    deptid = db.Column(db.Integer, primary_key=True)
    deptname = db.Column(db.String(100), unique=True, nullable=False)

class Patient(db.Model):
    __tablename__ = 'patient'
    patientid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patientname = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.Text)

class Admission(db.Model):
    __tablename__ = 'admission'
    admissionid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admissiontype = db.Column(db.Integer, db.ForeignKey('admissiontype.admissiontypeid'))
    department = db.Column(db.Integer, db.ForeignKey('department.deptid'))
    patient = db.Column(db.Integer, db.ForeignKey('patient.patientid'))
    administrator = db.Column(db.String(50), db.ForeignKey('doctordetails.username'))
    condition = db.Column(db.Text)
    admissiondate = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    dischargedate = db.Column(db.DateTime(timezone=True))
    fee = db.Column(db.Numeric(10, 2))

class AdmissionType(db.Model):
    __tablename__ = 'admissiontype'
    admissiontypeid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admissiontypename = db.Column(db.String(50), unique=True, nullable=False)

class AdmissionDetails(db.Model):
    __tablename__ = 'admissiondetails'
    detailid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admissionid = db.Column(db.Integer, db.ForeignKey('admission.admissionid'), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    temperature = db.Column(db.Numeric(4, 1))
    blood_pressure = db.Column(db.String(20))
    pulse_rate = db.Column(db.Integer)
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.String(50), db.ForeignKey('doctordetails.username'))

class MedicalDetails(db.Model):
    __tablename__ = 'medical_details'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admission_id = db.Column(db.Integer, db.ForeignKey('admission.admissionid'), nullable=False)
    diagnosis = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    medications = db.Column(db.Text)
    notes = db.Column(db.Text)
    next_checkup = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# Error handling function
def handle_error(e, error_message, should_rollback=True):
    logger.error(f"{error_message}: {str(e)}\nTraceback: {traceback.format_exc()}")
    if should_rollback:
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {str(rollback_error)}")
    return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        logger.debug("Starting to fetch dashboard data")
        
        # Fetch summary statistics
        stats = {
            'patients': {
                'total': Patient.query.count(),
                'active': Admission.query.filter_by(dischargedate=None).count()
            },
            'doctors': {
                'total': Doctor.query.count(),
                'active': Doctor.query.filter(
                    Doctor.username.in_(
                        db.session.query(Admission.administrator)
                        .filter(Admission.dischargedate == None)
                        .distinct()
                    )
                ).count()
            },
            'departments': {
                'total': Department.query.count(),
                'with_patients': db.session.query(func.count(func.distinct(Admission.department)))
                    .filter(Admission.dischargedate == None)
                    .scalar() or 0
            },
            'beds': {
                'total': 200,
                'occupied': Admission.query.filter_by(dischargedate=None).count()
            }
        }
        logger.debug(f"Stats fetched: {stats}")
        
        # Fetch recent admissions
        try:
            recent_admissions = (Admission.query
                .order_by(Admission.admissiondate.desc())
                .limit(5)
                .all())
            logger.debug(f"Recent admissions fetched: {len(recent_admissions)}")
        except Exception as e:
            logger.error(f"Error fetching recent admissions: {str(e)}")
            recent_admissions = []
        
        # Fetch department statistics
        try:
            dept_stats = (Department.query
                .outerjoin(Admission, Department.deptid == Admission.department)
                .add_columns(
                    func.count(Admission.admissionid).label('total_admissions'),
                    func.sum(case([(Admission.dischargedate == None, 1)], else_=0)).label('active_patients')
                )
                .group_by(Department.deptid)
                .all())
            logger.debug(f"Department stats fetched: {len(dept_stats)}")
        except Exception as e:
            logger.error(f"Error fetching department stats: {str(e)}")
            dept_stats = []
        
        # Fetch doctor statistics
        try:
            doctor_stats = (Doctor.query
                .outerjoin(Admission, Doctor.username == Admission.administrator)
                .add_columns(
                    func.count(Admission.admissionid).label('total_patients'),
                    func.sum(case([(Admission.dischargedate == None, 1)], else_=0)).label('active_patients')
                )
                .group_by(Doctor.username)
                .all())
            logger.debug(f"Doctor stats fetched: {len(doctor_stats)}")
        except Exception as e:
            logger.error(f"Error fetching doctor stats: {str(e)}")
            doctor_stats = []
        
        return render_template('dashboard.html',
                            stats=stats,
                            recent_admissions=recent_admissions,
                            dept_stats=dept_stats,
                            doctor_stats=doctor_stats)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}\nTraceback: {traceback.format_exc()}")
        flash('Error loading dashboard data: ' + str(e))
        return render_template('dashboard.html', error=True, error_message=str(e))

@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    try:
        with db.session.begin():
            # Calculate current month's revenue
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue = db.session.query(func.sum(Admission.fee)).filter(
                Admission.admissiondate >= current_month
            ).scalar() or 0
            
            # Calculate admission trends
            today = datetime.utcnow().date()
            daily_admissions = []
            for i in range(7):
                date = today - timedelta(days=i)
                count = Admission.query.filter(
                    func.date(Admission.admissiondate) == date
                ).count()
                daily_admissions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            # Department occupancy
            dept_occupancy = []
            departments = Department.query.all()
            for dept in departments:
                active_patients = Admission.query.filter_by(
                    department=dept.deptid,
                    dischargedate=None
                ).count()
                capacity = 50  # This should be configured per department
                dept_occupancy.append({
                    'name': dept.deptname,
                    'occupancy': round((active_patients / capacity) * 100, 1)
                })
            
            return jsonify({
                'revenue': {
                    'monthly': float(monthly_revenue),
                    'formatted': f"${float(monthly_revenue):,.2f}"
                },
                'admission_trends': daily_admissions,
                'department_occupancy': dept_occupancy
            })
            
    except Exception as e:
        return handle_error(e, "Error fetching dashboard statistics")

@app.route('/api/dashboard/recent-activities')
@login_required
def get_recent_activities():
    try:
        with db.session.begin():
            # Get recent admissions
            recent_admissions = Admission.query.order_by(
                Admission.admissiondate.desc()
            ).limit(10).all()
            
            activities = []
            for admission in recent_admissions:
                patient = Patient.query.get(admission.patient)
                doctor = Doctor.query.get(admission.administrator)
                department = Department.query.get(admission.department)
                
                activities.append({
                    'type': 'admission',
                    'timestamp': admission.admissiondate.isoformat(),
                    'details': {
                        'patient_name': patient.patientname if patient else 'Unknown',
                        'doctor_name': doctor.doctorname if doctor else 'Unknown',
                        'department': department.deptname if department else 'Unknown',
                        'status': 'Active' if not admission.dischargedate else 'Discharged'
                    }
                })
            
            return jsonify(activities)
            
    except Exception as e:
        return handle_error(e, "Error fetching recent activities")

@app.route('/api/dashboard/alerts')
@login_required
def get_dashboard_alerts():
    try:
        with db.session.begin():
            alerts = []
            
            # Check bed capacity
            occupied_beds = Admission.query.filter_by(dischargedate=None).count()
            total_beds = 200  # This should come from configuration
            if occupied_beds / total_beds > 0.9:
                alerts.append({
                    'type': 'warning',
                    'message': 'Hospital bed capacity is above 90%',
                    'details': f'{occupied_beds} out of {total_beds} beds occupied'
                })
            
            # Check departments near capacity
            departments = Department.query.all()
            for dept in departments:
                active_patients = Admission.query.filter_by(
                    department=dept.deptid,
                    dischargedate=None
                ).count()
                capacity = 50  # This should be configured per department
                if active_patients / capacity > 0.9:
                    alerts.append({
                        'type': 'warning',
                        'message': f'{dept.deptname} department is near capacity',
                        'details': f'{active_patients} out of {capacity} beds occupied'
                    })
            
            return jsonify(alerts)
            
    except Exception as e:
        return handle_error(e, "Error fetching dashboard alerts")

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        loginid = request.form.get('loginid')
        passid = request.form.get('passid')
        user = Admin.query.get(loginid)
        
        if user and user.passid == passid:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/patients')
@login_required
def patients():
    return render_template('patients.html')

@app.route('/doctors')
@login_required
def doctors():
    return render_template('doctors.html')

@app.route('/departments')
@login_required
def departments():
    return render_template('departments.html')

@app.route('/admissions')
@login_required
def admissions():
    return render_template('admissions.html')

@app.route('/patients/<int:patient_id>')
@login_required
def patient_details(patient_id):
    try:
        # Get patient details
        patient = Patient.query.get_or_404(patient_id)
        
        # Get admission history
        admissions = (
            db.session.query(Admission, Department, Doctor, AdmissionType)
            .join(Department, Admission.department == Department.deptid)
            .join(Doctor, Admission.administrator == Doctor.username)
            .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
            .filter(Admission.patient == patient_id)
            .order_by(Admission.admissiondate.desc())
            .all()
        )
        
        # Calculate statistics
        total_admissions = len(admissions)
        total_spent = sum(float(adm[0].fee or 0) for adm in admissions)
        avg_stay = 0
        total_days = 0
        
        for admission, _, _, _ in admissions:
            if admission.dischargedate:
                days = (admission.dischargedate - admission.admissiondate).days
                total_days += days
        
        if total_admissions > 0:
            avg_stay = total_days / total_admissions
        
        # Get current admission if any
        current_admission = next(
            (adm for adm in admissions if not adm[0].dischargedate),
            None
        )
        
        return render_template('patient_details.html',
                           patient=patient,
                           admissions=admissions,
                           current_admission=current_admission,
                           stats={
                               'total_admissions': total_admissions,
                               'total_spent': total_spent,
                               'avg_stay': round(avg_stay, 1)
                           })
                           
    except Exception as e:
        logger.error(f"Error fetching patient details: {str(e)}\nTraceback: {traceback.format_exc()}")
        flash('Error loading patient details: ' + str(e))
        return redirect(url_for('patients'))

# API Routes for CRUD operations
@app.route('/api/patients', methods=['GET'])
@login_required
def get_patients():
    try:
        logger.debug("Fetching all patients")
        patients = Patient.query.all()
        logger.debug(f"Found {len(patients)} patients")
        
        result = []
        for p in patients:
            # Get admission status
            current_admission = Admission.query.filter_by(
                patient=p.patientid,
                dischargedate=None
            ).first()
            
            patient_data = {
                'id': p.patientid,
                'name': p.patientname,
                'condition': p.condition,
                'status': 'Admitted' if current_admission else 'Not Admitted'
            }
            result.append(patient_data)
            
        logger.debug("Successfully prepared patient data")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}\nTraceback: {traceback.format_exc()}")
        return handle_error(e, "Error fetching patients")

@app.route('/api/patients', methods=['POST'])
@login_required
def add_patient():
    try:
        data = request.json
        patient = Patient(
            patientname=data['name'],
            condition=data.get('condition')
        )
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'id': patient.patientid,
            'name': patient.patientname,
            'condition': patient.condition,
            'status': 'Not Admitted'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding patient: {str(e)}\nTraceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
@login_required
def update_patient(patient_id):
    try:
        patient = Patient.query.get_or_404(patient_id)
        data = request.json
        
        # Update patient fields
        patient.patientname = data.get('name', patient.patientname)
        patient.condition = data.get('condition', patient.condition)
        
        try:
            db.session.commit()
            logger.info("Successfully committed changes to database")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Database error occurred'}), 500
            
        return jsonify({
            'id': patient.patientid,
            'name': patient.patientname,
            'condition': patient.condition
        })
    except Exception as e:
        return handle_error(e, "Error updating patient")

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
@login_required
def delete_patient(patient_id):
    try:
        with db.session.begin():
            patient = Patient.query.get_or_404(patient_id)
            db.session.delete(patient)
            db.session.commit()
            return jsonify({'message': 'Patient deleted successfully'})
    except Exception as e:
        return handle_error(e, "Error deleting patient")

@app.route('/api/statistics/patients')
@login_required
def get_patient_statistics():
    try:
        total_patients = Patient.query.count()
        
        # Calculate trend (comparing with last month)
        last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        
        current_month_patients = Patient.query.filter(
            Patient.patientid.in_(
                db.session.query(Admission.patient)
                .filter(Admission.admissiondate >= datetime.utcnow().replace(day=1))
                .distinct()
            )
        ).count()
        
        last_month_patients = Patient.query.filter(
            Patient.patientid.in_(
                db.session.query(Admission.patient)
                .filter(Admission.admissiondate >= last_month_start)
                .filter(Admission.admissiondate < datetime.utcnow().replace(day=1))
                .distinct()
            )
        ).count()
        
        trend = 0
        if last_month_patients > 0:
            trend = ((current_month_patients - last_month_patients) / last_month_patients) * 100
        
        return jsonify({
            'total': total_patients,
            'trend': round(trend, 1)
        })
    except Exception as e:
        return handle_error(e, "Error fetching patient statistics")

@app.route('/api/statistics/admissions')
@login_required
def get_admission_statistics():
    try:
        total_active = Admission.query.filter_by(dischargedate=None).count()
        
        # Calculate trend
        today = datetime.utcnow().date()
        today_admissions = Admission.query.filter(
            func.date(Admission.admissiondate) == today
        ).count()
        
        yesterday = today - timedelta(days=1)
        yesterday_admissions = Admission.query.filter(
            func.date(Admission.admissiondate) == yesterday
        ).count()
        
        trend = 0
        if yesterday_admissions > 0:
            trend = ((today_admissions - yesterday_admissions) / yesterday_admissions) * 100
        
        return jsonify({
            'active': total_active,
            'today': today_admissions,
            'trend': round(trend, 1)
        })
    except Exception as e:
        return handle_error(e, "Error fetching admission statistics")

@app.route('/api/statistics/doctors')
@login_required
def get_doctor_statistics():
    try:
        total_doctors = Doctor.query.count()
        active_doctors = Doctor.query.filter(
            Doctor.username.in_(
                db.session.query(Admission.administrator)
                .filter(Admission.dischargedate == None)
                .distinct()
            )
        ).count()
        
        # Get detailed doctor stats
        doctor_stats = []
        doctors = Doctor.query.all()
        for doc in doctors:
            active_patients = Admission.query.filter_by(
                administrator=doc.username,
                dischargedate=None
            ).count()
            
            doctor_stats.append({
                'name': doc.doctorname,
                'department': 'General',  # You might want to add department to doctor model
                'active_patients': active_patients,
                'todays_appointments': 0  # Add appointment logic if needed
            })
        
        return jsonify(doctor_stats)
    except Exception as e:
        return handle_error(e, "Error fetching doctor statistics")

@app.route('/api/statistics/departments')
@login_required
def get_department_statistics():
    try:
        departments = Department.query.all()
        stats = []
        
        for dept in departments:
            active_patients = Admission.query.filter_by(
                department=dept.deptid,
                dischargedate=None
            ).count()
            
            total_revenue = db.session.query(func.sum(Admission.fee)).filter(
                Admission.department == dept.deptid,
                Admission.admissiondate >= datetime.utcnow().replace(day=1)
            ).scalar() or 0
            
            stats.append({
                'name': dept.deptname,
                'active_patients': active_patients,
                'occupancy': round((active_patients / 50) * 100, 1),  # Assuming 50 beds per department
                'revenue': float(total_revenue)
            })
        
        return jsonify(stats)
    except Exception as e:
        return handle_error(e, "Error fetching department statistics")

@app.route('/api/statistics/beds')
@login_required
def get_bed_statistics():
    try:
        total_beds = 200  # This should come from configuration
        occupied_beds = Admission.query.filter_by(dischargedate=None).count()
        available_beds = total_beds - occupied_beds
        
        return jsonify({
            'total': total_beds,
            'occupied': occupied_beds,
            'available': available_beds
        })
    except Exception as e:
        return handle_error(e, "Error fetching bed statistics")

@app.route('/api/statistics/revenue')
@login_required
def get_revenue_statistics():
    try:
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.session.query(func.sum(Admission.fee)).filter(
            Admission.admissiondate >= current_month
        ).scalar() or 0
        
        last_month = current_month - timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        last_month_revenue = db.session.query(func.sum(Admission.fee)).filter(
            Admission.admissiondate >= last_month_start,
            Admission.admissiondate < current_month
        ).scalar() or 0
        
        trend = 0
        if last_month_revenue > 0:
            trend = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100
            
        return jsonify({
            'monthly': float(monthly_revenue),
            'formatted': f"${float(monthly_revenue):,.2f}",
            'trend': round(trend, 1)
        })
    except Exception as e:
        return handle_error(e, "Error fetching revenue statistics")

@app.route('/api/statistics/doctors/count')
@login_required
def get_doctor_count():
    try:
        total_doctors = Doctor.query.count()
        active_doctors = Doctor.query.filter(
            Doctor.username.in_(
                db.session.query(Admission.administrator)
                .filter(Admission.dischargedate == None)
                .distinct()
            )
        ).count()
        
        return jsonify({
            'total': total_doctors,
            'active': active_doctors
        })
    except Exception as e:
        return handle_error(e, "Error fetching doctor count")

@app.route('/admissions/<int:admission_id>')
@login_required
def admission_details(admission_id):
    try:
        # Get admission details with related information
        admission_data = (
            db.session.query(
                Admission,
                Patient,
                Doctor,
                Department,
                AdmissionType
            )
            .join(Patient, Admission.patient == Patient.patientid)
            .join(Doctor, Admission.administrator == Doctor.username)
            .join(Department, Admission.department == Department.deptid)
            .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
            .filter(Admission.admissionid == admission_id)
            .first_or_404()
        )
        
        admission, patient, doctor, department, admission_type = admission_data
        
        # Calculate length of stay
        length_of_stay = None
        if admission.dischargedate:
            length_of_stay = (admission.dischargedate - admission.admissiondate).days
        else:
            length_of_stay = (datetime.utcnow() - admission.admissiondate).days
            
        return render_template(
            'admission_details.html',
            admission=admission,
            patient=patient,
            doctor=doctor,
            department=department,
            admission_type=admission_type,
            length_of_stay=length_of_stay
        )
        
    except Exception as e:
        logger.error(f"Error fetching admission details: {str(e)}\nTraceback: {traceback.format_exc()}")
        flash('Error loading admission details: ' + str(e))
        return redirect(url_for('admissions'))

@app.route('/api/admissions/<int:admission_id>')
@login_required
def get_admission_details(admission_id):
    try:
        # Get admission with related information
        admission_data = (
            db.session.query(
                Admission,
                Patient,
                Doctor,
                Department,
                AdmissionType
            )
            .join(Patient, Admission.patient == Patient.patientid)
            .join(Doctor, Admission.administrator == Doctor.username)
            .join(Department, Admission.department == Department.deptid)
            .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
            .filter(Admission.admissionid == admission_id)
            .first_or_404()
        )
        
        admission, patient, doctor, department, admission_type = admission_data
        
        # Calculate length of stay
        length_of_stay = None
        if admission.dischargedate:
            length_of_stay = (admission.dischargedate - admission.admissiondate).days
        else:
            length_of_stay = (datetime.utcnow() - admission.admissiondate).days
            
        return jsonify({
            'id': admission.admissionid,
            'patient': {
                'id': patient.patientid,
                'name': patient.patientname,
                'condition': patient.condition
            },
            'doctor': {
                'username': doctor.username,
                'name': doctor.doctorname,
                'email': doctor.email
            },
            'department': {
                'id': department.deptid,
                'name': department.deptname
            },
            'admission_type': {
                'id': admission_type.admissiontypeid,
                'name': admission_type.admissiontypename
            },
            'condition': admission.condition,
            'admission_date': admission.admissiondate.isoformat(),
            'discharge_date': admission.dischargedate.isoformat() if admission.dischargedate else None,
            'fee': float(admission.fee) if admission.fee else 0,
            'length_of_stay': length_of_stay,
            'status': 'Active' if not admission.dischargedate else 'Discharged'
        })
        
    except Exception as e:
        return handle_error(e, "Error fetching admission details")

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/reports/admissions')
@login_required
def get_admission_report():
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = db.session.query(
            Admission,
            Patient,
            Department,
            Doctor,
            AdmissionType
        ).join(Patient, Admission.patient == Patient.patientid)\
         .join(Department, Admission.department == Department.deptid)\
         .join(Doctor, Admission.administrator == Doctor.username)\
         .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Admission.admissiondate >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Admission.admissiondate <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        admissions = query.all()
        
        # Calculate statistics
        total_admissions = len(admissions)
        total_revenue = sum(admission[0].fee for admission in admissions if admission[0].fee)
        active_admissions = len([a for a in admissions if not a[0].dischargedate])
        
        # Department-wise breakdown
        dept_stats = {}
        for admission, patient, dept, doctor, adm_type in admissions:
            if dept.deptname not in dept_stats:
                dept_stats[dept.deptname] = {
                    'count': 0,
                    'revenue': 0,
                    'active': 0
                }
            dept_stats[dept.deptname]['count'] += 1
            dept_stats[dept.deptname]['revenue'] += float(admission.fee or 0)
            if not admission.dischargedate:
                dept_stats[dept.deptname]['active'] += 1
        
        # Admission type breakdown
        type_stats = {}
        for admission, patient, dept, doctor, adm_type in admissions:
            if adm_type.admissiontypename not in type_stats:
                type_stats[adm_type.admissiontypename] = 0
            type_stats[adm_type.admissiontypename] += 1
        
        return jsonify({
            'total_admissions': total_admissions,
            'total_revenue': float(total_revenue),
            'active_admissions': active_admissions,
            'department_stats': dept_stats,
            'type_stats': type_stats,
            'admissions': [{
                'id': admission.admissionid,
                'patient_name': patient.patientname,
                'department': dept.deptname,
                'doctor': doctor.doctorname,
                'type': adm_type.admissiontypename,
                'admission_date': admission.admissiondate.isoformat(),
                'discharge_date': admission.dischargedate.isoformat() if admission.dischargedate else None,
                'condition': admission.condition,
                'fee': float(admission.fee or 0)
            } for admission, patient, dept, doctor, adm_type in admissions]
        })
    except Exception as e:
        return handle_error(e, "Error generating admission report")

@app.route('/api/reports/revenue')
@login_required
def get_revenue_report():
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = db.session.query(
            func.date(Admission.admissiondate).label('date'),
            func.count(Admission.admissionid).label('count'),
            func.sum(Admission.fee).label('revenue')
        ).group_by(func.date(Admission.admissiondate))
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Admission.admissiondate >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Admission.admissiondate <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        daily_stats = query.all()
        
        # Calculate totals
        total_revenue = sum(stat.revenue for stat in daily_stats if stat.revenue)
        total_admissions = sum(stat.count for stat in daily_stats)
        
        return jsonify({
            'total_revenue': float(total_revenue),
            'total_admissions': total_admissions,
            'daily_stats': [{
                'date': stat.date.isoformat(),
                'count': stat.count,
                'revenue': float(stat.revenue or 0)
            } for stat in daily_stats]
        })
    except Exception as e:
        return handle_error(e, "Error generating revenue report")

@app.route('/api/reports/departments')
@login_required
def get_department_report():
    try:
        # Get department statistics
        dept_stats = db.session.query(
            Department.deptname,
            func.count(Admission.admissionid).label('total_admissions'),
            func.sum(case([(Admission.dischargedate == None, 1)], else_=0)).label('active_patients'),
            func.sum(Admission.fee).label('total_revenue')
        ).outerjoin(Admission, Department.deptid == Admission.department)\
         .group_by(Department.deptname)\
         .all()
        
        return jsonify([{
            'department': stat.deptname,
            'total_admissions': stat.total_admissions,
            'active_patients': stat.active_patients,
            'total_revenue': float(stat.total_revenue or 0)
        } for stat in dept_stats])
    except Exception as e:
        return handle_error(e, "Error generating department report")

@app.route('/api/admission-types')
@login_required
def get_admission_types():
    try:
        types = AdmissionType.query.all()
        return jsonify([{
            'id': t.admissiontypeid,
            'name': t.admissiontypename
        } for t in types])
    except Exception as e:
        return handle_error(e, "Error fetching admission types")

@app.route('/api/admissions/<int:admission_id>/discharge', methods=['POST'])
@login_required
def discharge_patient(admission_id):
    try:
        data = request.json
        admission = Admission.query.get_or_404(admission_id)
        
        if admission.dischargedate:
            return jsonify({'error': 'Patient is already discharged'}), 400
            
        admission.dischargedate = datetime.utcnow()
        admission.fee = data.get('fee', admission.fee)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Patient discharged successfully'
        })
    except Exception as e:
        return handle_error(e, "Error discharging patient")

@app.route('/api/admissions/<int:admission_id>/notes', methods=['GET'])
@login_required
def get_admission_notes(admission_id):
    try:
        # This is a placeholder - you'll need to create a Notes model and table
        return jsonify([])
    except Exception as e:
        return handle_error(e, "Error fetching admission notes")

@app.route('/api/admissions/<int:admission_id>/notes', methods=['POST'])
@login_required
def add_admission_note(admission_id):
    try:
        # This is a placeholder - you'll need to create a Notes model and table
        return jsonify({
            'success': True,
            'message': 'Note added successfully'
        })
    except Exception as e:
        return handle_error(e, "Error adding admission note")

@app.route('/api/admissions', methods=['GET'])
@login_required
def get_admissions():
    try:
        # Get filter parameters
        status = request.args.get('status')
        department = request.args.get('department')
        doctor = request.args.get('doctor')
        date = request.args.get('date')
        
        # Build query
        query = Admission.query
        
        if status == 'active':
            query = query.filter_by(dischargedate=None)
        elif status == 'discharged':
            query = query.filter(Admission.dischargedate != None)
            
        if department:
            query = query.filter_by(department=department)
            
        if doctor:
            query = query.filter_by(administrator=doctor)
            
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            query = query.filter(
                func.date(Admission.admissiondate) == date_obj.date()
            )
        
        # Get results
        admissions = query.order_by(Admission.admissiondate.desc()).all()
        result = []
        
        for admission in admissions:
            patient = Patient.query.get(admission.patient)
            doctor = Doctor.query.get(admission.administrator)
            department = Department.query.get(admission.department)
            admission_type = AdmissionType.query.get(admission.admissiontype)
            
            result.append({
                'id': admission.admissionid,
                'patient_name': patient.patientname if patient else 'Unknown',
                'doctor_name': doctor.doctorname if doctor else 'Unknown',
                'department_name': department.deptname if department else 'Unknown',
                'admission_type': admission_type.admissiontypename if admission_type else 'Unknown',
                'admission_date': admission.admissiondate.isoformat(),
                'discharge_date': admission.dischargedate.isoformat() if admission.dischargedate else None,
                'condition': admission.condition,
                'fee': float(admission.fee) if admission.fee else 0
            })
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Error fetching admissions")

@app.route('/api/admissions', methods=['POST'])
@login_required
def create_admission():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['patient_id', 'department_id', 'doctor_username', 'admission_type_id']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
            
        # Validate that referenced entities exist
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({'error': f'Patient with ID {data["patient_id"]} not found'}), 404
            
        department = Department.query.get(data['department_id'])
        if not department:
            return jsonify({'error': f'Department with ID {data["department_id"]} not found'}), 404
            
        doctor = Doctor.query.get(data['doctor_username'])
        if not doctor:
            return jsonify({'error': f'Doctor with username {data["doctor_username"]} not found'}), 404
            
        admission_type = AdmissionType.query.get(data['admission_type_id'])
        if not admission_type:
            return jsonify({'error': f'Admission type with ID {data["admission_type_id"]} not found'}), 404
        
        # Check if patient already has an active admission
        active_admission = Admission.query.filter_by(
            patient=data['patient_id'],
            dischargedate=None
        ).first()
        if active_admission:
            return jsonify({'error': 'Patient already has an active admission'}), 400
        
        # Create new admission
        admission = Admission(
            patient=data['patient_id'],
            department=data['department_id'],
            administrator=data['doctor_username'],
            admissiontype=data['admission_type_id'],
            condition=data.get('condition', ''),
            fee=data.get('fee', 0),
            admissiondate=datetime.utcnow()
        )
        
        db.session.add(admission)
        db.session.commit()
        
        return jsonify({
            'id': admission.admissionid,
            'message': 'Admission created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating admission: {str(e)}\nTraceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admissions/<int:admission_id>/details', methods=['GET'])
@login_required
def get_admission_medical_details(admission_id):
    try:
        details = AdmissionDetails.query.filter_by(admissionid=admission_id)\
            .order_by(AdmissionDetails.timestamp.desc()).all()
        
        result = []
        for detail in details:
            doctor = Doctor.query.get(detail.recorded_by)
            result.append({
                'id': detail.detailid,
                'timestamp': detail.timestamp.isoformat(),
                'temperature': float(detail.temperature) if detail.temperature else None,
                'blood_pressure': detail.blood_pressure,
                'pulse_rate': detail.pulse_rate,
                'notes': detail.notes,
                'recorded_by': {
                    'username': doctor.username,
                    'name': doctor.doctorname
                } if doctor else None
            })
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Error fetching admission details")

@app.route('/api/admissions/<int:admission_id>/details', methods=['POST'])
@login_required
def add_admission_detail(admission_id):
    try:
        data = request.json
        
        detail = AdmissionDetails(
            admissionid=admission_id,
            temperature=data.get('temperature'),
            blood_pressure=data.get('blood_pressure'),
            pulse_rate=data.get('pulse_rate'),
            notes=data.get('notes'),
            recorded_by=current_user.get_id()
        )
        
        db.session.add(detail)
        db.session.commit()
        
        return jsonify({
            'id': detail.detailid,
            'message': 'Detail added successfully'
        })
    except Exception as e:
        return handle_error(e, "Error adding admission detail")

@app.route('/doctors/<string:username>')
@login_required
def doctor_details(username):
    try:
        # Get doctor details
        doctor = Doctor.query.get_or_404(username)
        
        # Get active patients under this doctor
        active_patients = (
            db.session.query(Admission, Patient)
            .join(Patient, Admission.patient == Patient.patientid)
            .filter(Admission.administrator == username)
            .filter(Admission.dischargedate == None)
            .all()
        )
        
        # Get admission history
        admission_history = (
            db.session.query(Admission, Patient, Department, AdmissionType)
            .join(Patient, Admission.patient == Patient.patientid)
            .join(Department, Admission.department == Department.deptid)
            .join(AdmissionType, Admission.admissiontype == AdmissionType.admissiontypeid)
            .filter(Admission.administrator == username)
            .order_by(Admission.admissiondate.desc())
            .all()
        )
        
        # Calculate statistics
        total_patients = len(admission_history)
        current_patients = len(active_patients)
        total_discharged = sum(1 for adm in admission_history if adm[0].dischargedate)
        
        return render_template(
            'doctor_details.html',
            doctor=doctor,
            active_patients=active_patients,
            admission_history=admission_history,
            stats={
                'total_patients': total_patients,
                'current_patients': current_patients,
                'total_discharged': total_discharged
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching doctor details: {str(e)}\nTraceback: {traceback.format_exc()}")
        flash('Error loading doctor details: ' + str(e))
        return redirect(url_for('doctors'))

@app.route('/api/doctors', methods=['GET'])
@login_required
def get_doctors():
    try:
        doctors = Doctor.query.all()
        result = []
        
        for doctor in doctors:
            # Get active patients count
            active_patients = Admission.query.filter_by(
                administrator=doctor.username,
                dischargedate=None
            ).count()
            
            # Get total patients count
            total_patients = Admission.query.filter_by(
                administrator=doctor.username
            ).count()
            
            result.append({
                'username': doctor.username,
                'name': doctor.doctorname,
                'email': doctor.email,
                'active_patients': active_patients,
                'total_patients': total_patients
            })
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Error fetching doctors")

@app.route('/api/doctors', methods=['POST'])
@login_required
def add_doctor():
    try:
        data = request.json
        
        # First create admin entry
        admin = Admin(
            loginid=data['username'],
            passid=data['password']
        )
        
        # Then create doctor entry
        doctor = Doctor(
            username=data['username'],
            doctorname=data['name'],
            email=data.get('email')
        )
        
        db.session.add(admin)
        db.session.add(doctor)
        db.session.commit()
        
        return jsonify({
            'username': doctor.username,
            'name': doctor.doctorname,
            'email': doctor.email
        })
    except Exception as e:
        return handle_error(e, "Error adding doctor")

@app.route('/api/doctors/<string:username>', methods=['PUT'])
@login_required
def update_doctor(username):
    try:
        doctor = Doctor.query.get_or_404(username)
        data = request.json
        
        doctor.doctorname = data.get('name', doctor.doctorname)
        doctor.email = data.get('email', doctor.email)
        
        db.session.commit()
        
        return jsonify({
            'username': doctor.username,
            'name': doctor.doctorname,
            'email': doctor.email
        })
    except Exception as e:
        return handle_error(e, "Error updating doctor")

@app.route('/api/doctors/<string:username>', methods=['DELETE'])
@login_required
def delete_doctor(username):
    try:
        # Check if doctor has active patients
        active_patients = Admission.query.filter_by(
            administrator=username,
            dischargedate=None
        ).count()
        
        if active_patients > 0:
            return jsonify({
                'error': 'Cannot delete doctor with active patients'
            }), 400
        
        # Delete doctor and admin entries
        doctor = Doctor.query.get_or_404(username)
        admin = Admin.query.get_or_404(username)
        
        db.session.delete(doctor)
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Doctor deleted successfully'
        })
    except Exception as e:
        return handle_error(e, "Error deleting doctor")

@app.route('/api/departments', methods=['GET'])
@login_required
def get_departments():
    try:
        departments = Department.query.all()
        result = []
        
        for dept in departments:
            # Get active patients count
            active_patients = Admission.query.filter_by(
                department=dept.deptid,
                dischargedate=None
            ).count()
            
            # Get total admissions
            total_admissions = Admission.query.filter_by(
                department=dept.deptid
            ).count()
            
            # Calculate occupancy
            capacity = 50  # This should be configured per department
            occupancy = round((active_patients / capacity) * 100, 1)
            
            # Calculate monthly revenue
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue = db.session.query(func.sum(Admission.fee)).filter(
                Admission.department == dept.deptid,
                Admission.admissiondate >= current_month
            ).scalar() or 0
            
            result.append({
                'id': dept.deptid,
                'name': dept.deptname,
                'active_patients': active_patients,
                'total_admissions': total_admissions,
                'occupancy': occupancy,
                'revenue': float(monthly_revenue)
            })
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Error fetching departments")

@app.route('/api/departments', methods=['POST'])
@login_required
def add_department():
    try:
        data = request.json
        department = Department(deptname=data['name'])
        db.session.add(department)
        db.session.commit()
        
        return jsonify({
            'id': department.deptid,
            'name': department.deptname
        })
    except Exception as e:
        return handle_error(e, "Error adding department")

@app.route('/api/departments/<int:dept_id>', methods=['PUT'])
@login_required
def update_department(dept_id):
    try:
        department = Department.query.get_or_404(dept_id)
        data = request.json
        
        department.deptname = data.get('name', department.deptname)
        db.session.commit()
        
        return jsonify({
            'id': department.deptid,
            'name': department.deptname
        })
    except Exception as e:
        return handle_error(e, "Error updating department")

@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@login_required
def delete_department(dept_id):
    try:
        # Check if department has active patients
        active_patients = Admission.query.filter_by(
            department=dept_id,
            dischargedate=None
        ).count()
        
        if active_patients > 0:
            return jsonify({
                'error': 'Cannot delete department with active patients'
            }), 400
        
        department = Department.query.get_or_404(dept_id)
        db.session.delete(department)
        db.session.commit()
        
        return jsonify({
            'message': 'Department deleted successfully'
        })
    except Exception as e:
        return handle_error(e, "Error deleting department")

@app.route('/api/statistics/departments/count')
@login_required
def get_department_count():
    try:
        total_departments = Department.query.count()
        active_departments = Department.query.filter(
            Department.deptid.in_(
                db.session.query(Admission.department)
                .filter(Admission.dischargedate == None)
                .distinct()
            )
        ).count()
        
        total_patients = Admission.query.filter_by(dischargedate=None).count()
        
        return jsonify({
            'total': total_departments,
            'active': active_departments,
            'patients': total_patients
        })
    except Exception as e:
        return handle_error(e, "Error fetching department count")

@app.route('/api/recent-admissions')
@login_required
def get_recent_admissions():
    try:
        filter_type = request.args.get('filter', 'all')  # Default to 'all'
        
        # Base query
        query = (db.session.query(
            Admission, Patient, Department, Doctor
        ).join(
            Patient, Admission.patient == Patient.patientid
        ).join(
            Department, Admission.department == Department.deptid
        ).join(
            Doctor, Admission.administrator == Doctor.username
        ))
        
        # Apply time filter
        today = datetime.utcnow().date()
        if filter_type == 'today':
            query = query.filter(func.date(Admission.admissiondate) == today)
        elif filter_type == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(func.date(Admission.admissiondate) >= week_ago)
            
        # Get results ordered by admission date
        admissions = query.order_by(Admission.admissiondate.desc()).limit(10).all()
        
        result = [{
            'id': adm.admissionid,
            'patient_name': patient.patientname,
            'department': dept.deptname,
            'doctor': doctor.doctorname,
            'admission_date': adm.admissiondate.isoformat(),
            'status': 'Active' if not adm.dischargedate else 'Discharged'
        } for adm, patient, dept, doctor in admissions]
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Error fetching recent admissions")

@app.route('/api/admissions/<int:admission_id>/medical-details', methods=['PUT'])
@login_required
def update_medical_details(admission_id):
    try:
        data = request.json
        logger.debug(f"Received medical details update: {data}")
        
        # Validate required fields
        required_fields = ['diagnosis', 'symptoms', 'treatment']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

            
        # Get or create medical details
        medical_detail = MedicalDetails.query.filter_by(admission_id=admission_id).first()
        if not medical_detail:
            medical_detail = MedicalDetails(admission_id=admission_id)
            db.session.add(medical_detail)
        
        # Update fields
        medical_detail.diagnosis = data['diagnosis']
        medical_detail.symptoms = data['symptoms']
        medical_detail.treatment = data['treatment']
        medical_detail.medications = data.get('medications')
        medical_detail.notes = data.get('notes')
        medical_detail.next_checkup = datetime.fromisoformat(data['next_checkup']) if data.get('next_checkup') else None
        
        try:
            db.session.commit()
            logger.info("Successfully committed changes to database")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Database error occurred'}), 500
            
        return jsonify({
            'success': True,
            'message': 'Medical details updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating medical details: {str(e)}")
        return handle_error(e, "Error updating medical details")

@app.route('/api/admissions/<int:admission_id>/medical-details', methods=['GET'])
@login_required
def get_medical_details(admission_id):
    try:
        medical_detail = MedicalDetails.query.filter_by(admission_id=admission_id).first()
        
        if not medical_detail:
            return jsonify({
                'diagnosis': '',
                'symptoms': '',
                'treatment': '',
                'medications': '',
                'notes': '',
                'next_checkup': None
            })
        
        return jsonify({
            'diagnosis': medical_detail.diagnosis,
            'symptoms': medical_detail.symptoms,
            'treatment': medical_detail.treatment,
            'medications': medical_detail.medications,
            'notes': medical_detail.notes,
            'next_checkup': medical_detail.next_checkup.isoformat() if medical_detail.next_checkup else None
        })
        
    except Exception as e:
        return handle_error(e, "Error fetching medical details")

@app.route('/api/test-data')
def test_data():
    # Example query to check stored data
    medical_details = MedicalDetails.query.all()
    return jsonify([{
        'id': md.id,
        'diagnosis': md.diagnosis,
        'symptoms': md.symptoms,
        'treatment': md.treatment
    } for md in medical_details])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)