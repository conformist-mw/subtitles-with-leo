import re
import sys
import requests
from models import *
from getpass import getpass
from datetime import datetime
from sqlalchemy import create_engine
from configparser import ConfigParser
from sqlalchemy.orm import sessionmaker


def get_sql_session(db_uri):
    engine = create_engine(db_uri)
    Session = sessionmaker(engine)
    return Session()


def get_credentials(config):
    if not config['CREDENTIALS'].getboolean('from_config'):
        email = input('Email: ')
        password = getpass()
    else:
        email = config['CREDENTIALS']['email']
        password = config['CREDENTIALS']['password']
    return (email, password)


def save_credentials(config, email, password):
    config['CREDENTIALS']['email'] = email
    config['CREDENTIALS']['password'] = password
    config['CREDENTIALS']['from_config'] = 'yes'
    with open('config.ini', 'w') as config_file:
        config.write(config_file)


def get_auth_session(login_url, email, password):
    session = requests.Session()
    payload = {'email': email, 'password': password}
    r = session.post(login_url, data=payload)
    if 'dashboard' in r.url:
        return session


def add_dict_word(word):
    db_word = Word(**{
        'id': word['word_id'],
        'value': word['word_value'],
        'transcription': word['transcription'],
        'created': datetime.fromtimestamp(word['created_at']),
        'last_update': datetime.fromtimestamp(word['last_updated_at']),
        'picture_url': word['picture_url'],
        'sound_url': word['sound_url']
    })
    translates = []
    for translate in word['user_translates']:
        translates.append(Translate(**{
            'id': translate['translate_id'],
            'value': translate['translate_value'],
            'votes': translate['translate_votes']
        }))
    db_word.translates = translates
    session.add(db_word)


def extract_words(data):
    words = [word for item in data for word in item if word]
    word_count = 0
    for word in words:
        db_word = session.query(Word).filter(
            Word.value == word['word_value']).first()
        if not db_word:
            word_count += 1
            add_dict_word(word)
    return word_count


def download_dictionary(session, dict_url):
    params = {
        'sortBy': 'date',
        'wordType': 1,  # 0 if all (words, phrases, sentences)
        'filter': 'all',
        'page': 1,
        'groupId': 'dictionary'
    }
    show_more = True
    attempts = 0
    while show_more and attempts <= 3:
        r = session.get(dict_url, params=params)
        if r.ok:
            data = r.json()
            word_count = extract_words([i['words'] for i in data['userdict3']])
            if word_count == 0:  # if count is 0 the words are saved.
                attempts += 1  # download three more pages for sure.
            show_more = data['show_more']
            params['page'] += 1
        else:
            attempts += 1


def parse_subtitles(text):
    words = re.findall(r'\b[a-zA-Z\']{2,}\b', text)
    words = set([w.lower() for w in words])
    return list(words)


def add_translated_word(word, data):
    db_word = session.query(TranslatedWord).filter(
        TranslatedWord.value == word).first()
    if not db_word:
        translates = []
        for translate in data['translations']:
            translates.append(TranslatedOption(**{
                'id': translate['translate_id'],
                'value': translate['translate_value'],
                'votes': translate['translate_votes']
            }))
        word = TranslatedWord(**{
            'id': data['word_id'],
            'value': word,
            'transcription': data['transcription'],
            'sound_url': data['sound_url'],
        })
        word.translates = translates
        session.add(word)


def get_translations(url, words):
    for word in words:
        r = s.get(url.format(word))
        if not r.json()['error_msg']:
            word_data = r.json()['userdict3']
            if len(word_data['lemmas']) > 0:
                lemma = word_data['lemmas'][0]['lemma_value'].lower()
            else:
                lemma = word
            if word != lemma:
                r = s.get(url.format(lemma))
                word_data = r.json()['userdict3']
            db_word = session.query(Word).filter(
                Word.value == lemma).first()
            stop_word = session.query(StopWord).get(lemma)
            word_in_dict = bool(db_word)
            word_in_stop_words = bool(stop_word)
            no_trans = not bool(len(word_data['translations']))
            is_user = word_data['is_user']
            if not any([is_user, no_trans,
                        word_in_dict, word_in_stop_words]):
                add_translated_word(lemma, word_data)


if __name__ == '__main__':
    config = ConfigParser()
    config.read('config.ini')
    urls = dict(config.defaults())
    email, password = get_credentials(config)
    s = get_auth_session(urls['login_url'], email, password)
    if not s:
        sys.exit('Credentials are not right, exiting')
    if not config['CREDENTIALS'].getboolean('from_config'):
        save_credentials(config, email, password)
    session = get_sql_session(urls['db_uri'])
    dictionary = download_dictionary(s, urls['dict_url'])
    session.commit()
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = f.read()
        dict_words = [w.value for w in session.query(Word).all()]
        movie_words = parse_subtitles(data)
        new_words = set([w for w in movie_words if w not in dict_words])
        get_translations(urls['translate_url'], new_words)
        session.commit()
