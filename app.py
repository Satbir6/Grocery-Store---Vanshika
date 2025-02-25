from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from flask import abort
import os
import random
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'static/uploads/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file):
    if file and allowed_file(file.filename):
        # Get the original filename and extension
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        
        # Generate the new filename with timestamp and random number
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_num = random.randint(1000, 9999)
        new_filename = f"{name}_{random_num}_{timestamp}{ext}"
        
        # Save the file using os.path.join for proper path handling
        filepath = os.path.join(app.root_path, 'static', 'uploads', 'products', new_filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Return the URL path with forward slashes for database storage
        return '/'.join(['static', 'uploads', 'products', new_filename]) 
    return None

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password = Column(String(200), nullable=False)
    is_seller = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    addresses = relationship('Address', back_populates='user')
    cart = relationship('Cart', uselist=False, back_populates='user')
    orders = relationship('Order', back_populates='user')
    wishlist_items = relationship('WishlistItem', back_populates='user')

    def __repr__(self):
        return f"<User {self.name}>"

class Address(db.Model):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    line1 = Column(String(200), nullable=False)
    line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='addresses')

    def __repr__(self):
        return f"<Address {self.line1}, {self.city}>"

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subcategories = relationship('SubCategory', back_populates='category', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"

class SubCategory(db.Model):
    __tablename__ = 'subcategories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign Key
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    # Relationships
    category = relationship('Category', back_populates='subcategories')
    products = relationship('Product', back_populates='subcategory', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SubCategory {self.name}>"

class Product(db.Model):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    sub_category_id = Column(Integer, ForeignKey('subcategories.id'), nullable=False)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    subcategory = relationship('SubCategory', back_populates='products')
    seller = relationship('User', backref=backref('seller_products', lazy=True))
    ratings = relationship('Rating', back_populates='product', cascade="all, delete-orphan")
    
    @property
    def avg_rating(self):
        if not self.ratings:
            return 0
        return sum(r.rating for r in self.ratings) / len(self.ratings)
    
    @property
    def total_ratings(self):
        return len(self.ratings)

    def __repr__(self):
        return f"<Product {self.name}>"

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='cart')
    items = relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(item.subtotal for item in self.items)

    def __repr__(self):
        return f"<Cart {self.id} for User {self.user_id}>"

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cart = relationship('Cart', back_populates='items')
    product = relationship('Product')


    def __repr__(self):
        return f"<CartItem Product {self.product_id} (Qty: {self.quantity})>"

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(String(50), default='Pending')
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='orders')
    address = relationship('Address')
    order_items = relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id} - User {self.user_id} - Status {self.status}>"

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Float, nullable=False)  # Price at the time of order
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship('Order', back_populates='order_items')
    product = relationship('Product')

    def __repr__(self):
        return f"<OrderItem Product {self.product_id} (Qty: {self.quantity})>"

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='wishlist_items')
    product = relationship('Product')

    def __repr__(self):
        return f"<WishlistItem User {self.user_id} - Product {self.product_id}>" 

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5 stars
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='ratings')
    product = relationship('Product', back_populates='ratings')
    
    def __repr__(self):
        return f"<Rating {self.rating} stars by User {self.user_id} for Product {self.product_id}>"

@app.route('/')
def home():
    # Fetch categories with their images
    categories = Category.query.all()
    return render_template('pages/home.html', categories=categories)

@app.route('/categories')
def categories():
    # Fetch all categories with their subcategories
    categories = Category.query.all()
    
    # Get popular subcategories (based on product count)
    popular_subcategories = (SubCategory.query
        .join(Product)
        .group_by(SubCategory.id)
        .order_by(func.count(Product.id).desc())
        .limit(8)
        .all())
    
    return render_template('pages/categories.html', 
                         categories=categories,
                         popular_subcategories=popular_subcategories)

@app.route('/api/subcategories/<int:category_id>')
def get_subcategories(category_id):
    subcategories = SubCategory.query.filter_by(category_id=category_id).all()
    return jsonify([{
        'id': sub.id,
        'name': sub.name
    } for sub in subcategories])

