from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, func
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Return the relative path for database storage
        return os.path.join('uploads', 'products', new_filename).replace('\\', '/')
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

@app.context_processor
def inject_cart():
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        return {'user_cart': cart}
    return {'user_cart': None}

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

    @property
    def subtotal(self):
        return self.product.price * self.quantity

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
    
    # Fetch featured products (newest products)
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    
    # Fetch top deals (products with highest ratings)
    top_deals = Product.query.join(Rating).group_by(Product.id).order_by(
        func.avg(Rating.rating).desc()
    ).limit(4).all()
    
    # Get user's wishlist information if authenticated
    user_wishlist_product_ids = []
    user_wishlist_items = {}
    
    if current_user.is_authenticated:
        wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).all()
        user_wishlist_product_ids = [item.product_id for item in wishlist_items]
        user_wishlist_items = {item.product_id: item.id for item in wishlist_items}
    
    return render_template('pages/home.html', 
                          categories=categories,
                          featured_products=featured_products,
                          top_deals=top_deals,
                          user_wishlist_product_ids=user_wishlist_product_ids,
                          user_wishlist_items=user_wishlist_items)

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
    
    # Get user's saved addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    return render_template('pages/checkout.html', cart=cart, addresses=addresses)

@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    # Get user's cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    # Check if all products have sufficient stock
    insufficient_stock = []
    for cart_item in cart.items:
        product = cart_item.product
        if product.stock < cart_item.quantity:
            insufficient_stock.append(f"{product.name} (only {product.stock} available)")
    
    if insufficient_stock:
        flash(f"Insufficient stock for: {', '.join(insufficient_stock)}", 'error')
        return redirect(url_for('cart'))
    
    # Get address information
    address_id = request.form.get('address_id')
    
    # Handle new address
    if address_id == 'new':
        # Check if user wants to save the address
        save_address = 'save_address' in request.form
        
        # Create new address
        address = Address(
            user_id=current_user.id,
            line1=request.form.get('line1'),
            line2=request.form.get('line2'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            country=request.form.get('country'),
            zip_code=request.form.get('zip_code')
        )
        
        # Validate required fields
        if not address.line1 or not address.city or not address.state or not address.country or not address.zip_code:
            flash('Please fill in all required address fields', 'error')
            return redirect(url_for('checkout'))
        
        # Save address if requested
        if save_address:
            db.session.add(address)
            db.session.commit()
        else:
            # Add to session but don't commit yet
            db.session.add(address)
            db.session.flush()
    else:
        # Use existing address
        address = Address.query.get(address_id)
        if not address or address.user_id != current_user.id:
            flash('Invalid address selected', 'error')
            return redirect(url_for('checkout'))
    
    # Calculate order total
    shipping_fee = 0 if cart.total >= 50 else 4.99
    tax = cart.total * 0.1
    total_amount = cart.total + shipping_fee + tax
    
    # Create order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status='Pending',
        address_id=address.id
    )
    db.session.add(order)
    db.session.flush()  # Get order ID without committing
    
    # Create order items and update product stock
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price  # Store current price
        )
        db.session.add(order_item)
        
        # Decrease product stock
        product = Product.query.get(cart_item.product_id)
        product.stock -= cart_item.quantity
    
    # Clear the cart
    CartItem.query.filter_by(cart_id=cart.id).delete()
    
    # Commit all changes
    db.session.commit()
    
    flash('Order placed successfully!', 'success')
    return redirect(url_for('order_confirmation', order_id=order.id))

