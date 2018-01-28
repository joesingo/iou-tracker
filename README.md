# iou-tracker

Flask web app to record IOUs between friends.

## Install

Install requirements in a Python 3 virtualenv:

```
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

Create database:

```
sqlite3 ioudb < schema.sql
```

Run Flask app

```
python app.py
```

## Tests

Tests are written with `pytest` - to run use:

```
pytest tests.py
```
