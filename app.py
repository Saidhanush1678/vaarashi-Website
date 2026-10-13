
import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, abort
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    DATABASE=os.environ.get(
        "DATABASE_PATH",
        os.path.join(INSTANCE_DIR, "vaaraahi.db")
    ),
    BUSINESS_PHONE=os.environ.get(
        "BUSINESS_PHONE", "917981903060"
    ),
    BUSINESS_ADDRESS=os.environ.get(
        "BUSINESS_ADDRESS", "Kishanpura, Hanamkonda"
    ),
    GOOGLE_MAPS_URL=os.environ.get(
        "GOOGLE_MAPS_URL",
        "https://share.google/VpnMX2Zu9HV9KZZ8l"
    ),
    ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
    ADMIN_PASSWORD=os.environ.get(
        "ADMIN_PASSWORD", "change-this-password"
    ),
)

SERVICES = [
    ("Dry Cleaning", "Careful cleaning for suits, dresses, delicate fabrics and special garments.", "Dry Cleaning"),
    ("Laundry & Wash Care", "Everyday washing, drying, folding and fresh-clothes care.", "Laundry"),
    ("Premium Saree Care", "Special handling and finishing for silk, designer and occasion sarees.", "Saree Care"),
    ("Saree Rolling", "Neat saree rolling and presentation for easier storage and travel.", "Saree Rolling"),
    ("Saree Polishing", "Finishing and polishing services selected to suit the garment.", "Polishing"),
    ("Steam Ironing & Pressing", "Wrinkle reduction and crisp finishing for everyday and occasion wear.", "Ironing"),
    ("Stain Removal", "Fabric-appropriate treatment for suitable stains, subject to inspection.", "Stain Removal"),
    ("Blanket & Bedding Care", "Freshen selected blankets, bed covers and household textiles.", "Bedding Care"),
]


