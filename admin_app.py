from flask import Flask, render_template, request, url_for, redirect, flash, session
from datetime import datetime
from functools import wraps
import os

from config import apply_flask_config, env_flag, env_int, is_production, validate_env
from db_config import fetch_all, fetch_one, execute_query, validate_db_config

app = Flask(__name__)
apply_flask_config(app)

db_ok, db_message = validate_db_config()
if not db_ok:
    raise RuntimeError(db_message)

# Admin Credentials from .env (no sensitive defaults)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Fail fast if required environment variables are missing
missing_env = validate_env(['ADMIN_USERNAME', 'ADMIN_PASSWORD'])
if missing_env:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_env)}.\nPlease copy .env.example to .env and set the values before running the app.")

if is_production() and len(ADMIN_PASSWORD) < 12:
    raise RuntimeError("ADMIN_PASSWORD is too weak for production. Use at least 12 characters.")

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


def get_menu_items_for_dashboard():
    return fetch_all("""
        SELECT
            i.item_id,
            i.item_name,
            i.category,
            i.price,
            i.availability_status,
            ds.discount_percentage,
            CASE WHEN ds.item_id IS NOT NULL THEN 1 ELSE 0 END AS is_special,
            CASE
                WHEN ds.item_id IS NOT NULL
                THEN ROUND(i.price * (1 - ds.discount_percentage / 100), 2)
                ELSE i.price
            END AS discounted_price
        FROM item i
        LEFT JOIN daily_special ds
            ON i.item_id = ds.item_id AND ds.date = CURDATE()
        ORDER BY i.category, i.item_name
    """)

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
    all_items = get_menu_items_for_dashboard()
    
    # 2. Fetch Active Orders
    active_orders = fetch_all("""
        SELECT
            oi.order_id,
            oi.order_date,
            oi.order_time,
            oi.total_amount,
            oi.status,
            p.payment_mode,
            p.payment_status,
            s.name as student_name
        FROM order_info oi
        JOIN student s ON oi.student_id = s.student_id
        LEFT JOIN payment p ON oi.order_id = p.order_id
        WHERE oi.status IN ('Awaiting Payment Confirmation', 'Pending')
        ORDER BY oi.order_date ASC, oi.order_time ASC
    """)
    
    # 3. Fetch Items for each Order
    for order in active_orders:
        order['items'] = fetch_all("""
            SELECT i.item_name, oit.quantity
            FROM order_item oit
            JOIN item i ON oit.item_id = i.item_id
            WHERE oit.order_id = %s
        """, (order['order_id'],))
        
    return render_template('admin_dashboard.html', menu_items=all_items, orders=active_orders)


@app.route('/health')
def health():
    return {"status": "ok", "service": "admin"}, 200


