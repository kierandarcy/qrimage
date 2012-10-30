import os.path
import uuid

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy

import qrcode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///%s' % os.path.join(app.root_path, 'qrimage.db')

db = SQLAlchemy(app)

# Models
qrcodes = db.Table('qrcodes',
    db.Column('qrcode_id', db.Integer, db.ForeignKey('qrcode.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, unique=True)
    name = db.Column(db.Unicode)
    qrcodes = db.relationship('Qrcode', secondary=qrcodes,
                              backref=db.backref('users', lazy='dynamic'))

    def __init__(self, username, name):
        self.username = username
        self.name = name

class Qrcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Unicode, unique=True)
    filename = db.Column(db.Unicode, unique=True)
    #users = an implied column

    def __init__(self, content):
        self.content = content
        self.filename = u'%s.png' % uuid.uuid4()
        self.save_image_file()

    def save_image_file(self):
        filename = os.path.join(app.instance_path, self.filename)
        if not os.path.exists(filename):
            qr = qrcode.make(self.content)
            qr.save(filename)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/brew-coffee/')
def coffee():
    return render_template('coffee.html')

@app.route('/create-qrcode/')
def create():
    return render_template('create.html')

@app.route('/my-qrcodes/')
def user_qrcodes():
    return render_template('user_qrcodes.html')


if __name__ == '__main__':
    app.run(debug=True)
