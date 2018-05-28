from flask import Flask,render_template,redirect,request,session
import requests
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from urllib.parse import parse_qs
import os,json
app = Flask(__name__)
app.secret_key="lskhfkjashfkasjhflakshdjlkasjdh"
app.jinja_env.filters['zip'] = zip



redirect_uri_sp = 'https://youspot.herokuapp.com/spotify_callback'
scope_sp = 'user-library-read user-read-private user-read-email playlist-read-private playlist-modify-public playlist-modify-private playlist-read-collaborative'
token_url_sp = "https://accounts.spotify.com/api/token"


@app.route('/')
def inicio():
	if token_valido_spotify():
		return redirect('/perfil_usuario_spotify')
	else:
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
		session["id"]=doc["id"]
		return render_template("perfil_spotify.html", datos=doc)
	else:
		return redirect('/perfil_spotify')

@app.route('/logout_spotify')
def salir_spotify():
	session.pop("token_sp",None)
	return redirect("/")



@app.route('/mis_playlist')
def mis_playlist():
	if not "id" in session:
		return redirect('/')

	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
		r = oauth2.get('https://api.spotify.com/v1/users/{}/playlists' .format(session["id"]))
		doc=json.loads(r.content.decode("utf-8"))
		return render_template("misplaylist.html", datos=doc)
	else:
		return redirect('/')


@app.route('/newplaylist')
def newplaylist():
	return render_template("nuevaplaylist.html")


@app.route('/nuevaplaylist', methods=['post', 'get'])
def nuevaplaylist():
	if not "id" in session:
		return redirect('/')
	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token, scope=scope_sp)
		nombre = request.form.get('nombre')
		desc = request.form.get('desc')
		public = request.form.get('public')
		headers = {'Accept': 'application/json', 'Content-Type': 'application-json', 'Authorization': 'Bearer ' + session['token_sp']}
		payload={'name':nombre, 'description':desc, 'public':public}
		r = oauth2.post('https://api.spotify.com/v1/users/{}/playlists' .format(session["id"]), data=json.dumps(payload), headers=headers)
		doc=json.loads(r.content.decode("utf-8"))
		return redirect('/mis_playlist')
		#return render_template("creacionplaylist.html", datos=doc, nombre=nombre, desc=desc, public=public)
	else:
		return redirect('/')


@app.route('/cancionesplaylist/<idc>')
def saludo(idc):
	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
		r = oauth2.get('https://api.spotify.com/v1/users/{}/playlists/{}/tracks' .format(session["id"], idc))
		doc=json.loads(r.content.decode("utf-8"))
		return render_template("cancionesplaylist.html", datos=doc)
	else:
		return redirect('/spotify')




@app.route('/listasyt')
def listasyt():
	return render_template("formularioyt.html")


@app.route('/buscar_listasyt', methods=["post", "get"])
def buscar_listasyt():
	buscar = request.form.get('buscar')
	cantidad = request.form.get('cantidad')
	key=os.environ["key_yt"]
	playlist="playlist"
	part="id,snippet"
	payload={"part":part,"key":key, "q":buscar, "maxResults":cantidad, "type":playlist}
	r=requests.get('https://www.googleapis.com/youtube/v3/search',params=payload)
	if r.status_code==200:
		js=json.loads(r.text)
		lista_ti=[]
		lista_id=[]
		for x in js['items']:
			lista_id.append(x['id']['playlistId'])
			lista_ti.append(x['snippet']['title'])
		if len(lista_id) != 0:
			return render_template('listasyt.html', lista_id=lista_id, lista_ti=lista_ti, buscar=buscar)
		else:
			return render_template('listanoencontrada.html')
	else:
		return render_template('listanoencontrada.html')

@app.route('/videoslista/<videoid>')
def videoslista(videoid):
	key=os.environ["key_yt"]
	part="id,snippet"
	idplaylist=videoid
	payload={"part":part,"key":key, "playlistId":idplaylist, "maxResults":25}
	r=requests.get('https://www.googleapis.com/youtube/v3/playlistItems',params=payload)
	if r.status_code==200:
		js=json.loads(r.text)
		lista_ti=[]
		lista_id=[]
		for x in js['items']:
			lista_id.append(x['snippet']['resourceId']['videoId'])
			lista_ti.append(x['snippet']['title'])
		if len(lista_id) != 0:
			return render_template('cancioneslistasyt.html', lista_id=lista_id, lista_ti=lista_ti)


