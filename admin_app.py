from flask import Flask, render_template, request, url_for, redirect, flash, session
from datetime import datetime
from functools import wraps
import os
from dotenv import load_dotenv
# Import shared database functions from db_config.py
# MAKE SURE db_config.py IS IN THE SAME FOLDER!
from db_config import fetch_all, fetch_one, execute_query

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Do not keep any real secret in source — require users to set FLASK_SECRET_KEY in .env
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

# Admin Credentials from .env (no sensitive defaults)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Fail fast if required environment variables are missing
missing_env = []
if not app.secret_key:
    missing_env.append('FLASK_SECRET_KEY')
if not ADMIN_USERNAME:
    missing_env.append('ADMIN_USERNAME')
if not ADMIN_PASSWORD:
    missing_env.append('ADMIN_PASSWORD')
if missing_env:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_env)}.\nPlease copy .env.example to .env and set the values before running the app.")

# --- Context Processor (Prevents Footer Error) ---
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Admin access required.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Routes ---

@app.route('/')
def index():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # 1. Fetch Menu Items
    all_items = fetch_all("SELECT * FROM item ORDER BY category, item_name")
    
    # 2. Fetch Pending Orders
    pending_orders = fetch_all("""
        SELECT oi.order_id, oi.order_date, oi.order_time, oi.total_amount, oi.status, s.name as student_name
        FROM order_info oi
        JOIN student s ON oi.student_id = s.student_id
        WHERE oi.status = 'Pending'
        ORDER BY oi.order_date ASC, oi.order_time ASC
    """)
    
    # 3. Fetch Items for each Order
    for order in pending_orders:
        order['items'] = fetch_all("""
            SELECT i.item_name, oit.quantity
            FROM order_item oit
            JOIN item i ON oit.item_id = i.item_id
            WHERE oit.order_id = %s
        """, (order['order_id'],))
        
    return render_template('admin_dashboard.html', menu_items=all_items, orders=pending_orders)

@app.route('/admin/update_availability/<int:item_id>', methods=['POST'])
@admin_required
def update_availability(item_id):
    item = fetch_one("SELECT availability_status FROM item WHERE item_id = %s", (item_id,))
    if item:
        new_status = 1 - item['availability_status']
        execute_query("UPDATE item SET availability_status = %s WHERE item_id = %s", (new_status, item_id))
        flash("Item status updated.", 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status')
    execute_query("UPDATE order_info SET status = %s WHERE order_id = %s", (new_status, order_id))
    flash(f"Order #{order_id} marked as {new_status}.", 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # This runs on PORT 5001 to be separate from the student app
    print("--- ADMIN APP RUNNING ON PORT 5001 ---")
    app.run(debug=True, port=5001)