# app.py

from flask import Flask, render_template, request, jsonify, Request
from flask_wtf import FlaskForm
import requests
import json
from json import dumps
from nanoid import generate
from user import User, serializeUser
from api import createUser, deleteUser, createCommand, deleteCommand, runCommand
from generative import new_user_row, new_command_row, new_registration, command_response

ZENCODE_REST = "http://localhost:3333"
USERS_API = '/users'

users = []

app = Flask(__name__)

@app.route("/index", methods=["GET"])
@app.route("/", methods=["GET"])
def code():
    return render_template("index.html", users=users)

@app.route("/register", methods=["GET"])
def register():
    return new_registration()

@app.route("/submit", methods=["POST"])
def submit():
    e_mail = f'{generate(size=10)}{request.form["email"]}'
    p_word = request.form["password"]
    usr = createUser(e_mail, p_word)
    users.append(serializeUser(usr))
    return new_user_row(e_mail, usr.id)

@app.route("/delete/<string:id>", methods=["DELETE"])
def delete(id: str):
    usr = getUserById(id)
    deleteUser(usr)
    users.remove(usr)
    return ""

@app.route("/command/delete/<string:command_id>", methods=["DELETE"])
def command_delete(command_id: str):
    usr = json.loads(request.form["user"])
    deleteCommand(command_id, usr)
    return ""

@app.route("/command/<string:user_id>", methods=["POST"])
def command(user_id: str):
    usr = getUserById(user_id)
    print(request.form)
    type = request.form["typec"]
    command = request.form["command"]
    command_id = createCommand(usr, command, type)
    return new_command_row(command, type, command_id, usr)

@app.route("/command_type", methods=["POST"])
def command_type():
    type = request.form["typec"]
    return f"""
            <button id="add" hx-post="/command/{id}" hx-target="#user_row" hx-swap="afterend" class="btn btn-primary">
                {type.upper()}
            </button>
    """

@app.route("/execute/<string:command_id>", methods=["POST"])
def execute(command_id: str):
    print(command_id)
    usr = json.loads(request.form["user"])
    result = runCommand(command_id, usr)
    return command_response(json.dumps(result, indent=4, sort_keys=True))


def getUserById(id: str):
    for user in users:
        if user['id'] == id:
            return user
