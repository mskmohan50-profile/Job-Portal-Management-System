from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Job, Application
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jobportal_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Public routes ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    jobs = Job.query
    if search:
        jobs = jobs.filter(Job.title.ilike(f'%{search}%') | Job.company.ilike(f'%{search}%'))
    if location:
        jobs = jobs.filter(Job.location.ilike(f'%{location}%'))
    jobs = jobs.order_by(Job.id.desc()).all()
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('index.html', jobs=jobs, user=user, search=search, location=location)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    already_applied = False
    if user and user.role == 'seeker':
        already_applied = Application.query.filter_by(user_id=user.id, job_id=job_id).first() is not None
    return render_template('job_detail.html', job=job, user=user, already_applied=already_applied)


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
        user = User(
            username=username, email=email,
            password=generate_password_hash(password), role=role
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for(f'dashboard_{user.role}'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))


# ── Seeker routes ─────────────────────────────────────────────────────────────
@app.route('/dashboard/seeker')
@role_required('seeker')
def dashboard_seeker():
    user = User.query.get(session['user_id'])
    apps = Application.query.filter_by(user_id=user.id).all()
    applied_jobs = [(a, Job.query.get(a.job_id)) for a in apps]
    return render_template('dashboard_seeker.html', user=user, applied_jobs=applied_jobs)

@app.route('/apply/<int:job_id>', methods=['POST'])
@role_required('seeker')
def apply(job_id):
    existing = Application.query.filter_by(user_id=session['user_id'], job_id=job_id).first()
    if existing:
        flash('You have already applied for this job.', 'warning')
    else:
        db.session.add(Application(user_id=session['user_id'], job_id=job_id))
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    return redirect(url_for('job_detail', job_id=job_id))


# ── Employer routes ───────────────────────────────────────────────────────────
@app.route('/dashboard/employer')
@role_required('employer')
def dashboard_employer():
    user = User.query.get(session['user_id'])
    jobs = Job.query.filter_by(employer_id=user.id).order_by(Job.id.desc()).all()
    return render_template('dashboard_employer.html', user=user, jobs=jobs)

@app.route('/job/post', methods=['GET', 'POST'])
@role_required('employer')
def post_job():
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            company=request.form['company'],
            location=request.form['location'],
            salary=request.form['salary'],
            description=request.form['description'],
            employer_id=session['user_id']
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('dashboard_employer'))
    return render_template('post_job.html', user=User.query.get(session['user_id']))

@app.route('/job/edit/<int:job_id>', methods=['GET', 'POST'])
@role_required('employer')
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard_employer'))
    if request.method == 'POST':
        job.title = request.form['title']
        job.company = request.form['company']
        job.location = request.form['location']
        job.salary = request.form['salary']
        job.description = request.form['description']
        db.session.commit()
        flash('Job updated.', 'success')
        return redirect(url_for('dashboard_employer'))
    return render_template('post_job.html', user=User.query.get(session['user_id']), job=job)

@app.route('/job/delete/<int:job_id>', methods=['POST'])
@role_required('employer')
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        flash('Access denied.', 'danger')
    else:
        Application.query.filter_by(job_id=job_id).delete()
        db.session.delete(job)
        db.session.commit()
        flash('Job deleted.', 'info')
    return redirect(url_for('dashboard_employer'))

@app.route('/job/<int:job_id>/applicants')
@role_required('employer')
def view_applicants(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard_employer'))
    apps = Application.query.filter_by(job_id=job_id).all()
    applicants = [(a, User.query.get(a.user_id)) for a in apps]
    return render_template('applicants.html', job=job, applicants=applicants,
                           user=User.query.get(session['user_id']))

@app.route('/application/<int:app_id>/status', methods=['POST'])
@role_required('employer')
def update_status(app_id):
    app_obj = Application.query.get_or_404(app_id)
    job = Job.query.get(app_obj.job_id)
    if job.employer_id != session['user_id']:
        flash('Access denied.', 'danger')
    else:
        app_obj.status = request.form['status']
        db.session.commit()
        flash('Status updated.', 'success')
    return redirect(url_for('view_applicants', job_id=app_obj.job_id))


# ── Admin routes ──────────────────────────────────────────────────────────────
@app.route('/dashboard/admin')
@role_required('admin')
def dashboard_admin():
    user = User.query.get(session['user_id'])
    users = User.query.all()
    jobs = Job.query.order_by(Job.id.desc()).all()
    apps = Application.query.all()
    return render_template('dashboard_admin.html', user=user, users=users, jobs=jobs, apps=apps)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@role_required('admin')
def admin_delete_user(user_id):
    u = User.query.get_or_404(user_id)
    Application.query.filter_by(user_id=user_id).delete()
    db.session.delete(u)
    db.session.commit()
    flash('User deleted.', 'info')
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/delete_job/<int:job_id>', methods=['POST'])
@role_required('admin')
def admin_delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    Application.query.filter_by(job_id=job_id).delete()
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'info')
    return redirect(url_for('dashboard_admin'))


# ── Seed ──────────────────────────────────────────────────────────────────────
@app.route('/seed')
def seed():
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', email='admin@portal.com',
                            password=generate_password_hash('admin123'), role='admin'))
    if not User.query.filter_by(username='employer1').first():
        emp = User(username='employer1', email='emp@portal.com',
                   password=generate_password_hash('emp123'), role='employer')
        db.session.add(emp)
        db.session.flush()
        jobs_data = [
            ('Senior Python Developer', 'TechCorp India', 'Bangalore', '₹18-25 LPA', emp.id,
             'We are looking for an experienced Python developer with expertise in Django, FastAPI, and microservices architecture.'),
            ('React Frontend Engineer', 'StartupHub', 'Remote', '₹12-18 LPA', emp.id,
             'Join our fast-growing startup to build modern React applications with TypeScript and Tailwind CSS.'),
            ('Full Stack Developer', 'GlobalSoft', 'Chennai', '₹15-22 LPA', emp.id,
             'Full stack role requiring Node.js, React, MongoDB and AWS deployment experience.'),
        ]
        for t, c, l, s, eid, d in jobs_data:
            db.session.add(Job(title=t, company=c, location=l, salary=s, employer_id=eid, description=d))
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
