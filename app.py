from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session


def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=DESKTOP-0BOKRG9\\SQLEXPRESS;'
        'DATABASE=cattle_farm;'
        'Trusted_Connection=yes;'
        'Encrypt=no;'
    )
    return conn

# home page


@app.route('/')
def home():
    return render_template('home.html')


# login page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserID, Username, Password, Role FROM Users WHERE Username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        # Basic match (you can replace with hashing later)
        if row and password == row[2]:
            session['username'] = row[1]
            session['role'] = row[3]
            return redirect(url_for('home'))
        else:
            return "Invalid username or password."
    return render_template('login.html')

# logout page


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------- USERS --------------------


@app.route('/users')
def users():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied. Admins only."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, Username, FullName, Email, Role FROM Users")
    rows = cursor.fetchall()
    users = [dict(UserID=row[0], Username=row[1], FullName=row[2],
                  Email=row[3], Role=row[4]) for row in rows]
    conn.close()
    return render_template('users.html', users=users)


@app.route('/add_user', methods=['POST'])
def add_user():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    username = request.form['username']
    fullname = request.form['fullname']
    email = request.form['email']
    role = request.form['role']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Users (Username, Password, FullName, Email, Role)
        VALUES (?, ?, ?, ?, ?)
    """, (username, password, fullname, email, role))
    conn.commit()
    conn.close()

    return redirect(url_for('users'))


@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    username = request.form['username']
    fullname = request.form['fullname']
    email = request.form['email']
    role = request.form['role']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Users
        SET Username = ?, FullName = ?, Email = ?, Role = ?
        WHERE UserID = ?
    """, (username, fullname, email, role, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('users'))


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Users WHERE UserID = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('users'))

# -------------------- Milk_collection --------------------


@app.route('/milk_collection')
def milk_collection():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied. Admins only."

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mc.CollectionID, a.AnimalName, mc.AnimalID, mc.Date, mc.QuantityLitres
        FROM MilkCollection mc
        JOIN Animals a ON mc.AnimalID = a.AnimalID
    """)
    rows = cursor.fetchall()
    records = [dict(ID=row[0], Animal=row[1], AnimalID=row[2],
                    Date=row[3], Qty=row[4]) for row in rows]

    cursor.execute("SELECT AnimalID, AnimalName FROM Animals")
    animals = cursor.fetchall()
    animals = [dict(id=row[0], name=row[1]) for row in animals]

    conn.close()
    return render_template('milk_collection.html', records=records, animals=animals)


@app.route('/add_milk', methods=['POST'])
def add_milk():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    animal_id = request.form['animal_id']
    date = request.form['date']
    qty = request.form['quantity']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO MilkCollection (AnimalID, Date, QuantityLitres)
        VALUES (?, ?, ?)
    """, (animal_id, date, qty))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_collection'))


@app.route('/update_milk/<int:id>', methods=['POST'])
def update_milk(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    animal_id = request.form['animal_id']
    date = request.form['date']
    qty = request.form['quantity']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE MilkCollection
        SET AnimalID=?, Date=?, QuantityLitres=?
        WHERE CollectionID=?
    """, (animal_id, date, qty, id))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_collection'))


@app.route('/delete_milk/<int:id>')
def delete_milk(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM MilkCollection WHERE CollectionID=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_collection'))

 # -------------------- Milk_sale --------------------


@app.route('/milk_sale')
def milk_sale():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SaleID, Date, QuantityLitres, PricePerLitre, (QuantityLitres * PricePerLitre) AS TotalAmount FROM MilkSale")
    rows = cursor.fetchall()
    records = [
        dict(ID=row[0], Date=row[1], Qty=row[2], Price=row[3], Total=row[4])
        for row in rows
    ]
    conn.close()
    return render_template('milk_sale.html', records=records)


@app.route('/add_sale', methods=['POST'])
def add_sale():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    date = request.form['date']
    qty = float(request.form['quantity'])
    price = float(request.form['price'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO MilkSale (Date, QuantityLitres, PricePerLitre) VALUES (?, ?, ?)", (date, qty, price))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_sale'))


@app.route('/update_sale/<int:id>', methods=['POST'])
def update_sale(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    date = request.form['date']
    qty = float(request.form['quantity'])
    price = float(request.form['price'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE MilkSale SET Date=?, QuantityLitres=?, PricePerLitre=? WHERE SaleID=?", (date, qty, price, id))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_sale'))


@app.route('/delete_sale/<int:id>')
def delete_sale(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM MilkSale WHERE SaleID=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_sale'))


# -------------------- Expenses --------------------
@app.route('/expenses')
def expenses():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ExpenseID, Date, ExpenseType, Amount, Description FROM Expense")
    rows = cursor.fetchall()
    records = [
        dict(ID=row[0], Date=row[1], Type=row[2],
             Amount=row[3], Description=row[4])
        for row in rows
    ]
    conn.close()
    return render_template('expenses.html', records=records)


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    date = request.form['date']
    type_ = request.form['type']
    amount = request.form['amount']
    description = request.form['description']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Expense (Date, ExpenseType, Amount, Description) VALUES (?, ?, ?, ?)",
                   (date, type_, amount, description))
    conn.commit()
    conn.close()
    return redirect(url_for('expenses'))


@app.route('/update_expense/<int:id>', methods=['POST'])
def update_expense(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    date = request.form['date']
    type_ = request.form['type']
    amount = request.form['amount']
    description = request.form['description']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Expense
        SET Date=?, ExpenseType=?, Amount=?, Description=?
        WHERE ExpenseID=?
    """, (date, type_, amount, description, id))
    conn.commit()
    conn.close()
    return redirect(url_for('expenses'))


