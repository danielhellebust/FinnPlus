from flask import Blueprint, render_template, request, flash, redirect, url_for

# import db object from root folder
from . import mongo

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """ Route to login page. Function checks if username and password exist in database
     and flash a login message if successful. The function does not perform any login logic except flashing message.
     This functionality must be developed. """

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(email, password)

        customers = mongo.db.customer.find({"_id": email})
        for customer in customers:
            if customer['Password'] == password:
                flash('Logged in successfully', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Password is incorrect', category='danger')

    return render_template('login.html', boolean=True)


@auth.route('/logout')
def logout():
    """ Route to logout a logged in user. The function does not perform any logout logic
    except redirecting to an empty page. This functionality must be developed. """
    return "<p>Logout</p>"


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """ Route to sign_up form page. This function grabs all input from the signup form and
     does simple validation of email password fields. If validation is successful,
     a new customer is added to the customer collection in the MongoDB database.
     NB! Password is stored as plain text and must be encrypted for security reasons """

    if request.method == 'POST':
        customer_collection = mongo.db.customer

        # Grab input from sign_up form
        email = request.form.get('email')
        name = request.form.get('name')
        address = request.form.get('address')
        zipcode = request.form.get('zipCode')
        city = request.form.get('city')
        country = request.form.get('country')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if len(email) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(name) < 2:
            flash('First name must be greater than 1 characters', category='error')
        elif password1 != password2:
            flash('Passwords do not match', category='error')
        elif len(password1) < 7:
            flash('Passwords musty be at least 7 characters', category='error')
        else:
            # Insert query for a new customer in the database. Email is set as a primary key and _id for the document.
            # Password is plain text and must be encrypted for security reasons.
            customer_collection.insert_one({"_id": email, "CustomerName": name, "Address": address, "ZipCode": zipcode,
                                            "City": city, "Country": country, "Password": password1})
            flash('Account created!', category='success')

            # If successful sign_up, customer is redirected to the login page.
            return redirect(url_for('auth.login'))

    return render_template('sign_up.html')