@app.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user can only view their own orders
    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('account'))
    
    return render_template('pages/order-confirmation.html', order=order)

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    # Get filter parameters
    category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    stock_filter = request.args.get('stock', '')
    products_only = request.args.get('products_only') == 'true'
    orders_only = request.args.get('orders_only') == 'true'
    order_status = request.args.get('status', '')  # Changed from order_status to status to match the template
    order_sort_by = request.args.get('order_sort_by', 'created_at')
    order_sort_order = request.args.get('order_sort_order', 'desc')
    
    # Get page number for pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    
    # Calculate seller statistics
    stats = {}
    
    # Get total number of products
    stats['total_products'] = Product.query.filter_by(seller_id=current_user.id).count()
    
    # Get total sales amount
    seller_product_ids = db.session.query(Product.id).filter_by(seller_id=current_user.id).all()
    seller_product_ids = [p[0] for p in seller_product_ids]
    
    # Calculate total sales from order items
    total_sales = db.session.query(func.sum(OrderItem.price * OrderItem.quantity)).filter(
        OrderItem.product_id.in_(seller_product_ids)
    ).scalar() or 0
    stats['total_sales'] = total_sales
    
    # Count total orders with seller's products
    order_items_subquery = db.session.query(OrderItem.order_id).filter(
        OrderItem.product_id.in_(seller_product_ids)
    ).distinct().subquery()
    stats['total_orders'] = db.session.query(Order.id).filter(Order.id.in_(order_items_subquery)).count()
    
    # Calculate average rating
    avg_rating = db.session.query(func.avg(Rating.rating)).join(Product).filter(
        Product.seller_id == current_user.id
    ).scalar() or 0
    stats['avg_rating'] = round(avg_rating, 1)
    
    # Count total ratings
    stats['total_ratings'] = db.session.query(Rating).join(Product).filter(
        Product.seller_id == current_user.id
    ).count()
    
    # Base query for products
    products_query = Product.query.filter_by(seller_id=current_user.id)
    
    # Apply filters
    if category_id:
        subcategories = SubCategory.query.filter_by(category_id=category_id).all()
        subcategory_ids = [sub.id for sub in subcategories]
        products_query = products_query.filter(Product.sub_category_id.in_(subcategory_ids))
    
    if search_query:
        products_query = products_query.filter(Product.name.ilike(f'%{search_query}%'))
    
    if stock_filter == 'in_stock':
        products_query = products_query.filter(Product.stock > 0)
    elif stock_filter == 'out_of_stock':
        products_query = products_query.filter(Product.stock == 0)
    
    # Apply sorting
    if sort_by == 'name':
        products_query = products_query.order_by(Product.name.asc() if sort_order == 'asc' else Product.name.desc())
    elif sort_by == 'price':
        products_query = products_query.order_by(Product.price.asc() if sort_order == 'asc' else Product.price.desc())
    elif sort_by == 'stock':
        products_query = products_query.order_by(Product.stock.asc() if sort_order == 'asc' else Product.stock.desc())
    else:  # default to created_at
        products_query = products_query.order_by(Product.created_at.asc() if sort_order == 'asc' else Product.created_at.desc())
    
    # Get orders that contain the seller's products
    if not products_only:
        # Find all orders that contain products from this seller
        seller_product_ids = db.session.query(Product.id).filter_by(seller_id=current_user.id).all()
        seller_product_ids = [p[0] for p in seller_product_ids]
        
        # Find order items that contain these products
        order_items_subquery = db.session.query(OrderItem.order_id).filter(
            OrderItem.product_id.in_(seller_product_ids)
        ).distinct().subquery()
        
        # Get the orders
        orders_query = Order.query.filter(Order.id.in_(order_items_subquery))
        
        # Apply order status filter
        if order_status:
            orders_query = orders_query.filter(Order.status == order_status)
        
        # Apply sorting to orders
        if order_sort_by == 'created_at':
            orders_query = orders_query.order_by(Order.created_at.asc() if order_sort_order == 'asc' else Order.created_at.desc())
        elif order_sort_by == 'total_amount':
            orders_query = orders_query.order_by(Order.total_amount.asc() if order_sort_order == 'asc' else Order.total_amount.desc())
        else:
            orders_query = orders_query.order_by(Order.created_at.desc())
        
        # Paginate orders if only showing orders
        if orders_only:
            orders = orders_query.paginate(page=page, per_page=per_page, error_out=False)
            order_pagination = orders
            orders = orders.items
            products = None
        else:
            orders = orders_query.limit(5).all()  # Show only 5 recent orders on the dashboard
            order_pagination = None
            products = products_query.paginate(page=page, per_page=per_page, error_out=False)
    else:
        # Only show products
        products = products_query.paginate(page=page, per_page=per_page, error_out=False)
        orders = None
        order_pagination = None
    
    # Get categories for filter dropdown
    categories = Category.query.all()
    
    # Prepare current filters for display
    current_filters = {
        'search': search_query,
        'category_id': category_id,
        'stock': stock_filter
    }
    
    # Check if this is an AJAX request
    is_ajax = request.args.get('ajax') == 'true'
    
    if is_ajax:
        if products_only:
            return render_template('partials/product-list.html', 
                                  products=products,
                                  current_filters=current_filters)
        elif orders_only:
            return render_template('partials/order-list.html',
                                  orders=orders,
                                  order_pagination=order_pagination)
    
    return render_template('pages/seller-dashboard.html', 
                          products=products, 
                          orders=orders,
                          order_pagination=order_pagination,
                          categories=categories,
                          category_id=category_id,
                          search_query=search_query,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          stock_filter=stock_filter,
                          current_filters=current_filters,
                          products_only=products_only,
                          orders_only=orders_only,
                          order_status=order_status,
                          stats=stats)

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
        
        # Update product details
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.sub_category_id = int(request.form['subcategory'])
        
        try:
            db.session.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('seller_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
            return redirect(request.url)
    
    categories = Category.query.all()
    return render_template('pages/edit-product.html', product=product, categories=categories)

@app.route('/seller/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(id)
    if product.seller_id != current_user.id:
        flash('Access denied. You can only delete your own products.', 'error')
        return redirect(url_for('seller_dashboard'))
    
    # Check if product is in any orders
    order_items = OrderItem.query.filter_by(product_id=product.id).first()
    if order_items:
        # Don't delete, just mark as out of stock
        product.stock = 0
        db.session.commit()
        flash('Product has been marked as out of stock. Cannot delete products with order history.', 'warning')
        return redirect(url_for('seller_dashboard'))
    
    # Delete product image if it exists
    if product.image_url:
        image_path = os.path.join(app.root_path, 'static', product.image_url.lstrip('/'))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Remove from carts and wishlists
    CartItem.query.filter_by(product_id=product.id).delete()
    WishlistItem.query.filter_by(product_id=product.id).delete()
    
    # Delete the product
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('seller_dashboard'))

@app.route('/seller/orders/<int:id>')
@login_required
def order_details(id):
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(id)
    # Check if the seller has any products in this order
    has_access = any(item.product.seller_id == current_user.id for item in order.order_items)
    if not has_access:
        flash('Access denied. You can only view orders containing your products.', 'error')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('pages/order-details.html', order=order)

@app.route('/seller/orders/<int:id>/update-status', methods=['POST'])
@login_required
def update_order_status(id):
    if not current_user.is_seller:
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(id)
    # Check if the seller has any products in this order
    has_access = any(item.product.seller_id == current_user.id for item in order.order_items)
    if not has_access:
        flash('Access denied. You can only update orders containing your products.', 'error')
        return redirect(url_for('seller_dashboard'))
    
    new_status = request.form.get('status')
    old_status = order.status
    
    if new_status in ['Processing', 'Shipped', 'Delivered', 'Cancelled']:
        # If order is being cancelled and wasn't already cancelled, restore stock
        if new_status == 'Cancelled' and old_status != 'Cancelled':
            for item in order.order_items:
                if item.product.seller_id == current_user.id:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock += item.quantity
        
        order.status = new_status
        db.session.commit()
        
        if new_status == 'Cancelled' and old_status != 'Cancelled':
            flash('Order cancelled and product stock restored', 'success')
        else:
            flash(f'Order status updated to {new_status}', 'success')
    else:
        flash('Invalid status value', 'error')
    
    return redirect(url_for('order_details', id=id))

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
        phone = request.form.get('phone')
        is_seller = request.form.get('is_seller') == "on"
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, phone=phone, password=hashed_password, is_seller=is_seller)
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