@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Expense WHERE ExpenseID=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('expenses'))


# -------------------- Profit and Loss Report --------------------
@app.route('/profit_loss')
def profit_loss():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(s.Date, e.Date) AS Date,
            ISNULL(SUM(s.QuantityLitres * s.PricePerLitre), 0) AS TotalIncome,
            ISNULL(SUM(e.Amount), 0) AS TotalExpense,
            ISNULL(SUM(s.QuantityLitres * s.PricePerLitre), 0) - ISNULL(SUM(e.Amount), 0) AS NetProfit
        FROM MilkSale s
        FULL OUTER JOIN Expense e ON s.Date = e.Date
        GROUP BY COALESCE(s.Date, e.Date)
        ORDER BY Date DESC
    """)
    rows = cursor.fetchall()
    reports = [dict(Date=row[0], Income=row[1], Expense=row[2],
                    Profit=row[3]) for row in rows]
    conn.close()
    return render_template('profit_loss.html', reports=reports)


# -------------------- register--------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        email = request.form['email']
        role = 'User'  # All registered users default to User

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return "Username already exists. Try a different one."

        # Insert new user
        cursor.execute("""
            INSERT INTO Users (Username, Password, FullName, Email, Role)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, fullname, email, role))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# Route: View Animal Profile (for Admin + User)

