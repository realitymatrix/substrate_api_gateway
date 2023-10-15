from json import dumps
import requests
from user import User

API_PROTOCOL = 'http'
API_HOST = 'localhost'
API_PORT = '3333'
API_URL = f'{API_PROTOCOL}://{API_HOST}:{API_PORT}'

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
        url=f'{API_URL}/users',
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
        url=f'{API_URL}/users/{user["id"]}'
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
        url=f'{API_URL}/auth',
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
        url=f'{API_URL}/commands/commandString',
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
        url=f'{API_URL}/commands/commandId'
    )
    assert del_res.status_code == 200

def runCommand(command_id: str, user: str, data: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {user["access_T"]}'
    }
    if data:
        body = {
            'commandId': command_id,
            'userId': user['id'],
            'data': data
        }
    else:
        body = {
            'commandId': command_id,
            'userId': user['id']
        }
    run_res = requests.post(
        headers=headers,
        data=dumps(body),
        url=f'{API_URL}/commands/runCommand'
    )
    if not run_res.ok:
        return f'status: {run_res.status_code} ' + f'There was an internal error. {run_res.text}'
    
    response = run_res.json()
    # print(response['result']['data'])
    return response['result']['data']