@app.route('/account/update', methods=['POST'])
@login_required
def update_account():
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    # Validate email uniqueness if changed
    if email != current_user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already in use by another account.', 'error')
            return redirect(url_for('account'))
    
    # Update user information
    current_user.name = name
    current_user.email = email
    current_user.phone = phone
    
    db.session.commit()
    flash('Account information updated successfully!', 'success')
    return redirect(url_for('account'))

@app.route('/account/change-password', methods=['POST'])
@login_required
def change_password():
    # Get form data
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate input
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('account'))
    
    # Check if current password is correct
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('account'))
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('account'))
    
    # Update password
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Your password has been updated', 'success')
    return redirect(url_for('account'))

@app.route('/account/addresses')
@login_required
def view_addresses():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('pages/addresses.html', addresses=addresses)

@app.route('/account/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    if request.method == 'POST':
        # Get form data
        line1 = request.form.get('line1')
        line2 = request.form.get('line2')
        city = request.form.get('city')
        state = request.form.get('state')
        country = request.form.get('country')
        zip_code = request.form.get('zip_code')
        
        # Validate input
        if not line1 or not city or not state or not country or not zip_code:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('add_address'))
        
        # Create new address
        address = Address(
            user_id=current_user.id,
            line1=line1,
            line2=line2,
            city=city,
            state=state,
            country=country,
            zip_code=zip_code
        )
        
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully', 'success')
        return redirect(url_for('view_addresses'))
    
    return render_template('pages/add-address.html')