@app.route('/animal_profile/<int:animal_id>')
def animal_profile(animal_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get animal info
    cursor.execute("""
        SELECT a.AnimalID, a.AnimalName, at.TypeName, a.DOB, a.Weight, a.HealthStatus,a.price
        FROM Animals a
        JOIN AnimalType at ON a.AnimalTypeID = at.AnimalTypeID
        WHERE a.AnimalID = ?
    """, (animal_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Animal not found", 404

    animal = {
        'AnimalID': row[0],
        'AnimalName': row[1],
        'TypeName': row[2],
        'DOB': row[3],
        'Weight': row[4],
        'HealthStatus': row[5],
        'Price': row[6]
    }

    # Vaccination records
    cursor.execute("""
        SELECT VaccineName, Date, NextDueDate
        FROM VaccinationRecord
        WHERE AnimalID = ?
        ORDER BY Date DESC
    """, (animal_id,))
    vaccinations = [dict(VaccineName=r[0], Date=r[1], NextDueDate=r[2])
                    for r in cursor.fetchall()]

    # Health check records
    cursor.execute("""
        SELECT Date, Diagnosis, Treatment
        FROM HealthCheck
        WHERE AnimalID = ?
        ORDER BY Date DESC
    """, (animal_id,))
    health_checks = [dict(Date=r[0], Diagnosis=r[1], Treatment=r[2])
                     for r in cursor.fetchall()]

    # Feeding records
    cursor.execute("""
        SELECT Date, FeedType, QuantityKg
        FROM FeedingRecord
        WHERE AnimalID = ?
        ORDER BY Date DESC
    """, (animal_id,))
    feedings = [dict(Date=r[0], FeedType=r[1], QuantityKg=r[2])
                for r in cursor.fetchall()]

    conn.close()

    return render_template(
        'animal_profile.html',
        animal=animal,
        vaccinations=vaccinations,
        health_checks=health_checks,
        feedings=feedings
    )


# Route: View Animals (for Admin + User)
@app.route('/animals')
def animals():
    if 'username' not in session:
        return redirect(url_for('login'))  # allow both Admin and User

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get animals list
    cursor.execute("""
        SELECT a.AnimalID, a.AnimalName, a.DOB, a.Weight, a.HealthStatus,
               at.TypeName AS AnimalType, a.AnimalTypeID,a.price
        FROM Animals a
        JOIN AnimalType at ON a.AnimalTypeID = at.AnimalTypeID
    """)
    animals = [dict(
        AnimalID=row[0],
        AnimalName=row[1],
        DOB=row[2],
        Weight=row[3],
        HealthStatus=row[4],
        AnimalType=row[5],
        AnimalTypeID=row[6],
        Price=row[7]
    ) for row in cursor.fetchall()]

    # Get types
    cursor.execute(
        "SELECT AnimalTypeID AS id, TypeName AS name FROM AnimalType")
    types = [dict(id=r[0], name=r[1]) for r in cursor.fetchall()]

    conn.close()

    return render_template('animals.html', animals=animals, types=types)


# buy animal

@app.route('/buy_animal/<int:animal_id>', methods=['GET', 'POST'])
def buy_animal(animal_id):
    if 'username' not in session or session.get('role') != 'User':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get animal details to show on the form
    cursor.execute("""
        SELECT a.AnimalID, a.AnimalName, at.TypeName
        FROM Animals a
        JOIN AnimalType at ON a.AnimalTypeID = at.AnimalTypeID
        WHERE a.AnimalID = ?
    """, (animal_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Animal not found", 404

    animal = {
        'AnimalID': row[0],
        'AnimalName': row[1],
        'TypeName': row[2]
    }

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        cursor.execute("""
            INSERT INTO AnimalOrders (AnimalID, CustomerName, Email, Phone)
            VALUES (?, ?, ?, ?)
        """, (animal_id, name, email, phone))
        conn.commit()
        conn.close()

        return "Thank you! Your request to buy this Animal has been submitted and is pending approval."

    conn.close()
    return render_template('buy_animal.html', animal=animal)

# animal order


@app.route('/animal_orders')
def animal_orders():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied. Admins only."

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT o.OrderID, o.CustomerName, o.Email, o.Phone, o.PurchaseDate, o.Status,
               a.AnimalName, at.TypeName
        FROM AnimalOrders o
        JOIN Animals a ON o.AnimalID = a.AnimalID
        JOIN AnimalType at ON a.AnimalTypeID = at.AnimalTypeID
        ORDER BY o.PurchaseDate DESC
    """)
    orders = [dict(
        OrderID=r[0],
        CustomerName=r[1],
        Email=r[2],
        Phone=r[3],
        PurchaseDate=r[4],
        Status=r[5],
        AnimalName=r[6],
        TypeName=r[7]
    ) for r in cursor.fetchall()]

    conn.close()
    return render_template('animal_orders.html', orders=orders)

# accept or reject the order


@app.route('/update_order_status/<int:order_id>/<string:new_status>')
def update_order_status(order_id, new_status):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied. Admins only."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE AnimalOrders SET Status = ? WHERE OrderID = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('animal_orders'))


# add_animal

@app.route('/add_animal', methods=['POST'])
def add_animal():
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied", 403

    name = request.form['animal_name']
    animal_type = request.form['animal_type']
    dob = request.form['dob']
    weight = request.form['weight']
    health_status = request.form['health_status']
    price = request.form['price']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Animals (AnimalName, AnimalTypeID, DOB, Weight, HealthStatus, Price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, animal_type, dob, weight, health_status, price))
    conn.commit()
    conn.close()
    return redirect(url_for('animals'))

# update animal


@app.route('/update_animal/<int:animal_id>', methods=['POST'])
def update_animal(animal_id):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied", 403

    name = request.form['animal_name']
    animal_type = request.form['animal_type']
    dob = request.form['dob']
    weight = request.form['weight']
    health_status = request.form['health_status']
    price = request.form.get('price')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Animals
        SET AnimalName = ?, AnimalTypeID = ?, DOB = ?, Weight = ?, HealthStatus = ?, Price = ?
        WHERE AnimalID = ?
    """, (name, animal_type, dob, weight, health_status, price, animal_id))
    conn.commit()
    conn.close()
    return redirect(url_for('animals'))

# payment method


@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    if 'username' not in session or session.get('role') != 'User':
        return redirect(url_for('login'))

    if request.method == 'POST':
        payment_method = request.form['payment_method']
        # Optionally save payment method or show confirmation
        return "Thank you! Your payment method was selected: " + payment_method

    return render_template('payment.html', order_id=order_id)


# User Places a Milk Order
@app.route('/milk_order', methods=['GET', 'POST'])
def milk_order():
    if 'username' not in session or session.get('role') != 'User':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        quantity = request.form['quantity']
        price = request.form['price']
        method = request.form['payment_method']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MilkOrder (CustomerName, Email, Phone, QuantityLitres, PricePerLitre, PaymentMethod)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, phone, quantity, price, method))
        conn.commit()
        conn.close()

        return "Your milk order has been placed. Await admin approval."

    return render_template('milk_order.html')
# Admin View for Pending Orders


@app.route('/milk_orders')
def milk_orders():
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT OrderID, CustomerName, Email, Phone, OrderDate, QuantityLitres, PricePerLitre, TotalAmount, Status, PaymentMethod
        FROM MilkOrder ORDER BY OrderDate DESC
    """)
    orders = [dict(
        OrderID=r[0],
        CustomerName=r[1],
        Email=r[2],
        Phone=r[3],
        OrderDate=r[4],
        QuantityLitres=r[5],
        PricePerLitre=r[6],
        TotalAmount=r[7],
        Status=r[8],
        PaymentMethod=r[9]
    ) for r in cursor.fetchall()]
    conn.close()
    return render_template('milk_orders.html', orders=orders)
# Admin Status Update Route


@app.route('/update_milk_order/<int:order_id>/<string:new_status>')
def update_milk_order(order_id, new_status):
    if 'username' not in session or session.get('role') != 'Admin':
        return "Access denied."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE MilkOrder SET Status = ? WHERE OrderID = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('milk_orders'))


if __name__ == '__main__':
    app.run(debug=True)
