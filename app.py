from flask import Flask, render_template

app = Flask(__name__)

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
