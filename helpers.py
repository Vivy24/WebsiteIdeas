import os
import requests


from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """

    Decorate routes to require login.



    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("user_id") is None:

            return render_template("login.html", message="Please log in")

        return f(*args, **kwargs)

    return decorated_function


def formatProject(project):
    return {
        "id": project[0],
        "user_id": project[1],
        "name": project[2],
        "purpose": project[3],
        "description": project[4],
        "languages": project[5],
        "time": project[6],
        "note": project[7],
        "status": project[8]
    }


class postgresSQLConnection:
    def __init__(self, connection):
        self.connection = connection
        self.dbcursor = connection.cursor()

    def execute(self, command, query=None):
        try:
            if query is None:
                self.dbcursor.execute(command)
            else:
                self.dbcursor.execute(command, query)
            if "SELECT" in command:
                result = list(self.dbcursor.fetchall())
                return result
            else:
                self.connection.commit()
        except:
            self.dbcursor.execute("rollback")

    def __del__(self):
        self.dbcursor.close()
        self.connection.close()
