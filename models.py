from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(100))
    transcription = db.Column(db.String(120))
    created = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime)
    picture_url = db.Column(db.String(80))
    sound_url = db.Column(db.String(80))
    translates = db.relationship('Translate', backref='word')

    def __str__(self):
        return self.value


class Translate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(120))
    votes = db.Column(db.Integer)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))

    def __str__(self):
        return self.value


class StopWord(db.Model):
    word = db.Column(db.String(80), primary_key=True)

    def __str__(self):
        return self.value


class TranslatedWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(100))
    transcription = db.Column(db.String(120))
    sound_url = db.Column(db.String(80))
    translates = db.relationship('TranslatedOption', backref='translated_word')

    def __str__(self):
        return self.value


class TranslatedOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(120))
    votes = db.Column(db.Integer)
    translated_word_id = db.Column(db.Integer, db.ForeignKey('translated_word.id'))

    def __str__(self):
        return self.value


if __name__ == '__main__':
    db.create_all()
