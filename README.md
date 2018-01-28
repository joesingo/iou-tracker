# iou-tracker

Flask web app to record IOUs between friends.

## Development install

Install requirements in a Python 3 virtualenv:

```
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

Create database:

```
touch ioudb
./setup.py --tables
```

Run Flask app

```
python app.py
```

Adding IOU between users is not yet implemented in UI; instead use:
```
./setup.py --add-iou <user1> <user2>
```

## Tests

Tests are written with `pytest` - to run use:

```
pytest tests.py
```

## Docker install

```
# If creating new DB, touch DB file
touch ioudb

docker build -t iou .
docker run -d -p 5321:7000 -v $(pwd)/ioudb:/iou/ioudb iou

# If using a new DB then need to create tables
docker exec <container ID> /iou/setup.py --tables
```

This will start the app on local port 5321, and use the local file `ioudb` for
the SQLite database.
