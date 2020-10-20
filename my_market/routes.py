from my_market import app, db, models, forms, mail
from flask_mail import Message
import flask
import flask_login
from flask_login import login_required
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug import security


@app.route('/')
def home():
    page = flask.request.args.get('page', 1, type=int)
    products = models.Product.query.order_by(models.Product.date_posted.desc()).paginate(page=page, per_page=40)
    # for item in products.items:
    #     if item.category == 'Laptops':
    #         print(item.id)
    return flask.render_template('home.jin', products=products)


""" with the user id it gets the all products list the loop through it and change the owner attributes!"""


@app.route('/user_account/<user_id>', methods=['GET', 'POST'])
def user_account(user_id):
    print(user_id)
    user_from_db = models.User.query.get(user_id)
    print(user_from_db.userstuffs[0].id) # IMPORTANT BE CARE FULL 'IS IS A LIST use [0 or 1 ...]'
    all_ordered_obj = user_from_db.userstuffs
    print(" all_stuffs ===> ",all_ordered_obj)
    for stf in all_ordered_obj:
        print(stf.phone)
    form = forms.ResetAddres()
    if flask.request.method == 'GET':
        form.fullname.data = user_from_db.userstuffs[0].name
        form.email.data    = user_from_db.userstuffs[0].email
        form.address.data  = user_from_db.userstuffs[0].address
        form.phone.data    = user_from_db.userstuffs[0].phone
        flask.flash('Resetting Address....', 'warning')
        return flask.render_template('user_account.jin', reset_address=form)
    else:
        if form.validate_on_submit():
            for stf in all_ordered_obj:
                stf.name    = form.fullname.data
                stf.email   = form.email.data
                stf.address = form.address.data
                stf.phone   = form.phone.data

            db.session.commit()
            flask.flash('your address has been reset Successfully', "success")
            return flask.redirect(flask.url_for('home'))
        return flask.render_template('user_account.jin', reset_address=form)


@app.route("/signin", methods=('GET', 'POST'))
def signin():
    form = forms.SignIn()
    if flask.request.method == "GET":
        return flask.render_template('signin.jin', signinform=form)

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = models.User.check_signin(username, password)
        if user:
            flask.flash(f"Welcome -> {username} <- logged in successfully 'Now you can order products'!", 'info')
            flask_login.login_user(user)
            return flask.redirect(flask.url_for('home'))
        else:
            flask.flash("Invalid username/password combination", 'warning')
            return flask.redirect(flask.url_for('signin'))

    else:
        flask.flash("Invalid form!", 'warning')
        return flask.render_template('signin.jin', signinform=form)


@app.route("/signup", methods=('GET', 'POST'))
def signup():
    form = forms.Signup()

    if flask.request.method == "GET":  # STATE 1: The user requests only the html content
        return flask.render_template("signup.jin", signupform=form)

    else:  # STATE 2: The user already saw the page and filled the content

        if form.validate_on_submit():  # STATE 2a: The form is valid

            # Create a user
            user = models.User()
            user.name = form.username.data
            user.age = form.age.data
            user.email = form.email.data
            user.city = form.city.data
            #
            user.add_password(form.password.data)
            models.User.add_to_db(user)
            flask.flash("Registered Successfully, " + form.username.data + " login pls", 'success')
            return flask.redirect(flask.url_for('signin'))

        else:  # STATE 2b: The form is invalid
            flask.flash("Invalid form" 'warning')
            return flask.render_template("signup.jin", signupform=form)




# when USER logged out delete his products as well
@app.route('/logout')
def logout():
    flask_login.logout_user()
    flask.flash('Logged out', 'info')
    return flask.redirect(flask.url_for('home'))




@app.route("/view:<product_id>/", methods=('GET',)) # don't forget ',' cuz it is tuple or use ['GET']
def view(product_id):
    product = models.Product.query.get(product_id)
    return flask.render_template('view.jin', product=product)


