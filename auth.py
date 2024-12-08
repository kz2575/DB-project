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
        db = get_db()
        print(db)
        cursor = db.cursor()
        cursor.execute("SELECT rDescription FROM Role")
        available_roles = [row[0] for row in cursor.fetchall()]
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            role = request.form['role']  # Added for role selection

            error = None

            # Check if username already exists
            cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            # Error handling for missing fields
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif not first_name or not last_name:
                error = 'Name is required.'
            elif not email:
                error = 'Email is required.'
            elif role not in available_roles:
                error = 'Invalid role selected.'
            elif existing_user:
                error = f"User {username} is already registered."

            if error is None:
                print("here")
                try:
                    # Insert user into the user table
                    cursor.execute(
                        """
                        INSERT INTO user (first_name, last_name, username, password, email) 
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (first_name, last_name, username, generate_password_hash(password), email),
                    )
                    db.commit()

                    # Fetch roleID for the selected role
                    cursor.execute("SELECT roleID FROM Role WHERE rDescription = %s", (role,))
                    role_id = cursor.fetchone()

                    if role_id:
                        # Insert user role into Act table
                        cursor.execute(
                            """
                            INSERT INTO Act (userName, roleID)
                            VALUES (%s, %s)
                            """,
                            (username, role_id[0]),
                        )
                        db.commit()
                    else:
                        error = f"Role {role} does not exist. Contact admin to set up roles."

                    return redirect(url_for("auth.login"))
                except mysql.connector.IntegrityError:
                    error = f"User {username} is already registered."
            flash(error)

        return render_template('auth/register.html', roles=available_roles)

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
    @login_required
    def index():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT r.rDescription 
            FROM Role r
            JOIN Act a ON r.roleID = a.roleID
            WHERE a.userName = %s
            """,
            (current_user.username,)
        )
        roles = [row['rDescription'] for row in cursor.fetchall()]

        buttons = [
            {"name": "Find Item", "url": url_for('auth.find_item')},
            {"name": "Find Order", "url": url_for('auth.find_order')},
            {"name": "Add to Order", "url": url_for('auth.add_to_order')}
        ]

        if 'staff' in roles:
            buttons.append({"name": "Accept Donation", "url": url_for('auth.accept_donation')})
            buttons.append({"name": "Start Order", "url": url_for('auth.start_order')})

        return render_template('auth/index.html', buttons=buttons)

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

            # 检查if donor
            cursor.execute(
                """
                SELECT r.rDescription
                FROM User u
                JOIN Act a ON u.userName = a.userName
                JOIN Role r ON a.roleID = r.roleID
                WHERE u.userName = %s
                """,
                (donor_id,)
            )
            donor_role = cursor.fetchone()

            if not donor_role:
                error = f"Donor with ID {donor_id} is not registered."
            elif donor_role['rDescription'] != 'donor':
                error = f"User {donor_id} is not authorized as a donor."

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

    @bp.route('/start_order', methods=('GET', 'POST'))
    @login_required
    def start_order():
        if not current_user.is_authenticated or not is_staff_user(current_user.username):
            flash("You must be a staff member to accept donations.")
            return redirect(url_for('auth.index'))
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

        # 获取当前用户关联订单
        cursor.execute(
            """
            SELECT o.orderID, o.orderDate, u.first_name AS supervisor_name, o.orderNotes
            FROM Ordered o
            JOIN user u ON o.supervisor = u.username
            WHERE o.client = %s
            ORDER BY o.orderDate DESC
            """,
            (current_user.username,)
        )
        orders = cursor.fetchall()

        if not orders:
            flash("No active orders found for your account.")
            return redirect(url_for('auth.index'))

        # 获取类别和子类别
        cursor.execute("SELECT DISTINCT mainCategory, subCategory FROM Category")
        categories = cursor.fetchall()

        items = None  # 用于存储查询的物品列表
        selected_order_id = None  # 存储ID

        if request.method == 'POST':
            selected_order_id = request.form.get('order_id')
            main_category = request.form.get('main_category')
            sub_category = request.form.get('sub_category')
            item_id = request.form.get('item_id')

            if not selected_order_id:
                error = "You must select an order to add items."
            elif not any(order['orderID'] == int(selected_order_id) for order in orders):
                error = "The selected order does not belong to your account."
            elif main_category and sub_category:
                # 查询属于指定类别且未被订购的物品
                cursor.execute(
                    """
                    SELECT i.itemID, i.iDescription, i.color, i.isNew, i.material
                    FROM Item i
                    WHERE i.mainCategory = %s 
                      AND i.subCategory = %s
                      AND i.itemID NOT IN (
                          SELECT itemID FROM ItemIn
                      )
                    """,
                    (main_category, sub_category)
                )
                items = cursor.fetchall()

            if item_id and not error:
                try:
                    # 检查物品是否已在其他订单中
                    cursor.execute(
                        """
                        SELECT itemID FROM ItemIn 
                        WHERE itemID = %s AND orderID != %s
                        """,
                        (item_id, selected_order_id)
                    )
                    existing_item = cursor.fetchone()
                    if existing_item:
                        error = f"Item {item_id} is already added to another order."
                    else:
                        # 将物品添加到订单
                        cursor.execute(
                            """
                            INSERT INTO ItemIn (itemID, orderID, found)
                            VALUES (%s, %s, %s)
                            """,
                            (item_id, selected_order_id, False)
                        )
                        db.commit()
                        flash(f"Item {item_id} added to order {selected_order_id} successfully.")
                        return redirect(request.url)
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

        if error:
            flash(error)

        return render_template(
            'auth/add_to_order.html',
            orders=orders,
            categories=categories,
            items=items,
            selected_order_id=selected_order_id
        )

    @bp.route('/prepare_order', methods=('GET', 'POST'))
    @login_required
    def prepare_order():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None

        orders = None  # 用于存储查询的订单列表
        items = None  # 用于存储查询的物品列表

        if request.method == 'POST':
            # 根据客户端用户名或订单号搜索
            client_username = request.form.get('client_username')
            order_id = request.form.get('order_id')

            if client_username:
                cursor.execute(
                    """
                    SELECT o.orderID, o.orderDate, o.orderNotes, u.first_name AS supervisor_name
                    FROM Ordered o
                    JOIN user u ON o.supervisor = u.username
                    WHERE o.client = %s
                    """,
                    (client_username,)
                )
                orders = cursor.fetchall()

            elif order_id:
                cursor.execute(
                    """
                    SELECT o.orderID, o.orderDate, o.orderNotes, u.first_name AS supervisor_name
                    FROM Ordered o
                    JOIN user u ON o.supervisor = u.username
                    WHERE o.orderID = %s
                    """,
                    (order_id,)
                )
                orders = cursor.fetchall()

            # 更新物品状态为“等待配送”
            if request.form.get('update_order') and order_id:
                try:
                    cursor.execute(
                        """
                        UPDATE ItemIn
                        SET found = TRUE
                        WHERE orderID = %s
                        """,
                        (order_id,)
                    )
                    db.commit()
                    flash(f"Order {order_id} marked as ready for delivery.")
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

        if error:
            flash(error)

        return render_template('auth/prepare_order.html', orders=orders, items=items)

    @bp.route('/user_tasks', methods=('GET',))
    @login_required
    def user_tasks():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 根据当前用户角色获取相关订单信息
        if current_user.is_authenticated:
            user_role = None
            cursor.execute(
                "SELECT r.rDescription FROM Act a JOIN Role r ON a.roleID = r.roleID WHERE a.userName = %s",
                (current_user.username,)
            )
            user_role = cursor.fetchone()

            if user_role and user_role['rDescription'] == 'client':
                cursor.execute(
                    """
                    SELECT o.orderID, o.orderDate, o.orderNotes
                    FROM Ordered o
                    WHERE o.client = %s
                    """,
                    (current_user.username,)
                )
                orders = cursor.fetchall()

            elif user_role and user_role['rDescription'] == 'volunteer':
                cursor.execute(
                    """
                    SELECT o.orderID, o.orderDate, o.orderNotes, u.first_name AS client_name
                    FROM Ordered o
                    JOIN user u ON o.client = u.username
                    WHERE o.orderID IN (
                        SELECT DISTINCT orderID
                        FROM ItemIn
                    )
                    """
                )
                orders = cursor.fetchall()
            else:
                orders = None

        return render_template('auth/user_tasks.html', orders=orders)

    return bp
