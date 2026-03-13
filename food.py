from flask import Flask, request, render_template, redirect, session, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure key

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="W@123",
        database="fwmsdb"
    )


@app.route('/')
def home1():
   return render_template('home.html')

@app.route('/')
def home():  # Changed function name to avoid conflict
    return redirect(url_for('admin_login'))

@app.route('/about')
def about():
    return render_template('about.html')

#Admin login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Query to check admin credentials
        cursor.execute("SELECT * FROM admin WHERE email = %s AND password = %s", (email, password))
        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' in session:
        return render_template('admin_dashboard.html')
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('admin_login'))
    

    
#contact    
@app.route("/contact_us", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            sql = "INSERT INTO contact_us (name, email, message) VALUES (%s, %s, %s)"
            values = (name, email, message)
            cursor.execute(sql, values)
            db.commit()
            flash("Feedback Submitted Successfully!", "success")
        except Exception as e:
            db.rollback()
            flash("Error submitting feedback: " + str(e), "danger")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for("contact_us"))

    return render_template("contact_us.html")

@app.route('/view_report')
def view_report():
    db = get_db_connection()  # Establish database connection
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name, email, message FROM contact_us")  # Fetch reports from contact_us table
    reports = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('view_report.html', reports=reports)  # Use the correct template file



@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        fullname = request.form['fullname']
        foodname = request.form['foodname']
        meal = request.form['meal']
        quantity = request.form['quantity']
        pickupdate = request.form['pickupdate']
        address = request.form['address']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Insert data into MySQL database
        sql = "INSERT INTO donate (fullname, foodname, meal, quantity, pickupdate, address) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (fullname, foodname, meal, quantity, pickupdate, address)

        cursor.execute(sql, values)
        db.commit()

        flash("Donation message has been successfully submitted!", "success")
        return redirect(url_for('donate'))

    return render_template('donate.html')


# Route to view food donations (for admin)
@app.route('/view_donations')
def view_donations():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM donate ORDER BY submitted_at DESC")
    donations = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('view_donations.html', donations=donations)


# Accept Donation
@app.route('/accept_donation/<int:donation_id>', methods=['POST'])
def accept_donation(donation_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("UPDATE donate SET status = 'Accepted' WHERE id = %s", (donation_id,))
        db.commit()
        flash("Donation accepted successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error accepting donation: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('view_donations'))

# Reject Donation
@app.route('/reject_donation/<int:donation_id>', methods=['POST'])
def reject_donation(donation_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("UPDATE donate SET status = 'Rejected' WHERE id = %s", (donation_id,))
        db.commit()
        flash("Donation rejected successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error rejecting donation: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('view_donations'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form['password']
        c_password = request.form['c_password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            sql = "INSERT INTO register (fullname, email, password, c_password) VALUES (%s, %s, %s, %s)"
            values = (fullname, email, password, c_password)
            cursor.execute(sql, values)
            db.commit()
            flash("Feedback Submitted Successfully!", "success")
        except Exception as e:
            db.rollback()
            flash("Error submitting feedback: " + str(e), "danger")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for("user_login"))

    return render_template("register.html")


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute('SELECT * FROM register WHERE email = %s AND password = %s', (email, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['email'] = account['email']
            return redirect(url_for('user_dashboard'))
        else:
            msg = 'Incorrect email/password!'
    return render_template('user_login.html', msg=msg)


@app.route('/user_dashboard')
def user_dashboard():
    if 'loggedin' in session:  # Check if the user is logged in
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            # Fetch user donations from the 'donate' table based on session user ID or email
            cursor.execute("SELECT * FROM register WHERE email = %s ORDER BY pickupdate DESC", (session['email'],))
            donations = cursor.fetchall()
        except Exception as e:
            flash(f"Error fetching donations: {str(e)}", "danger")
            donations = []  # Return an empty list in case of an error
        finally:
            cursor.close()
            db.close()
        
        return render_template('user_dashboard.html', donations=donations)
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('user_login'))
    

@app.route('/view_request')
def view_request():
    """Fetches donation requests from the database and renders the HTML page."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM donate")
    requests = cursor.fetchall()
    cursor.close()
    #conn.close()
    return render_template('view_request.html', requests=requests)

@app.route('/inquiry', methods=['GET', 'POST'])
def inquiry():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        inquiry_type = request.form['inquiry-type']
        message = request.form['message']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        sql = "INSERT INTO inquiry (fullname, email, inquiry_type, message) VALUES (%s, %s, %s, %s)"
        values = (fullname, email, inquiry_type, message)

        cursor.execute(sql, values)
        db.commit()

        return redirect(url_for('inquiry'))  # Redirect after submission

    return render_template('inquiry.html')

if __name__ == '__main__':
    app.run(debug=True)