kill -9 $(lsof -ti:8000)
python3 manage.py runserver