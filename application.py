import os
import psycopg2

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re
from helpers import login_required, postgresSQLConnection, formatProject
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

connection = psycopg2.connect(
    database=os.getenv("DATABASE_NAME"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    host=os.getenv("DATABASE_HOST"),
    port=os.getenv("DATABASE_PORT")
)

db = postgresSQLConnection(connection)
# db = connection.cursor()

# db = SQL(os.getenv("DATABASE_URL"))


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", message="")
    name = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    if name == "":
        return render_template("register.html", message="Missing name")
    elif password == "" or confirmation == "":
        return render_template("register.html", message="Missing password or confirm your password")
    elif password != confirmation:
        return render_template("register.html", message="Confirm password and password does not match")
    namepattern = re.compile("^(?=.{8,20}$)")
    passwordpattern = re.compile("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")
    if bool(namepattern.search(name)) is False:
        return render_template("register.html", message="Invalid username. Username must be 8-20 characters")
    elif bool(passwordpattern.search(password)) is False:
        return render_template("register.html", message="Invalid password. Password must be 8 characters, includes at least one number and one letter")
    name = name.strip().upper()
    nameList = db.execute(
        "SELECT * FROM users WHERE username=%(uname)s", {"uname": name})
    print(nameList)
    if nameList:
        return render_template("register.html", message="Duplicated username")
    hash = generate_password_hash(password)
    db.execute("INSERT INTO users (username, hash) VALUES (%(username)s, %(hash)s)", {
               "username": name, "hash": hash})
    return redirect("/login")


@app.route("/guestLogin")
def guestLogin():
    result = db.execute("SELECT * FROM users WHERE username = %(username)s",
                        {"username": "GUESTLOGIN"})
    # Remember which user has logged in
    session["user_id"] = result[0][0]
    return redirect("/lists")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", message="")
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", message="Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", message="Must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = %(username)s",
                          {"username": request.form.get("username").strip().upper()})

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return render_template("login.html", message="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page

        return redirect("/lists")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    userId = session["user_id"]
    functionsList = db.execute(
        "SELECT name FROM functions WHERE user_id = 0 OR user_id=%(userid)s", {"userid": userId})
    if request.method == "GET":
        return render_template("addform.html", message="", functions=functionsList)
    name = request.form.get("projectname").title().strip()
    purpose = request.form.get("projectpurpose").capitalize().strip()
    description = request.form.get("description").capitalize().strip()
    languages = request.form.get("languages").title().strip()
    expectedTime = request.form.get("time").title().strip()
    note = request.form.get("notes").capitalize().strip()
    functionsAddList = request.form.getlist("functions")
    if name == "" or purpose == "" or functionsAddList == "":
        return render_template("addform.html", message="Please fullfill all required information", functions=functionsList)
    if "Other" in functionsAddList:
        otherFunc = request.form.get("text").strip().capitalize()
        functionsAddList.remove('Other')
        functionsAddList.append(otherFunc)
    db.execute("INSERT INTO projects (user_id,name,purpose,description,languages,time,note) VALUES (%(userid)s,%(name)s,%(purpose)s,%(description)s,%(languages)s,%(expectedTime)s,%(note)s)",
               {"userid": userId, "name": name,  "purpose": purpose, "description": description, "languages": languages, "expectedTime": expectedTime, "note": note})
    projectId = db.execute(
        "SELECT id from projects order by id DESC limit 1")[0][0]
    for functions in functionsAddList:
        db.execute("INSERT INTO proFunctions (project_id,name) VALUES (%(projID)s,%(name)s)",
                   {"projID": projectId, "name": functions.strip().capitalize()})
    return redirect("/lists")


@app.route("/addfunction", methods=["GET", "POST"])
@login_required
def addfunction():
    userId = session["user_id"]
    functionsList = db.execute(
        "SELECT * FROM functions WHERE user_id=%(userid)s", {"userid": userId})

    formattedFunctionList = []
    for function in functionsList:
        formatedFunction = {
            "id": function[0],
            "name": function[2],
            "status": function[3],
        }
        formattedFunctionList.append(formatedFunction)

    if request.method == "GET":
        return render_template("addfunction.html", message="", functions=formattedFunctionList)
    functionName = request.form.get("functionName").capitalize().strip()
    if functionName == "":
        return render_template("addfunction.html", message="New function can not be blank", functions=formattedFunctionList)
    duplicated = db.execute(
        "SELECT * FROM functions WHERE user_id=%(userid)s AND name=%(name)s", {"userid": userId, "name": functionName})
    if duplicated:
        return render_template("addfunction.html", message="You already have this function in your list", functions=formattedFunctionList)
    db.execute("INSERT INTO functions (name,user_id) VALUES (%(name)s,%(userid)s)",
               {"name": functionName, "userid": userId})
    return redirect("/add")


@app.route("/deletefunction", methods=["GET", "POST"])
@login_required
def deletefunction():
    if request.method == "GET":
        return redirect("/addfunction")
    functionId = request.form['functionbtn']
    db.execute("DELETE FROM functions WHERE id=%(functionid)s",
               {"functionid": functionId})
    return redirect("/addfunction")


@app.route("/lists")
@login_required
def lists():
    message = request.args.get("message")
    userId = session["user_id"]
    user = db.execute(
        "SELECT * FROM users WHERE id =%(userid)s", {"userid": userId})
    projectList = db.execute(
        "SELECT * FROM projects WHERE user_id=%(userid)s ORDER BY status DESC", {"userid": userId})

    formattedProjectList = []
    for project in projectList:
        formattedProject = formatProject(project)
        formattedProjectList.append(formattedProject)
    if message:
        return render_template("list.html", message=message, projectList=formattedProjectList)
    return render_template("list.html", message="", projectList=formattedProjectList)


@app.route("/viewPro")
@login_required
def viewPro():
    userId = session["user_id"]
    projectId = request.args.get("projectId")
    project = db.execute(
        "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": projectId, "userID": userId})
    if len(project) != 1:
        return redirect("/lists?message='Project is not exist.'")

    formattedProjects = []
    for singleProject in project:
        formattedProject = formatProject(singleProject)
        formattedProjects.append(formattedProject)

    functionList = db.execute(
        "SELECT * FROM proFunctions WHERE project_id=%(projectID)s", {"projectID": projectId})

    formattedFunctionList = []
    for function in functionList:
        formatedFunction = {
            "id": function[0],
            "name": function[2],
            "status": function[3],
        }
        print(formatedFunction)
        formattedFunctionList.append(formatedFunction)

    return render_template("viewsFunc.html", projects=formattedProjects, functionList=formattedFunctionList)


