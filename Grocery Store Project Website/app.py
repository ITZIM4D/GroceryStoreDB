from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

bcrypt = Bcrypt(app) 

db = mysql.connector.connect(
    host='localhost',
    user='root',
    database='GroceryStore'
)
cursor = db.cursor()


@app.route('/')
def home():
    if 'username' in session:
        employee_id = session['username']
        query = "SELECT name, position FROM employee WHERE employee_id = %s"
        cursor.execute(query, (employee_id,))
        result = cursor.fetchone()

        if result:
            session['job_title'] = result[1]
            employee_name, job_title = result

            if job_title == 'Manager':
                return render_template('home_admin.html', employee_name=employee_name, job_title=job_title)
            else:
                return render_template('home_user.html', employee_name=employee_name, job_title=job_title)

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT password FROM employee WHERE employee_id=%s', (username,))
        hashed_password = cursor.fetchone()
        is_valid = bcrypt.check_password_hash(hashed_password[0], password)

        if is_valid:
            cursor.execute('SELECT * FROM employee WHERE employee_id=%s', (username,))
            user = cursor.fetchone()

            if user:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return 'Invalid login credentials'

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        

        if request.method == 'POST' and request.form['action'] == 'New Register':
            starting_cash = request.form['starting_cash']
            current_cash = request.form['current_cash']

            cursor.execute('INSERT INTO register (starting_cash, current_cash) VALUES (%s, %s)',
                           (starting_cash, current_cash))
            db.commit()
        cursor.execute('SELECT register_id, starting_cash, current_cash FROM register')
        register_info = cursor.fetchall()

        

        if request.method == 'POST' and request.form['action'] == 'New Transaction':
            register_id = request.form['register']
            barcode = request.form['barcode']
            receipt_number = request.form['receipt_number']
            transaction_date = request.form['transaction_date']

            cursor.execute('INSERT INTO sells (register_id, barcode, receipt_number, transaction_date) VALUES (%s, %s, %s, %s)',
                           (register_id, barcode, receipt_number, transaction_date))
            db.commit()

        cursor.execute('SELECT register_id, barcode, receipt_number, transaction_date FROM sells')
        transaction_info = cursor.fetchall()

        

        if request.method == 'POST' and request.form['action'] == 'New Employee Register':
            employee_id = request.form['employee_id']
            register_id = request.form['register']

            cursor.execute('INSERT INTO operates (employee_id, register_id) VALUES (%s, %s)',
                           (employee_id, register_id))
            db.commit()

        cursor.execute('SELECT e.name, o.register_id FROM operates as o, employee as e WHERE o.employee_id = e.employee_id')
        employee_info = cursor.fetchall()

        return render_template('register.html',
                               register_info=register_info,
                               transaction_info=transaction_info,
                               employee_info=employee_info)
    else:
        return 'Access Denied: You do not have the required permissions.'
    
    
@app.route('/employees', methods=['GET', 'POST'])
def employees():
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        if request.method == 'POST':
            if '_method' in request.form and request.form['_method'] == 'DELETE':
                employee_id = request.form['delete_employee_id']
                cursor.execute('DELETE FROM employee WHERE employee_id = %s', (employee_id,))
                db.commit()
            else:
                password = request.form['password']
                name = request.form['name']
                position = request.form['position']
                salary = request.form['salary']
            
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # encrypts the password

                cursor.execute('INSERT INTO employee (password, name, position, salary) VALUES (%s, %s, %s, %s)',
                               (hashed_password, name, position, salary))
                db.commit()

        cursor.execute('SELECT employee_id, salary, name, position, password FROM employee')
        employee_info = cursor.fetchall()

        return render_template('employees.html', employee_info=employee_info)
    else:
        return render_template('restricted_access.html')


@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        
        
        if request.method == 'POST':
            if '_method' in request.form and request.form['_method'] == 'DELETE':
                customer_id = request.form['delete_customer_id']
                cursor.execute('DELETE FROM customer WHERE customer_id = %s', (customer_id,))
                db.commit()
            else:
                phone_number = request.form['phone_number']
                address = request.form['address']
                name = request.form['name']

                cursor.execute('INSERT INTO customer (phone_number, address, name) VALUES (%s, %s, %s)',
                               (phone_number, address, name))
                db.commit()

        cursor.execute('SELECT customer_id, phone_number, address, name FROM customer')
        customer_info = cursor.fetchall()   
        
        return render_template('customers.html',
                            customer_info = customer_info)
    else:
        return render_template('restricted_access.html')


