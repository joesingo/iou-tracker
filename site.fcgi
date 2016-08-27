#!/usr/bin/python
import sys

from flup.server.fcgi import WSGIServer
from app import app

if __name__ == "__main__":
    WSGIServer(app, bindAddress=sys.argv[1]).run()


