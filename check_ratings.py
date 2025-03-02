from app import app, db, Rating

with app.app_context():
    rating = Rating.query.first()
    if rating:
        print(f"Rating details:")
        print(f"Product ID: {rating.product_id}")
        print(f"User ID: {rating.user_id}")
        print(f"Rating: {rating.rating} stars")
        print(f"Review: {rating.review}")
        print(f"Created at: {rating.created_at}")
    else:
        print("No ratings found")
