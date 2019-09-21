from flask import Flask, render_template, request
from baloney.WebScraper import search

app = Flask(__name__)


@app.route('/')
def webpage():
    return render_template('webpage.html')


@app.route('/result', methods=['POST'])
def result():
    return render_template('result.html', buckets=search(request.form['userinput']))


if __name__ == '__main__':
    app.run(debug=True)
