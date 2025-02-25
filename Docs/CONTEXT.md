# Grocery Store Website - Functional Flow and Features

## 1. Homepage Layout
### Hero Section
- Displays featured products or promotional banners at the top.

### Quick Categories
- Icons for key categories:
  - Fruits & Vegetables
  - Dairy
  - Snacks
  - Beverages
  - Bakery
  - Oils & Spices

### Top Deals Section
- Carousel showcasing discounted products.

### Search Bar
- Prominently placed at the top for easy product searches.

---

## 2. Navbar Structure
### Left Side
- **Logo**: Links to homepage.
- **Categories Dropdown**: Lists major product categories such as:
  - Pantry
  - Beverages
  - Personal Care

### Right Side
- **Search Icon**
- **Account Icon**: Dropdown for Login/Register.
- **Cart Icon**: Displays item count.
- **"Become a Seller" Button**: Redirects to a basic sign-up form.

---

## 3. Product Display
### Category Pages
- Grid layout with product cards.
- Each product card includes:
  - Product image
  - Name
  - Price
  - "Add to Cart" button
- **Sidebar Filters**:
  - Price range (static input fields)
  - Brand (checkbox selection)

### Product Page
- Large image gallery.
- Product title and price.
- Quantity selector.
- Short description with weight/variant options.
- "Add to Cart" button.

---

## 4. User Account Section
### Registration/Login
- Basic form with:
  - Email/Phone
  - Password

### Dashboard
- **Order History**: Displays order status (Delivered/Pending).
- **Saved Addresses**: Users can add/edit saved addresses.
- **Wishlist Section**: Users can save products for later.
- **Seller Mode Toggle**: Available if user is approved as a seller.

---

## 5. Cart & Checkout
### Cart Page
- List of items with:
  - Quantity controls
  - Total price summary
  - "Proceed to Checkout" button

### Checkout
- Address selection (existing or new entry option).
- Placeholder payment section with a "Confirm Order" button.
- No real payment gateway integration.

---

## 6. Seller Section (Simplified)
### "Become a Seller" Page
- Basic form with:
  - Name
  - Email
  - Mobile Number
- "Submit Request" button simulating approval process.

### Seller Dashboard (Post Approval)
- **Add Product** button: Allows sellers to list products.
- **Product Listing Table**: Sellers can edit/remove their products.
- **Basic Sales Stats**: Placeholder charts/data.

---

## 7. Excluded Elements (As Specified)
❌ No GSTIN/bank details collection
❌ No document uploads/verification
❌ No payment method selection
❌ No order tracking/SMS receipts

---

## 8. Sample User Flow
### Customer Flow
1. User lands on homepage.
2. Browses categories.
3. Adds items to cart.
4. Proceeds to checkout.

### Seller Flow
1. User clicks "Become a Seller."
2. Submits simplified form.
3. Gains access to seller dashboard.
4. Adds products via basic form.
5. Products appear in public categories.

---

This document provides a structured overview for developers to implement the grocery store website efficiently.
