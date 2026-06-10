# ⚡ JobPortal — Flask Job Board

Full-stack job portal with role-based access for **Job Seekers**, **Employers**, and **Admins**.

## Tech Stack
- Python, Flask, SQLAlchemy, SQLite, Jinja2, Custom CSS

## Setup
```bash
pip install flask flask-sqlalchemy werkzeug
python app.py
# Visit → http://127.0.0.1:5000
```

## Seed Data
Visit `/seed` once to load sample jobs, then log in with:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Employer | `employer1` | `emp123` |
| Seeker | `seeker1` | `seek123` |

## Features
- Browse & search jobs
- Apply to jobs (seekers)
- Post, edit, delete jobs (employers)
- Review & update applicant status
- Admin panel for full oversight
- Password hashing, session auth, flash messages

## Project Structure
```
jobportal/
├── app.py
├── models.py
├── static/style.css
└── templates/
    ├── base.html, index.html, login.html, register.html
    ├── job_detail.html, post_job.html, applicants.html
    └── dashboard_seeker/employer/admin.html
```

## Author
[GitHub](https://github.com/mskmohan50-profile) · [LinkedIn](https://linkedin.com/in/mohan-raj-g-6670b7299)
