import os
from bson import ObjectId
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, current_app, url_for
from werkzeug.utils import secure_filename
from . import mongo, ALLOWED_EXTENSIONS

views = Blueprint('views', __name__)


def allowed_file(filename):
    """ Function to check if uploaded image file from add_product() route has valid file extension. """

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.context_processor
def cart_counter():
    """ Shopping cart counter function"""
    cart_collection = mongo.db.cart

    cart_count = cart_collection.find({}).count()

    return dict(cart_count=cart_count)

@views.context_processor
def filter_counter():
    """ Filter counter function"""
    product_collection = mongo.db.products

    # Brand Filter
    park_tool_count = product_collection.find({"brand": "Park Tool"}).count()
    gt_count = product_collection.find({"brand": "GT"}).count()
    specialized_count = product_collection.find({"brand": "Specialized"}).count()
    trek_count = product_collection.find({"brand": "Trek"}).count()

    # Category Filter
    bike_count = product_collection.find({"productCategory": "Bike"}).count()
    clothing_count = product_collection.find({"productCategory": "Clothing"}).count()
    tools_count = product_collection.find({"productCategory": "Tools"}).count()

    # Color Filter
    black_count = product_collection.find({"color": "Black"}).count()
    blue_count = product_collection.find({"color": "Blue"}).count()
    grey_count = product_collection.find({"color": "Grey"}).count()
    yellow_count = product_collection.find({"color": "Yellow"}).count()
    white_count = product_collection.find({"color": "White"}).count()

    # Price Range Filter
    count0to1000 = product_collection.find({'price': {'$gte': 0, '$lt': 1000}}).count()
    count1000to2000 = product_collection.find({'price': {'$gte': 1000, '$lt': 2000}}).count()
    count2000to5000 = product_collection.find({'price': {'$gte': 2000, '$lt': 5000}}).count()
    count5000to10000 = product_collection.find({'price': {'$gte': 5000, '$lt': 10000}}).count()
    countover10000 = product_collection.find({'price': {'$gte': 10000}}).count()

    return dict(park_tool_count=park_tool_count,gt_count=gt_count,
                specialized_count=specialized_count, trek_count=trek_count,
                bike_count=bike_count, clothing_count=clothing_count,
                tools_count=tools_count, black_count=black_count,
                blue_count=blue_count, grey_count=grey_count,
                yellow_count=yellow_count, white_count=white_count,
                count0to1000=count0to1000, count1000to2000=count1000to2000,
                count2000to5000=count2000to5000, count5000to10000=count5000to10000,
                countover10000=countover10000)


@views.route('/', methods=['GET', 'POST'])
def home():
    """ Route to home page. Home page shows all products in the database and filter products based on
     the left column or the free-text search. If a product is added to cart, the function grabs
      the product _id, query the database for relevant data and create a document which is inserted to the
      cart collection. """

    product_collection = mongo.db.products
    products = product_collection.find()

    if request.method == 'POST':
        # If add to cart button is pressed, product info are inserted to the cart collection
        # and product status is sat to Sold
        add_to_cart = request.form.get('addToCart')
        if add_to_cart != None:
            product_collection = mongo.db.products
            objinstance = ObjectId(add_to_cart)
            product_in_cart = product_collection.find({'_id': objinstance})
            for p in product_in_cart:

                # Product information to be inserted to the cart collection.
                cart_dict = {
                    'ProductId': p['_id'],
                    'ProductName': p['productName'],
                    'ProductDesc': p['productDescription'],
                    'ProductSKU': p['sku'],
                    'ProductBrand': p['brand'],
                    'ProductPrice': p['price']
                }
                cart_collection = mongo.db.cart

                # Query to insert the variable cart_dict into the cart collection.
                cart_collection.insert_one(cart_dict)
                flash('Product added to Cart')

                # Update product status to sold, and make it unavailable for others. Button in home.html is
                # changed to Sold !.
                product_collection.update_one({'_id': objinstance}, {"$set": {"status": "Sold"}})
                print(objinstance)

        # free-text search which use a regular expression the check if the free-text search string is
        # present in any of the document fields. $options:i makes it case in-sensitive.
        free_text_search = request.form.get('productSearch')
        if len(free_text_search) > 0:
            regex = free_text_search
            myquery = {'$or': [{'tags': {'$regex': regex, '$options': 'i'}},
                               {'sku': {'$regex': regex, '$options': 'i'}},
                               {'productName': {'$regex': regex, '$options': 'i'}},
                               {'productCategory': {'$regex': regex, '$options': 'i'}},
                               {'productDescription': {'$regex': regex, '$options': 'i'}},
                               {'brand': {'$regex': regex, '$options': 'i'}},
                               {'color': {'$regex': regex, '$options': 'i'}}]}
            product_collection = mongo.db.products
            products = product_collection.find(myquery)

        else:
            # empty lists until checkbox is checked.
            brands = request.form.getlist('checkBrand')
            category = request.form.getlist('checkCategory')
            color = request.form.getlist('checkColor')
            price_range = request.form.getlist('checkPrice')

            # Placeholders for query. If lists are empty, return everything not in the empty list.
            # Which will return every product.
            brands_query = {'brand': {'$nin': brands}}
            category_query = {'productCategory': {'$nin': category}}
            color_query = {'color': {'$nin': color}}
            price_query = {'$gt': 0}

            # Check if checkbox is checked. If yes, update query to find every product in the list.
            if len(brands) > 0:
                brands_query = {'brand': {'$in': brands}}

            if len(category) > 0:
                category_query = {'productCategory': {'$in': category}}

            if len(color) > 0:
                color_query = {'color': {'$in': color}}

            if len(price_range) > 0:
                price_range_lower = price_range[0].split(',')[0]
                price_range_upper = price_range[0].split(',')[1]
                if price_range_upper == '>':
                    price_query = {'$gte': int(price_range_lower)}
                else:
                    price_query = {'$gte': int(price_range_lower), '$lt': int(price_range_upper)}

            # Query to return products which has all the checked boxes in the filter.
            # ex. brand AND category AND color etc.
            filterquery = {'$and': [brands_query, category_query, color_query, {'price': price_query}]}

            product_collection = mongo.db.products
            products = product_collection.find(filterquery)


    return render_template("home.html", products=products)





