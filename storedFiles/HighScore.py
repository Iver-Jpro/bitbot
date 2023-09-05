import requests
import json

url = "https://jz23.jpro.no/api/v2/player_score"
secret = "SECRET"

def post_score(score, name, email):
    headers = {'Content-Type': 'application/json', 'secret': secret}

    payload = {'score': score, 'player_username': name}
    if(email!= None and email!= ""):
        payload['player_email'] = email
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.status_code
