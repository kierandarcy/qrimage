import os.path
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash,\
                  abort, g, session, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import LoginManager, AnonymousUser, UserMixin, login_user,\
                            login_required, logout_user, current_user
from flask.ext.wtf import Form, SelectMultipleField, Required, URL, TextField
from flask.ext.wtf.html5 import URLField

import qrcode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_very_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///%s' % os.path.join(app.root_path, 'qrimage.db')

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))

# Models
qrcodes = db.Table('qrcodes',
    db.Column('qrcode_id', db.Integer, db.ForeignKey('qrcode.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, unique=True)
    name = db.Column(db.Unicode)
    qrcodes = db.relationship('Qrcode', secondary=qrcodes,
                              backref=db.backref('users', lazy='dynamic'))

    def __init__(self, username, name):
        self.username = username
        self.name = name

    def get_id(self):
        return unicode(self.id)
        
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

# Forms
class CoffeeForm(Form):
    options = SelectMultipleField(u'How do you like your coffee?', 
                         choices=[
                            ('milk','Milk'),
                            ('sugar','Sugar'),
                            ('whiskey','Whiskey')
                            ])

class LoginForm(Form):
    username = TextField(u'Enter your user name', validators=[Required(),],
                         description=u'Enter your user name to log in')

class QrcodeForm(Form):
    url = URLField(u'Enter a URL', validators=[Required(), URL()],
                   description=u'Enter a well-formed URL to create a QR code \
                                 image with this link')

def process_qrcode(content):
    g.last_image = None
    session.pop('last_image_id', None)

    # Find an existing image, or create a new one
    qr = Qrcode.query.filter_by(content=content).first()
    if not qr:
        qr = Qrcode(content)
        db.session.add(qr)

    if current_user.is_authenticated():
        qr.users.append(current_user)

    db.session.commit()
    g.last_image = qr
    session['last_image_id'] = qr.id

@app.before_request
def before_request():
    g.last_image = Qrcode.query.get(session.get('last_image_id', 0))
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/brew-coffee/', methods=['GET','POST'])
def coffee():
    form = CoffeeForm()
    if request.method == 'POST':
        abort(418)
    return render_template('coffee.html', form=form)

@app.route('/create-qrcode/', methods=['GET','POST'])
def create():
    form = QrcodeForm()
    if form.validate_on_submit():
        process_qrcode(form.url.data)
        return render_template('create.html', form=form, show_last_image=True)
    return render_template('create.html', form=form)

@app.route('/most-recent/qrcode.png')
@app.route('/most-recent/qrcode.png<download>')
def last_image(download=False):
    if g.last_image:
        return send_from_directory(app.instance_path, g.last_image.filename, 
                                   cache_timeout=0,
                                   mimetype='image/png',
                                   attachment_filename='qrcode.png',
                                   as_attachment=download == '+' or False)
    abort(403)

@app.route('/my-qrcodes/')
@login_required
def user_qrcodes():
    return render_template('user_qrcodes.html')

@app.route('/my-qrcodes/qrcode-<int:id>.png')
@app.route('/my-qrcodes/qrcode-<int:id>.png<download>')
@login_required
def user_qrcode(id, download=False):
    qr = Qrcode.query.get(id)
    if qr in current_user.qrcodes:
        return send_from_directory(app.instance_path, qr.filename, 
                                   mimetype='image/png',
                                   attachment_filename='qrcode.png',
                                   as_attachment=download == '+' or False)
    abort(404)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            login_user(user)
            flash('You were logged in!', 'info')
            return redirect(request.args.get('next') or url_for('home'))
        flash('You could not be logged in.','error')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You were logged out.', 'info')
    return redirect(request.args.get('next') or url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
