import re
import sys
import json
import requests
from configparser import ConfigParser


def get_credentials(config):
    if not config['CREDENTIALS'].getboolean('from_config'):
        email = input('Email: ')
        password = input('Password: ')
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


def extract_words(data):
    dictionary = {}
    words = [word for item in data for word in item if word]
    for word in words:
        if word['word_value'] not in saved_dict:
            dictionary[word['word_value'].lower()] = {
                'word_id': word['word_id'],
                'transcription': word['transcription'],
                'translate': [w['translate_value'] for w
                              in word['user_translates']],
                'picture_url': word['picture_url'],
                'sound_url': word['sound_url']
            }
    return dictionary


def save_dictionary(session, dict_url):
    params = {
        'sortBy': 'date',
        'wordType': 1,  # 0 if all (words, phrases, sentences)
        'filter': 'all',
        'page': 1,
        'groupId': 'dictionary'
    }
    dictionary = {}
    show_more = True
    attempts = 0
    while show_more and attempts <= 3:
        r = session.get(dict_url, params=params)
        if r.ok:
            data = r.json()
            words = extract_words([i['words'] for i in data['userdict3']])
            if len(words) == 0:
                attempts += 1
            dictionary.update(words)
            show_more = data['show_more']
            params['page'] += 1
        else:
            attempts += 1
    return dictionary


def parse_subtitles(data):
    with open('english.txt') as f:
        stop_words = [word.strip() for word in f.readlines()]
    words = re.findall(r'\b[a-zA-Z]{2,}\b', data)
    words = set([w.lower() for w in words])
    return [w for w in words if w not in stop_words]


def translate_word(word, data):
    translations = []
    for translate in data['translations']:
        t = {
            'translate_id': translate['translate_id'],
            'translate_value': translate['translate_value'],
            'translate_votes': translate['translate_votes']
        }
        translations.append(t)
    return {
        'word': word,
        'word_id': data['word_id'],
        'transcription': data['transcription'],
        'sound_url': data['sound_url'],
        'translations': translations
    }


def get_translations(url, words):
    translated = []
    for word in words:
        r = s.get(url.format(word))
        if r.ok:
            translate = r.json()['userdict3']
            if len(translate['lemmas']) > 0:
                lemma = translate['lemmas'][0]['lemma_value'].lower()
            else:
                lemma = word
            if word != lemma:
                r = s.get(url.format(lemma))
                translate = r.json()['userdict3']
            is_user = translate['is_user']
            no_trans = not bool(len(translate['translations']))
            has_error = bool(r.json()['error_msg'])
            word_in_saved_dict = lemma in saved_dict
            if not any([is_user, no_trans, has_error, word_in_saved_dict]):
                translated.append(translate_word(lemma, translate))
    return translated


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
    with open('dictionary.json') as f:
        saved_dict = json.load(f)
    dictionary = save_dictionary(s, urls['dict_url'])
    saved_dict.update(dictionary)
    with open('dictionary.json', 'w') as f:
        f.write(json.dumps(saved_dict, ensure_ascii=False))
    with open(sys.argv[1]) as f:
        data = f.read()
    movie_words = parse_subtitles(data)
    new_words = set([w for w in movie_words if w not in saved_dict])
    translated_words = get_translations(urls['translate_url'], new_words)
    with open('translated_words.json', 'w') as f:
        f.write(json.dumps(translated_words, ensure_ascii=False, indent=4))
