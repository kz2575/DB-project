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
            {"name": "Add to Order", "url": url_for('auth.add_to_order')},
            {"name": "User Tasks", "url": url_for('auth.user_tasks')},
            {"name": "Rank System", "url": url_for('auth.rank_system')}
        ]

        if 'staff' in roles:
            buttons.append({"name": "Accept Donation", "url": url_for('auth.accept_donation')})
            buttons.append({"name": "Start Order", "url": url_for('auth.start_order')})

        return render_template('auth/index.html', buttons=buttons)

    @bp.route('/find_item', methods=('GET', 'POST'))
    @login_required
    def find_item():
        if request.method == 'POST':
            item_id = request.form['item_id']  # get item id
            db = get_db()
            cursor = db.cursor(dictionary=True)
            error = None

            try:
                cursor.execute(
                    """
                    SELECT p.itemID, p.pieceNum, p.pDescription, p.roomNum, p.shelfNum
                    FROM Piece p
                    WHERE p.itemID = %s
                    """,
                    (item_id,)
                )
                results = cursor.fetchall()

                if not results:
                    error = f"No storage locations found for Item ID: {item_id}"
            except Exception as e:
                error = f"An error occurred while retrieving data: {e}"

            if error:
                flash(error)
                return render_template('auth/find_item.html', results=None)

            return render_template('auth/find_item.html', results=results)

        return render_template('auth/find_item.html', results=None)

    @bp.route('/find_order', methods=('GET', 'POST'))
    @login_required
    def find_order():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None
        results = []

        if request.method == 'POST':
            order_id = request.form['order_id']
            try:
                cursor.execute(
                    """
                    SELECT 
                        i.itemID, 
                        p.pieceNum, 
                        p.pDescription, 
                        p.roomNum, 
                        p.shelfNum
                    FROM 
                        ItemIn i
                    LEFT JOIN 
                        Piece p ON i.itemID = p.itemID
                    WHERE 
                        i.orderID = %s
                    """,
                    (order_id,)
                )
                results = cursor.fetchall()

                if not results:
                    error = f"No items found for Order ID: {order_id}"
            except Exception as e:
                error = f"An error occurred: {e}"

        if error:
            flash(error)

        return render_template('auth/find_order.html', results=results)

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

        db = get_db()
        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':
            donor_id = request.form['donor_id']
            item_description = request.form['item_description']
            main_category = request.form['main_category']
            sub_category = request.form['sub_category']
            color = request.form['color']
            material = request.form['material']
            is_new = request.form.get('is_new', 'no') == 'yes'

            piece_descriptions = request.form.getlist('piece_descriptions[]')
            piece_lengths = request.form.getlist('piece_lengths[]')
            piece_widths = request.form.getlist('piece_widths[]')
            piece_heights = request.form.getlist('piece_heights[]')
            piece_room_nums = request.form.getlist('piece_room_nums[]')
            piece_shelf_nums = request.form.getlist('piece_shelf_nums[]')
            piece_notes = request.form.getlist('piece_notes[]')

            pieces = []
            for i in range(len(piece_descriptions)):
                pieces.append({
                    "description": piece_descriptions[i],
                    "length": float(piece_lengths[i]) if piece_lengths[i] else None,
                    "width": float(piece_widths[i]) if piece_widths[i] else None,
                    "height": float(piece_heights[i]) if piece_heights[i] else None,
                    "room_num": piece_room_nums[i],
                    "shelf_num": piece_shelf_nums[i],
                    "notes": piece_notes[i] if piece_notes[i] else None
                })

            print(f"Number of pieces: {len(pieces)}")  # Debugging

            error = None

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
                        (item_description, main_category, sub_category, color, material, is_new, len(pieces) > 1)
                    )
                    item_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO DonatedBy (ItemID, userName, donateDate)
                        VALUES (%s, %s, NOW())
                        """,
                        (item_id, donor_id)
                    )

                    for idx, piece in enumerate(pieces, start=1):
                        cursor.execute(
                            """
                            INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (item_id, idx, piece["description"], piece["length"], piece["width"], piece["height"],
                             piece["room_num"], piece["shelf_num"], piece["notes"])
                        )

                    db.commit()
                    flash("Donation accepted successfully.")
                    return redirect(url_for('auth.index'))
                except Exception as e:
                    db.rollback()
                    error = f"An error occurred: {e}"

            flash(error)

        cursor.execute("SELECT DISTINCT mainCategory FROM Category")
        main_categories = [row['mainCategory'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT subCategory FROM Category")
        sub_categories = [row['subCategory'] for row in cursor.fetchall()]

        return render_template(
            'auth/accept_donation.html',
            main_categories=main_categories,
            sub_categories=sub_categories
        )

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

            cursor.execute('SELECT * FROM user WHERE userName = %s', (client_username,))
            client = cursor.fetchone()
            if not client:
                error = f"Client username {client_username} does not exist."

            if error is None:
                try:
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

        cursor.execute("SELECT DISTINCT mainCategory, subCategory FROM Category")
        categories = cursor.fetchall()

        items = None
        selected_order_id = None

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

    @bp.route('/rank_system', methods=('GET', 'POST'))
    @login_required
    def rank_system():
        if not current_user.is_authenticated or not is_staff_user(current_user.username):
            flash("You must be a staff member to view the rank system.")
            return redirect(url_for('auth.index'))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None
        results = []

        if request.method == 'POST':
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            try:
                cursor.execute(
                    """
                    SELECT d.username AS volunteer, COUNT(d.orderID) AS task_count
                    FROM Delivered d
                    JOIN Ordered o ON d.orderID = o.orderID
                    WHERE o.orderDate BETWEEN %s AND %s
                    GROUP BY d.username
                    ORDER BY task_count DESC
                    """,
                    (start_date, end_date)
                )
                results = cursor.fetchall()

                if not results:
                    error = "No tasks found in the given time period."
            except Exception as e:
                error = f"An error occurred: {e}"

            if error:
                flash(error)

        return render_template('auth/rank_system.html', results=results)

    @bp.route('/user_tasks', methods=('GET',))
    @login_required
    def user_tasks():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        orders = None
        user_role = None

        if current_user.is_authenticated:
            cursor.execute(
                """
                SELECT r.rDescription
                FROM Act a
                JOIN Role r ON a.roleID = r.roleID
                WHERE a.userName = %s
                """,
                (current_user.username,)
            )
            user_role = cursor.fetchone()

            if user_role:
                role_description = user_role['rDescription']

                if role_description == 'client':
                    cursor.execute(
                        """
                        SELECT o.orderID, o.orderDate, o.orderNotes, o.supervisor
                        FROM Ordered o
                        WHERE o.client = %s
                        """,
                        (current_user.username,)
                    )
                    orders = cursor.fetchall()


                elif role_description == 'staff':
                    cursor.execute(

                        """
                        SELECT o.orderID, o.orderDate, o.orderNotes, o.supervisor, u.first_name AS client_name
                        FROM Ordered o
                        JOIN User u ON o.client = u.username
                        WHERE o.supervisor = %s
                        """,

                        (current_user.username,)

                    )

                    staff_orders = cursor.fetchall()
                    cursor.execute(

                        """
                        SELECT o.orderID, o.orderDate, o.orderNotes, d.username AS volunteer, o.supervisor, u.first_name AS client_name
                        FROM Delivered d
                        JOIN Ordered o ON d.orderID = o.orderID
                        JOIN User u ON o.client = u.username
                        WHERE d.username = %s
                        """,

                        (current_user.username,)

                    )

                    delivered_orders = cursor.fetchall()

                    orders_dict = {order['orderID']: order for order in (staff_orders + delivered_orders)}
                    orders = list(orders_dict.values())

                elif role_description == 'volunteer':
                    cursor.execute(
                        """
                        SELECT o.orderID, o.orderDate, o.orderNotes, u.first_name AS client_name, o.supervisor
                        FROM Delivered d
                        JOIN Ordered o ON d.orderID = o.orderID
                        JOIN User u ON o.client = u.username
                        WHERE d.username = %s
                        """,
                        (current_user.username,)
                    )
                    orders = cursor.fetchall()

        return render_template('auth/user_tasks.html', orders=orders, user_role=user_role)

    return bp
