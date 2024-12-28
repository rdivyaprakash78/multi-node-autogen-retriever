from flask import Flask, render_template,request, jsonify, redirect, url_for, session, Response
import assemblyai as aai
import os
from dotenv import load_dotenv
import sys
load_dotenv()
sys.path.append('../')
from retrieverv2 import get_response

aai.settings.api_key = os.environ.get('ASSEMBLYAI_API_KEY')
transcriber = aai.Transcriber()

app = Flask(__name__, template_folder= "Templates")
app.secret_key = "project-secret-key"

@app.route('/', methods=['GET', 'POST'])
def home():
    """if request.method == 'POST':
        question = request.form["ques"]
        session["question"] = question
        return redirect(url_for("answer"))"""
    return render_template('home.html')

@app.route('/answer', methods=['GET', 'POST'])
def answer():
    if request.method == 'POST':
        question = request.form["question"]
        session["question"] = question
        return jsonify({"redirect": url_for("answer")}) 
    if "question" in session:
        answer = get_response(session["question"])
        if isinstance(answer, str):
            return render_template('error.html', ans = answer)
        return render_template('answer.html', ans=answer)
    
@app.route("/upload", methods=["POST"])
def upload():
    audio_file = request.files['audio']
    transcript = transcriber.transcribe(audio_file)
    return jsonify({"transcript" : transcript.text})
        
if __name__ == '__main__':
    app.run(debug=True)