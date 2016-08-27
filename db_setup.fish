#!/usr/bin/fish
set db_url "http://localhost:5984/iou"

# Create database
curl -X PUT $db_url

# Create design doc
curl -H "Content-Type: application/json" -X POST -d @couchdb.json $db_url
