# Hospital Database Management System

A comprehensive web-based solution for managing hospital admissions, patients, and departments.

## Features

- User authentication system
- Patient management
- Admission tracking
- Department management
- Doctor management
- Real-time dashboard with statistics
- Modern and responsive UI

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd hospital-database-management-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
- Create a new database named 'hospital_db'
- Run the SQL script provided in the repository to create the tables and insert sample data

5. Configure the database connection:
- Open `app.py` and update the `SQLALCHEMY_DATABASE_URI` with your database credentials:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/hospital_db'
```

6. Run the application:
```bash
python app.py
```

7. Open your web browser and navigate to:
```
http://localhost:5000
```

## Default Login Credentials

- Admin:
  - Username: admin
  - Password: admin123

- Doctor:
  - Username: doctor1
  - Password: doctor123

## Project Structure

```
hospital-database-management-system/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── login.html        # Login page
    └── dashboard.html    # Dashboard page
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 