def quitar_palabras_claves(cad):
	palabras=["ft.", "Ft", "Remix","[Official Video]","(Official Video)", "Video Oficial", "|", "Prod. Afro Bros & Jeon", "01.", "02.", "03.", "04.", "05.", "06.", "07.", "08.", "09.", "10.", "11.","12."]
	claves=cad[cad.find("("):cad.find(")")+1]
	claves2=cad[cad.find("["):cad.find("]")+1]
	palabras.append(claves)
	palabras.append(claves2)
	for palabra in palabras:
		cad=cad.replace(palabra,"")
	return cad

@app.route('/cancionesyt/<title>')
def cancionesyt(title):
	title=quitar_palabras_claves(title)
	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
		headers = {'Accept': 'application/json', 'Content-Type': 'application-json', 'Authorization': 'Bearer ' + session['token_sp']}
		payload={'q':title, 'type':'track,artist', 'market':'ES'}
		r = oauth2.get('https://api.spotify.com/v1/search', params=payload, headers=headers)
		doc=json.loads(r.content.decode("utf-8"))
		return render_template("cancionesyt.html", datos=doc)
	else:
		return redirect('/cancionesyt/<title>')



def tratar_lista_titulos(lista):
	lista_ok=[]
	for tit in lista:
		titu=quitar_palabras_claves(tit)
		lista_ok.append(titu)
	return lista_ok


@app.route('/tratarlista/<lista_tit>')
def tratarlista(lista_tit):
	lista_tit2=lista_tit[1:-1].replace("'","").split(",")
	lista_ok=tratar_lista_titulos(lista_tit2)
	lista_uri=[]
	if token_valido_spotify():
		for ti in lista_ok:
			token=json.loads(session["token_sp"])
			oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
			headers = {'Accept': 'application/json', 'Content-Type': 'application-json', 'Authorization': 'Bearer ' + session['token_sp']}
			payload={'q':ti, 'type':'track,artist', 'market':'ES'}
			r = oauth2.get('https://api.spotify.com/v1/search', params=payload, headers=headers)
			doc=json.loads(r.content.decode("utf-8"))
			if doc["tracks"]["items"][0]["uri"]:
				datos=doc["tracks"]["items"][0]["uri"]
			else:
				"No ha encontrado cancion"
			lista_uri.append(datos)

		return render_template("cancioneslistacompletayt.html", datos=lista_uri)
	else:
		return redirect('/cancionesyt/<title>')




@app.route('/elegirplaylist/<uri>', methods=["post", "get"])
def añadiraplaylist(uri):
	if not "id" in session:
		return redirect('/')

	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
		r = oauth2.get('https://api.spotify.com/v1/users/{}/playlists' .format(session["id"]))
		doc=json.loads(r.content.decode("utf-8"))
		return render_template("elegirplaylist.html", datos=doc, uri=uri)
	else:
		return redirect('/')


@app.route('/añadircancionplaylist/<idc>/<uri>', methods=['post', 'get'])
def añadircancionplaylist(idc, uri):
	if not "id" in session:
		return redirect('/')
	if token_valido_spotify():
		token=json.loads(session["token_sp"])
		oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token, scope=scope_sp)
		headers = {'Accept': 'application/json', 'Content-Type': 'application-json', 'Authorization': 'Bearer ' + session['token_sp']}
		payload={'uris':uri}
		r = oauth2.post('https://api.spotify.com/v1/users/{}/playlists/{}/tracks' .format(session["id"], idc), params=payload, headers=headers)
		doc=json.loads(r.content.decode("utf-8"))
		return render_template("cancionañadida.html", datos=doc)
	else:
		return redirect('/')



if __name__ == '__main__':
	port=os.environ["PORT"]
	app.run('0.0.0.0',int(port), debug=True)