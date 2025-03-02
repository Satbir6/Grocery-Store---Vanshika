# 🛒 Modern Grocery Store E-commerce Platform

A full-featured e-commerce platform built with Flask and modern frontend technologies, offering a seamless shopping experience for both customers and sellers.

## ✨ Features

### 🛍️ For Customers
- User authentication and profile management
- Browse products by categories and subcategories
- Advanced product search and filtering
- Shopping cart functionality
- Wishlist management
- Order placement and tracking
- Multiple delivery addresses
- Product ratings and reviews
- Responsive, modern UI

### 🏪 For Sellers
- Dedicated seller dashboard
- Product management (CRUD operations)
- Order management and status updates
- Sales analytics and reporting
- Inventory management

## 🚀 Tech Stack

### Backend
- Python 3.x
- Flask - Web framework
- SQLAlchemy - ORM
- SQLite - Database
- Flask-Login - User authentication
- Werkzeug - Security and utilities

### Frontend
- TailwindCSS 3.3.5 - Utility-first CSS framework
- Flowbite 3.1.2 - UI components
- Modern responsive design
- Dynamic client-side interactions

## 🛠️ Setup and Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd grocery-store
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install flask flask-sqlalchemy flask-login werkzeug
```

4. Install Node.js dependencies:
```bash
npm install
```

5. Initialize the database:
```bash
python
>>> from app import app, db, init_db
>>> with app.app_context():
...     db.create_all()
...     init_db()
```

6. Build the frontend assets:
```bash
npm run build
```

7. Start the development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🗂️ Project Structure

```
grocery-store/
├── app.py              # Main application file
├── static/             # Static assets
│   ├── src/           # Source styles
│   ├── dist/          # Compiled assets
│   └── uploads/       # User uploads
├── templates/         # HTML templates
├── instance/         # Instance-specific files
└── node_modules/    # Frontend dependencies
```

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## 📝 License

ISC License

## 👤 Author

Vanshika

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 