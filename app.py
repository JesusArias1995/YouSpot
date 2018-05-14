from flask import Flask, request, abort, url_for, render_template
import requests
import os
app = Flask(__name__)

key=os.environ["key"]

@app.route("/")
def canciones():
		key=os.environ["key"]
		payload={"part": "snippet" ,"key":key, "playlistId":"RDEM8aipvdmzsFDwIJv4gJiAgw"}

		r=requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=payload)
		if r.status_code == 200:
				doc=r.json()

		return doc


app.run(debug=True)