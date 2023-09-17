from json import dumps
import requests
from user import User, serializeUser

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