# ===========================================================================================
#                              SQLAlchemy Database with StudentDetails
# ===========================================================================================
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/resume'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Login register Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # e.g., "student", "company"

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

# # ------------------------------------------------------------
#                       Routes
# # ------------------------------------------------------------
# Home Page
@app.route('/')
def index():
    return render_template('index.html', user=current_user)

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form['role']

        # Ensure valid roles
        if role not in ['student', 'company']:
            flash('Invalid role selected', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')

            # Redirect based on user role
            if user.role == 'company':
                return redirect(url_for('companyDashboard'))
            elif user.role == 'student':
                return redirect(url_for('studentDashboard'))
            else:
                flash('Invalid role. Contact support.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Login failed. Check your credentials.', 'danger')
    return render_template('login.html')
# -----------------------------------------------------------------
# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
# ------------------------------------------------------------------
# Admin Dashboard Route
@app.route('/companyDashboard')
@login_required
def companyDashboard():  # Changed function name to adminDashboard
    if current_user.role == 'company':
        return render_template('companyDashboard.html', user=current_user)
    else:
        flash('Access Denied!', 'danger')
        return redirect(url_for('index'))

# -------------------------------------------------------------------
# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------------------------
# StudentDetails Model
class StudentDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    education = db.Column(db.String(500), nullable=True)
    skills = db.Column(db.String(500), nullable=True)
    contact = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    user = db.relationship('User', backref=db.backref('student_details', uselist=False))
    def __repr__(self):
        return f"StudentDetails('{self.education}', '{self.skills}', '{self.contact}')"

# ------------------------------------------------------------------------------------------
# Helper function for file uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ------------------------------------------------------------------------------------------
# Route: Student Dashboard
@app.route('/studentDashboard')
@login_required
def studentDashboard():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))
    student_details = StudentDetails.query.filter_by(user_id=current_user.id).first()
    return render_template('studentDashboard.html', user=current_user, details=student_details)

# ------------------------------------------------------------------------------------------
# Route: Create Student Details

@app.route('/create_student_details', methods=['GET', 'POST'])
@login_required
def create_student_details():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        education = request.form['education']
        skills = request.form['skills']
        contact = request.form['contact']
        address = request.form['address']
        # Save student details
        details = StudentDetails(
            user_id=current_user.id,
            education=education,
            skills=skills,
            contact=contact,
            address=address
            # resume=resume_filename
        )
        db.session.add(details)
        db.session.commit()
        flash('Details added successfully!', 'success')
        return redirect(url_for('studentDashboard'))

    return render_template('create_student_details.html')

# ------------------------------------------------------------------------------------------
# Route: Update Student Details
@app.route('/update_student_details', methods=['GET', 'POST'])
@login_required
def update_student_details():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    details = StudentDetails.query.filter_by(user_id=current_user.id).first()
    if not details:
        flash("No details found to update!", "danger")
        return redirect(url_for('create_student_details'))

    if request.method == 'POST':
        details.education = request.form['education']
        details.skills = request.form['skills']
        details.contact = request.form['contact']
        details.address = request.form['address']
        db.session.commit()
        flash('Details updated successfully!', 'success')
        return redirect(url_for('studentDashboard'))

    return render_template('update_student_details.html', details=details)

# ------------------------------------------------------------------------------------------
# Route: Delete Student Details
@app.route('/delete_student_details', methods=['POST'])
@login_required
def delete_student_details():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    details = StudentDetails.query.filter_by(user_id=current_user.id).first()
    if details:
        db.session.delete(details)
        db.session.commit()
        flash('Details deleted successfully!', 'info')
    else:
        flash("No details found to delete!", "danger")

    return redirect(url_for('studentDashboard'))

# ================================================================
#                    student profile 
# ================================================================
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(120), nullable=True)  # Store the profile picture filename
    user = db.relationship('User', backref=db.backref('profile', uselist=False))  # One-to-one relationship

    def __repr__(self):
        return f"Profile('{self.full_name}', '{self.profile_pic}')"


from werkzeug.utils import secure_filename
import os

app.config['UPLOAD_FOLDER'] = 'static/profile_pics'  # Folder where profile pictures will be stored
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image extensions

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# -----------------------------------------------------------------------------

