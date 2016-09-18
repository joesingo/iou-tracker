from passlib.hash import pbkdf2_sha256
import json, re
from datetime import datetime

from flask import Flask, session, redirect, render_template, request, abort
import requests

BASE_DB_URL = "http://localhost:5984/"
DB_URL = BASE_DB_URL + "iou/"

PASSWORDS_FILE = "passwd.json"

app = Flask(__name__)

def create_iou(a, b):
    """
    Create a new IOU doc for persons a and b and save in DB. Return True if
    successful, False if not
    """
    doc = {}
    doc["people"] = [a, b]
    doc["transactions"] = []
    doc["currency"] = u"\xA3"

    res = requests.get(BASE_DB_URL + "_uuids")
    uuid = json.loads(res.content)["uuids"][0]

    res = requests.put(DB_URL + uuid, data=json.dumps(doc))
    content = json.loads(res.content)

    return "error" not in content


def is_logged_in():
    return "username" in session


@app.route("/")
def home():
    """
    Show a list of all IOUs for this user and the associated transactions for
    each
    """
    if not is_logged_in():
        return redirect("/login/")

    res = requests.get(DB_URL + "_design/iou/_view/getious/?key=\"{}\"" \
                                .format(session["username"]))

    content = json.loads(res.content)

    if "error" in content:
        abort(500)

    data = {}

    for row in content["rows"]:
        # Get the username of the other person
        names = row["value"]["people"]
        names.remove(session["username"])
        person = names[0]

        data[person] = row["value"]

        # Work out the amount owed to the user
        data[person]["owed"] = 0
        data[person]["total_borrowed"] = 0
        data[person]["total_owed"] = 0
        for i, t in enumerate(row["value"]["transactions"]):
            sign = -1 if t["borrower"] == session["username"] else 1
            data[person]["owed"] += sign * t["amount"]

            if t["borrower"] == session["username"]:
                data[person]["total_borrowed"] += t["amount"]
            else:
                data[person]["total_owed"] += t["amount"]

            # Format date so it can be displayed nicely in template
            date = datetime.fromtimestamp(t["timestamp"])
            data[person]["transactions"][i]["formatted_date"] = format(date, "%d/%m/%y")

        # Sort by date - newest first
        data[person]["transactions"].sort(key=lambda x: -x["timestamp"])

    return render_template("list.html", data=data, username=session["username"],
                           format_money=format_money)


@app.route("/save/", methods=["POST"])
def save():
    """
    Take a JSON object containing new transactions to be saved and append them
    to the doc in the DB
    """
    req = request.json

    # Get the document
    res = requests.get(DB_URL + "_design/iou/_view/getiou/?key=[\"{}\",\"{}\"]" \
                                 .format(session["username"], req["person"]))

    content = json.loads(res.content)

    if "error" in content or len(content["rows"]) != 1:
        abort(500)

    doc = content["rows"][0]["value"]

    for t in req["transactions"]:
        # TODO: Validate transactions
        t["amount"] = float(t["amount"])
        doc["transactions"].append(t)

    # Put new doc in DB
    res = requests.put(DB_URL + doc["_id"], data=json.dumps(doc))
    content = json.loads(res.content)
    if "error" in content:
        abort(500)
    else:
        return "woohoo"


@app.route("/login/")
def login_form(login_error=False):
    return render_template("login.html", error=login_error)


@app.route("/login/", methods=["POST"])
def login():
    if "username" not in request.form or "password" not in request.form:
        return login_form()
    else:
        with open(PASSWORDS_FILE) as passwords_file:
            password_store = json.load(passwords_file)

            if request.form["username"] in password_store:
                password_hash = password_store[request.form["username"]]
                if pbkdf2_sha256.verify(request.form["password"], password_hash):
                    #Login was successful
                    session["username"] = request.form["username"]
                    return redirect("/")

    return login_form(login_error=True)


@app.route("/create-account/", methods=["GET"])
def create_account_form(error_msg=None):
    return render_template("create_account.html", error_msg=error_msg)


@app.route("/create-account/", methods=["POST"])
def create_account():
    if "username" not in request.form or "password" not in request.form:
        return create_account_form()

    with open(PASSWORDS_FILE, "r") as passwords_file:
        password_store = json.load(passwords_file)

    # Check there is not already a user with this username
    if request.form["username"] in password_store:
        message = "Username '{}' is already in use".format(request.form["username"])
        return create_account_form(error_msg=message)

    # Add user to the JSON file
    hashed_password = pbkdf2_sha256.encrypt(request.form["password"],
                                            rounds=2000, salt_size=16)
    password_store[request.form["username"]] = hashed_password

    with open(PASSWORDS_FILE, "w") as passwords_file:
        json.dump(password_store, passwords_file)

    # Log in as newly created user
    session["username"] = request.form["username"]
    return home()


@app.route("/logout/")
def logout():
    if "username" in session:
        del session["username"]
    return redirect("/login/")


def format_money(n):
    """
    Convert n to a string and add an extra 0 on the end if necessary
    """
    s = str(n)
    if re.search("\.\d$", s):
        s += "0"

    return s


app.secret_key = "\xf2%Z\xfa\\0\xd0\xb5\x8e9\x87\xea\xa4{\x8es"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=7000)