@views.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """ Route to add_product page. Add_product page has a form to enter product details and insert it to the database.
     It is also requiered to upload a product image. The product image is stored in /static/uploads folder and the
     filename is stored in the database as a reference."""

    if request.method == 'POST':
        product_collection = mongo.db.products

        # Grab input from add_product form
        productname = request.form.get('productName')
        productdescription = request.form.get('productDescription')
        sku = request.form.get('sku')
        productcategory = request.form.get('productCategory')
        brand = request.form.get('brand')
        color = request.form.get('color')
        price = request.form.get('price', type=int)
        tags = request.form.get('tags')

        # split tags and make a list variable
        tags_list = tags.split(',')
        tags_list = [x.strip() for x in tags_list]

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # grab uploaded product image and check if file extension is valid
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file, please upload product picture', category='danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):

            # obtain a secure version of the filename through the secure_filename function
            filename = secure_filename(file.filename)

            # identify path to uploads folder
            path = os.path.join(current_app.root_path, 'static/uploads', filename)

            # save image to uploads folder
            file.save(path)
        else:
            filename = ''
            flash('Product image not added!', category='danger')

        # Query to insert a new product into product collection in the database
        product_collection.insert_one({'productName': productname, 'productDescription': productdescription,
                                       'sku': sku, 'productCategory': productcategory, 'brand': brand,
                                       'price': price,
                                       'color': color,
                                       'tags': tags_list, 'imageFile': filename, 'status': 'Available'})
        flash('Product added!', category='success')
        return redirect(url_for('views.add_product'))
    return render_template('add_product.html')


@views.route('/cart', methods=['GET', 'POST'])
def cart():
    """ Route to cart page. Cart page list all products from the cart collection. Further, you can send products to
    checkout collection or remove products from the cart. Removed products will have status updated to Available"""

    cart_collection = mongo.db.cart
    checkout_collection = mongo.db.checkout
    cart = cart_collection.find({})
    if request.method == 'POST':


        # delete product from cart collection if delete button is pressed. Grab product _id and remove product
        # from cart collection in the database

        delete_from_cart = request.form.get('deleteFromCart')
        objinstance = ObjectId(delete_from_cart)
        product_collection = mongo.db.products
        productid = cart_collection.find_one({'_id':objinstance})
        if productid != None:
            product_collection.update_one({'_id': productid['ProductId']}, {"$set": {"status": "Available"}})
        cart_collection.delete_one({'_id': objinstance})
        flash('Product removed from cart', category='danger')

        empty_cart = request.form.get('emptyCart')
        checkout = request.form.get('checkOut')

        # if empty cart button is pressed, all products in the cart are removed. And all products have their
        # status updated to Available
        if empty_cart == 'emptyCart':

            cart_list = cart_collection.find({})
            cart_id_list = []

            for product in cart_list:
                cart_id_list.append(ObjectId(product['ProductId']))

            for id in cart_id_list:
                product_collection.update_one({'_id': id},{"$set": {"status": "Available"}})

            cart_collection.delete_many({})
            flash('Shopping Cart is empty', category='danger')

        # if checkout button is pressed, all products in cart are inserted into the checkout collection
        # and removed from the cart collection
        cart_count = cart_collection.find().count()
        if checkout == 'checkOut' and cart_count > 0:
            checkout_list = []
            for product in cart:
                checkout_dict = {
                    'ProductId': product['ProductId'],
                    'ProductName': product['ProductName'],
                    'ProductDesc': product['ProductDesc'],
                    'ProductSKU': product['ProductSKU'],
                    'ProductBrand': product['ProductBrand'],
                    'ProductPrice': product['ProductPrice']
                }
                checkout_list.append(checkout_dict)

            # insert products from cart collection into checkout collection
            checkout_collection.insert_many(checkout_list)
            cart_collection.delete_many({})
            flash('Shopping cart checkout', category='success')

            # redirect customer to checkout page
            return redirect(url_for('views.checkout'))

    return render_template('cart.html', cart=cart)