@app.route('/assisted_by', methods=['GET', 'POST'])
def assisted_by():
    
    if 'username' in session:
        if request.method == 'POST':
            if 'action' in request.form and request.form['action'] == 'New Review':
                customer_id = request.form['customer_id']
                employee_id = request.form['employee_id']
                service_rating = request.form['service_rating']

                cursor.execute('INSERT INTO assisted_by (customer_id, employee_id, service_rating) VALUES (%s, %s, %s)',
                               (customer_id, employee_id, service_rating))
                db.commit()

            elif 'action' in request.form and request.form['action'] == 'Delete':
                customer_id = request.form['delete_customer_id']
                employee_id = request.form['delete_employee_id']

                cursor.execute('DELETE FROM assisted_by WHERE customer_id = %s AND employee_id = %s',
                               (customer_id, employee_id))
                db.commit()

        cursor.execute('SELECT customer_id, employee_id, service_rating FROM assisted_by')
        assistance_info = cursor.fetchall()
                
        return render_template('assisted_by.html',
                            assistance_info = assistance_info)
    else:
        return render_template('not_logged_in.html')


@app.route('/purchases', methods=['GET', 'POST'])
def purchases():
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        
        
        if request.method == 'POST':
            if '_method' in request.form and request.form['_method'] == 'DELETE':
                customer_id = request.form['delete_customer_id']
                barcode = request.form['delete_barcode']
                cursor.execute('DELETE FROM purchases WHERE customer_id = %s AND barcode = %s', (customer_id, barcode))
                db.commit()
            else:
                customer_id = request.form['customer_id']
                barcode = request.form['barcode']
                purchase_date = request.form['purchase_date']
                quantity = request.form['quantity']

                cursor.execute('INSERT INTO purchases (customer_id, barcode, purchase_date, quantity) VALUES (%s, %s, %s, %s)',
                               (customer_id, barcode, purchase_date, quantity))
                db.commit()

        cursor.execute('SELECT customer_id, barcode, purchase_date, quantity FROM purchases')
        purchase_info = cursor.fetchall()
            
        return render_template('purchases.html',
                            purchase_info = purchase_info)
    else:
        return render_template('restricted_access.html')


@app.route('/supplier', methods=['GET', 'POST'])
def supplier():
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        
        
        if request.method == 'POST':
            if '_method' in request.form and request.form['_method'] == 'DELETE':
                supplier_id = request.form['delete_supplier_id']
                cursor.execute('DELETE FROM supplier WHERE supplier_id = %s', (supplier_id,))
                db.commit()
            else:
                supplier_id = request.form['supplier_id']
                delivery_day = request.form['delivery_day']
                company_name = request.form['company_name']

                cursor.execute('INSERT INTO supplier (supplier_id, delivery_day, company_name) VALUES (%s, %s, %s)',
                               (supplier_id, delivery_day, company_name))
                db.commit()

        cursor.execute('SELECT supplier_id, delivery_day, company_name FROM supplier')
        supplier_info = cursor.fetchall()
            
        return render_template('supplier.html',
                            supplier_info = supplier_info)
    else:
        return render_template('restricted_access.html')


@app.route('/product', methods=['GET', 'POST'])
def product():
    
    if 'username' in session and 'job_title' in session and session['job_title'] == 'Manager':
        if request.method == 'POST':
            if '_method' in request.form and request.form['_method'] == 'DELETE':
                barcode = request.form['delete_barcode']
                cursor.execute('DELETE FROM product WHERE barcode = %s', (barcode,))
                db.commit()
            else:
                barcode = request.form['barcode']
                name = request.form['name']
                price = request.form['price']
                product_type = request.form['product_type']
                brand = request.form['brand']
                aisle_number = request.form['aisle_number']
                supplier_id = request.form['supplier_id']
                supply_price = request.form['supply_price']
                supply_quantity = request.form['supply_quantity']

                cursor.execute('INSERT INTO product (barcode, name, price, product_type, brand, aisle_number, supplier_id, supply_price, supply_quantity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                               (barcode, name, price, product_type, brand, aisle_number, supplier_id, supply_price, supply_quantity))
                db.commit()
        cursor.execute('SELECT barcode, name, price, product_type, brand, aisle_number, supplier_id, supply_price, supply_quantity FROM product')
        product_info = cursor.fetchall()
                
        return render_template('product_admin.html',
                            product_info = product_info)
        
    if 'username' in session and 'job_title' in session and session['job_title'] != 'Manager':
        cursor.execute('SELECT barcode, name, price, product_type, brand, aisle_number, supplier_id, supply_price, supply_quantity FROM product')
        product_info = cursor.fetchall()
                
        return render_template('product_user.html',
                            product_info = product_info)
        
    else:
        return render_template('not_logged_in.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
