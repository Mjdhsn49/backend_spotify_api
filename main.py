from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import datetime
import json

app = FastAPI()

#Credentials
BASE_URI = "https://api.spotify.com/v1"
TOKEN_URI ='https://accounts.spotify.com/api/token'
client_id = 'c6c918d70cff4e9bb8e4dac6f020a074' # Your client id
client_secret = '0521dcf6acce43fa8c05b4be25094cc4' # Your secret
client_creds =f"{client_id}:{client_secret}"

#BASE64 encoding
clients_creds_b64 = base64.b64encode(client_creds.encode())
client_id =  "Basic "+clients_creds_b64.decode()

data = {
    "grant_type":"client_credentials",
    
}
headers ={
    "Authorization":client_id,
    "Content-Type":"application/x-www-form-urlencoded"
}
#Generating Access Token
r= requests.post(TOKEN_URI,data=data,headers=headers)
token = r.json()["access_token"]

#New header for each neq request
new_header = {"Authorization":f"Bearer {token}",
                "Content-Type":"application/json"
             }
#spotify specifics
type="album,artist,playlist,track,show,episode"

origins = [
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.middleware("http")
async def save_history(request: Request,call_next):
    ts = datetime.datetime.now().timestamp()
    uri = request.url.path
    uri = uri + str(request.query_params)
    token = request.headers.get('Authorization')
    print(request.headers)
    token = token[7:]
    json_data =[]
    try:
        with open('history.json') as json_file:
            json_data = json.load(json_file)
            print(json_data)
    except:
        with open('history.json', 'x') as f:
            json.dump([], f)

    found = False
    try:
        for _ in json_data:
            if _["userToken"] == token:
                _["actions"].append({
                    "timestamp":ts,
                    "uri":uri
                })
                found=True
                break
    except:
        pass
    if found==False:
        json_data.append({
            "userToken":token,
            "actions":[
                {
                    "timestamp":ts,
                    "uri":uri
                }
            ]
        })
    with open('history.json', 'w') as outfile:
        json.dump(json_data, outfile)
    response = await call_next(request)
    return response




@app.get("/api/search/")
async def search(q: str):
    r = requests.get(BASE_URI+"/search",params={"q":q,"type":type},headers=new_header)
    r_json = r.json()
    type_list = type.split(",")
    type_list =[x + "s" for x in type_list]
    Count = 0
    Records =[]
    for _ in type_list:
        Count= Count + r_json[_]["total"]
        Records.append({_:r_json[_]["items"]})
    
    return {"Count":Count,"Records":Records}



# 6qqNVTkY8uBg9cP3Jd7DAH  -- billie ellish id
# 5ZsFI1h6hIdQRw2ti0hz81   -- zayn malik id
@app.get("/api/artist/{spotify_artists_id}")
async def artist(spotify_artists_id: str):
    return requests.get(BASE_URI+"/artists/"+spotify_artists_id,headers=new_header).json()


@app.get("/api/system/history")
async def system_history(request: Request):
    token = request.headers.get('Authorization')
    token = token[7:]
    with open('history.json') as json_file:
        json_data = json.load(json_file)
        print(json_data)
    found = False
    try:
        for _ in json_data:
            if _["userToken"] == token:
                return _
    except:
        pass
    
    return {
        "message":"no history found!"
    }

    