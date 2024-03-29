# app.py

from flask import Flask, render_template, request, jsonify, Request, current_app
from flask_wtf import FlaskForm
import requests
import json
from bs4 import BeautifulSoup
from json import dumps
from nanoid import generate
from user import User, serializeUser
from api import createUser, deleteUser, createCommand, deleteCommand, runCommand
from generative import (new_user_row, new_command_row, new_registration, command_response, 
                        open_websocket_connection, new_websocket_connection, write_response)
from kernel_service import createKernel, createWebsocket

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
    return new_user_row(usr)

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
    type = request.form["typec"]
    command = request.form["command"]
    data = request.form["command_data"]
    command_id = createCommand(usr, command, type)
    return new_command_row(command, type, command_id, usr, data)

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
    print(request.form)
    usr = json.loads(request.form["user"])
    data = None
    # print(data)
    if not data:
        data = None
    result = runCommand(command_id, usr, data)
    if not isinstance(result, dict) and result[0:15] == '<!DOCTYPE HTML>':
        result = BeautifulSoup(result, "html.parser").find(class_='error').findChild('h1').text
    return command_response(json.dumps(result, indent=4, sort_keys=True))

@app.route("/kernel", methods=["POST"])
def kernel():
    usr = json.loads(request.form["user"])
    kernel_id = createKernel(usr)
    return open_websocket_connection(kernel_id, usr)

@app.route("/websocket/open/<string:kernel_id>", methods=["POST"])
def websocket_open(kernel_id: str):
    usr = json.loads(request.form["user"])
    print(f'Connection with kernel {kernel_id} initiated by user {usr["id"]}')
    global client
    client = createWebsocket(kernel_id)
    return new_websocket_connection(kernel_id, usr)

@app.route("/websocket/run/<string:kernel_id>", methods=["POST"])
def websocket_run(kernel_id: str):
    code = request.form["ws_text"]
    print(f'Sending message: {code}')
    res = client.execute(code)
    if not res[1]:
        print(f'Received response: {res[0].strip()}')
        return write_response(res[0].strip())
    else:
        return write_response('Code Error')

@app.route("/websocket/close/<string:kernel_id>", methods=["DELETE"])
def websocket_close(kernel_id: str):
    global client
    client.shutdown()
    del client
    usr = json.loads(request.form["user"])
    kernel_id = createKernel(usr)
    return open_websocket_connection(kernel_id, usr)

@app.route("/clear", methods=["DELETE"])
def clear():
    return ''

def getUserById(id: str):
    for user in users:
        if user['id'] == id:
            return user
