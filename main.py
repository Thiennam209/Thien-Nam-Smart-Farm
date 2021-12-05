# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
import sqlite3
import re
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import paho.mqtt.client as mqtt
import json
import io

app = Flask(__name__, static_folder='static', static_url_path='')

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
    1: {'name': 'Watering', 'room': 'Room 1', 'board': 'esp8266', 'topic': 'esp8266/1', 'state': 'False'},
    2: {'name': 'Light', 'room': 'Room 1', 'board': 'esp8266', 'topic': 'esp8266/2', 'state': 'False'},
    3: {'name': 'Watering', 'room': 'Room 2', 'board': 'esp8266', 'topic': 'esp8266/3', 'state': 'False'},
    4: {'name': 'Light', 'room': 'Room 2', 'board': 'esp8266', 'topic': 'esp8266/4', 'state': 'False'},
    5: {'name': 'Watering', 'room': 'Room 3', 'board': 'esp8266', 'topic': 'esp8266/5', 'state': 'False'},
    6: {'name': 'Light', 'room': 'Room 3', 'board': 'esp8266', 'topic': 'esp8266/6', 'state': 'False'},
    7: {'name': 'Watering', 'room': 'Room 4', 'board': 'esp8266', 'topic': 'esp8266/7', 'state': 'False'},
    8: {'name': 'Light', 'room': 'Room 4', 'board': 'esp8266', 'topic': 'esp8266/8', 'state': 'False'},
    9: {'name': 'Watering', 'room': 'Room 5', 'board': 'esp8266', 'topic': 'esp8266/9', 'state': 'False'},
    10: {'name': 'Light', 'room': 'Room 5', 'board': 'esp8266', 'topic': 'esp8266/10', 'state': 'False'},
    11: {'name': 'Watering', 'room': 'Room 6', 'board': 'esp8266', 'topic': 'esp8266/11', 'state': 'False'},
    12: {'name': 'Light', 'room': 'Room 6', 'board': 'esp8266', 'topic': 'esp8266/12', 'state': 'False'},
    13: {'name': 'Watering', 'room': 'Room 7', 'board': 'esp8266', 'topic': 'esp8266/13', 'state': 'False'},
    14: {'name': 'Light', 'room': 'Room 7', 'board': 'esp8266', 'topic': 'esp8266/14', 'state': 'False'},
}

dbname = 'mynewsensorsData.db'


def maxRowsTable():
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    sql = "select COUNT(temp) from  DHT_data"
    for row in curs.execute(sql):
        maxNumberRows = row[0]
    conn.close()
    return maxNumberRows


# define and initialize global variables
global numSamples
numSamples = maxRowsTable()
if (numSamples > 51):
    numSamples = 50

# Retrieve LAST data from database


def getLastData():
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    sql = "SELECT * FROM DHT_data ORDER BY timestamp DESC LIMIT 1"
    for row in curs.execute(sql):
        time = str(row[0])
        temp = row[1]
        hum = row[2]
    conn.close()
    return time, temp, hum


def getHistData(numSamples):
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    sql = "SELECT * FROM DHT_data ORDER BY timestamp DESC LIMIT " + \
        str(numSamples)
    curs.execute(sql)
    data = curs.fetchall()
    dates = []
    temps = []
    hums = []
    for row in reversed(data):
        dates.append(row[0])
        temps.append(row[1])
        hums.append(row[2])
    conn.close()
    return dates, temps, hums


slider1 = 5
slider2 = 10
slider3 = 15
slider4 = 20
time, temp, hum = getLastData()
leng = int(len(pins) / 2 + 1)


@app.route('/')
def index():
    msg = ''
    return render_template('index.html', msg=msg)


@app.route('/smarthome', methods=['GET', 'POST'])
def smarthome():
    global numSamples
    numSamples = int(request.form.get("numSamples", False))
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    time, temp, hum = getLastData()
    templateData = {
        'pins': pins,
        'leng': leng,
        'time': time,
        'temp': temp,
        'hum': hum,
        'numSamples': numSamples,
        'slider_val_1': slider1,
        'slider_val_2': slider2,
        'slider_val_3': slider3,
        'slider_val_4': slider4
    }
    return render_template('smarthome.html', **templateData)


@app.route('/plot/temp')
def plot_temp():
    times, temps, hums = getHistData(numSamples)
    ys = temps
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Temperature [°C]")
    axis.set_xlabel("Samples")
    axis.grid(True)
    xs = range(numSamples)
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response


@app.route('/plot/hum')
def plot_hum():
    times, temps, hums = getHistData(numSamples)
    ys = hums
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Humidity [%]")
    axis.set_xlabel("Samples")
    axis.grid(True)
    xs = range(numSamples)
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response