@app.route('/account/addresses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_address(id):
    address = Address.query.get_or_404(id)
    
    # Check if address belongs to current user
    if address.user_id != current_user.id:
        flash('You do not have permission to edit this address', 'danger')
        return redirect(url_for('view_addresses'))
    
    if request.method == 'POST':
        # Get form data
        address.line1 = request.form.get('line1')
        address.line2 = request.form.get('line2')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.country = request.form.get('country')
        address.zip_code = request.form.get('zip_code')
        
        # Validate input
        if not address.line1 or not address.city or not address.state or not address.country or not address.zip_code:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_address', id=id))
        
        db.session.commit()
        
        flash('Address updated successfully', 'success')
        return redirect(url_for('view_addresses'))
    
    return render_template('pages/edit-address.html', address=address)

@app.route('/account/addresses/<int:id>/delete', methods=['POST'])
@login_required
def delete_address(id):
    address = Address.query.get_or_404(id)
    
    # Check if address belongs to current user
    if address.user_id != current_user.id:
        flash('You do not have permission to delete this address', 'danger')
        return redirect(url_for('view_addresses'))
    
    # Check if address is used in any orders
    orders = Order.query.filter_by(address_id=id).first()
    if orders:
        flash('This address cannot be deleted as it is used in orders', 'danger')
        return redirect(url_for('view_addresses'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Address deleted successfully', 'success')
    return redirect(url_for('view_addresses'))

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
    
    # Check if user has purchased this product
    has_purchased = db.session.query(OrderItem).join(Order).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == id,
        Order.status.in_(['Delivered', 'Shipped'])  # Only count completed orders
    ).first() is not None
    
    if not has_purchased:
        flash('You can only rate products you have purchased', 'error')
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
    has_purchased = False
    
    if current_user.is_authenticated:
        # Check if user has rated this product
        user_rating = Rating.query.filter_by(
            user_id=current_user.id,
            product_id=id
        ).first()
        
        # Check if user has purchased this product
        has_purchased = db.session.query(OrderItem).join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == id,
            Order.status.in_(['Delivered', 'Shipped'])  # Only count completed orders
        ).first() is not None
    
    # Get all ratings for this product with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of reviews per page
    
    ratings_query = Rating.query.filter_by(product_id=id).order_by(Rating.created_at.desc())
    ratings_pagination = ratings_query.paginate(page=page, per_page=per_page, error_out=False)
    ratings = ratings_pagination.items
    
    # Get related products from the same subcategory
    related_products = Product.query.filter(
        Product.sub_category_id == product.sub_category_id,
        Product.id != product.id
    ).order_by(func.random()).limit(4).all()
    
    return render_template('pages/product-details.html',
                         product=product,
                         user_rating=user_rating,
                         ratings=ratings,
                         pagination=ratings_pagination,
                         has_purchased=has_purchased,
                         related_products=related_products)

@app.route('/wishlist')
@login_required
def wishlist():
    # Get user's wishlist items
    wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    
    # Get recommended products (products not in wishlist)
    recommended_products = []
    if wishlist_items:
        # Get subcategories of wishlist items
        wishlist_subcategories = [item.product.sub_category_id for item in wishlist_items]
        wishlist_product_ids = [item.product_id for item in wishlist_items]
        
        # Get products from same subcategories but not in wishlist
        recommended_products = Product.query.filter(
            Product.sub_category_id.in_(wishlist_subcategories),
            ~Product.id.in_(wishlist_product_ids)
        ).order_by(func.random()).limit(4).all()
    
    # If not enough recommended products, get top-rated products
    if len(recommended_products) < 4:
        needed = 4 - len(recommended_products)
        existing_ids = [p.id for p in recommended_products]
        if wishlist_items:
            existing_ids.extend([item.product_id for item in wishlist_items])
        
        top_rated = Product.query.filter(
            ~Product.id.in_(existing_ids)
        ).order_by(func.random()).limit(needed).all()
        
        recommended_products.extend(top_rated)
    
    # Prepare wishlist data for AJAX functionality
    user_wishlist_product_ids = [item.product_id for item in wishlist_items]
    user_wishlist_items = {item.product_id: item.id for item in wishlist_items}
    
    return render_template('pages/wishlist.html', 
                          wishlist_items=wishlist_items,
                          recommended_products=recommended_products,
                          user_wishlist_product_ids=user_wishlist_product_ids,
                          user_wishlist_items=user_wishlist_items)

@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    # Check if product already in wishlist
    existing_item = WishlistItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if existing_item:
        message = 'Product already in your wishlist'
        if is_ajax:
            return jsonify({
                'success': True,
                'message': message,
                'wishlist_item_id': existing_item.id
            })
        flash(message, 'info')
    else:
        wishlist_item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        message = 'Product added to wishlist'
        if is_ajax:
            return jsonify({
                'success': True,
                'message': message,
                'wishlist_item_id': wishlist_item.id
            })
        flash(message, 'success')
    
    # Redirect back for non-AJAX requests
    next_page = request.referrer or url_for('products')
    return redirect(next_page)

@app.route('/wishlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    wishlist_item = WishlistItem.query.get_or_404(item_id)
    
    # Verify wishlist item belongs to user
    if wishlist_item.user_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        abort(403)
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Item removed from wishlist'
        })
    
    flash('Item removed from wishlist', 'success')
    return redirect(url_for('wishlist'))

