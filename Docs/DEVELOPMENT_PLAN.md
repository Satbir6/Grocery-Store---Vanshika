# Grocery Store Website Development Plan

## Tech Stack
- **Frontend**:
  - **HTML, CSS, JavaScript** for structure and interactivity.
  - **AJAX** for asynchronous data fetching to enhance user experience.
- **UI Framework**:
  - **Tailwind CSS** for utility-first styling.
  - **Flowbite** for prebuilt, accessible UI components.
- **Backend**:
  - **Flask (Python)** for server-side logic, routing, and data processing.
- **Database**:
  - **SQLite** for a lightweight, file-based relational database solution.

## Use SQLAlchemy(app) for database
### Database Models
"""python
class User(db.Model):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # A category can have many subcategories
    subcategories = relationship('SubCategory', back_populates='category', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"


class SubCategory(db.Model):
    __tablename__ = 'subcategories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign Key: which parent category this subcategory belongs to
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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    # Link product to a specific subcategory
    sub_category_id = Column(Integer, ForeignKey('subcategories.id'), nullable=False)
    
    # If you have sellers who manage products:
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    subcategory = relationship('SubCategory', back_populates='products')
    seller = relationship('User', backref=backref('seller_products', lazy=True))
    
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='orders')
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

"""

## Phase 1: Core Infrastructure (Week 1)

### 1.1 Project Initialization
- Tailwind CSS, python and everything is setup just make the basic project structure
- There should be only one python file and that is app.py
- There should be a folder called templates and that will contain all the html files and the html files should be placed in proper folders and subfolders


## Phase 2: User Interface Development (Weeks 2-3)

### 2.1 Common Components
- Navbar with search, cart, and account icons
- Footer
- Product card component
- Category card component
- Loading states and error boundaries

### 2.2 Homepage Implementation
- Hero section with banner
- Quick category navigation
- Top deals carousel
- Featured products section
- Search functionality

### 2.3 Product Pages
- Category view with grid layout
- Product filtering system
- Individual product page
- Image gallery implementation
- Quantity selector

### 2.4 User Account Features
- Login/Registration forms
- User dashboard layout
- Order history display
- Address management
- Wishlist functionality

## Phase 3: Backend Development (Weeks 4-5)

### 3.1 Database Schema
- User model
- Product model
- Order model
- Cart model
- Category model

### 3.2 API Endpoints
- Authentication routes
- Product management routes
- Order processing routes
- Cart management
- User profile management

### 3.3 Seller Features
- Seller registration
- Product listing management
- Basic analytics dashboard
- Order management interface

## Phase 4: Shopping Features (Week 6)

### 4.1 Cart Implementation
- Add to cart functionality
- Cart management
- Quantity updates
- Price calculations

### 4.2 Checkout Process
- Address selection
- Order summary
- Basic order confirmation

## Phase 5: Testing and Optimization (Week 7)

### 5.1 Testing
- Unit tests for components
- API endpoint testing
- Integration testing
- User flow testing

### 5.2 Optimization
- Performance optimization
- Image optimization
- Loading speed improvements
- Code splitting

## Phase 6: Deployment and Documentation (Week 8)

### 6.1 Deployment
- Frontend deployment
- Backend deployment
- Environment configuration
- Domain setup

### 6.2 Documentation
- API documentation
- User guide
- Admin documentation
- Deployment guide

## Excluded Features (As Specified)
- Payment gateway integration
- GSTIN/bank details collection
- Document verification system
- Order tracking/SMS notifications

## Development Guidelines

### Code Organization
- Feature-based folder structure
- Consistent naming conventions

### Best Practices
- Responsive design
- Accessibility compliance
- Error handling
- Loading states
- Form validation