""" this route gets the product id then bring the actual obj from DB then it adds to the models.py( cart  = [] ) """
# @flask_login.login_required
@app.route("/add_to_cart:<product_id>/", methods=('GET',))
def add_to_cart(product_id):
    add_toCart = models.User.cart
    usr = flask_login.current_user
    if not usr:  # means if he is not authenticated
        return flask.redirect(flask.url_for('home'))
    else:

        product_from_db = models.Product.query.filter_by(id=product_id).first()
        if add_toCart != []:
            existed = False
            for item in add_toCart:
                if item.id == product_from_db.id:
                    existed = True
                    flask.flash(f" product is already in your chart...!", 'warning')
            if existed == False:
                add_toCart.append(product_from_db)
                flask.flash(f" product has been added to your chart...!", 'success')

        else:
            add_toCart.append(product_from_db)
            flask.flash(f" product has been added to your chart...!", 'success')

    total_price = sum([o.price for o in add_toCart])
    return flask.render_template('user_products.jin', ordered_products=add_toCart, total_price=total_price)



""" this route is connected with the cart symbol and it has access to the model.py(cart = []) then loop through it and render it"""
@login_required
@app.route('/cart')
def cart():
    add_toCart = models.User.cart
    usr = flask_login.current_user
    if usr.is_authenticated:
        return flask.render_template('user_products.jin', ordered_products=add_toCart,)
    # else:
    #     return flask.render_template('all_orders.jin', ordered_obj=[])


# don't forget ',' cuz it is tuple or use ['GET']
@app.route("/view:<product_id>/", methods=('GET',))
def view2(product_id):
    product = models.UserStaff.query.get(product_id)
    return flask.render_template('view.jin', product=product)


""" this route will let you order from the products only if you are logged in """


# if u use this you have to be logged in to click at the order button
@login_required
@app.route("/order:<product_id>/", methods=('GET', 'POST'))
def order(product_id):
    form = forms.OrderForm()
    if not flask_login.current_user.is_authenticated:
        flask.flash('You need to login FIRST', 'danger')
        return flask.redirect(flask.url_for('signin'))
    usr = flask_login.current_user
    user = models.User.query.get(usr.id)
    product = models.Product.query.get(product_id)
    ordered_obj = user.userstuffs
    total_price = sum([o.product_price for o in ordered_obj])
    return flask.render_template('order.jin', product=product, orderform=form, total_price=total_price, ordered_obj=ordered_obj)


""" this route calculate the total price and add all the orders to the table at the (all_orders.jin) file"""
@login_required
@app.route('/all_orders')
def all_orders():
    usr = flask_login.current_user
    user = models.User.query.get(usr.id)
    ordered_obj = user.userstuffs
    total_price = sum([o.product_price for o in ordered_obj])
    print(total_price)
    if usr.is_authenticated:
        return flask.render_template('all_orders.jin', ordered_obj=ordered_obj, total_price=total_price)
    # else:
    #     return flask.render_template('all_orders.jin', ordered_obj=[])


""" this route will let you """
@app.route("/buy:<product_id>/", methods=('GET', 'POST'))
def buy(product_id):
    form = forms.OrderForm()
    product_obj = models.Product.query.get(product_id)

    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for('all_orders'))

    else:
        if form.validate_on_submit():
            customer         = models.UserStaff()  # DB
            customer.name    = form.fullname.data
            customer.email   = form.email.data
            customer.phone   = form.phone.data
            customer.address = form.address.data
            customer.product_price = product_obj.price
            customer.product_name  = product_obj.id
            customer.product_pic = product_obj.pic_url
            customer.owner   = flask_login.current_user  # create a connection b/n User and UserStaff
            customer.owner_stuff = product_obj  # create a connection b/n Product and UserStaff through backref
            db.session.add(customer)
            db.session.commit()
            flask.flash('Your order has been approved', 'info')
            return flask.redirect(flask.url_for("home"))
        else:  # STATE 2b: The form is invalid
            flask.flash("Invalid form", 'danger')
            return flask.redirect(flask.url_for('order', product_id=product_obj.id))



# @app.route('/search/by-content/<searched_txt>', methods=("GET","POST"))
# def content_search(searched_txt):
#     searched_txt = searched_txt.lower()
#     all_posts = Post.query.all()
#     matched_posts = []
#     for post in all_posts:
#         match = re.search(searched_txt, post.content.lower()) # not clear
#         if match:
#             matched_posts.append(post)
#
#     return render_template('search_result.html', posts=matched_posts)



