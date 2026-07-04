# Digital Canteen Automation System

Digital Canteen is a Flask + MySQL project with two web apps:

- `student_app.py` for students to browse the menu, manage a cart, and place orders
- `admin_app.py` for canteen staff to manage inventory and update order status

This repository is now set up for both local development and cloud deployment.

## Architecture

- Backend: Flask
- Database: MySQL
- Templates: Jinja2
- Production server: Gunicorn
- Deployment layout: two web services sharing one MySQL database

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and set real values:

```bash
copy .env.example .env
```

Required values:

- `FLASK_SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

### 3. Initialize the database

```bash
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql
```

### 4. Run both apps

Student app:

```bash
python student_app.py
```

Admin app:

```bash
python admin_app.py
```

Default local URLs:

- Student app: `http://127.0.0.1:5000`
- Admin app: `http://127.0.0.1:5001`

## Deployment

This project should be deployed as two separate Python web services connected to the same MySQL database.

### Included deployment files

- `render.yaml` defines two Render web services
- `wsgi_student.py` exposes the student app for Gunicorn
- `wsgi_admin.py` exposes the admin app for Gunicorn

### Render deployment

1. Push this repository to GitHub.
2. Create a managed MySQL database, or use an external MySQL provider.
3. In Render, create services from `render.yaml`.
4. Add the same database credentials to both services.
5. Set secure production values:

- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `SESSION_COOKIE_SECURE=true`
- `FLASK_SECRET_KEY=<strong-random-secret>`
- `ADMIN_USERNAME=<your-admin-user>`
- `ADMIN_PASSWORD=<your-admin-password>`
- `DB_HOST=<mysql-host>`
- `DB_PORT=3306`
- `DB_USER=<mysql-user>`
- `DB_PASSWORD=<mysql-password>`
- `DB_NAME=<database-name>`

6. Run `schema.sql` and `seed.sql` against the deployed database.
7. Check both health endpoints after deploy:

- Student: `/health`
- Admin: `/health`

### Start commands

Student service:

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi_student:app
```

Admin service:

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi_admin:app
```

## Production notes

- The app now fails fast if `FLASK_SECRET_KEY` is missing.
- The app now fails fast if `FLASK_SECRET_KEY` is weak or placeholder-like.
- The admin app rejects short production passwords.
- Session cookies can be marked secure in production with `SESSION_COOKIE_SECURE=true`.
- Ports are controlled by environment variables instead of hardcoded debug-only startup.
- The `daily_special` route redirects back into the menu page where specials are displayed.

## Important security reminder

Do not commit your real `.env` file. If the current `.env` contains real passwords, rotate them before publishing the repository.
