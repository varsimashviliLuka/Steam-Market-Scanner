import requests
from flask import Flask, render_template, request, session, redirect, send_file
import random

LINK = "https://marketscanner.pythonanywhere.com/"

codes = {
    "register": {
    "0": "Username is already taken",
    "1": "Account created successfully",
    "2": "Access denied",
    "3": "There was an error creating your account",
    "4": "Impossible to communicate with the server"
    },
    "deactivate": {
        "0": "Username is not found",
        "1": "Account deactivated successfully",
        "2": "Access denied",
        "3": "There was an error creating your account",
        "4": "Impossible to communicate with the server"
    }
}

class User:
    def __init__(self, username, password=None,price=None,days=None):
        self.username = username
        self.password = password
        self.price = price
        self.days = days

    def __str__(self):
        return f"Username: {self.username}\nPassword: {self.password}\nPrice: {self.price}₾"

    def add_user_to_base(self,secret_key):
        data = {
            "username": self.username,
            "password": self.password,
            "price": self.price,
            "secret_key": secret_key,
            "days": self.days
        }
        try:
            r =requests.post(f"{LINK}add_user_to_base", json=data)
        except:
            code = "4"
            return code
        if r.status_code == 200:
            code = r.content.decode('utf-8')
            return code

    def remove_user_from_base(self,secret_key):
        data = {
            "username": self.username,
            "secret_key": secret_key
        }

        try:
            r =requests.post(f"{LINK}remove_user_from_base", json=data)
        except:
            code = "4"
            return code
        if r.status_code == 200:
            code = r.content.decode('utf-8')
            return code


app = Flask(__name__)
app.config['SECRET_KEY'] = f'{random.randint(1000000000,9999999999)}'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
        return render_template('register_user.html')
    else:
        username = request.form['username']
        password = request.form['password']
        price = request.form['price']
        secret_key = request.form['secret_key']
        days = request.form['days']
        new_user = User(username, password, price, days)
        code = new_user.add_user_to_base(secret_key)
        session['status'] = codes["register"][code]
        return redirect('/register_user')


@app.route('/deactivate_user', methods=['GET', 'POST'])
def deactivate_user():
    if request.method == 'GET':
        return render_template('deactivate_user.html')
    else:
        username = request.form['username']
        secret_key = request.form['secret_key']
        new_user = User(username=username)
        code = new_user.remove_user_from_base(secret_key)
        session['status'] = codes["deactivate"][code]
        return redirect('/deactivate_user')


@app.route('/check_users', methods=['POST', 'GET'])
def check_users():
    if request.method == 'GET':
        return render_template('check_users.html')
    else:
        with open('/home/varsimashvililuka/mysite/users.txt', 'w') as f:
            f.write('')
        secret_key = request.form['secret_key']

        data = {
            "secret_key": secret_key
        }
        try:
            r = requests.post(f"{LINK}check_users", json=data).json()
            ids = r['ids']
            usernames = r['usernames']
            active_tills = r['active_tills']
            prices = r['prices']
            with open('/home/varsimashvililuka/mysite/users.txt','a') as f:
                for i in range(len(ids)):
                    f.write(f'''\
{ids[i]}  |  {usernames[i]}  |  {active_tills[i]}  |  {prices[i]}₾
''')
            session['status'] = "Users has been downloaded"
            return redirect('/download_users')
            return redirect('/check_users')
        except:
            session['status'] = "Impossible to communicate with the server"
            return redirect('/check_users')


@app.route('/download_users')
def download_users():
    PATH = 'users.txt'
    return send_file(PATH,as_attachment=True)



