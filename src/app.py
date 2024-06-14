from flask import Flask, render_template, request, redirect, url_for, jsonify
import pika, json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # User form input
        distance = request.form.get('distance', type=int)
        food_type = request.form.get('food_type')

        # Send data to data collector via RabbitMQ
        send_preferences(distance, food_type)
        return redirect(url_for('results'))
    return render_template('index.html')

@app.route('/results')
def results():
    # This route will be refreshed by AJAX to display results
    return render_template('results.html')

def send_preferences(distance, food_type):
    # Setup RabbitMQ Connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    # Send the message
    message = json.dumps({'distance': distance, 'food_type': food_type})
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
    app.run(debug=True)

