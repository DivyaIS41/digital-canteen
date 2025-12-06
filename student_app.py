import mysql.connector
from flask import Flask, render_template, request, url_for, redirect, flash, session
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
app = Flask(__name__)
# Require FLASK_SECRET_KEY; do not embed real secrets in source
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

# MySQL Configuration from .env — password default is intentionally empty
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'canteen')
}

# Validate required environment variables early
missing_env = []
if not app.secret_key:
    missing_env.append('FLASK_SECRET_KEY')
if not DB_CONFIG.get('password'):
    missing_env.append('DB_PASSWORD')
if not DB_CONFIG.get('database'):
    missing_env.append('DB_NAME')
if missing_env:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_env)}.\nPlease copy .env.example to .env and set the values before running the app.")

# --- Database Functions ---

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        flash("Database connection error. Please contact administrator.", 'danger')
        return None

def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn: return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        # Convert Decimals to float
        for row in result:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)
        return result
    except mysql.connector.Error as err:
        print(f"Database error in fetch_all: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn: return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        if result:
            for key, value in result.items():
                if isinstance(value, Decimal):
                    result[key] = float(value)
        return result
    except mysql.connector.Error as err:
        print(f"Database error in fetch_one: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=None, fetch_id=False):
    conn = get_db_connection()
    if not conn: return None
        
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        if fetch_id:
            last_id = cursor.lastrowid
            return last_id
        return True
    except mysql.connector.Error as err:
        print(f"Database error in execute_query: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

# --- Utility Functions ---

def get_cart_data(student_id):
    """Retrieves the current cart items and calculates the total."""
    cart = session.get('cart', [])
    
    if not isinstance(cart, list):
        cart = []
        session['cart'] = cart

    order_total = 0.0

    if not cart:
        return [], 0.0

    item_ids = [item['item_id'] for item in cart]
    if not item_ids:
        return [], 0.0
        
    placeholders = ', '.join(['%s'] * len(item_ids))
    
    item_query = f"""
    SELECT 
        i.item_id, i.item_name, i.price, i.availability_status,
        CASE WHEN ds.item_id IS NOT NULL THEN 1 ELSE 0 END AS is_special,
        CASE WHEN ds.item_id IS NOT NULL 
             THEN ROUND(i.price * (1 - ds.discount_percentage / 100), 2)
             ELSE i.price 
        END AS discounted_price
    FROM 
        item i
    LEFT JOIN 
        daily_special ds ON i.item_id = ds.item_id AND ds.date = CURDATE()
    WHERE
        i.item_id IN ({placeholders});
    """
    
    live_items_list = fetch_all(item_query, item_ids)
    live_items_map = {item['item_id']: item for item in live_items_list}
    
    updated_cart = []
    order_total = 0.0
    
    for cart_item in cart:
        item_id = cart_item['item_id']
        if item_id in live_items_map and live_items_map[item_id]['availability_status'] == 1:
            live_item = live_items_map[item_id]
            
            cart_item['item_name'] = live_item['item_name']
            cart_item['price'] = live_item['price']
            cart_item['is_special'] = live_item['is_special']
            cart_item['discounted_price'] = live_item['discounted_price']

            final_price = live_item['discounted_price']
            cart_item['line_total'] = final_price * cart_item['quantity']
            order_total += cart_item['line_total']
            updated_cart.append(cart_item)
        else:
            flash(f"'{cart_item.get('item_name', 'An item')}' is no longer available and was removed.", 'warning')

    session['cart'] = updated_cart 
    session.modified = True
    return updated_cart, order_total

# --- Context Processor ---
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# --- Decorators ---

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Student Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id'].strip().upper()
        student_query = """
        SELECT student_id, name 
        FROM student 
        WHERE student_id = %s AND department = %s AND year IN (%s, %s)
        """
        student = fetch_one(student_query, (student_id, 'IS', 2, 3))

        if student:
            session.clear()
            session['student_id'] = student['student_id']
            session['student_name'] = student['name']
            session['cart'] = [] 
            flash(f"Welcome, {student['name']}! You are logged in.", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid Student ID, or you are not an authorized IS student (Year 2 or 3).", 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'success')
    return redirect(url_for('login'))

@app.route('/')
@student_required
def index():
    """Home page: Displays the digital menu."""
    menu_query = """
    SELECT i.item_id, i.item_name, i.price, i.category, i.availability_status,
           ds.discount_percentage,
           CASE WHEN ds.item_id IS NOT NULL THEN 1 ELSE 0 END AS is_special,
           CASE WHEN ds.item_id IS NOT NULL 
                THEN ROUND(i.price * (1 - ds.discount_percentage / 100), 2)
                ELSE i.price 
           END AS discounted_price
    FROM item i
    LEFT JOIN daily_special ds ON i.item_id = ds.item_id AND ds.date = CURDATE()
    WHERE i.availability_status = 1
    ORDER BY i.category, i.item_name;
    """
    menu_items = fetch_all(menu_query)

    categories = {}
    for item in menu_items:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        
    return render_template('index.html', categories=categories)

@app.route('/menu')
@student_required
def menu():
    return index() # Reuses the logic from index

@app.route('/daily_special')
@student_required
def daily_special():
    menu_query = """
    SELECT i.item_id, i.item_name, i.price, i.category, i.availability_status,
           ds.discount_percentage,
           1 AS is_special,
           ROUND(i.price * (1 - ds.discount_percentage / 100), 2) AS discounted_price
    FROM item i
    JOIN daily_special ds ON i.item_id = ds.item_id AND ds.date = CURDATE()
    WHERE i.availability_status = 1
    ORDER BY i.category, i.item_name;
    """
    menu_items = fetch_all(menu_query)

    categories = {}
    for item in menu_items:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        
    cart = session.get('cart', [])
    if not isinstance(cart, list): cart = []

    return render_template('daily_special.html', categories=categories, cart_item_count=len(cart))


@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
@student_required
def add_to_cart(item_id):
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0: raise ValueError
    except ValueError:
        flash("Quantity must be positive.", 'danger')
        return redirect(url_for('menu'))

    item_query = """
    SELECT i.item_id, i.item_name, i.price, 
           ds.discount_percentage,
           CASE WHEN ds.item_id IS NOT NULL THEN 1 ELSE 0 END AS is_special,
           CASE WHEN ds.item_id IS NOT NULL 
                THEN ROUND(i.price * (1 - ds.discount_percentage / 100), 2)
                ELSE i.price 
           END AS discounted_price
    FROM item i
    LEFT JOIN daily_special ds ON i.item_id = ds.item_id AND ds.date = CURDATE()
    WHERE i.item_id = %s AND i.availability_status = 1;
    """
    item_details = fetch_one(item_query, (item_id,))
    
    if not item_details:
        flash("Item not found or unavailable.", 'danger')
        return redirect(url_for('menu'))
        
    cart = session.get('cart', [])
    if not isinstance(cart, list): cart = []

    found = False
    for cart_item in cart:
        if cart_item['item_id'] == item_id:
            cart_item['quantity'] += quantity
            found = True
            break
            
    if not found:
        new_cart_item = {
            'item_id': item_details['item_id'],
            'item_name': item_details['item_name'],
            'price': item_details['price'],
            'is_special': item_details['is_special'],
            'discounted_price': item_details['discounted_price'],
            'quantity': quantity,
            'line_total': item_details['discounted_price'] * quantity 
        }
        cart.append(new_cart_item)
        
    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} x {item_details['item_name']} added to cart.", 'success')
    return redirect(url_for('menu'))

@app.route('/cart')
@student_required
def cart():
    cart, order_total = get_cart_data(session['student_id'])
    return render_template('cart.html', cart=cart, order_total=order_total)


@app.route('/update_cart/<int:item_id>', methods=['POST'])
@student_required
def update_cart(item_id):
    cart = session.get('cart', [])
    if not isinstance(cart, list): cart = []
    
    try:
        new_quantity = int(request.form.get('quantity', 0))
    except ValueError:
        flash("Invalid quantity value.", 'danger')
        return redirect(url_for('cart'))

    updated_cart = []
    item_name = ""
    for item in cart:
        if item['item_id'] == item_id:
            item_name = item['item_name']
            if new_quantity > 0:
                item['quantity'] = new_quantity
                updated_cart.append(item)
                flash(f"Quantity for {item_name} updated to {new_quantity}.", 'info')
            else:
                flash(f"{item_name} removed from cart.", 'danger')
        else:
            updated_cart.append(item)
            
    session['cart'] = updated_cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@student_required
def remove_from_cart(item_id):
    cart = session.get('cart', [])
    if not isinstance(cart, list): cart = []
    
    updated_cart = []
    item_name = ""
    for item in cart:
        if item['item_id'] != item_id:
            updated_cart.append(item)
        else:
            item_name = item['item_name']
            
    session['cart'] = updated_cart
    session.modified = True
    flash(f"{item_name} removed from cart.", 'danger')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@student_required
def checkout():
    cart, order_total = get_cart_data(session['student_id'])

    if not cart:
        flash("Your cart is empty. Please add items to place an order.", 'warning')
        return redirect(url_for('index'))

    # Fetch wallet balance for the GET request or POST check
    conn = get_db_connection()
    if not conn: return redirect(url_for('cart'))
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT balance FROM student WHERE student_id = %s", (session['student_id'],))
    res = cursor.fetchone()
    balance = float(res['balance']) if res else 0.0

    if request.method == 'POST':
        try:
            payment_mode = request.form['payment_mode']
            student_id = session['student_id']
            
            # WALLET LOGIC
            if payment_mode == 'Wallet':
                if balance < order_total:
                    flash("Insufficient wallet balance.", 'danger')
                    return redirect(url_for('checkout'))
                
                # Deduct Balance
                new_balance = balance - order_total
                cursor.execute("UPDATE student SET balance = %s WHERE student_id = %s", (new_balance, student_id))

            # Insert Order
            order_info_query = """
            INSERT INTO order_info (student_id, order_date, order_time, total_amount, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            order_params = (student_id, date.today(), datetime.now().strftime('%H:%M:%S'), Decimal(order_total), 'Pending')
            cursor.execute(order_info_query, order_params)
            new_order_id = cursor.lastrowid

            # Insert Payment
            payment_status = 'Completed' if payment_mode in ['UPI', 'Card', 'Wallet'] else 'Pending'
            payment_query = """
            INSERT INTO payment (order_id, payment_mode, amount_paid, payment_status, transaction_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            payment_params = (new_order_id, payment_mode, Decimal(order_total), payment_status, date.today())
            cursor.execute(payment_query, payment_params)
            
            # Insert Items
            order_item_query = """
            INSERT INTO order_item (order_id, item_id, quantity, subtotal)
            VALUES (%s, %s, %s, %s)
            """
            for item in cart:
                item_params = (new_order_id, item['item_id'], item['quantity'], Decimal(item['line_total']))
                cursor.execute(order_item_query, item_params)

            conn.commit()
            session.pop('cart', None)
            session.modified = True
            flash("Order placed successfully!", 'success')
            return redirect(url_for('order_success', order_id=new_order_id))

        except mysql.connector.Error as err:
            print(f"Checkout Error: {err}")
            conn.rollback()
            flash(f"An error occurred during checkout: {err}", 'danger')
            return redirect(url_for('cart'))
        finally:
            cursor.close()
            conn.close()

    return render_template('checkout.html', cart=cart, order_total=order_total, balance=balance)

@app.route('/order_success/<int:order_id>')
@student_required
def order_success(order_id):
    order_query = """
    SELECT oi.order_id, oi.total_amount, oi.status, p.payment_mode, s.name as student_name
    FROM order_info oi
    JOIN payment p ON oi.order_id = p.order_id
    JOIN student s ON oi.student_id = s.student_id
    WHERE oi.order_id = %s AND oi.student_id = %s
    """
    order = fetch_one(order_query, (order_id, session['student_id']))

    if not order:
        flash("Order not found.", 'danger')
        return redirect(url_for('index'))

    items_query = """
    SELECT i.item_name, oit.quantity, oit.subtotal
    FROM order_item oit
    JOIN item i ON oit.item_id = i.item_id
    WHERE oit.order_id = %s
    """
    items = fetch_all(items_query, (order_id,))

    return render_template('order_success.html', order=order, items=items)


@app.route('/orders')
@student_required
def orders():
    student_id = session['student_id']
    orders_query = """
    SELECT oi.order_id, oi.order_date, oi.order_time, oi.total_amount, oi.status, p.payment_mode
    FROM order_info oi
    LEFT JOIN payment p ON oi.order_id = p.order_id
    WHERE oi.student_id = %s
    ORDER BY oi.order_date DESC, oi.order_time DESC
    """
    orders_list = fetch_all(orders_query, (student_id,))

    for order in orders_list:
        order_items_query = """
        SELECT i.item_name, oit.quantity, oit.subtotal
        FROM order_item oit
        JOIN item i ON oit.item_id = i.item_id
        WHERE oit.order_id = %s
        """
        order['order_items'] = fetch_all(order_items_query, (order['order_id'],)) 
        order['total_amount'] = float(order['total_amount']) 
        
    return render_template('orders.html', orders=orders_list)

if __name__ == '__main__':
    print("--- STUDENT APP RUNNING ON PORT 5000 ---")
    app.run(debug=True, port=5000)