@views.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """ Route to checkout page. Checkout page list all products from the checkout collection and serves as a summary
        before order is placed. If customer would like to do changes before order is placed, shopping cart
        will be restored and checkout collection empty. """

    checkout_collection = mongo.db.checkout
    cart_collection = mongo.db.cart
    order_collection = mongo.db.order
    customer_collection = mongo.db.customer

    checkout = checkout_collection.find({})
    customer = customer_collection.find_one({})

    # Display Current total of products in checkout collection
    current_total = 0
    pipe = [{'$group': {'_id': None, 'total': {'$sum': '$ProductPrice'}}}]
    total_sum = checkout_collection.aggregate(pipeline=pipe)
    for i in total_sum:
        current_total = i['total']

    if request.method == 'POST':

        # If continue shopping button is pressed, products in checkout collection will be inserted into
        # cart collection and checkout collection will be empty.
        continue_shopping = request.form.get('continueShopping')

        if continue_shopping == 'continueShopping':
            continue_list = []
            for product in checkout:
                continue_dict = {
                    'ProductId': product['ProductId'],
                    'ProductName': product['ProductName'],
                    'ProductDesc': product['ProductDesc'],
                    'ProductSKU': product['ProductSKU'],
                    'ProductBrand': product['ProductBrand'],
                    'ProductPrice': product['ProductPrice']
                }
                continue_list.append(continue_dict)
            cart_collection.insert_many(continue_list)
            checkout_collection.delete_many({})
            flash('Shopping cart restored, continue shopping.', category='success')
            return redirect(url_for('views.cart'))

        # If place order button is pressed, all products in checkout collection will be inserted into
        # productDetails in order collection. Further a timestamp will be added as OrderDate and customer
        # is supposed to be the logged in user. Logged in user functionality must be added.

        place_order = request.form.get('placeOrder')
        if place_order == 'placeOrder':
            order_list = []
            for product in checkout:
                order_dict = {
                    'ProductId': product['ProductId'],
                    'ProductName': product['ProductName'],
                    'ProductDesc': product['ProductDesc'],
                    'ProductSKU': product['ProductSKU'],
                    'ProductBrand': product['ProductBrand'],
                    'ProductPrice': product['ProductPrice']
                }
                order_list.append(order_dict)

            order_date = datetime.now()
            customer_name = customer['CustomerName']
            customer_address = f'{customer["Address"]},{customer["ZipCode"]} ' \
                               f'{customer["City"]}, {customer["Country"]}'

            # status variable  is default set to Pending. May be updated based on payment, delivery etc.
            status = 'Pending'
            product_details = order_list

            # Query to insert data to order collection.
            order_collection.insert_one({"OrderDate": order_date, "CustomerName": customer_name,
                                         "CustomerAddress": customer_address, "Status": status, "ProductDetails": product_details})


            # Calculate Total Order
            current_order = order_collection.find_one({"OrderDate": order_date, "CustomerName": customer_name,
                                         "CustomerAddress": customer_address})
            order_total = 0
            for i in current_order['ProductDetails']:
                order_total = order_total + i['ProductPrice']

            order_collection.update_one({'_id': current_order['_id']},{"$set": {"OrderTotal": order_total}})

            # Empty checkout collection when order is placed.
            checkout_collection.delete_many({})
            flash('Order placed! ', category='success')

            # Redirect customer to order page.
            return redirect(url_for('views.order'))

    return render_template('checkout.html', checkout=checkout, current_total=current_total)


@views.route('/order', methods=['GET', 'POST'])
def order():
    """ Route to order page. Order page list all orders. Customer can sort orders by total high-low/low-high
     and date new-old/old-new"""

    order_collection = mongo.db.order

    order = order_collection.find({}).sort('OrderDate', -1)


    # Sort by function

    if request.method == 'POST':
        sortby = request.form.get('search_type')

        if sortby == 'orderHighLow':
            order = order_collection.find({}).sort('OrderTotal', -1)

        if sortby == 'orderLowHigh':
            order = order_collection.find({}).sort('OrderTotal', 1)

        if sortby == 'dateNewOld':
            order = order_collection.find({}).sort('OrderDate', -1)

        if sortby == 'dateOldNew':
            order = order_collection.find({}).sort('OrderDate', 1)

    return render_template('order.html', order=order)
