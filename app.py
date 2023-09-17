# app.py

from flask import Flask, render_template, request, jsonify
import requests
from json import dumps
from nanoid import generate
from user import User, serializeUser
from api import createUser, deleteUser

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
    response = f"""
    <tr>
        <td>{e_mail}</td>
        <td>{usr.id}</td>
        <td>
            <button hx-delete="/delete/{usr.id}"
                class="btn btn-primary">
                Delete
            </button>
        </td>
    </tr>
    """
    return response

@app.route("/delete/<string:id>", methods=["DELETE"])
def delete(id: str):
    for user in users:
        if user['id'] == id:
            deleteUser(user)
            users.remove(user)
    return ""
