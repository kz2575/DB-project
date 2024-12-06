import mysql.connector
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, current_user, login_required
from flask import session


# Define your User class that extends UserMixin
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


def create_auth_blueprint(login_manager: LoginManager):
    bp = Blueprint('auth', __name__, url_prefix='/auth')

    # login_manager.init_app(current_app)

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE cid = %s', (user_id,))
        columns = [column[0] for column in cursor.description]
        res = cursor.fetchone()

        if res is None:
            return None

        res_dict = dict(zip(columns, res))
        user_id = res_dict.get("cid")
        username = res_dict.get("username")
        return User(user_id, username)

    @bp.route('/register', methods=('GET', 'POST'))
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            billing_address = request.form['billing_address']
            db = get_db()
            print(db)
            error = None
            cursor = db.cursor()
            cursor.execute("SELECT 1 FROM user WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif (not first_name) or (not last_name):
                error = 'Name is required.'
            elif not billing_address:
                error = 'Billing Address is required.'
            elif existing_user:
                error = f"User {username} is already registered."

            if error is None:
                print("here")
                try:
                    cursor.execute(
                        "INSERT INTO user (first_name, last_name, username, password, billAddr) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, username, generate_password_hash(password), billing_address),
                    )
                    db.commit()
                except mysql.connector.IntegrityError:
                    error = f"User {username} is already registered."
                else:
                    return redirect(url_for("auth.login"))

            flash(error)

        return render_template('auth/register.html')

    @bp.route('/login', methods=('GET', 'POST'))
    def login():

        if current_user.is_authenticated:
            return redirect(url_for('auth.index'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            db = get_db()
            cursor = db.cursor()
            error = None
            cursor.execute(
                'SELECT * FROM user WHERE username = %s', (username,)
            )
            columns = [column[0] for column in cursor.description]
            print(columns)
            user = cursor.fetchone()
            if user is None:
                error = 'Non-existing username'
            elif not check_password_hash(user[4], password):
                error = 'Incorrect password.'

            if error is None:
                res_dict = dict(zip(columns, user))
                user_id = res_dict.get("cid")
                username = res_dict.get("username")
                wrapped_user = User(user_id, username)
                login_user(wrapped_user)
                return redirect(url_for('auth.index'))  # change to your main page here
            flash(error)

        return render_template('auth/login.html')

    @bp.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('auth.login'))

    @bp.route('/index', methods=('GET', 'POST'))
    def index():
        return render_template('auth/index.html')

    @bp.route('/find_item', methods=('GET', 'POST'))
    def find_item():
        if request.method == 'POST':
            item_id = request.form['item_id']  # get item id
            db = get_db()
            cursor = db.cursor()
            error = None

            cursor.execute(
                """
                SELECT roomNum, shelfNum
                FROM Piece
                WHERE itemID = %s
                """,
                (item_id,)
            )
            results = cursor.fetchall()

            if not results:
                error = f"No storage locations found for Item ID: {item_id}"

            if error:
                flash(error)
                return render_template('auth/find_item.html')
            else:
                return render_template('auth/find_item.html', results=results)

        return render_template('auth/find_item.html')

    @bp.route('/find_order', methods=('GET', 'POST'))
    def find_order():
        if request.method == 'POST':
            order_id = request.form['order_id']  # get order id
            db = get_db()
            cursor = db.cursor(dictionary=True)  # 使用 dictionary=True 获取字典形式的结果
            error = None

            cursor.execute(
                """
                SELECT i.itemID, p.roomNum, p.shelfNum
                FROM ItemIn i
                LEFT JOIN Piece p ON i.itemID = p.itemID
                WHERE i.orderID = %s
                """,
                (order_id,)
            )
            results = cursor.fetchall()

            if not results:
                error = f"No items found for Order ID: {order_id}"

            if error:
                flash(error)
                return render_template('auth/find_order.html')
            else:
                return render_template('auth/find_order.html', results=results)

        return render_template('auth/find_order.html')

    def is_staff_user(username):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT roleID FROM Act WHERE userName = %s AND roleID = (SELECT roleID FROM Role WHERE rDescription = 'staff')",
            (username,)
        )
        return cursor.fetchone() is not None

    @bp.route('/accept_donation', methods=('GET', 'POST'))
    @login_required
    def accept_donation():
        if not current_user.is_authenticated or not is_staff_user(current_user.username):
            flash("You must be a staff member to accept donations.")
            return redirect(url_for('auth.index'))

        if request.method == 'POST':
            donor_id = request.form['donor_id']
            item_description = request.form['item_description']
            main_category = request.form['main_category']
            sub_category = request.form['sub_category']
            color = request.form['color']
            material = request.form['material']
            is_new = request.form.get('is_new', 'off') == 'on'
            requires_assembly = request.form.get('requires_assembly', 'off') == 'on'
            room_num = request.form['room_num']
            shelf_num = request.form['shelf_num']

            db = get_db()
            cursor = db.cursor(dictionary=True)
            error = None

            cursor.execute('SELECT * FROM User WHERE userName = %s', (donor_id,))
            donor = cursor.fetchone()
            if donor is None:
                error = f"Donor with ID {donor_id} is not registered."

            if error is None:
                try:
                    cursor.execute(
                        """
                        INSERT INTO Item (iDescription, mainCategory, subCategory, color, material, isNew, hasPieces)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (item_description, main_category, sub_category, color, material, is_new, requires_assembly)
                    )
                    item_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO DonatedBy (ItemID, userName, donateDate)
                        VALUES (%s, %s, NOW())
                        """,
                        (item_id, donor_id)
                    )

                    cursor.execute(
                        """
                        INSERT INTO Piece (ItemID, pieceNum, roomNum, shelfNum, pDescription)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (item_id, 1, room_num, shelf_num, f"Main piece of item {item_id}")
                    )
                    db.commit()
                    flash("Donation accepted successfully.")
                    return redirect(url_for('auth.index'))
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

            flash(error)

        return render_template('auth/accept_donation.html')

    @bp.route('/assign_role', methods=('GET', 'POST'))
    @login_required
    def assign_role():
        if request.method == 'POST':
            username = request.form['username']
            role_description = request.form['role_description']

            db = get_db()
            cursor = db.cursor(dictionary=True)
            error = None

            cursor.execute('SELECT * FROM user WHERE userName = %s', (username,))
            user = cursor.fetchone()
            if not user:
                error = f"User {username} does not exist."

            cursor.execute('SELECT * FROM Role WHERE rDescription = %s', (role_description,))
            role = cursor.fetchone()
            if not role:
                error = f"Role {role_description} does not exist."

            if error is None:
                cursor.execute(
                    """
                    SELECT * FROM Act WHERE userName = %s AND roleID = %s
                    """,
                    (username, role['roleID'])
                )
                existing_assignment = cursor.fetchone()
                if existing_assignment:
                    error = f"User {username} already has the role {role_description}."

            if error is None:
                try:
                    cursor.execute(
                        """
                        INSERT INTO Act (userName, roleID)
                        VALUES (%s, %s)
                        """,
                        (username, role['roleID'])
                    )
                    db.commit()
                    flash(f"Role {role_description} assigned to {username} successfully.")
                    return redirect(request.url)
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

            flash(error)

        return render_template('auth/assign_role.html')

    @bp.route('/add_role', methods=('GET', 'POST'))
    @login_required
    def add_role():
        if request.method == 'POST':
            role_description = request.form['role_description']

            db = get_db()
            cursor = db.cursor(dictionary=True)
            error = None

            cursor.execute('SELECT * FROM Role WHERE rDescription = %s', (role_description,))
            if cursor.fetchone():
                error = f"Role '{role_description}' already exists."

            if error is None:
                try:
                    cursor.execute(
                        """
                        INSERT INTO Role (rDescription)
                        VALUES (%s)
                        """,
                        (role_description,)
                    )
                    db.commit()
                    flash(f"Role '{role_description}' added successfully.")
                    return redirect(request.url)
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

            flash(error)

        return render_template('auth/add_role.html')

    @bp.route('/start_order', methods=('GET', 'POST'))
    @login_required
    def start_order():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':
            client_username = request.form['client_username']
            error = None

            # 验证用户名
            cursor.execute('SELECT * FROM user WHERE userName = %s', (client_username,))
            client = cursor.fetchone()
            if not client:
                error = f"Client username {client_username} does not exist."

            if error is None:
                try:
                    # 创建订单
                    cursor.execute(
                        """
                        INSERT INTO Ordered (orderDate, supervisor, client)
                        VALUES (NOW(), %s, %s)
                        """,
                        (current_user.username, client_username)
                    )
                    db.commit()

                    order_id = cursor.lastrowid

                    session['current_order_id'] = order_id
                    flash(f"Order {order_id} started successfully for client {client_username}.")
                    return redirect(url_for('auth.index'))
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

            flash(error)

        return render_template('auth/start_order.html')

    @bp.route('/add_to_order', methods=('GET', 'POST'))
    @login_required
    def add_to_order():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None

        order_id = session.get('current_order_id')
        if not order_id:
            flash("No active order found. Start an order first.")
            return redirect(url_for('auth.start_order'))

        # 获取类别和子类别
        cursor.execute("SELECT DISTINCT mainCategory, subCategory FROM Category")
        categories = cursor.fetchall()

        items = None  # 用于存储查询的物品列表
        if request.method == 'POST':
            main_category = request.form.get('main_category')
            sub_category = request.form.get('sub_category')
            item_id = request.form.get('item_id')

            if main_category and sub_category:
                # 查询属于指定类别且未被订购的物品
                cursor.execute(
                    """
                    SELECT * FROM Item
                    WHERE mainCategory = %s AND subCategory = %s AND itemID NOT IN (
                        SELECT itemID FROM ItemIn
                    )
                    """,
                    (main_category, sub_category)
                )
                items = cursor.fetchall()

            if item_id:
                try:
                    # 将物品添加到订单
                    cursor.execute(
                        """
                        INSERT INTO ItemIn (itemID, orderID, found)
                        VALUES (%s, %s, %s)
                        """,
                        (item_id, order_id, False)
                    )
                    db.commit()
                    flash(f"Item {item_id} added to order {order_id} successfully.")
                    return redirect(request.url)
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

        if error:
            flash(error)

        return render_template('auth/add_to_order.html', categories=categories, items=items)

    return bp