# it only retrieves from the search html form and -
# give it to the content_search func. cuz it can't get it by itself and put it on the route as an argument


# @app.route('/bridges/content-search', methods=['POST'])
# def bridge_content_search():
#     searched_txt = flask.request.form['searched_txt'] # if i put 'i love python' is it going to be a string or a list of strs
#     return flask.redirect(flask.url_for('content_search', searched_txt=searched_txt))



@app.route('/delete:<product_id>/', )
def delete(product_id):
    print('---> delete', product_id)
    get_the_cart = models.User.cart
    for item in get_the_cart:
        if item.id == product_id:
            get_the_cart.remove(item)
    flask.flash('Your product has been deleted', 'warning')
    total_price = sum([x.price for x in get_the_cart])

    return flask.render_template('user_products.jin', ordered_products=get_the_cart, total_price=total_price)



@app.route('/delete_from_my_order:<product_id>/')
def delete_from_my_order(product_id):
    product_to_delete = models.UserStaff.query.get(product_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    flask.flash('Your product has been deleted', 'warning')
    return flask.redirect(flask.url_for('all_orders'))





@app.route('/content_search:/', methods=('GET', 'POST'), defaults={'text_to_search':None})
@app.route('/content_search:<text_to_search>/', methods=('GET', 'POST'))
def content_search(text_to_search):
    if not text_to_search:
        return flask.redirect(flask.url_for('home'))
    text_to_search = text_to_search.lower()
    all_categories = []
    category = models.Product.query.all()
    print(category)
    for product in category:
        match = re.search(text_to_search, product.category.lower())
        if match:
            print(match)
            all_categories.append(product)
        else:
            print('not found', match)
            continue
    return flask.render_template('searched_product.jin', all_categories=all_categories, text_to_search=text_to_search)


@app.route('/bridges', methods=['POST'])
def bridge():
    text_to_search = flask.request.form['searched_txt'] # if i put 'i love python' is it going to be a string or a list of strs
    print(text_to_search)
    return flask.redirect(flask.url_for('content_search', text_to_search=text_to_search)) # the args should be the same with the args of content_search func


def send_email_to_user(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='menkregrma12@gamil.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{flask.url_for('reset_password', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route('/reset_request', methods=('GET', 'POST'))
def reset_request():
    form = forms.ResetRequestForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        print(user)
        send_email_to_user(user)
        flask.flash('Email has been sent to your Email!', 'info')
    return flask.render_template('reset_request.jin', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    user = models.User.verify_reset_token(token)   # TODO create method in the models cuz it is better
    print(user)

    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        hash_pwd  = security.generate_password_hash(form.password.data)
        user.pwd_hash = hash_pwd
        print(hash_pwd)
        db.session.commit()
        flask.flash('Updated Pwd', 'info')
        return flask.redirect(flask.url_for('signin'))
    return flask.render_template('reset_password.jin', form=form)


# # https://my-online-marketing.herokuapp.com/

@app.route('/thank_you')
def thank_you():
    models.User.cart = []
    return flask.render_template('thank_you.jin')


@app.route('/help')
def help():
    return flask.render_template('help.jin')


@app.route('/award')
def award():
    return flask.render_template('award.jin')


@app.route('/contact_us')
def contact_us():
    form = forms.ContactAs()
    return flask.render_template('contact_us.jin', contactAs=form)


@app.route('/products')
def products():
    return flask.redirect(flask.url_for('home'))


@app.route('/about_us')
def about_us():
    return flask.render_template('about_us.jin')


@app.route('/assessories')
def assessories():
    page = flask.request.args.get('page', 1, type=int)
    products = models.Product.query.order_by(models.Product.date_posted.desc()).paginate(page=page, per_page=40)
    return flask.render_template('assessories.jin', products=products)


@app.route('/laptops')
def laptops():
    page = flask.request.args.get('page', 1, type=int)
    products = models.Product.query.order_by(models.Product.date_posted.desc()).paginate(page=page, per_page=40)
    return flask.render_template('laptops.jin', products=products)
