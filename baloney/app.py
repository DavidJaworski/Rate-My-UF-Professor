from flask import Flask, render_template, request
from WebScraper import scraper, geneds

app = Flask(__name__)


@app.route('/')
def webpage():
    return render_template('webpage.html')


@app.route('/result', methods=['POST'])
def result():
    return render_template('result.html', output=scraper(request.form['userinput']))


@app.route('/result2', methods=['POST'])
def result2():
    return render_template('result2.html', output=geneds(request.form['userinput']))


if __name__ == '__main__':
    app.run(debug=True)