@app.route('/admin/add_item', methods=['POST'])
@admin_required
def add_item():
    item_name = request.form.get('item_name', '').strip()
    category = request.form.get('category', '').strip()
    availability_status = 1 if request.form.get('availability_status') == '1' else 0

    try:
        price = float(request.form.get('price', '0'))
        discount_raw = request.form.get('discount_percentage', '').strip()
        discount = float(discount_raw) if discount_raw else 0.0
    except ValueError:
        flash("Enter valid numeric values for the new item price and discount.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if not item_name:
        flash("Item name is required.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if not category:
        flash("Category is required.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if price <= 0:
        flash("Price must be greater than zero.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if discount < 0 or discount >= 100:
        flash("Discount must be between 0 and 99.99.", 'danger')
        return redirect(url_for('admin_dashboard'))

    existing_item = fetch_one(
        "SELECT item_id FROM item WHERE LOWER(item_name) = LOWER(%s)",
        (item_name,)
    )
    if existing_item:
        flash("An item with that name already exists.", 'warning')
        return redirect(url_for('admin_dashboard'))

    new_item_id = execute_query(
        """
        INSERT INTO item (item_name, price, category, availability_status)
        VALUES (%s, %s, %s, %s)
        """,
        (item_name, price, category, availability_status),
        fetch_id=True
    )
    if not new_item_id:
        flash("Could not add the new menu item.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if discount > 0:
        special_ok = execute_query(
            "INSERT INTO daily_special (item_id, date, discount_percentage) VALUES (%s, CURDATE(), %s)",
            (new_item_id, discount)
        )
        if not special_ok:
            flash("Item added, but today's discount could not be saved.", 'warning')
            return redirect(url_for('admin_dashboard'))

    flash(f"{item_name} added to the menu successfully.", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update_item/<int:item_id>', methods=['POST'])
@admin_required
def update_item(item_id):
    item = fetch_one("SELECT item_id, item_name FROM item WHERE item_id = %s", (item_id,))
    if not item:
        flash("Item not found.", 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        price = float(request.form.get('price', '0'))
        discount_raw = request.form.get('discount_percentage', '').strip()
        discount = float(discount_raw) if discount_raw else 0.0
    except ValueError:
        flash("Enter valid numeric values for price and discount.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if price <= 0:
        flash("Price must be greater than zero.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if discount < 0 or discount >= 100:
        flash("Discount must be between 0 and 99.99.", 'danger')
        return redirect(url_for('admin_dashboard'))

    update_price_ok = execute_query(
        "UPDATE item SET price = %s WHERE item_id = %s",
        (price, item_id)
    )
    if not update_price_ok:
        flash("Could not update item price.", 'danger')
        return redirect(url_for('admin_dashboard'))

    special_exists = fetch_one(
        "SELECT special_id FROM daily_special WHERE item_id = %s AND date = CURDATE()",
        (item_id,)
    )

    if discount > 0:
        if special_exists:
            special_ok = execute_query(
                "UPDATE daily_special SET discount_percentage = %s WHERE special_id = %s",
                (discount, special_exists['special_id'])
            )
        else:
            special_ok = execute_query(
                "INSERT INTO daily_special (item_id, date, discount_percentage) VALUES (%s, CURDATE(), %s)",
                (item_id, discount)
            )
        if not special_ok:
            flash("Price updated, but daily special could not be saved.", 'warning')
            return redirect(url_for('admin_dashboard'))
        flash(f"{item['item_name']} updated with price and today's discount.", 'success')
        return redirect(url_for('admin_dashboard'))

    if special_exists:
        remove_ok = execute_query(
            "DELETE FROM daily_special WHERE special_id = %s",
            (special_exists['special_id'],)
        )
        if not remove_ok:
            flash("Price updated, but removing the daily special failed.", 'warning')
            return redirect(url_for('admin_dashboard'))

    flash(f"{item['item_name']} price updated.", 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_item/<int:item_id>', methods=['POST'])
@admin_required
def delete_item(item_id):
    item = fetch_one("SELECT item_name FROM item WHERE item_id = %s", (item_id,))
    if not item:
        flash("Item not found.", 'danger')
        return redirect(url_for('admin_dashboard'))

    order_count = fetch_one(
        "SELECT COUNT(*) AS count FROM order_item WHERE item_id = %s",
        (item_id,)
    )
    if order_count and order_count['count'] > 0:
        unavailable_ok = execute_query(
            "UPDATE item SET availability_status = 0 WHERE item_id = %s",
            (item_id,)
        )
        if not unavailable_ok:
            flash("Could not mark item unavailable.", 'danger')
            return redirect(url_for('admin_dashboard'))

        flash(
            f"{item['item_name']} is used in past orders, so it was marked unavailable instead of deleted.",
            'warning'
        )
        return redirect(url_for('admin_dashboard'))

    delete_special_ok = execute_query("DELETE FROM daily_special WHERE item_id = %s", (item_id,))
    if not delete_special_ok:
        flash("Could not remove the item from today's specials.", 'warning')
        return redirect(url_for('admin_dashboard'))

    delete_item_ok = execute_query("DELETE FROM item WHERE item_id = %s", (item_id,))
    if delete_item_ok:
        flash(f"{item['item_name']} deleted from the menu.", 'success')
    else:
        flash("Could not delete item.", 'danger')

    return redirect(url_for('admin_dashboard'))


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
    order = fetch_one("""
        SELECT oi.order_id, oi.status, p.payment_status
        FROM order_info oi
        LEFT JOIN payment p ON oi.order_id = p.order_id
        WHERE oi.order_id = %s
    """, (order_id,))
    if not order:
        flash("Order not found.", 'danger')
        return redirect(url_for('admin_dashboard'))

    if new_status == 'Pending':
        execute_query(
            "UPDATE payment SET payment_status = %s WHERE order_id = %s",
            ('Completed', order_id),
        )
    elif new_status == 'Canceled':
        execute_query(
            "UPDATE payment SET payment_status = %s WHERE order_id = %s",
            ('Rejected', order_id),
        )
    elif new_status == 'Completed':
        execute_query(
            "UPDATE payment SET payment_status = %s WHERE order_id = %s AND payment_status != %s",
            ('Completed', order_id, 'Completed'),
        )

    execute_query("UPDATE order_info SET status = %s WHERE order_id = %s", (new_status, order_id))
    flash(f"Order #{order_id} marked as {new_status}.", 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = env_int('ADMIN_PORT', 5001)
    debug = env_flag('FLASK_DEBUG', default=False)
    print(f"--- ADMIN APP RUNNING ON PORT {port} ---")
    app.run(host='0.0.0.0', port=port, debug=debug)
