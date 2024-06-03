import requests
from flask import Flask, render_template, request, redirect, session, jsonify
import concurrent.futures
from flask_sqlalchemy import SQLAlchemy
import datetime
import random
import hashlib
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = f'{random.randint(100000000000,999999999999)}'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    active_till = db.Column(db.String(80), nullable=False)
    price = db.Column(db.String(80), nullable=False)
    page = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Skin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.String,nullable=False)
    name = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    link = db.Column(db.String, nullable=False)
    price = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Skin %r>' % self.name

class Order:
    def __init__(self,name,description,image,skin_name,skin_image):
        self.name=name
        self.description=description
        self.image=image
        self.skin_name=skin_name
        self.skin_image=skin_image

class Skin_:

    def __init__(self,name,image,link):
        self.name=name
        self.image=image
        self.link=link

    def __str__(self):
        return self.name


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/', methods=["GET","POST"])
def login():
    if request.method == "GET":
        try:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                if session['password'] == user.password:
                    session['able']
                    return redirect('/market_scanner')
                else:
                    return render_template('login.html')
            else:
                return render_template('login.html')
        except:
            return render_template('login.html')
    else:
        session['username'] = request.form['username']
        session['password'] = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = User.query.filter_by(username=session['username']).first()
        if user:
            if session['password'] == user.password:
                session['able'] = True
                return redirect('/market_scanner')
            else:
                return redirect('/')
        else:
            return redirect('/')


@app.route('/market_scanner', methods=["GET","POST"])
def finder():
    try:
        if session['able']:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                if user.password == session['password']:
                    if request.method == "GET":
                        return render_template('market_scanner.html')
                    else:
                        session['minPrice'] = request.form['minPrice']
                        session['maxPrice'] = request.form['maxPrice']
                        unfiltered_skins = Skin.query.all()
                        tempskins = []
                        other_tempskins = []
                        last_tempskins = []
                        orders = []

                        for each in unfiltered_skins:
                            if float(each.price) > float(session['minPrice']) and float(each.price) < float(session['maxPrice']):
                                tempskins.append(each)

                        for i in range(60):
                            if user.page == None:
                                user.page = 0
                                db.session.commit()

                            if int(user.page) >= len(tempskins)-1:
                                user.page = 0
                                db.session.commit()

                            other_tempskins.append(tempskins[user.page])
                            user.page = int(user.page) + 1
                            db.session.commit()

                        for i in other_tempskins:
                            skin = Skin_(i.name,i.image,i.link)
                            last_tempskins.append(skin)


                        def send_it(item):
                            r = requests.get(item.link).json()
                            if len(r['activity']) == 0:
                                pass
                            else:
                                r = r['activity'][0]
                                name = r.split('class="market_ticker_name">')[1].split('</span>')[0]
                                description = \
                                r.split('class="market_ticker_name">')[1].split('</span> ')[1].split('</span>')[0]
                                image = r.split('"market_ticker_avatar"><img src="')[1].split('"></span>')[0]
                                if "buy" in description or "purchased" in description:
                                    pass
                                else:
                                    order = Order(name, description, image, item.name, item.image)
                                    orders.append(order)

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            executor.map(send_it, last_tempskins)

                        conn = sqlite3.connect(f'{session["username"]}database.db')
                        cursor = conn.cursor()


                        for order in orders:
                            cursor.execute("INSERT INTO skins (name,image,description,skin_name,skin_image,date) VALUES (?,?,?,?,?,?)", (order.name.lower(),order.image,order.description,order.skin_name,order.skin_image,datetime.datetime.today()))
                            conn.commit()
                        conn.close()
                        return render_template('market_scanner.html',orders=orders)


                else:
                    session['able'] = False
                    return redirect('/')
            else: 
                session['able'] = False
                return redirect('/')
        else:
            return redirect('/')
    except:
        return redirect('/')

