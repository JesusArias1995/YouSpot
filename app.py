from flask import Flask,render_template,redirect,request,session
import requests
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from urllib.parse import parse_qs
import os,json
app = Flask(__name__)



redirect_uri_sp = 'https://oauth-jd.herokuapp.com/spotify_callback'
scope_sp = 'user-read-private user-read-email'
token_url_sp = "https://accounts.spotify.com/api/token"


@app.route('/')
def inicio():
    return render_template("inicio.html")


def token_valido_spotify():
    try:
        token=json.loads(session["token_sp"])
    except:
        token = False
    if token:
        token_ok = True
        try:
            oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
            r = oauth2.get('https://api.spotify.com/v1/me')
        except TokenExpiredError as e:
            token_ok = False
    else:
        token_ok = False
    return token_ok


@app.route('/spotify')
def spotify():
    return render_template("oauth2_spotify.html")

@app.route('/perfil_spotify')
def info_perfil_spotify():
  if token_valido_spotify():
    return redirect("/perfil_usuario_spotify")
  else:
    oauth2 = OAuth2Session(os.environ["client_id_spotify"], redirect_uri=redirect_uri_sp,scope=scope_sp)
    authorization_url, state = oauth2.authorization_url('https://accounts.spotify.com/authorize')
    session.pop("token_sp",None)
    session["oauth_state_sp"]=state
    return redirect(authorization_url)  

@app.route('/spotify_callback')
def get_token_spotify():
    oauth2 = OAuth2Session(os.environ["client_id_spotify"], state=session["oauth_state_sp"],redirect_uri=redirect_uri_sp)
    print (request.url)
    token = oauth2.fetch_token(token_url_sp, client_secret=os.environ["client_secret_spotify"],authorization_response=request.url[:4]+"s"+request.url[4:])
    session["token_sp"]=json.dumps(token)
    return redirect("/perfil_usuario_spotify")

@app.route('/perfil_usuario_spotify')
def info_perfil_usuario_spotify():
    if token_valido_spotify():
        token=json.loads(session["token_sp"])
        oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
        r = oauth2.get('https://api.spotify.com/v1/me')
        doc=json.loads(r.content.decode("utf-8"))
        return render_template("perfil_spotify.html", datos=doc)
    else:
        return redirect('/perfil')

@app.route('/logout_spotify')
def salir_spotify():
    session.pop("token_sp",None)
    return redirect("/spotify")

if __name__ == '__main__':
    port=os.environ["PORT"]
    app.run('0.0.0.0',int(port), debug=True)