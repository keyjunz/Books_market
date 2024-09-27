from flask import Flask, render_template, request, session, redirect, url_for, flash
from config import Config
from middle_secure import auth
import bcrypt
import os
from models import db, User, Book, Transaction_History
from data_loader import load_sample_data

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/logout')
@auth
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            return redirect(url_for('home'))
        
        return render_template('login.html', error="Invalid email or password")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error="Email is already in use.")
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password, name=name)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['email'] = new_user.email
        return redirect(url_for('home'))
    
    return render_template('register.html')

#Quản trị account
@app.route('/sitemanager', methods=['GET', 'POST'])
def sitemanager():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('site_manager_dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('sitemanager.html')

@app.route('/site_manager_dashboard')
def site_manager_dashboard():
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    users_count = User.query.count()
    books_count = Book.query.count()
    return render_template('site_manager_dashboard.html', users_count=users_count, books_count=books_count)

@app.route('/site_manager_users')
def site_manager_users():
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    users = User.query.all()
    return render_template('site_manager_users.html', users=users)

@app.route('/site_manager_user/add', methods=['POST'])
def site_manager_add_user():
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    new_user = User(username=username, email=email, password=password, name=username)
    db.session.add(new_user)
    db.session.commit()
    flash("User added successfully", "success")
    return redirect(url_for('site_manager_users'))

@app.route('/site_manager_user/edit/<int:user_id>', methods=['GET', 'POST'])
def site_manager_edit_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        if request.form['password']:
            user.password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        db.session.commit()
        flash("User updated successfully", "success")
        return redirect(url_for('site_manager_users'))
    return render_template('site_manager_edit_user.html', user=user)

@app.route('/site_manager_user/delete/<int:user_id>', methods=['POST'])
def site_manager_delete_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for('site_manager_users'))

@app.route('/site_manager_books')
def site_manager_books():
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    books = Book.query.all()
    return render_template('site_manager_books.html', books=books)

@app.route('/site_manager_book/add', methods=['GET', 'POST'])
def site_manager_add_book():
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    if request.method == 'POST':
        new_book = Book(
            title=request.form['title'],
            author=request.form['author'],
            price=float(request.form['price']),
            cover_image=request.form['cover_image']
        )
        db.session.add(new_book)
        db.session.commit()
        flash("Book added successfully", "success")
        return redirect(url_for('site_manager_books'))
    return render_template('site_manager_add_book.html')

@app.route('/site_manager_book/edit/<int:book_id>', methods=['GET', 'POST'])
def site_manager_edit_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.price = float(request.form['price'])
        book.cover_image = request.form['cover_image']
        db.session.commit()
        flash("Book updated successfully", "success")
        return redirect(url_for('site_manager_books'))
    return render_template('site_manager_edit_book.html', book=book)

@app.route('/site_manager_book/delete/<int:book_id>', methods=['POST'])
def site_manager_delete_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('sitemanager'))
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully", "success")
    return redirect(url_for('site_manager_books'))
#--------------------------------------------------------

#Giỏ hàng
@app.route('/cart')
@auth
def cart():
    user = User.query.get(session['user_id'])
    cart_items = session.get('cart', [])
    cart_total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)


@app.route('/checkout', methods=['POST'])
@auth
def checkout():
    user_id = session['user_id']
    phone = request.form['phone']
    address = request.form['address']
    
    session['phone'] = phone
    session['address'] = address

    cart_items = session.get('cart', [])
    cart_total = sum(item['price'] * item['quantity'] for item in cart_items)
    product_details = "\n".join([f"{item['title']} x {item['quantity']}" for item in cart_items])

    transaction = Transaction_History(
    user_id=user_id,
    product_details=product_details,
    total_amount=cart_total + 30000, 
    phone=phone,
    address=address
    )

    db.session.add(transaction)
    db.session.commit()
    session.pop('cart', None)

    flash("Đặt hàng thành công!", "success")
    return redirect(url_for('profile'))


@app.route('/transaction_history')
@auth
def transaction_history():
    user_id = session['user_id']
    transactions = Transaction_History.query.filter_by(user_id=user_id).all()
    return render_template('transaction_history.html', transactions=transactions)
#---------------------------------------------------------

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    books = Book.query.paginate(page=page, per_page=20)
    return render_template('index.html', books=books)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)
@app.route('/add-to-cart/<int:book_id>')
@auth
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    if 'cart' not in session:
        session['cart'] = []
    
    # Kiểm tra xem sách đã có trong giỏ hàng chưa
    cart_item = next((item for item in session['cart'] if item['id'] == book_id), None)
    
    if cart_item:
        # Nếu sách đã có trong giỏ hàng, tăng số lượng lên 1
        cart_item['quantity'] += 1
    else:
        # Nếu sách chưa có trong giỏ hàng, thêm mới
        session['cart'].append({
            'id': book.id,
            'title': book.title,
            'price': book.price,
            'quantity': 1
        })
    
    session.modified = True
    flash('Sách đã được thêm vào giỏ hàng', 'success')
    return redirect(url_for('home'))


@app.route('/category/<string:category_name>')
def category(category_name):
    # Lấy danh sách sách theo thể loại
    books = Book.query.filter_by(category=category_name).all()
    return render_template('category.html', books=books, category_name=category_name)

@app.route('/profile')
@auth
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

def init_db():
    db.create_all()



if __name__ == '__main__':
    with app.app_context():
        load_sample_data()
    
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