@app.route("/completeFunc")
@login_required
def completeFunc():
    userId = session["user_id"]
    funcId = request.args.get("funcId", None)
    proId = request.args.get("projectId", None)

    proExist = db.execute(
        "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
    if proExist:
        db.execute(
            "UPDATE proFunctions SET status='Complete' WHERE function_id=%(functionID)s AND project_id=%(projectID)s", {"functionID": funcId, "projectID": proId})
        return redirect(f"/viewPro?projectId={proId}")
    return redirect("/lists?message='Project or function is not exist.'")


@app.route("/deleteProFunc")
@login_required
def deleteProFunc():
    userId = session["user_id"]
    funcId = request.args.get("funcId", None)
    proId = request.args.get("projectId", None)
    proExist = db.execute(
        "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
    if proExist:
        db.execute(
            "DELETE FROM proFunctions WHERE function_id=%(functionID)s AND project_id=%(projectID)s", {"functionID": funcId, "projectID": proId})
        return redirect(f"/viewPro?projectId={proId}")
    return redirect("/lists?message='Project or function is not exist.'")


@app.route("/completePro")
@login_required
def completePro():
    userId = session["user_id"]
    proId = request.args.get("projectId")
    project = db.execute(
        "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
    if len(project) != 1:
        return redirect("/lists?message='Project is not exist.'")
    db.execute(
        "UPDATE projects SET status='Complete' WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
    return redirect(f"/viewPro?projectId={proId}")


@app.route("/deletePro")
@login_required
def deletePro():
    userId = session["user_id"]
    proId = request.args.get("projectId")
    project = db.execute(
        "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
    if len(project) != 1:
        return redirect("/lists?message='Project is not exist.'")
    db.execute("DELETE FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {
               "projID": proId, "userID": userId})
    return redirect("/lists?message='Successfully delete'")


@app.route("/proFunction", methods=["GET", "POST"])
@login_required
def proFunction():
    userId = session["user_id"]
    proId = request.args.get("projectId")
    if request.method == "GET":
        project = db.execute(
            "SELECT * FROM projects WHERE id=%(projID)s AND user_id=%(userID)s", {"projID": proId, "userID": userId})
        if len(project) != 1:
            return redirect("/lists?message='Project is not exist.'")
        functionsList = db.execute(
            "SELECT * FROM proFunctions WHERE project_id=%(projID)s", {"projID": proId})
        formattedFunctionList = []
        for function in functionsList:
            formatedFunction = {
                "id": function[0],
                "name": function[2],
                "status": function[3],
            }
            formattedFunctionList.append(formatedFunction)
        return render_template("proFunction.html", message="", functions=formattedFunctionList, proId=proId)
    functionName = request.form.get("functionName").capitalize().strip()
    if functionName == "":
        return render_template("proFunction.html", message="New function can not be blank", functions=formattedFunctionList)
    duplicated = db.execute(
        "SELECT * FROM proFunctions WHERE project_id=%(projID)s AND name=%(name)s", {"projID": proId, "name": functionName})
    if duplicated:
        return render_template("proFunction.html", message="You already have this function in your list", functions=formattedFunctionList)
    db.execute(
        "INSERT INTO proFunctions (project_id,name) VALUES (%(projectID)s,%(name)s)", {"projectID": proId, "name": functionName})
    return redirect(f"/viewPro?projectId={proId}")


@app.route("/profile")
@login_required
def profile():
    userId = session["user_id"]
    user = db.execute(
        "SELECT * FROM users WHERE id=%(userID)s", {"userID": userId})
    completeFunc = db.execute(
        "SELECT COUNT(*) as complete FROM projects WHERE user_id = %(userID)s AND status='Complete'", {"userID": userId})[0][0]
    print(completeFunc)
    pendingFunc = db.execute(
        "SELECT COUNT(*) as pending FROM projects WHERE user_id = %(userID)sAND status='Pending'", {"userID": userId})[0][0]
    print(pendingFunc)
    return render_template("profile.html", user=user, completeFunc=completeFunc, pendingFunc=pendingFunc)
