import os
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from config import apply_flask_config, env_flag, env_int, is_production
from db_config import execute_query, fetch_all, fetch_one, get_db_connection, validate_db_config

# --- Configuration ---
app = Flask(__name__)
apply_flask_config(app)
WALLET_PIN = os.getenv('WALLET_PIN', '')

db_ok, db_message = validate_db_config()
if not db_ok:
    raise RuntimeError(db_message)

if is_production() and not WALLET_PIN:
    raise RuntimeError("WALLET_PIN is required in production.")

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
            cart_item['price'] = float(live_item['price'])
            cart_item['is_special'] = int(live_item['is_special'])
            cart_item['discounted_price'] = float(live_item['discounted_price'])

            final_price = float(live_item['discounted_price'])
            cart_item['line_total'] = final_price * cart_item['quantity']
            order_total += cart_item['line_total']
            updated_cart.append(cart_item)
        else:
            flash(f"'{cart_item.get('item_name', 'An item')}' is no longer available and was removed.", 'warning')

    session['cart'] = updated_cart 
    session.modified = True
    return updated_cart, order_total


def get_student_balance(student_id):
    student = fetch_one(
        "SELECT balance FROM student WHERE student_id = %s",
        (student_id,),
    )
    if not student:
        return 0.0
    return float(student['balance'])


def normalize_money(value):
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

