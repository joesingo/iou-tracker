import os
import re
from datetime import datetime

from flask import Flask, session, redirect, render_template, request, abort

from iou import IOUApp, Transaction
from exceptions import DuplicateUsernameError

app = Flask(__name__)
iou_app = IOUApp()


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

    data = {}
    user = session["username"]
    for statement in iou_app.get_ious(user):
        data[statement.other_person] = {
            "owed": statement.owed,
            "total_owed": statement.total_owed,
            "total_borrowed": statement.total_borrowed,
            "transactions": iou_app.get_transactions(user, statement.other_person)
        }
    return render_template("list.html", data=data, format_money=format_money,
                           format_timestamp=format_timestamp, username=user)

@app.route("/save/", methods=["POST"])
def save():
    """
    Take a JSON object containing new transactions to be saved and append them
    to the doc in the DB
    """
    data = request.json
    try:
        t_list = map(lambda d: Transaction(**d), data["transactions"])
    except KeyError:
        abort(400)


    try:
        iou_app.add_transactions(t_list)
    except sqlite3.DatabaseError:
        abort(500)

    return "success"

@app.route("/login/")
def login_form(login_error=False):
    return render_template("login.html", error=login_error)


@app.route("/login/", methods=["POST"])
def login():
    if "username" not in request.form or "password" not in request.form:
        return login_form()

    if not iou_app.authenticate_user(request.form["username"],
                                     request.form["password"]):
        return login_form(login_error=True)

    session["username"] = request.form["username"]
    return redirect("/")


@app.route("/create-account/", methods=["GET"])
def create_account_form(error_msg=None):
    return render_template("create_account.html", error_msg=error_msg)


@app.route("/create-account/", methods=["POST"])
def create_account():
    if "username" not in request.form or "password" not in request.form:
        return create_account_form()

    try:
        iou_app.add_user(request.form["username"], request.form["password"])
    except DuplicateUsernameError as ex:
        return create_account_form(error_msg=str(ex))

    session["username"] = request.form["username"]
    return redirect("/")

@app.route("/logout/")
def logout():
    if "username" in session:
        del session["username"]
    return redirect("/login/")

def format_money(n):
    """
    Return a string representation of n to 2 decimal places
    """
    return "{:.2f}".format(n)

def format_timestamp(timestamp):
    """
    Return a string representation of a timestamp
    """
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%y")

app.secret_key = os.urandom(16)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=7000)
