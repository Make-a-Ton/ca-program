# Commands

## setup up python env (linux)

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## set up python env (windows)

- comment out psycopg2-binary==2.9.6 in requirements.txt
- uncomment this line before pushing

```bash
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

## migrate database

```bash
python manage.py migrate
```

## run Server

```bash
python manage.py runserver
```

## create superuser

```bash
python manage.py createsuperuser
```

## if changes in models

```bash
python manage.py makemigrations
python manage.py migrate
```
