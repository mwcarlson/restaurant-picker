import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika, json, threading

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')

# Replace postgres:// with postgresql:// if necessary
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)

latest_restaurant_data = None

def rabbitmq_consumer():
    RABBITMQ_HOST = os.getenv('CLOUDAMQP_URL')
    params = pika.URLParameters(RABBITMQ_HOST)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='frontend_queue', durable=True)

    def on_message_received(ch, method, properties, body):
        global latest_restaurant_data
        try:
            # Decode the restaurant data
            latest_restaurant_data = json.loads(body)
            print("Updated restaurant data received")
        except json.JSONDecodeError as e:
            print("Failed to decode message: ", e)
        finally:
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='frontend_queue', on_message_callback=on_message_received, auto_ack=False)
    app.logger.info("Starting RabbitMQ consumer")
    channel.start_consuming()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        zip_code = request.form.get('zip')
        distance_miles = request.form.get('distance')
        # Convert miles to meters (1 mile is approximately 1609 meters)
        distance_meters = int(distance_miles) * 1609.34

        keyword = request.form.get('keyword')
        #excluded_cuisines = request.form.getlist('exclude_cuisine')
        #print("Excluded Cuisines:", excluded_cuisines)
        #print("Distance in Meters:", distance_meters)

        global latest_restaurant_data
        latest_restaurant_data = None

        send_preferences(zip_code, distance_meters, keyword)

        return redirect(url_for('results'))
    return render_template('index.html')

@app.route('/results')
def results():
    global latest_restaurant_data
    # This route will be refreshed by AJAX to display results
    if latest_restaurant_data:
        return render_template('results.html', restaurant=latest_restaurant_data)
    else:
        return render_template('results.html', restaurant={"error": "No data available yet."})
    #return render_template('results.html')

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
    # Setup RabbitMQ Connection
    RABBITMQ_HOST = os.getenv('CLOUDAMQP_URL')
    params = pika.URLParameters(RABBITMQ_HOST)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    # Send the message
    message = json.dumps({'zip': zip_code, 'distance': distance, 'keyword': keyword})
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    print(" [x] Sent %r" % message)
    connection.close()

if __name__ == '__main__':
    threading.Thread(target=rabbitmq_consumer, daemon=True).start()
    #app.run(debug=True, use_reloader=False)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)