# SMARTTRIP – A Trip Planning and Budget Estimation Application Using Polyglot Persistence

## 1. Project Overview

SMARTTRIP is a web-based trip planning and budget estimation application developed using Python Flask and Polyglot Persistence.

The application helps users plan trips by selecting destinations, travel dates, transport modes and hotels. It also estimates travel expenses to help users understand their approximate trip budget.

The project uses two different databases:
- **MySQL:** Stores structured information such as user accounts, trip details, expenses and payment records.
- **MongoDB:** Stores destination information, hotel details, transport estimates, attractions and other travel-related data.

The application demonstrates how multiple databases can work together in a single application.

## 2. Objectives

- To develop a user-friendly trip planning application.
- To implement Polyglot Persistence using MySQL and MongoDB.
- To store structured and unstructured data in appropriate databases.
- To calculate estimated trip expenses.
- To provide a centralized platform for managing trip information.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Relational database |
| MongoDB | NoSQL database |
| HTML | Web page structure |
| CSS | Styling |
| Bootstrap | Responsive user interface |
| JavaScript | Client-side interactions |
| Visual Studio Code | Development environment |

## 4. Database Design

### MySQL Database – smarttrip_db

MySQL is used to store structured application data.

Tables:
- users
- trips
- expenses
- payments

### MongoDB Database – smarttrip_mongo

MongoDB is used to store destination-related information.

Collection:
- destinations

The collection contains destination details, hotels, transport options, estimated food costs, activity costs and attractions.

## 5. Application Features

The project includes the following features:

- User registration and login.
- User dashboard.
- Trip planning form.
- Destination selection.
- Destination-specific hotel options.
- Transport selection.
- Travel date selection.
- Estimated miscellaneous expense calculation.
- MySQL and MongoDB database connectivity.

Additional planned features include trip history, detailed trip summaries and simulated payment processing.

## 6. Project Structure

```text
SmartTrip/
│
├── app.py
├── requirements.txt
├── .env.example
├── README.md
│
├── database/
│   ├── __init__.py
│   ├── mysql_db.py
│   └── mongodb_db.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── create_trip.html
│
├── static/
│   └── css/
│
└── test_db.py
```

## 7. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SmartTrip
```

Replace the repository URL with your actual GitHub repository URL.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory.

Add your own database configuration:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_MYSQL_PASSWORD
MYSQL_DATABASE=smarttrip_db

MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=smarttrip_mongo

SECRET_KEY=YOUR_SECRET_KEY
```

Do not upload your actual `.env` file or database password to GitHub.

### Step 5: Set Up Databases

1. Start MySQL and MongoDB.
2. Create the MySQL database named `smarttrip_db`.
3. Create the required MySQL tables.
4. Create the MongoDB database named `smarttrip_mongo`.
5. Insert the sample destination documents into the `destinations` collection.

### Step 6: Test Database Connections

Run:

```bash
python test_db.py
```

### Step 7: Run the Application

```bash
python app.py
```

Open the following address in your browser:

http://127.0.0.1:5000/

## 8. Polyglot Persistence Implementation

SMARTTRIP uses two databases to manage different types of information.

**MySQL** is used for relational data that requires structured tables and relationships, such as users and trips.

**MongoDB** is used for flexible destination-related documents containing nested hotel, transport and attraction information.

Python Flask coordinates communication between the two databases and uses their data to support trip planning.

## 9. Sample Data

The application currently uses sample destination information for:

- Goa
- Manali
- Mumbai
- Jaipur
- Munnar

Hotel and transport prices are illustrative estimates for academic demonstration purposes and are not live booking prices.

## 10. Future Enhancements

- Complete trip history and trip summary pages.
- Simulated payment confirmation.
- Improved expense reports.
- More destinations and travel options.
- Advanced search and filtering.
- Improved user profile management.

## 11. Author

**Project:** SMARTTRIP  
**Course:** Master of Computer Applications (MCA)  
**Project Type:** Mini Project – Polyglot Persistence Application

---

**Note:** This project is developed for academic and educational purposes. It does not perform real hotel bookings, transport bookings or financial transactions.
