import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
#import json

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)

latest_restaurant_data = None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        zip_code = request.form.get('zip')
        distance_miles = request.form.get('distance')
        distance_meters = int(distance_miles) * 1609.34
        keyword = request.form.get('keyword')

        global latest_restaurant_data
        latest_restaurant_data = None

        # send preferences to RabbitMQ
        send_preferences(zip_code, distance_meters, keyword)

        return redirect(url_for('results'))
    return render_template('index.html')

@app.route('/results')
def results():
    global latest_restaurant_data
    if latest_restaurant_data:
        return render_template('results.html', restaurant=latest_restaurant_data)
    else:
        return render_template('results.html', restaurant={"error": "No data available yet."})

@app.route('/fetch-data')
def fetch_data():
    global latest_restaurant_data
    if latest_restaurant_data:
        print("fetch data success")
        return jsonify(latest_restaurant_data)
    else:
        print("fetch data failure")
        return jsonify({"error": "No data available yet."})

def send_preferences(zip_code, distance, keyword):
    from worker import send_to_queue
    send_to_queue(zip_code, distance, keyword)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
