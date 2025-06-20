# Gujarat Plumber Finder

A professional web application to help users find the best available plumbers in Gujarat based on their requirements such as location, work type, time slot, and language preference.

---

## Features
- **Smart Matching:** Find plumbers by district, work specialization, available time slot, and language.
- **Professional UI:** Clean, responsive frontend built with HTML, CSS (Bootstrap), and JavaScript.
- **Fast Results:** Instantly see a sorted list of matching plumbers with all relevant details.
- **Easy Setup:** Simple to run locally with Python and pip.
- **Role-based Dashboards:** Separate dashboards for customers, plumbers, and admins.
- **Booking Notifications:** Plumbers and admins see notifications for new bookings on their dashboards.
- **Location-Aware Booking:** Customers must set their location using the "Use My Current Location" button before booking.
- **Analytics:** Admin dashboard includes charts for bookings per month and top plumbers.

---

## Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd project plumber
```

### 2. Install Dependencies
Make sure you have Python 3.8+ and pip installed.
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Open in Browser
Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to use the app. You will be redirected to the login page first.

---

## File Structure
```
project plumber/
├── app.py                  # Flask backend
├── gujarat_plumbers_dataset.csv  # Plumber data
├── requirements.txt        # Python dependencies
├── models.py               # SQLAlchemy models
├── templates/
│   ├── index.html          # (not used, root redirects to login)
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── customer_dashboard.html
│   ├── plumber_dashboard.html
│   ├── admin_dashboard.html
│   └── book_plumber.html
├── static/
│   ├── style.css           # Custom styles
│   └── script.js           # Frontend JS logic
└── README.md               # This file
```

---

## How It Works
1. **User registers and logs in** as customer, plumber, or admin.
2. **Customers:**
   - Book plumbers by selecting date, time slot, work type, language, and setting their location.
   - Must click "Use My Current Location" before booking.
   - See booking confirmation and all bookings in their dashboard.
3. **Plumbers:**
   - See new booking notifications on their dashboard.
   - Accept/reject/complete jobs, update availability, and view reviews.
4. **Admins:**
   - See new booking notifications and analytics on their dashboard.
   - Manage all users, plumbers, bookings, and reviews.

---

## Troubleshooting
- **Dropdowns not working in booking form:**
  - Make sure you have at least one plumber registered with specialization and free time slots.
  - If you want to bulk import plumbers from the CSV, ask for a script.
- **Location error when booking:**
  - You must click "Use My Current Location" and allow browser geolocation before booking.
- **Login page is the first page:**
  - This is by design for security and clarity.
- **Notifications not showing:**
  - Notifications for new bookings appear once on plumber/admin dashboards after a booking is made.

---

## Future Improvements
- User ratings & reviews
- Map view of plumbers
- Booking & scheduling calendar
- Plumber profiles
- Cost estimation
- Admin dashboard analytics
- Multi-language support
- Online payments
- Email/SMS notifications

---

## License
MIT License 