@app.route('/add_user_to_base',methods=['POST'])
def add_user():
    correct_secret_key = "ff6640320d972eea79ee0f844f0396df497edb95a0d2f67a80ab7f7bc6969ab7"
    data = request.get_json()
    secret_key = hashlib.sha256(data['secret_key'].encode()).hexdigest()

    if secret_key == correct_secret_key:
        price = data['price']
        username = data['username']
        days = data['days']
        password = hashlib.sha256(data['password'].encode()).hexdigest()
        users = User.query.all()
        code = '3'
        for user in users:
            if user.username == username:
                code = '0'
                break
            else:
                code = '3'
                continue

        if code == '3':
            user = User(username=username,
                        password=password,
                        active_till=datetime.date.today()+datetime.timedelta(days=int(days)),
                        price=price,
                        page=0)

            db.session.add(user)
            db.session.commit()

            conn =sqlite3.connect(f'{username}database.db')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS skins (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, image TEXT,description TEXT, skin_name TEXT, skin_image TEXT,date TEXT)")
            conn.commit()
            conn.close()

            code = '1'

        return code
    else:
        return "2"

@app.route('/remove_user_from_base', methods=['POST'])
def remove_user():
    correct_secret_key = "ff6640320d972eea79ee0f844f0396df497edb95a0d2f67a80ab7f7bc6969ab7"
    data = request.get_json()
    secret_key = hashlib.sha256(data['secret_key'].encode()).hexdigest()

    if secret_key == correct_secret_key:
        user = User.query.filter_by(username=data['username']).first()
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
                code = "1"
            except:
                code = "3"
            return code
        else:
            #User is not found
            code = "0"
            return code
    else:
        # Access Denied
        code = "2"
        return code


@app.route('/check_users',methods=['POST'])
def check_users():
    correct_secret_key = "ff6640320d972eea79ee0f844f0396df497edb95a0d2f67a80ab7f7bc6969ab7"
    data = request.get_json()
    secret_key = hashlib.sha256(data['secret_key'].encode()).hexdigest()

    if secret_key == correct_secret_key:
        users = User.query.all()
        ids = []
        usernames = []
        active_tills = []
        prices = []
        for user in users:
            ids.append(user.id)
            usernames.append(user.username)
            active_tills.append(user.active_till)
            prices.append(user.price)

        response = {
            "ids": ids,
            "usernames": usernames,
            "active_tills": active_tills,
            "prices": prices
        }

        return jsonify(response)

    else:
        response = {
            "access": "denied"
        }
        return jsonify(response)

@app.route('/log_out')
def log_out():
    try:
        session.pop('able',default=None)
        session.pop('username',default=None)
        session.pop('password',default=None)
    except:
        pass

    return redirect('/')

@app.route('/database',methods=['POST','GET'])
def database():
    try:
        if session['able']:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                if user.password == session['password']:
                    if request.method == "GET":
                        conn = sqlite3.connect(f'{session["username"]}database.db')
                        cursor = conn.cursor()
                        skins = cursor.execute("SELECT * FROM skins ORDER BY date DESC").fetchall()
                        conn.close()
                        return render_template('database.html',skins=skins)
                    else:
                        session['name'] = request.form['name']
                        if session['name'] == '':
                            return redirect('/database')
                        conn = sqlite3.connect(f'{session["username"]}database.db')
                        cursor = conn.cursor()
                        skins = cursor.execute("SELECT * FROM skins WHERE name LIKE ? ORDER BY date DESC",(f"%{session['name'].lower()}%",)).fetchall()
                        conn.close()
                        return render_template('database.html',skins=skins)
                else:
                    return redirect('/')
            else:
                return redirect('/')
        else:
            return redirect('/')
    except:
        return redirect('/')


@app.route('/clear_database')
def clear_database():
    try:
        if session['able']:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                if user.password == session['password']:
                    conn = sqlite3.connect(f'{session["username"]}database.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM skins WHERE id>0")
                    conn.commit()
                    conn.close()
                    return redirect('/database')
                else:
                    return redirect('/')
            else:
                return redirect('/')
        else:
            return redirect('/')
    except:
        return redirect('/')




