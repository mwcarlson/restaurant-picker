import os
import pika
import json

def rabbitmq_consumer():
    RABBITMQ_HOST = os.getenv('CLOUDAMQP_URL')
    params = pika.URLParameters(RABBITMQ_HOST)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='frontend_queue', durable=True)

    def on_message_received(ch, method, properties, body):
        # Assuming `latest_restaurant_data` is a global variable managed elsewhere
        print("Updated restaurant data received:", body)

    channel.basic_consume(queue='frontend_queue', on_message_callback=on_message_received, auto_ack=True)
    print("Starting RabbitMQ consumer")
    channel.start_consuming()

def send_to_queue(zip_code, distance, keyword):
    RABBITMQ_HOST = os.getenv('CLOUDAMQP_URL')
    params = pika.URLParameters(RABBITMQ_HOST)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    message = json.dumps({'zip': zip_code, 'distance': distance, 'keyword': keyword})
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(" [x] Sent %r" % message)
    connection.close()

if __name__ == '__main__':
    rabbitmq_consumer()
