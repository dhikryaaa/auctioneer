import os

SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8000"),
    "activity": os.getenv("ACTIVITY_SERVICE_URL", "http://localhost:8000"),
    "bids": os.getenv("BID_SERVICE_URL", "http://localhost:8000"),
    "auctions": os.getenv("LISTING_SERVICE_URL", "http://localhost:8000"),
}

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

