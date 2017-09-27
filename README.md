# Subtitles with Lingualeo.com

This project allows you to download whole dictionary from [lingualeo.com](https://lingualeo.com) and save the new words from choosen text file.

TL;DR

Result of script work can be found [here](https://conformist-mw.github.io/subtitles-with-leo/pages/)

### Installation

It's pretty simple:
- download or clone this repo
- cd in downloaded dir
- optional: activate virtualenv ([docs](https://docs.python.org/3/library/venv.html))
- run `pip3 install -r requirements.txt`

### How to use?
At this moment you are ready to run `main.py`
```bash
python3 main.py
```
and as it is the first run, script question you a login data (email, password). If you input it correctly script saved it in `config.ini` in `CREDENTIALS` section and never asked it again.
If you do not specify the text file then script just save your whole dictionary from site to `dictionary.json` otherwise script parsed out the file and save new words in `translated_words.json` and creates `pages/index.html` with them.

### I specified text file, how to add new words?

Very simple. Now you run `python3 server.py` and open [127.0.0.1:5000](http://127.0.0.1:5000) in browser. Here you can choose the preffered translate for every word or ignore it. Ignored words writes to `stopwords.txt` and never show up in  `translated_words.json` again.

### Can I help you with this project?

Yes. Issues are welcome.