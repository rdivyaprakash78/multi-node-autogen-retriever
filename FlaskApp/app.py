from flask import Flask, render_template,request, redirect, url_for, session

app = Flask(__name__, template_folder= "Templates")
app.secret_key = "project-secret-key"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        question = request.form["ques"]
        session["question"] = question
        return redirect(url_for("answer"))
    return render_template('home.html')

@app.route('/answer', methods=['GET', 'POST'])
def answer():
    prev_length = len(session["question"])
    if request.method == 'POST':
        question = request.form["ques"]
        session["question"] = question
        return redirect(url_for("answer"))
    if "question" in session:
        ques = session["question"]
        return render_template('answer.html', ques=ques, prev_length=prev_length)
        
if __name__ == '__main__':
    app.run(debug=True)