# The function below is executed when someone requests a URL with the pin number and action in it:
@app.route("/<board>/<changePin>/<action>", methods=['POST'])
def action(board, changePin, action):
    global numSamples
    # Convert the pin from the URL into an integer:
    changePin = int(changePin)
    # Get the device name for the pin being changed:
    devicePin = pins[changePin]['name']
    time, temp, hum = getLastData()

    # If the action part of the URL is "on," execute the code indented below:
    for i in range(1, leng):
        newboard = 'esp8266_'
        newboard += str(i)
        if action == "1" and board == newboard:
            mqttc.publish(pins[changePin]['topic'], "1")
            pins[changePin]['state'] = 'True'

        if action == "0" and board == newboard:
            mqttc.publish(pins[changePin]['topic'], "0")
            pins[changePin]['state'] = 'False'

    templateData = {
        'pins': pins,
        'leng': leng,
        'time': time,
        'temp': temp,
        'hum': hum,
        'numSamples': numSamples,
        'slider_val_1': slider1,
        'slider_val_2': slider2,
        'slider_val_3': slider3,
        'slider_val_4': slider4
    }
    return render_template('smarthome.html', **templateData)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/esp8266/dhtsensor")


# The callback for when a PUBLISH message is received from the ESP8266.

def on_message(client, userdata, message):
    if message.topic == "/esp8266/dhtsensor":
        dhtreadings = json.loads(message.payload)
        # val_temp = int(dhtreadings["temperature"])
        val_temp = int(float(dhtreadings["temperature"]))
        # val_humi = int(dhtreadings["humidity"])
        val_humi = int(float(dhtreadings["humidity"]))
        # print(val_temp)
        # print(val_humi)
        conn = sqlite3.connect(dbname)
        curs = conn.cursor()
        curs.execute(
            "INSERT INTO DHT_data values(datetime('now'), (?), (?))", (val_temp, val_humi))
        conn.commit()
        conn.close()


@ app.route("/test", methods=["POST"])
def test():
    global slider1
    global slider2
    global slider3
    global slider4
    slider1 = request.form["slider1"]
    slider2 = request.form["slider2"]
    slider3 = request.form["slider3"]
    slider4 = request.form["slider4"]
    mqttc.publish("Servo1", str(slider1))
    mqttc.publish("Servo2", str(slider2))
    mqttc.publish("Servo3", str(slider3))
    mqttc.publish("Servo4", str(slider4))
    templateData = {
        'pins': pins,
        'leng': leng,
        'time'	: time,
        'temp'	: temp,
        'hum'	: hum,
        'numSamples': numSamples,
        'slider_val_1': slider1,
        'slider_val_2': slider2,
        'slider_val_3': slider3,
        'slider_val_4': slider4
    }
    return render_template('smarthome.html', **templateData)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        myusername = request.form['username']
        mypassword = request.form['password']
        if myusername == 'admin' and mypassword == '123':
            return render_template('register.html')
        else:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?', (myusername, mypassword))
            account = cursor.fetchone()
            if account:
                msg = 'Logged in successfully !'
                conn.close()
                time, temp, hum = getLastData()
                templateData = {
                    'pins': pins,
                    'leng': leng,
                    'time': time,
                    'temp': temp,
                    'hum': hum,
                    'numSamples': numSamples,
                    'slider_val_1': slider1,
                    'slider_val_2': slider2,
                    'slider_val_3': slider3,
                    'slider_val_4': slider4
                }
                return render_template('smarthome.html', **templateData)
            else:
                conn.close()
                msg = 'Incorrect username / password !'
                return render_template('login.html', msg=msg)
    return render_template('login.html', msg=msg)


@app.route('/register', methods=['POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute(
                "INSERT INTO users (username,password) VALUES (?,?)", (username, password))
            conn.commit()
            conn.close()
            msg = 'You have successfully registered !'

    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


@app.route('/histemphum', methods=['GET', 'POST'])
def histemphum():
    global numSamples
    numSamples = int(request.form.get("numSamples", False))
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    time, temp, hum = getLastData()
    templateData = {
        'temp': temp,
        'hum': hum,
        'numSamples': numSamples,
    }
    return render_template('histemphum.html', **templateData)


@app.route('/logout')
def logout():
    return redirect(url_for('login'))


@app.route('/backsh')
def backsh():
    return redirect(url_for('smarthome'))


@app.route('/histh')
def histh():
    return redirect(url_for('histemphum'))


if __name__ == "__main__":
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect("localhost", 1883, 60)
    mqttc.loop_start()
    app.run(host='0.0.0.0', port=8181, debug=True)
