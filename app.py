import json, re
from datetime import datetime

from flask import Flask, session, redirect, render_template, request, abort
import requests

from passwd import PASSWORDS

BASE_DB_URL = "http://localhost:5984/"
DB_URL = BASE_DB_URL + "iou/"

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
        for i, t in enumerate(row["value"]["transactions"]):
            sign = -1 if t["borrower"] == session["username"] else 1
            data[person]["owed"] += sign * t["amount"]

            # Format date so it can be displayed nicely in template
            date = datetime.fromtimestamp(t["timestamp"])
            data[person]["transactions"][i]["formatted_date"] = format(date, "%d/%m/%y")

        # Sort by date - newest first
        data[person]["transactions"].sort(key=lambda x: -x["timestamp"])

    return render_template("list.html", data=data, username=session["username"],
                           format_money=format_money)


@app.route("/save/", methods=["POST"])
def save():
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
        if request.form["username"] in PASSWORDS and \
             PASSWORDS[request.form["username"]] == request.form["password"]:

            #Login was successful
            session["username"] = request.form["username"]
            return redirect("/")
        else:
            return login_form(login_error=True)


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
    app.run(debug=True, host="0.0.0.0", port=80)