# --- Context Processor ---
@app.context_processor
def inject_now():
    wallet_balance = None
    if session.get('student_id'):
        wallet_balance = get_student_balance(session['student_id'])
    return {'now': datetime.now(), 'wallet_balance': wallet_balance}

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
        login_password = request.form.get('login_password', '')
        student_query = """
        SELECT student_id, name 
        FROM student 
        WHERE student_id = %s AND login_password = %s AND department = %s AND year IN (%s, %s)
        """
        student = fetch_one(student_query, (student_id, login_password, 'IS', 2, 3))

        if student:
            session.clear()
            session['student_id'] = student['student_id']
            session['student_name'] = student['name']
            session['cart'] = [] 
            flash(f"Welcome, {student['name']}! You are logged in.", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid Student ID or password, or you are not an authorized IS student (Year 2 or 3).", 'danger')

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
    specials = []
    for item in menu_items:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        if item['is_special']:
            specials.append(item)
        
    return render_template('index.html', categories=categories, specials=specials)

@app.route('/menu')
@student_required
def menu():
    return index() # Reuses the logic from index

@app.route('/health')
def health():
    return {"status": "ok", "service": "student"}, 200

@app.route('/daily_special')
@student_required
def daily_special():
    return redirect(url_for('index') + '#daily-specials')


@app.route('/wallet', methods=['GET', 'POST'])
@student_required
def wallet():
    student_id = session['student_id']
    balance = get_student_balance(student_id)

    if request.method == 'POST':
        try:
            recharge_amount = float(request.form.get('amount', '0'))
        except ValueError:
            flash("Enter a valid recharge amount.", 'danger')
            return redirect(url_for('wallet'))

        recharge_method = request.form.get('recharge_method', 'Manual')

        if recharge_amount <= 0:
            flash("Recharge amount must be greater than zero.", 'danger')
            return redirect(url_for('wallet'))

        if recharge_amount > 5000:
            flash("For this demo, recharge is capped at Rs. 5000 per transaction.", 'warning')
            return redirect(url_for('wallet'))

        updated_balance = balance + recharge_amount
        recharge_ok = fetch_one(
            "SELECT student_id FROM student WHERE student_id = %s",
            (student_id,),
        )
        if not recharge_ok:
            flash("Student record not found.", 'danger')
            return redirect(url_for('index'))

        update_ok = execute_query(
            "UPDATE student SET balance = %s WHERE student_id = %s",
            (updated_balance, student_id),
        )
        if not update_ok:
            flash("Wallet recharge failed. Please try again.", 'danger')
            return redirect(url_for('wallet'))

        flash(
            f"Wallet recharged with Rs. {recharge_amount:.2f} using {recharge_method}. New balance: Rs. {updated_balance:.2f}.",
            'success'
        )
        return redirect(url_for('wallet'))

    return render_template('wallet.html', balance=balance)


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
            'price': normalize_money(item_details['price']),
            'is_special': int(item_details['is_special']),
            'discounted_price': normalize_money(item_details['discounted_price']),
            'quantity': quantity,
            'line_total': normalize_money(item_details['discounted_price']) * quantity 
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
    
    # Note: Assuming column name is 'balance' based on user input. 
    # If DB uses 'wallet_balance', change this query accordingly.
    cursor.execute(
        "SELECT balance FROM student WHERE student_id = %s",
        (session['student_id'],),
    )
    res = cursor.fetchone()
    balance = float(res['balance']) if res else 0.0

    if request.method != 'POST':
        cursor.close()
        conn.close()
        return render_template('checkout.html', cart=cart, order_total=order_total, balance=balance)

    if request.method == 'POST':
        try:
            payment_mode = request.form['payment_mode']
            student_id = session['student_id']
            payment_status = 'Pending Confirmation'
            order_status = 'Awaiting Payment Confirmation'
            
            # WALLET LOGIC
            if payment_mode == 'Wallet':
                # --- NEW PIN VERIFICATION LOGIC ---
                pin = request.form.get('wallet_pin')
                
                if not WALLET_PIN or pin != WALLET_PIN:
                    flash("Invalid Wallet PIN. Payment failed.", 'danger')
                    return redirect(url_for('checkout'))

                # Verify Balance
                if balance < order_total:
                    flash("Insufficient wallet balance.", 'danger')
                    return redirect(url_for('checkout'))
                
                # Deduct Balance
                new_balance = balance - order_total
                cursor.execute(
                    "UPDATE student SET balance = %s WHERE student_id = %s",
                    (new_balance, student_id),
                )
                payment_status = 'Completed'
                order_status = 'Pending'
                # ----------------------------------
            elif payment_mode in ['UPI', 'Card', 'Cash']:
                payment_status = 'Pending Confirmation'
                order_status = 'Awaiting Payment Confirmation'

            # Insert Order
            order_info_query = """
            INSERT INTO order_info (student_id, order_date, order_time, total_amount, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            order_params = (student_id, date.today(), datetime.now().strftime('%H:%M:%S'), order_total, order_status)
            cursor.execute(order_info_query, order_params)
            new_order_id = cursor.lastrowid

            # Insert Payment
            payment_query = """
            INSERT INTO payment (order_id, payment_mode, amount_paid, payment_status, transaction_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            payment_params = (new_order_id, payment_mode, order_total, payment_status, date.today())
            cursor.execute(payment_query, payment_params)
            
            # Insert Items
            order_item_query = """
            INSERT INTO order_item (order_id, item_id, quantity, subtotal)
            VALUES (%s, %s, %s, %s)
            """
            for item in cart:
                item_params = (new_order_id, item['item_id'], item['quantity'], item['line_total'])
                cursor.execute(order_item_query, item_params)

            conn.commit()
            session.pop('cart', None)
            session.modified = True
            flash("Order placed successfully!", 'success')
            return redirect(url_for('order_success', order_id=new_order_id))

        except Exception as err:
            print(f"Checkout Error: {err}")
            conn.rollback()
            flash(f"An error occurred during checkout: {err}", 'danger')
            return redirect(url_for('cart'))
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('cart'))

@app.route('/order_success/<int:order_id>')
@student_required
def order_success(order_id):
    order_query = """
    SELECT oi.order_id, oi.total_amount, oi.status, p.payment_mode, p.payment_status, s.name as student_name
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
    SELECT oi.order_id, oi.order_date, oi.order_time, oi.total_amount, oi.status, p.payment_mode, p.payment_status
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
    port = env_int('PORT', 5000)
    debug = env_flag('FLASK_DEBUG', default=False)
    print(f"--- STUDENT APP RUNNING ON PORT {port} ---")
    app.run(host='0.0.0.0', port=port, debug=debug)