def get_db():
    if "db" not in g:
        db_path = app.config["DATABASE"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db_path = app.config["DATABASE"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = sqlite3.connect(db_path)

    db.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'per item',
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT DEFAULT '',
            address TEXT NOT NULL,
            pickup_date TEXT NOT NULL,
            pickup_time TEXT NOT NULL,
            service_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            notes TEXT DEFAULT '',
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Order received',
            created_at TEXT NOT NULL,
            FOREIGN KEY(service_id) REFERENCES services(id)
        )
    """)

    existing = db.execute(
        "SELECT COUNT(*) FROM services"
    ).fetchone()[0]

    if existing == 0:
        defaults = [
            ("Dry Cleaning", "Careful cleaning for suits, dresses and delicate garments.", 0, "per item", 1),
            ("Laundry & Wash Care", "Washing, drying and folding.", 0, "per kg", 1),
            ("Premium Saree Care", "Special handling and finishing for premium sarees.", 0, "per saree", 1),
            ("Saree Rolling", "Neat saree rolling.", 0, "per saree", 1),
            ("Saree Polishing", "Finishing service for suitable sarees.", 0, "per saree", 1),
            ("Steam Ironing & Pressing", "Wrinkle reduction and crisp pressing.", 0, "per item", 1),
            ("Stain Removal", "Treatment for suitable stains after inspection.", 0, "per item", 1),
            ("Blanket & Bedding Care", "Care for selected household textiles.", 0, "per item", 1),
        ]

        db.executemany("""
            INSERT INTO services
            (name, description, price, unit, active)
            VALUES (?, ?, ?, ?, ?)
        """, defaults)

    db.commit()
    db.close()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash(
                "Please sign in to the admin dashboard.",
                "error"
            )
            return redirect(url_for("admin_login"))

        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    return {
        "business_phone": app.config["BUSINESS_PHONE"],
        "business_address": app.config["BUSINESS_ADDRESS"],
        "google_maps_url": app.config["GOOGLE_MAPS_URL"],
        "year": datetime.now().year,
    }


@app.route("/")
def home():
    db = get_db()

    services = db.execute("""
        SELECT * FROM services
        WHERE active = 1
        ORDER BY id
        LIMIT 6
    """).fetchall()

    return render_template("index.html", services=services)


@app.route("/services")
def services_page():
    services = get_db().execute("""
        SELECT * FROM services
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    return render_template(
        "services.html",
        services=services
    )


@app.route("/order", methods=["GET", "POST"])
def order():
    db = get_db()

    services = db.execute("""
        SELECT * FROM services
        WHERE active = 1
        ORDER BY name
    """).fetchall()

    if request.method == "POST":
        name = request.form.get(
            "customer_name", ""
        ).strip()

        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        pickup_date = request.form.get(
            "pickup_date", ""
        ).strip()

        pickup_time = request.form.get(
            "pickup_time", ""
        ).strip()

        notes = request.form.get("notes", "").strip()

        payment = request.form.get(
            "payment_method", ""
        ).strip()

        service_id = request.form.get(
            "service_id", type=int
        )

        quantity = request.form.get(
            "quantity", type=int
        )

        if not all([
            name, phone, address, pickup_date,
            pickup_time, service_id, payment
        ]):
            flash(
                "Please complete all required fields.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        if len(phone) < 8 or len(phone) > 20:
            flash(
                "Please enter a valid contact number.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        if quantity is None or quantity < 1 or quantity > 100:
            flash(
                "Quantity must be between 1 and 100.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        if payment not in {
            "Cash", "UPI", "Online payment"
        }:
            flash(
                "Choose a valid payment option.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        service = db.execute("""
            SELECT id FROM services
            WHERE id = ? AND active = 1
        """, (service_id,)).fetchone()

        if not service:
            flash(
                "That service is no longer available.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        try:
            pickup_dt = datetime.strptime(
                pickup_date, "%Y-%m-%d"
            ).date()

            if pickup_dt < datetime.now().date():
                raise ValueError

        except ValueError:
            flash(
                "Please choose today or a future pickup date.",
                "error"
            )
            return render_template(
                "order.html", services=services
            )

        code = "VAA" + secrets.token_hex(3).upper()

        db.execute("""
            INSERT INTO orders (
                order_code, customer_name, phone, email,
                address, pickup_date, pickup_time,
                service_id, quantity, notes, payment_method,
                status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            phone,
            email,
            address,
            pickup_date,
            pickup_time,
            service_id,
            quantity,
            notes,
            payment,
            "Order received",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        db.commit()

        session["last_order_code"] = code

        return redirect(
            url_for(
                "order_confirmation",
                order_code=code
            )
        )

    return render_template(
        "order.html",
        services=services
    )


@app.route("/order/confirmation/<order_code>")
def order_confirmation(order_code):
    db = get_db()

    row = db.execute("""
        SELECT o.*, s.name AS service_name
        FROM orders o
        JOIN services s ON s.id = o.service_id
        WHERE o.order_code = ?
    """, (order_code,)).fetchone()

    if not row:
        abort(404)

    if (
        session.get("last_order_code") != order_code
        and not session.get("is_admin")
    ):
        abort(403)

    message = (
        f"Hello Vaaraahi Dry Cleaners, I placed order "
        f"{row['order_code']}. "
        f"Name: {row['customer_name']}; "
        f"Service: {row['service_name']}; "
        f"Pickup: {row['pickup_date']} {row['pickup_time']}; "
        f"Address: {row['address']}. "
        f"Please confirm my pickup."
    )

    whatsapp_number = "".join(
        ch for ch in app.config["BUSINESS_PHONE"]
        if ch.isdigit()
    )

    whatsapp_url = (
        f"https://wa.me/{whatsapp_number}"
        f"?text={quote(message)}"
    )

    return render_template(
        "confirmation.html",
        order=row,
        whatsapp_url=whatsapp_url
    )


@app.route("/track", methods=["GET", "POST"])
def track_order():
    order_row = None

    if request.method == "POST":
        code = request.form.get(
            "order_code", ""
        ).strip().upper()

        phone = request.form.get(
            "phone", ""
        ).strip()

        order_row = get_db().execute("""
            SELECT
                o.order_code,
                o.customer_name,
                o.pickup_date,
                o.pickup_time,
                o.status,
                o.created_at,
                s.name AS service_name
            FROM orders o
            JOIN services s ON s.id = o.service_id
            WHERE o.order_code = ? AND o.phone = ?
        """, (code, phone)).fetchone()

        if not order_row:
            flash(
                "We couldn't find an order matching that code and phone number.",
                "error"
            )

    return render_template(
        "track.html",
        order=order_row
    )


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        configured_user = app.config["ADMIN_USERNAME"]
        configured_password = app.config["ADMIN_PASSWORD"]

        if (
            secrets.compare_digest(
                username, configured_user
            )
            and secrets.compare_digest(
                password, configured_password
            )
        ):
            session.clear()
            session["is_admin"] = True
            session["admin_user"] = username

            return redirect(url_for("admin_dashboard"))

        flash(
            "Invalid admin username or password.",
            "error"
        )

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()

    orders = db.execute("""
        SELECT
            o.*,
            s.name AS service_name,
            s.price AS service_price
        FROM orders o
        JOIN services s ON s.id = o.service_id
        ORDER BY o.id DESC
        LIMIT 250
    """).fetchall()

    services = db.execute("""
        SELECT * FROM services
        ORDER BY name
    """).fetchall()

    counts = {
        "total": db.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0],

        "new": db.execute("""
            SELECT COUNT(*) FROM orders
            WHERE status = 'Order received'
        """).fetchone()[0],

        "processing": db.execute("""
            SELECT COUNT(*) FROM orders
            WHERE status = 'Cleaning in progress'
        """).fetchone()[0],

        "ready": db.execute("""
            SELECT COUNT(*) FROM orders
            WHERE status = 'Ready for delivery'
        """).fetchone()[0],
    }

    return render_template(
        "admin_dashboard.html",
        orders=orders,
        services=services,
        counts=counts
    )


@app.route(
    "/admin/service/<int:service_id>",
    methods=["POST"]
)
@admin_required
def update_service(service_id):
    name = request.form.get("name", "").strip()

    description = request.form.get(
        "description", ""
    ).strip()

    unit = request.form.get(
        "unit", "per item"
    ).strip()

    price = request.form.get("price", type=float)

    active = (
        1 if request.form.get("active") == "on"
        else 0
    )

    if (
        not name
        or price is None
        or price < 0
        or price > 1000000
    ):
        flash(
            "Enter a valid service name and non-negative price.",
            "error"
        )
    else:
        try:
            cursor = get_db().execute("""
                UPDATE services
                SET name = ?, description = ?,
                    price = ?, unit = ?, active = ?
                WHERE id = ?
            """, (
                name,
                description,
                price,
                unit,
                active,
                service_id
            ))

            get_db().commit()

            if cursor.rowcount == 0:
                flash("Service not found.", "error")
            else:
                flash(
                    "Service and price updated.",
                    "success"
                )

        except sqlite3.IntegrityError:
            flash(
                "That service name already exists.",
                "error"
            )

    return redirect(
        url_for("admin_dashboard") + "#pricing"
    )


@app.route(
    "/admin/order/<int:order_id>/status",
    methods=["POST"]
)
@admin_required
def update_order_status(order_id):
    status = request.form.get("status", "")

    allowed = {
        "Order received",
        "Pickup scheduled",
        "Picked up",
        "Cleaning in progress",
        "Ready for delivery",
        "Out for delivery",
        "Delivered",
        "Cancelled"
    }

    if status not in allowed:
        flash("Invalid order status.", "error")
    else:
        cursor = get_db().execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )

        get_db().commit()

        if cursor.rowcount == 0:
            flash("Order not found.", "error")
        else:
            flash(
                "Order status updated.",
                "success"
            )

    return redirect(
        url_for("admin_dashboard") + "#orders"
    )


@app.route("/admin/logout")
def admin_logout():
    session.clear()

    flash(
        "You have been signed out.",
        "success"
    )

    return redirect(url_for("home"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


with app.app_context():
    init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