@app.route('/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        full_name = request.form['full_name']
        bio = request.form['bio']
        
        # Handle file upload
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None  # Default profile picture if none is uploaded

        # Check the user's role (e.g., 'student' or 'company')
        if current_user.role == 'student':
            # If the user is a student, create the profile for the student
            profile = Profile(user_id=current_user.id, full_name=full_name, bio=bio, profile_pic=filename)
            db.session.add(profile)
            db.session.commit()
            flash('Profile created successfully!', 'success')
            return redirect(url_for('studentDashboard'))
        elif current_user.role == 'company':
            # If the user is a company, create a company-specific profile (optional)
            # You can add more fields specific to the company profile if needed.
            profile = Profile(user_id=current_user.id, full_name=full_name, bio=bio, profile_pic=filename)
            db.session.add(profile)
            db.session.commit()
            flash('Company profile created successfully!', 'success')
            return redirect(url_for('companyDashboard'))
        else:
            flash('Invalid role', 'danger')
            return redirect(url_for('home'))  # Redirect to a safe place like home page
        
    return render_template('create_profile.html')

# ------------------------------------------------------------------------------------

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    # Retrieve the current user's profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    # Ensure the user has a profile before proceeding
    if not profile:
        flash('Profile not found.', 'danger')
        return redirect(url_for('studentDashboard'))

    if request.method == 'POST':
        profile.full_name = request.form['full_name']
        profile.bio = request.form['bio']
        
        # Handle file upload for profile picture update
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile.profile_pic = filename  # Update the profile picture

        # Commit the changes to the database
        db.session.commit()

        # Handle different behaviors based on the role
        if current_user.role == 'student':
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('studentDashboard'))
        elif current_user.role == 'company':
            flash('Company profile updated successfully!', 'success')
            return redirect(url_for('companyDashboard'))
        else:
            flash('Invalid role', 'danger')
            return redirect(url_for('home'))  # Redirect to home if the role is invalid

    return render_template('update_profile.html', profile=profile)

# ------------------------------------------------------------------------------------
@app.route('/delete_profile', methods=['POST'])
@login_required
def delete_profile():
    # Retrieve the profile of the currently logged-in user
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    # If profile exists, proceed with deletion
    if profile:
        # Optionally, delete the profile picture from the server
        if profile.profile_pic:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile.profile_pic))
        
        # Delete the profile from the database
        db.session.delete(profile)
        db.session.commit()

        # Role-based logic for redirection and flash message
        if current_user.role == 'student':
            flash('Profile deleted successfully!', 'info')
            return redirect(url_for('studentDashboard'))
        elif current_user.role == 'company':
            flash('Company profile deleted successfully!', 'info')
            return redirect(url_for('companyDashboard'))
        else:
            flash('Invalid role', 'danger')
            return redirect(url_for('home'))  # Redirect to home if the role is invalid

    # If no profile is found for the user, handle it gracefully
    flash('No profile found to delete.', 'danger')
    return redirect(url_for('home'))  # Or redirect to a specific dashboard

# ================================resume===================================================

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)  # Resume file name
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Timestamp for upload

    user = db.relationship('User', backref=db.backref('resumes', lazy=True))  # Many-to-one relationship

# app.config['RESUME_UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['RESUME_UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'resumes')