@app.route('/products')
def products():
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    subcategory_id = request.args.get('subcategory', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    
    # Base query
    query = Product.query
    
    # Apply filters
    if category_id:
        query = query.join(SubCategory).filter(SubCategory.category_id == category_id)
    if subcategory_id:
        query = query.filter(Product.sub_category_id == subcategory_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Apply sorting
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    # Paginate results
    products = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get all categories with their subcategories
    categories = Category.query.all()
    
    return render_template('pages/products.html',
                         products=products,
                         categories=categories,
                         selected_category=category_id,
                         selected_subcategory=subcategory_id,
                         min_price=min_price,
                         max_price=max_price,
                         sort=sort)

@app.route('/cart')
@login_required
def cart():
    # Get user's cart or create one if it doesn't exist
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    return render_template('pages/cart.html', cart=cart)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = request.form.get('quantity', 1, type=int)
    
    # Get or create cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Check if product already in cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    quantity = request.form.get('quantity', 1, type=int)
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Verify cart item belongs to user
    if cart_item.cart.user_id != current_user.id:
        abort(403)
    
    if quantity > 0:
        cart_item.quantity = quantity
    else:
        db.session.delete(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Verify cart item belongs to user
    if cart_item.cart.user_id != current_user.id:
        abort(403)
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    return render_template('pages/checkout.html', cart=cart)

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    products = Product.query.filter_by(seller_id=current_user.id).all()
    orders = Order.query.join(OrderItem).join(Product).filter(
        Product.seller_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate statistics
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    total_products = len(products)
    avg_rating = sum(p.avg_rating for p in products) / len(products) if products else 0
    total_ratings = sum(p.total_ratings for p in products)
    
    return render_template('pages/seller-dashboard.html',
                         products=products,
                         orders=orders,
                         stats={
                             'total_sales': total_sales,
                             'total_orders': total_orders,
                             'total_products': total_products,
                             'avg_rating': round(avg_rating, 1),
                             'total_ratings': total_ratings
                         })

@app.route('/seller/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image_path = save_product_image(request.files['image'])
            if not image_path and request.files['image'].filename:
                flash('Invalid image format. Allowed formats are: png, jpg, jpeg, gif, webp', 'error')
                return redirect(request.url)
        
        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            sub_category_id=int(request.form['subcategory']),
            seller_id=current_user.id,
            image_url=image_path
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully', 'success')
        return redirect(url_for('seller_dashboard'))
    
    categories = Category.query.all()
    return render_template('pages/add-product.html', categories=categories)

@app.route('/seller/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(id)
    if product.seller_id != current_user.id:
        flash('Access denied. You can only edit your own products.', 'error')
        return redirect(url_for('seller_dashboard'))
    
    if request.method == 'POST':
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            # Delete old image if it exists
            if product.image_url:
                old_image_path = os.path.join(app.root_path, 'static', product.image_url.lstrip('/'))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            image_path = save_product_image(request.files['image'])
            if not image_path:
                flash('Invalid image format. Allowed formats are: png, jpg, jpeg, gif, webp', 'error')
                return redirect(request.url)
            product.image_url = image_path
        
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.sub_category_id = int(request.form['subcategory'])
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('seller_dashboard'))
    
    categories = Category.query.all()
    return render_template('pages/edit-product.html', product=product, categories=categories)

@app.route('/seller/orders/<int:id>')
@login_required
def order_details(id):
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(id)
    # Check if the seller has any products in this order
    has_access = any(item.product.seller_id == current_user.id for item in order.items)
    if not has_access:
        flash('Access denied. You can only view orders containing your products.', 'error')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('pages/order-details.html', order=order)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/account')
@login_required
def account():
    # Get user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Get user's wishlist
    wishlist = WishlistItem.query.filter_by(user_id=current_user.id).all()
    
    # Get user's cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    return render_template('pages/account.html', 
                         orders=orders,
                         wishlist=wishlist,
                         cart=cart)

@app.route('/become-seller', methods=['GET', 'POST'])
@login_required
def become_seller():
    if current_user.is_seller:
        flash('You are already a seller!', 'info')
        return redirect(url_for('seller_dashboard'))
    
    if request.method == 'POST':
        # Update user to seller status
        current_user.is_seller = True
        
        # Add business details (you might want to create a separate Business model)
        current_user.business_name = request.form.get('business_name')
        current_user.business_type = request.form.get('business_type')
        current_user.tax_id = request.form.get('tax_id')
        current_user.business_address = request.form.get('address')
        current_user.business_phone = request.form.get('phone')
        
        db.session.commit()
        
        flash('Congratulations! Your seller account has been activated.', 'success')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('pages/become-seller.html')

@app.route('/products/<int:id>/rate', methods=['POST'])
@login_required
def rate_product(id):
    rating_value = request.form.get('rating', type=int)
    review = request.form.get('review')
    
    if not 1 <= rating_value <= 5:
        flash('Rating must be between 1 and 5 stars', 'error')
        return redirect(url_for('product_details', id=id))
    
    # Check if user has already rated this product
    existing_rating = Rating.query.filter_by(
        user_id=current_user.id,
        product_id=id
    ).first()
    
    if existing_rating:
        existing_rating.rating = rating_value
        existing_rating.review = review
        flash('Your rating has been updated!', 'success')
    else:
        rating = Rating(
            user_id=current_user.id,
            product_id=id,
            rating=rating_value,
            review=review
        )
        db.session.add(rating)
        flash('Thank you for your rating!', 'success')
    
    db.session.commit()
    return redirect(url_for('product_details', id=id))

@app.route('/products/<int:id>')
def product_details(id):
    product = Product.query.get_or_404(id)
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(
            user_id=current_user.id,
            product_id=id
        ).first()
    
    # Get all ratings for this product
    ratings = Rating.query.filter_by(product_id=id).order_by(Rating.created_at.desc()).all()
    
    return render_template('pages/product-details.html',
                         product=product,
                         user_rating=user_rating,
                         ratings=ratings)

# Initialize database with categories
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add categories if they don't exist
        categories = [
            {
                'name': 'Fruits & Vegetables',
                'description': 'Fresh produce delivered to your door',
                'image_url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Fresh Fruits',
                    'Fresh Vegetables',
                    'Organic Fruits',
                    'Organic Vegetables',
                    'Exotic Fruits',
                    'Leafy Greens',
                    'Herbs & Seasonings'
                ]
            },
            {
                'name': 'Dairy & Eggs',
                'description': 'Farm-fresh dairy products',
                'image_url': 'https://images.unsplash.com/photo-1628088062854-d1870b4553da?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Milk',
                    'Yogurt',
                    'Cheese',
                    'Butter & Spreads',
                    'Eggs',
                    'Cream & Condensed Milk',
                    'Paneer & Tofu'
                ]
            },
            {
                'name': 'Bakery',
                'description': 'Freshly baked breads and pastries',
                'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Bread',
                    'Cakes & Pastries',
                    'Cookies & Biscuits',
                    'Buns & Rolls',
                    'Muffins & Cupcakes',
                    'Donuts',
                    'Croissants'
                ]
            },
            {
                'name': 'Meat & Seafood',
                'description': 'Premium quality meats and seafood',
                'image_url': 'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Chicken',
                    'Mutton',
                    'Fish',
                    'Prawns & Seafood',
                    'Marinades',
                    'Cold Cuts',
                    'Eggs'
                ]
            },
            {
                'name': 'Pantry',
                'description': 'Essential cooking ingredients',
                'image_url': 'https://images.unsplash.com/photo-1584473457406-6240486418e9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Rice & Grains',
                    'Pulses & Lentils',
                    'Cooking Oils',
                    'Spices & Masalas',
                    'Flour & Sooji',
                    'Salt & Sugar',
                    'Dry Fruits & Nuts'
                ]
            },
            {
                'name': 'Beverages',
                'description': 'Refreshing drinks and juices',
                'image_url': 'https://images.unsplash.com/photo-1581006852262-e4307cf6283a?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80',
                'subcategories': [
                    'Soft Drinks',
                    'Juices',
                    'Tea & Coffee',
                    'Health Drinks',
                    'Energy Drinks',
                    'Water',
                    'Milk Drinks'
                ]
            }
        ]
        
        for cat_data in categories:
            # Check if category exists
            category = Category.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    image_url=cat_data['image_url']
                )
                db.session.add(category)
                db.session.flush()  # This assigns the ID to the category
            
            # Add subcategories
            for subcat_name in cat_data['subcategories']:
                if not SubCategory.query.filter_by(name=subcat_name, category_id=category.id).first():
                    subcategory = SubCategory(
                        name=subcat_name,
                        category_id=category.id,
                        description=f'{subcat_name} in {cat_data["name"]} category'
                    )
                    db.session.add(subcategory)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
