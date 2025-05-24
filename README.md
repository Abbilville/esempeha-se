# Temu-Balik Informasi Project

## Team: ESEMPEHA
### Member:
1. Abbilhaidar Farras Zulfikar (2206026012)
2. Ravie Hasan Abud (2206031864)
3. Steven Faustin Orginata (2206030855)

### Deployment
Link Deployment: [https://esempeha-search.com](https://tart-honor-abbilville-e18670b6.koyeb.app/)

---

## Prerequisite

- Python 3.9 or higher
- pip (Python package installer)

## Setting Up the Environment

### 1. Clone the Repository

```bash
git clone https://github.com/Abbilville/esempeha-se TK
cd TK
```

### 2. Set Up a Virtual Environment

#### On Windows:
```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
env\Scripts\activate
```

#### On macOS/Linux:
```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Project

### 1. Start the Development Server

```bash
python manage.py runserver
```

This will start the server at http://127.0.0.1:8000/

### 2. Access the Application

- Main application: http://127.0.0.1:8000/
- Admin interface: http://127.0.0.1:8000/admin/

## Project Structure

```
TK/
├── esempeha/            # Main project directory
│   ├── __init__.py      # init
│   ├── asgi.py          # ASGI configuration
│   ├── settings.py      # Project settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI configuration
├── main/                # App directory (actual name may vary)
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   ├── urls.py          # URL patterns for this app
│   └── templates/       # HTML templates
├── static/              # Static files (CSS, JS, images)
├── templates/           # base HTML
├── manage.py            # Django management script
├── package-lock.json    # For setup tailwind
├── package.json         # For setup tailwind
├── requirements.txt     # Django requirements module
├── tailwind.config.js   # For setup tailwind
└── README.md            # This file
```

## Common Tasks

### Making Migrations After Model Changes

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files for Production

```bash
python manage.py collectstatic
```

### Running Tests

```bash
python manage.py test
```

## Troubleshooting

### Database Issues

If you encounter database issues, you might need to reset your database:

```bash
# Delete the database file (for SQLite)
rm db.sqlite3

# Recreate the database
python manage.py migrate
```

### Package Installation Problems

If you're having trouble with package installations, try updating pip:

```bash
pip install --upgrade pip
```

### Port Already in Use

If port 8000 is already in use, you can specify a different port:

```bash
python manage.py runserver 8001
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)

## Contact

If you have any questions or issues, please contact
- Abbilhaidar Farras Zulfikar: abbilhaidar.farras@ui.ac.id
- Ravie Hasan Abud: ravie.hasan@ui.ac.id
- Steven Faustin Orginata: steven.faustin@ui.ac.id
