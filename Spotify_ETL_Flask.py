import requests
import urllib.parse
import datetime 
from flask import Flask,redirect,jsonify,session,request
import datetime
from json import loads
import pymssql



app=Flask(__name__)
app.secret_key= '123456789'

CLIENT_ID='Your client_id'
CLIENT_SECRET='your client_secret'
REDIRECT_URI='http://localhost:5000/callback'

AUTH_URL='https://accounts.spotify.com/authorize'
TOKEN_URL='https://accounts.spotify.com/api/token'
API_BASE_URL='https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "Welcome to Spotify App <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope='user-read-private user-read-email user-top-read'
    params={
        'client_id':CLIENT_ID,
        'response_type':'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
    }

    auth_url=f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body={
            'code':request.args['code'],
            'grant_type':'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response=requests.post(TOKEN_URL,data=req_body)
        token_info=response.json()
        print("token info",token_info)

        session['access_token']=token_info['access_token']
        session['refresh_token']=token_info['refresh_token']
        session['expires_at']= datetime.datetime.now(datetime.timezone.utc).timestamp() + token_info['expires_in']

        return redirect('/playlists')
    
@app.route('/playlists')

def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    if datetime.datetime.now(datetime.timezone.utc).timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers ={
        'Authorization': f"Bearer {session['access_token']}"
    }

    response=requests.get(API_BASE_URL+ 'me/playlists',headers=headers)
    playlists=response.json()
    return jsonify(playlists)

@app.route('/top/artists')

def get_artists():
    if 'access_token' not in session:
        return redirect('/login')
    if datetime.datetime.now(datetime.timezone.utc).timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers ={
        'Authorization': f"Bearer {session['access_token']}"
    }

    response=requests.get(API_BASE_URL+ 'me/top/artists',headers=headers)
    artists=response.json()
    conn = pymssql.connect(
        server='Server',         
        user='username',         
        password='password',     
        database='Demo'               
    )
    cursor = conn.cursor()
    cursor.execute("""
    IF OBJECT_ID('top_artist','U') is not null  
            DROP TABLE top_artist   
    CREATE TABLE top_artist(
        name VARCHAR(50),
        genres VARCHAR(500),
        popularity VARCHAR(50),
        followers VARCHAR(50)
    )
    """)
    cursor.connection.commit()
    conn.commit()

    for v in artists['items']: 
        
        genres = ','.join(v['genres'])
        name = v['name']
        popularity = v['popularity'] 
        followers =v['followers']['total']
        query = "INSERT INTO top_artist(name, genres, popularity, followers) VALUES (%(name)s, %(genres)s, %(popularity)s, %(followers)s)"
        params = {'name': name, 'genres': genres, 'popularity': popularity, 'followers': followers}
        cursor.execute(query, params)


        
       
    conn.commit()
    cursor.close()
    conn.close()

    return "Data is succesfully returned"

if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)

