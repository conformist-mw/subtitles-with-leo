# Subtitles with Lingualeo.com

This project allows you to download whole dictionary from [lingualeo.com](https://lingualeo.com) and save the new words from choosen text file.

**TL;DR**

Result of script:
![script result](https://raw.githubusercontent.com/conformist-mw/subtitles-with-leo/master/example.png)

### Installation

It's pretty simple:
- download or clone this repo
- cd in downloaded dir
- optional: activate virtualenv ([docs](https://docs.python.org/3/library/venv.html))
- run `pip3 install -r requirements.txt`

### How to use?
At this moment you are ready to run `main.py` (database in repo is empty, if you want to recreate it — just remove and run `python3 models.py`):
```bash
python3 main.py
```
and as it is the first run, script will ask you a login data (email, password). If you input it correctly script saved it in `config.ini` in `CREDENTIALS` section and never asked it again.
If you do not specify the text file then script just save your whole dictionary from site to `dictionary.db` otherwise script parsed out the file and save new words in `translated_words` table of db.

### I specified text file, how to add new words?

Very simple. Now you run `python3 server.py` and open [127.0.0.1:5000](http://127.0.0.1:5000) in browser. Here you can choose the preffered translate for every word or ignore it. Ignored words writes to `stopword` table and never show up in  `translated_words` again.

### How to extract subtitles from movie?

Using `ffmpeg`. For example, we have movie `example.mkv`, in order to know which stream (streams are video, audio, subtitle) you need you have to run:
```bash
~ $ ffmpeg -i exmaple.mkv
.....
Metadata:
title           : Dub, AC3 5.1 ~384 kbps
Stream #0:2(eng): Audio: ac3, 48000 Hz, 5.1(side), fltp, 384 kb/s
Metadata:
  title           : Original, AC3 5.1 ~384 kbps
Stream #0:3(rus): Subtitle: subrip (default)
Metadata:
  title           : forced
Stream #0:4(rus): Subtitle: subrip
Stream #0:5(eng): Subtitle: subrip
```
Here we see `Stream #0:5(eng)` — that's what we need. Now we map ffmpeg to this stream:
```bash
~ $ ffmpeg -i example.mkv -map 0:5 -c copy out.srt
```
and this file you can pass as first argument to script to add words from it.

### Can I help you with this project?

Yes. Issues and pull requests are welcome.