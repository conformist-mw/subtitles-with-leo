import json
from configparser import ConfigParser
from flask import Flask, request, render_template
from main import get_auth_session, get_credentials

app = Flask(__name__, template_folder='pages')

config = ConfigParser()
config.read('config.ini')
urls = dict(config.defaults())
email, password = get_credentials(config)
s = get_auth_session(urls['login_url'], email, password)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/addWord', methods=['POST'])
def add_word():
    payload = {
        'word_id': request.form['word_id'],
        'speech_part_id': 0,
        'groupId': 'dictionary',
        'translate_id': request.form['translate_id'],
        'translate_value': request.form['translate_value'],
        'user_word_value': request.form['user_word_value'],
        'from_syntrans_id': '',
        'to_systrans_id': ''
    }
    s.post('https://lingualeo.com/ru/userdict3/addWord', data=payload)
    return json.dumps(
        {'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/ignoreWord', methods=['POST'])
def ignore_word():
    word = request.form['word']
    with open('stopwords.txt', 'a') as f:
        f.write('\n' + word)
    return json.dumps(
        {'success': True}), 200, {'ContentType': 'application/json'}


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
