from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hotel123"

DATABASE = "hotel.db"

# -------------------------
# Create Database & Table
# -------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hotel_id INTEGER,
            name TEXT NOT NULL,
            checkin TEXT NOT NULL,
            checkout TEXT NOT NULL,
            room TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# -------------------------
# Sample Hotel Data
# -------------------------
hotels = {
    "goa": [
        {"id": 1, "name": "Goa Beach Resort", "price": 3000, "image": "goa.jpeg"}
    ],
    "mumbai": [
        {"id": 2, "name": "Taj Hotel", "price": 6000, "image": "tajhotel.jpeg"}
    ],
    "delhi": [
        {"id": 3, "name": "Delhi Palace", "price": 4000, "image": "airport.jpeg"}
    ]
}

# -------------------------
# Routes
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    city = request.form["city"].lower()
    return redirect(url_for("city_hotels", city=city))

@app.route("/city/<city>")
def city_hotels(city):
    data = hotels.get(city, [])
    return render_template("city.html", hotels=data, city=city)

# -------- Booking → Redirect to Payment --------
@app.route("/book/<int:hotel_id>", methods=["POST"])
def book_hotel(hotel_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]
    room = request.form["room"]

    session["booking_data"] = {
        "hotel_id": hotel_id,
        "name": name,
        "checkin": checkin,
        "checkout": checkout,
        "room": room
    }

    return redirect(url_for("payment"))
# -------- Payment Route --------
@app.route("/payment", methods=["GET", "POST"])
def payment():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        booking = session.get("booking_data")

        if booking:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bookings 
                (user_id, hotel_id, name, checkin, checkout, room)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                booking["hotel_id"],
                booking["name"],
                booking["checkin"],
                booking["checkout"],
                booking["room"]
            ))

            conn.commit()
            conn.close()

            session.pop("booking_data", None)

        return render_template("success.html")

    return render_template("payment.html")
# -------- History --------
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE user_id=?", 
                   (session["user_id"],))
    data = cursor.fetchall()

    conn.close()

    return render_template("history.html", bookings=data)
# -------- Admin --------
@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", bookings=data)
# -------- Login --------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        session.clear()  # clear old session first

        # Admin Login
        if username == "admin" and password == "123":
            session["role"] = "admin"
            return redirect(url_for("admin"))

        # User Login
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["role"] = "user"
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("home"))
        else:
            return "Invalid Credentials"

    return render_template("login.html")
#-----register by user____

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                           (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            conn.close()
            return "Username already exists"

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# -------- Run --------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)