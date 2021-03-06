import csv
from io import StringIO
from configparser import ConfigParser
from main import get_auth_session, get_credentials
from models import db, TranslatedWord, StopWord, TranslatedOption
from flask import Flask, request, render_template, jsonify, make_response

config = ConfigParser()
config.read('config.ini')
urls = dict(config.defaults())

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = urls['db_uri']
db.init_app(app)

per_page = 30

email, password = get_credentials(config)
s = get_auth_session(urls['login_url'], email, password)


@app.route('/', methods=['GET'])
@app.route('/<int:page>', methods=['GET'])
def index(page=1):
    words = TranslatedWord.query.paginate(page, per_page, False)
    return render_template('index.html', words=words)


@app.route('/addWord', methods=['POST'])
def add_word():
    word = db.session.query(TranslatedWord).get(request.form['word_id'])
    translate = db.session.query(TranslatedOption).get(
        request.form['translate_id'])
    payload = {
        'word_id': word.id,
        'speech_part_id': 0,
        'groupId': 'dictionary',
        'translate_id': translate.id,
        'translate_value': translate.value,
        'user_word_value': word.value,
        'from_syntrans_id': '',
        'to_systrans_id': ''
    }
    r = s.post('https://lingualeo.com/ru/userdict3/addWord', data=payload)
    db.session.delete(word)
    db.session.commit()
    return jsonify(r.json()['userdict3']['user_translates'][0])


@app.route('/ignoreWord', methods=['POST'])
def ignore_word():
    word_id = request.form['id']
    word = db.session.query(TranslatedWord).get(word_id)
    stop_word = StopWord(**{'word': word.value})
    db.session.add(stop_word)
    db.session.delete(word)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/saveCSV', methods=['GET'])
def save_csv():
    words = TranslatedWord.query.all()
    si = StringIO()
    cw = csv.writer(si, quoting=csv.QUOTE_ALL)
    for word in words:
        cw.writerow([word.value,
                     sorted(word.translates, key=lambda x: x.votes)[-1].value,
                     word.transcription, word.sound_url])
    out_csv = make_response(si.getvalue())
    out_csv.headers['Content-Disposition'] = 'attachment; filename=export.csv'
    out_csv.headers['Content-type'] = 'text/csv'
    return out_csv


if __name__ == "__main__":
    app.run(host='0.0.0.0')
