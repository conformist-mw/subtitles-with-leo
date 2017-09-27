import re
import sys
import json
import requests
from configparser import ConfigParser
from jinja2 import Environment, FileSystemLoader


def load_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def save_to_file(filename, data):
    with open(filename, 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False))


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


def download_dictionary(session, dict_url):
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
            if len(words) == 0:  # if page is empty the words are saved.
                attempts += 1  # download three more pages for sure.
            dictionary.update(words)
            show_more = data['show_more']
            params['page'] += 1
        else:
            attempts += 1
    return dictionary


def parse_subtitles(text, stop_words):
    words = re.findall(r'\b[a-zA-Z\']{2,}\b', text)
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
            word_data = r.json()['userdict3']
            if len(word_data['lemmas']) > 0:
                lemma = word_data['lemmas'][0]['lemma_value'].lower()
            else:
                lemma = word
            if word != lemma:
                r = s.get(url.format(lemma))
                word_data = r.json()['userdict3']
            is_user = word_data['is_user']
            no_trans = not bool(len(word_data['translations']))
            has_error = bool(r.json()['error_msg'])
            word_in_saved_dict = lemma in saved_dict
            if not any([is_user, no_trans, has_error, word_in_saved_dict]):
                translated.append(translate_word(lemma, word_data))
    return translated


def generate_pages(translated_words):
    env = Environment(loader=FileSystemLoader('./'))
    template = env.get_template('templates/index.html')
    with open('pages/index.html', 'w') as f:
        f.write(template.render(data=translated_words))


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
    saved_dict = load_from_file('dictionary.json')
    dictionary = download_dictionary(s, urls['dict_url'])
    saved_dict.update(dictionary)
    save_to_file('dictionary.json', saved_dict)
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = f.read()
        with open('stopwords.txt') as f:
            stop_words = [w.strip() for w in f.readlines()]
        movie_words = parse_subtitles(data, stop_words)
        new_words = set([w for w in movie_words if w not in saved_dict])
        translated_words = get_translations(urls['translate_url'], new_words)
        generate_pages(translated_words)
        save_to_file('translated_words.json', translated_words)
