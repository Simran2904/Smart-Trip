import os
import uuid
from datetime import datetime
from database.mongodb_db import get_mongo_database

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from mysql.connector import IntegrityError
from dotenv import load_dotenv

from database.mysql_db import get_mysql_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "development-key-change-me")


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        connection = None
        cursor = None

        try:
            connection = get_mysql_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO users
                (full_name, email, password_hash, phone)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (full_name, email, password_hash, phone or None)
            )
            connection.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except IntegrityError:
            flash("This email address is already registered.", "danger")

        except Exception as error:
            app.logger.exception("Registration error")
            flash("Registration failed. Please check the database connection.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_mysql_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT user_id, full_name, email, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(user[3], password):
                session.clear()
                session["user_id"] = user[0]
                session["full_name"] = user[1]
                session["email"] = user[2]

                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")

        except Exception:
            app.logger.exception("Login error")
            flash("Unable to log in. Please try again.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        full_name=session.get("full_name"),
        email=session.get("email")
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/create-trip", methods=["GET", "POST"])
def create_trip():
    if "user_id" not in session:
        return redirect(url_for("login"))

    mongo_client = None

    # GET: Display the trip form
    if request.method == "GET":
        try:
            mongo_client, mongo_db = get_mongo_database()

            destinations = list(
                mongo_db.destinations.find(
                    {},
                    {
                        "_id": 0,
                        "destination_id": 1,
                        "name": 1,
                        "state": 1,
                        "hotels": 1
                    }
                )
            )

            return render_template(
                "create_trip.html",
                destinations=destinations
            )

        except Exception:
            app.logger.exception("Could not load destinations")
            return "Unable to load destinations. Check the Flask terminal."

        finally:
            if mongo_client:
                mongo_client.close()

    # POST: Save the submitted trip
    connection = None
    cursor = None

    try:
        starting_city = request.form.get("starting_city", "").strip()
        destination_id = request.form.get("destination_id", "").strip()
        departure_text = request.form.get("departure_date", "")
        return_text = request.form.get("return_date", "")
        transport_mode = request.form.get("transport_mode", "").strip()
        hotel_name = request.form.get("hotel_name", "").strip()

        travellers = int(request.form.get("travellers", "0"))
        hotel_rooms = int(request.form.get("hotel_rooms", "0"))

        if (
            not starting_city or not destination_id or
            not departure_text or not return_text or
            not transport_mode or not hotel_name or
            travellers < 1 or hotel_rooms < 1
        ):
            flash("Please complete all trip details.", "danger")
            return redirect(url_for("create_trip"))

        departure_date = datetime.strptime(
            departure_text, "%Y-%m-%d"
        ).date()

        return_date = datetime.strptime(
            return_text, "%Y-%m-%d"
        ).date()

        nights = (return_date - departure_date).days

        if nights <= 0:
            flash("Return date must be after departure date.", "danger")
            return redirect(url_for("create_trip"))

        # Get the selected destination and its prices from MongoDB
        mongo_client, mongo_db = get_mongo_database()

        destination = mongo_db.destinations.find_one(
            {"destination_id": destination_id}
        )

        if not destination:
            flash("Selected destination was not found.", "danger")
            return redirect(url_for("create_trip"))

        selected_hotel = next(
            (
                hotel for hotel in destination.get("hotels", [])
                if hotel.get("name") == hotel_name
            ),
            None
        )

        selected_transport = next(
            (
                item for item in destination.get("transport", [])
                if item.get("mode", "").lower() == transport_mode.lower()
            ),
            None
        )

        if not selected_hotel or not selected_transport:
            flash("Selected hotel or transport is unavailable.", "danger")
            return redirect(url_for("create_trip"))

        # Calculate estimated costs
        transport_cost = (
            float(selected_transport.get("price_per_person", 0))
            * travellers
        )

        hotel_cost = (
            float(selected_hotel.get("price_per_room", 0))
            * hotel_rooms
            * nights
        )

        food_cost = (
            float(destination.get("food_estimate_per_person_per_day", 0))
            * travellers
            * nights
        )

        activities_cost = (
            float(destination.get("activity_estimate_per_person", 0))
            * travellers
        )

        miscellaneous_cost = 200 * travellers * nights

        total_cost = (
            transport_cost
            + hotel_cost
            + food_cost
            + activities_cost
            + miscellaneous_cost
        )

        # Save the trip and its expense breakdown in MySQL
        connection = get_mysql_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO trips (
                user_id, destination_id, destination_name,
                starting_city, departure_date, return_date,
                travellers, transport_mode, transport_cost,
                hotel_name, hotel_price_per_room, hotel_rooms,
                hotel_nights, food_cost, activities_cost,
                miscellaneous_cost, total_cost
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                session["user_id"],
                destination_id,
                destination.get("name", ""),
                starting_city,
                departure_date,
                return_date,
                travellers,
                transport_mode,
                transport_cost,
                hotel_name,
                float(selected_hotel.get("price_per_room", 0)),
                hotel_rooms,
                nights,
                food_cost,
                activities_cost,
                miscellaneous_cost,
                total_cost
            )
        )

        trip_id = cursor.lastrowid

        expenses = [
            ("Transport", "Estimated transport cost", transport_cost),
            ("Hotel", "Estimated hotel cost", hotel_cost),
            ("Food", "Estimated food cost", food_cost),
            ("Activities", "Estimated activities cost", activities_cost),
            ("Miscellaneous", "Estimated miscellaneous expenses", miscellaneous_cost)
        ]

        for category, description, amount in expenses:
            cursor.execute(
                """
                INSERT INTO expenses
                    (trip_id, category, description, amount, expense_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (trip_id, category, description, amount, departure_date)
            )

        connection.commit()

        flash("Your trip has been saved successfully!", "success")
        return redirect(url_for("trip_summary", trip_id=trip_id))

    except ValueError:
        if connection:
            connection.rollback()
        flash("Please enter valid numbers and dates.", "danger")
        return redirect(url_for("create_trip"))

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Error saving trip")
        flash("Could not save your trip. Please check the Flask terminal.", "danger")
        return redirect(url_for("create_trip"))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
        if mongo_client:
            mongo_client.close()


@app.route("/trip-summary/<int:trip_id>")
def trip_summary(trip_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        # Only allow the logged-in user to view their own trip
        cursor.execute(
            """
            SELECT *
            FROM trips
            WHERE trip_id = %s AND user_id = %s
            """,
            (trip_id, session["user_id"])
        )

        trip = cursor.fetchone()

        if not trip:
            flash("Trip not found.", "warning")
            return redirect(url_for("dashboard"))

        cursor.execute(
            """
            SELECT category, description, amount
            FROM expenses
            WHERE trip_id = %s
            ORDER BY expense_id
            """,
            (trip_id,)
        )

        expenses = cursor.fetchall()

        return render_template(
            "trip_summary.html",
            trip=trip,
            expenses=expenses
        )

    except Exception:
        app.logger.exception("Could not load trip summary")
        return "Unable to load trip summary. Check the Flask terminal."

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/payment/<int:trip_id>", methods=["GET", "POST"])
def payment(trip_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        # Verify that this trip belongs to the logged-in user
        cursor.execute(
            """
            SELECT trip_id, destination_name, total_cost
            FROM trips
            WHERE trip_id = %s AND user_id = %s
            """,
            (trip_id, session["user_id"])
        )

        trip = cursor.fetchone()

        if not trip:
            flash("Trip not found.", "danger")
            return redirect(url_for("dashboard"))

        if request.method == "POST":

            payment_method = request.form.get("payment_method", "")

            allowed_methods = ["UPI", "Card", "Net Banking"]

            if payment_method not in allowed_methods:
                flash("Please select a valid payment method.", "danger")
                return redirect(url_for("payment", trip_id=trip_id))

            # Prevent duplicate successful payments
            cursor.execute(
                """
                SELECT payment_id
                FROM payments
                WHERE trip_id = %s
                AND payment_status = 'Successful'
                """,
                (trip_id,)
            )

            if cursor.fetchone():
                flash("Payment for this trip is already completed.", "info")
                return redirect(url_for("payment", trip_id=trip_id))

            transaction_reference = "SIM-" + uuid.uuid4().hex[:12].upper()

            cursor.execute(
                """
                INSERT INTO payments (
                    trip_id,
                    payment_method,
                    amount,
                    payment_status,
                    transaction_reference
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    trip_id,
                    payment_method,
                    trip["total_cost"],
                    "Successful",
                    transaction_reference
                )
            )

            connection.commit()

            return render_template(
                "payment_success.html",
                trip=trip,
                payment_method=payment_method,
                transaction_reference=transaction_reference
            )

        return render_template("payment.html", trip=trip)

    except Exception:
        if connection:
            connection.rollback()

        app.logger.exception("Payment processing error")
        flash("Unable to process payment. Please try again.", "danger")
        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


@app.route("/trip-history")
def trip_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM trips
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (session["user_id"],))

        trips = cursor.fetchall()

        return render_template(
            "trip_history.html",
            trips=trips
        )

    except Exception:
        app.logger.exception("Trip history error")
        return "Unable to load trip history. Check Flask terminal."

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "account.html",
        full_name=session.get("full_name"),
        email=session.get("email")
    )


if __name__ == "__main__":
    app.run(debug=True)
