# app.py

from flask import Flask, render_template, request, jsonify
import requests
from json import dumps
from nanoid import generate
from user import User, serializeUser
from api import createUser, deleteUser, createCommand
from generative import new_user_row, new_command_row

ZENCODE_REST = "http://localhost:3333"
USERS_API = '/users'

users = []

app = Flask(__name__)

@app.route("/", methods=["GET"])
def code():
    return render_template("index.html", users=users)


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

@app.route("/command/<string:user_id>", methods=["POST"])
def command(user_id: str):
    usr = getUserById(user_id)
    print(user_id)

    # type = request.form['command_type']
    command = request.form['command_text']
    
    print(type, command)

    # command_id = createCommand(usr['id'], command, type)
    print(usr)
    return new_user_row(usr['email'], usr['id']) + new_command_row(command, type)


def getUserById(id: str):
    for user in users:
        if user['id'] == id:
            return user
