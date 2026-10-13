# Vaaraahi Dry Cleaners & Laundry

A responsive Flask + SQLite website for pickup requests, service pricing, order tracking, WhatsApp follow-up and an admin dashboard.

## Included
- Home page and service catalogue
- Dry cleaning, laundry, premium saree care, saree rolling, polishing, steam ironing, stain removal and bedding care
- Pickup request form with address, date, time, quantity, notes and payment preference
- SQLite storage for orders and service prices
- WhatsApp follow-up link after an order is placed
- Customer order tracking using order reference + phone
- Admin dashboard for order status and editable service prices
- Responsive mobile navigation

## Requirements
- Python 3.10 or newer
- Internet connection for Google Fonts and the remote decorative photos (the site layout and core functionality still work if images are unavailable)

## Windows setup (Command Prompt)
```bat
cd path\to\vaaraahi_laundry_website
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python app.py
```
Open `http://127.0.0.1:5000`.

If `py` is not recognized, try:
```bat
python -m venv venv
```

The SQLite database is created automatically at `instance\vaaraahi.db` when the app starts. No separate database installation is required.

## Admin login
For first local testing, if you have not configured environment variables:
- Username: `admin`
- Password: `change-this-password`

Change this password before using the site beyond local testing. The application reads `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`, `BUSINESS_PHONE`, `BUSINESS_ADDRESS` and `GOOGLE_MAPS_URL` from environment variables. For Windows CMD, set them before starting the app, for example:
```bat
set ADMIN_USERNAME=youradmin
set ADMIN_PASSWORD=your-strong-password
set SECRET_KEY=replace-with-a-long-random-secret
set BUSINESS_PHONE=919876543210
python app.py
```
`.env` is an example configuration file only; Flask does not automatically read it. To use `.env` directly, install `python-dotenv` and add `load_dotenv()` at the start of `app.py`, or set variables in CMD as above. Do not commit secrets to a public repository.

## Configure WhatsApp
Set `BUSINESS_PHONE` to the international number with country code, digits only, without `+`, spaces or dashes. Example for India: `919876543210`. Replace the placeholder before sharing the website. The WhatsApp button opens a pre-filled message; it does not send a message automatically.

## Payments
Cash, UPI and Online payment are currently saved as customer payment preferences only. No money is charged by this app. To accept actual online payments, integrate a payment gateway such as Razorpay or another provider and verify payments server-side before marking an order paid.

## Location
The default location text is `Kishanpura, Hanamkonda`; the map button uses the supplied Google Maps share link. Verify the pin/address and delivery service area before publishing.

## Important before public launch
- Use a strong `SECRET_KEY` and unique admin password.
- Do not run Flask's debug server in production. Deploy behind a production WSGI server and HTTPS.
- Add CSRF protection, rate limiting and stronger account/admin controls before public deployment.
- Confirm actual pickup/delivery areas, working hours, business phone and final prices.
- The pickup form creates a request; it does not guarantee a slot. Confirm bookings manually.
