from flask import Flask, session, redirect, render_template, request

PASSWORDS = {
    "joe": "pass"
}

app = Flask(__name__)

def is_logged_in():
    return "username" in session

@app.route("/")
def home():
    """
    Home page - show list of IOUs
    """

    if not is_logged_in():
        return redirect("/login")

    else:
        return "hey"

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


app.secret_key = "\xf2%Z\xfa\\0\xd0\xb5\x8e9\x87\xea\xa4{\x8es"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)