app.config['ALLOWED_RESUME_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

# Ensure the folder exists
import os
if not os.path.exists(app.config['RESUME_UPLOAD_FOLDER']):
    os.makedirs(app.config['RESUME_UPLOAD_FOLDER'])

def allowed_resume_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_RESUME_EXTENSIONS']


@app.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['resume']
        if file and allowed_resume_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['RESUME_UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Save resume record to database
            resume = Resume(user_id=current_user.id, filename=filename)
            db.session.add(resume)
            db.session.commit()

            flash('Resume uploaded successfully!', 'success')
            return redirect(url_for('studentDashboard'))
        else:
            flash('Invalid file type. Only PDF, DOC, and DOCX are allowed.', 'danger')

    return render_template('upload_resume.html')

@app.route('/view_resumes')
@login_required
def view_resumes():
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    resumes = Resume.query.filter_by(user_id=current_user.id).all()
    return render_template('view_resumes.html', resumes=resumes)

@app.route('/update_resume/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def update_resume(resume_id):
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['resume']
        if file and allowed_resume_file(file.filename):
            # Remove old resume file
            old_filepath = os.path.join(app.config['RESUME_UPLOAD_FOLDER'], resume.filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

            # Save new resume file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['RESUME_UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Update resume record
            resume.filename = filename
            db.session.commit()

            flash('Resume updated successfully!', 'success')
            return redirect(url_for('studentDashboard'))
        else:
            flash('Invalid file type. Only PDF, DOC, and DOCX are allowed.', 'danger')

    return render_template('update_resume.html', resume=resume)

@app.route('/delete_resume/<int:resume_id>', methods=['POST'])
@login_required
def delete_resume(resume_id):
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))

    # Remove the file from the filesystem
    filepath = os.path.join(app.config['RESUME_UPLOAD_FOLDER'], resume.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Delete the record from the database
    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted successfully!', 'info')

    return redirect(url_for('studentDashboard'))

@app.route('/uploads/resumes/<filename>')
@login_required
def serve_resume(filename):
    if current_user.role != 'student':
        flash("Access Denied!", "danger")
        return redirect(url_for('index'))
    
    # Return the requested file from the uploads/resumes folder
    return send_from_directory(app.config['RESUME_UPLOAD_FOLDER'], filename)

# ====================vacancies==============================================

class Vacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_date = db.Column(db.DateTime, nullable=False)

    company = db.relationship('User', backref='vacancies')  # Assuming 'User' is the company model

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vacancy_id = db.Column(db.Integer, db.ForeignKey('vacancy.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Selected', 'Rejected'
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', backref='applications', foreign_keys=[student_id])  # Assuming 'User' is the student model
    vacancy = db.relationship('Vacancy', backref='applications', foreign_keys=[vacancy_id])

# -------------for cmp--------------------

# company can see created vacancies by itself 
@app.route('/company/vacancies')
@login_required
def view_company_vacancies():
    if current_user.role != 'company':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    # Fetch vacancies created by the logged-in company
    vacancies = Vacancy.query.filter_by(company_id=current_user.id).all()
    return render_template('view_company_vacancies.html', vacancies=vacancies)

# ------------------------------------------------------------------------

@app.route('/company/create_vacancy', methods=['GET', 'POST'])
@login_required
def create_vacancy():
    if current_user.role != 'company':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        last_date = request.form['last_date']

        # Create a new vacancy and add it to the database
        vacancy = Vacancy(
            company_id=current_user.id,
            title=title,
            description=description,
            location=location,
            last_date=datetime.strptime(last_date, '%Y-%m-%d')
        )
        db.session.add(vacancy)
        db.session.commit()
        flash('Vacancy created successfully!', 'success')
        return redirect(url_for('companyDashboard'))

    return render_template('create_vacancy.html')

# --------------------------------------------------------------

@app.route('/company/delete_vacancy/<int:vacancy_id>', methods=['POST'])
@login_required
def delete_vacancy(vacancy_id):
    if current_user.role != 'company':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    vacancy = Vacancy.query.get_or_404(vacancy_id)

    # Ensure the logged-in company is the one who created this vacancy
    if vacancy.company_id != current_user.id:
        flash('You cannot delete this vacancy. It does not belong to your company.', 'danger')
        return redirect(url_for('view_company_vacancies'))

    # Delete all applications related to this vacancy
    applications = Application.query.filter_by(vacancy_id=vacancy_id).all()
    for application in applications:
        db.session.delete(application)
    
    # Now delete the vacancy
    db.session.delete(vacancy)
    db.session.commit()

    flash('Vacancy deleted successfully!', 'success')
    return redirect(url_for('view_company_vacancies'))


# --------------------for std-----------------------
# all vacancies available for students 
@app.route('/student/vacancies')
@login_required
def student_vacancies():
    if current_user.role != 'student':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    # Fetch all available vacancies
    vacancies = Vacancy.query.all()
    return render_template('student_vacancies.html', vacancies=vacancies)

# --------------------------------------------------------------
@app.route('/student/apply/<int:vacancy_id>', methods=['POST'])
@login_required
def apply_vacancy(vacancy_id):
    if current_user.role != 'student':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    # Check if the student has already applied for the vacancy
    existing_application = Application.query.filter_by(vacancy_id=vacancy_id, student_id=current_user.id).first()
    if existing_application:
        flash('You have already applied for this vacancy!', 'warning')
        return redirect(url_for('student_vacancies'))

    # Create a new application with "Pending" status
    application = Application(student_id=current_user.id, vacancy_id=vacancy_id, status='Pending')
    db.session.add(application)
    db.session.commit()

    flash('Applied successfully! Your status is now pending.', 'success')
    return redirect(url_for('student_vacancies'))

# -------------------------------------------------------------------------------
@app.route('/student/applied_vacancies')
@login_required
def applied_vacancies():
    if current_user.role != 'student':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    # Fetch all applications by the logged-in student
    applications = Application.query.filter_by(student_id=current_user.id).all()
    return render_template('applied_vacancies.html', applications=applications)

# ----------------------------------------------------------------------------------
@app.route('/company/view_applications')
@login_required
def view_applications():
    if current_user.role != 'company':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    # Get all vacancies created by the company
    vacancies = Vacancy.query.filter_by(company_id=current_user.id).all()

    # Retrieve all applications for these vacancies
    applications = []
    for vacancy in vacancies:
        vacancy_applications = Application.query.filter_by(vacancy_id=vacancy.id).all()
        applications.extend(vacancy_applications)

    # Render the applications with student details
    return render_template('view_applications.html', applications=applications)


@app.route('/company/update_application_status/<int:application_id>', methods=['GET', 'POST'])
@login_required
def update_application_status(application_id):
    if current_user.role != 'company':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))

    application = Application.query.get_or_404(application_id)

    if request.method == 'POST':
        # Here, you'll handle the form submission to update the status
        new_status = request.form['status']  # assuming you're using a form with a 'status' field
        application.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}!', 'success')
        return redirect(url_for('view_applications'))  # Redirect back to the view applications page

    return render_template('update_application_status.html', application=application)

# ========================================================================================


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
