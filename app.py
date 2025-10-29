from flask import Flask, jsonify
import nflmod

app = Flask(__name__)

@app.route("/lines")
def lines():
    return nflmod.get_lines().to_json()

@app.route("/picks")
def picks():
    return nflmod.get_picks().to_json()

@app.route("/scores")
def scores():
    return nflmod.get_scores().to_json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