@app.route('/orders/<int:id>')
@login_required
def user_order_details(id):
    order = Order.query.get_or_404(id)
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        flash('Access denied. You can only view your own orders.', 'error')
        return redirect(url_for('account'))
    
    return render_template('pages/user-order-details.html', order=order)

@app.route('/orders/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_order(id):
    order = Order.query.get_or_404(id)
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        flash('Access denied. You can only cancel your own orders.', 'error')
        return redirect(url_for('account'))
    
    # Check if the order can be cancelled (only Pending or Processing orders)
    if order.status not in ['Pending', 'Processing']:
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('user_order_details', id=order.id))
    
    # Store the old status
    old_status = order.status
    
    # Update order status
    order.status = 'Cancelled'
    
    # Restore product stock if order was not already cancelled
    if old_status != 'Cancelled':
        for item in order.order_items:
            product = item.product
            product.stock += item.quantity
    
    db.session.commit()
    flash('Order cancelled successfully.', 'success')
    return redirect(url_for('user_order_details', id=order.id))

# Initialize database with categories
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add categories if they don't exist
        categories = [
            {
                'name': 'Fruits & Vegetables',
                'description': 'Fresh produce delivered to your door',
                'image_url': '/static/images/categories/Fruits.avif'
,
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
                'image_url': '/static/images/categories/Dairy.avif'
,
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
                'image_url': '/static/images/categories/Bakery.avif'
,
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
                'image_url': '/static/images/categories/Meat.jpeg'
,
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
                'image_url': '/static/images/categories/Pantry.avif'
,
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
                'image_url': '/static/images/categories/Beverages.avif'
,
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
