from json import dumps
import requests
from user import User

def createUser(email: str, passwd: str):
    headers = {
        "Content-Type": "application/json"
    }
    body = {
            'email': email,
            'password': passwd
    }
    reg_res = requests.post(
        headers=headers,
        url='http://localhost:3333/users',
        data=dumps(body)
    )
    assert reg_res.status_code == 201
    tokens = authenticateUser(email, passwd)
    usr = User(
        email=email, 
        id=reg_res.json()["id"], 
        passwd=passwd,
        accessToken=tokens['access'],
        refreshToken=tokens['refresh']
        )
    return usr

def deleteUser(user: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {user["access_T"]}'
    }
    del_res = requests.delete(
        headers=headers,
        url=f'http://localhost:3333/users/{user["id"]}'
    )
    assert del_res.status_code == 204

def authenticateUser(email: str, passwd: str):
    headers = {
        "Content-Type": "application/json"
    }
    body = {
            'email': email,
            'password': passwd
    }
    auth_res = requests.post(
        headers=headers,
        url=f'http://localhost:3333/auth',
        data=dumps(body)
    )
    assert auth_res.status_code == 201
    return { 
        'access': auth_res.json()["accessToken"], 
        'refresh': auth_res.json()["refreshToken"] 
        }

def createCommand(user: str, command: str, type: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user['access_T']}"
    }
    body = {
            'command': command,
            'userId': user['id'],
            'type': type
    }
    command_res = requests.post(
        headers=headers,
        url=f'http://localhost:3333/commands/commandString',
        data=dumps(body)
    )
    assert command_res.status_code == 201
    return command_res.json()["_id"]

def deleteCommand(command_id: str, user: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {user["access_T"]}'
    }
    body = {
        'commandId': command_id,
        'userId': user['id'],
    }
    del_res = requests.delete(
        headers=headers,
        data=dumps(body),
        url=f'http://localhost:3333/commands/commandId'
    )
    assert del_res.status_code == 200

def runCommand(command_id: str, user: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {user["access_T"]}'
    }
    body = {
        'commandId': command_id,
        'userId': user['id']
    }
    run_res = requests.post(
        headers=headers,
        data=dumps(body),
        url='http://localhost:3333/commands/runCommand'
    )
    assert run_res.ok
    response = run_res.json()
    print(response['result']['data'])
    return response['result']['data']