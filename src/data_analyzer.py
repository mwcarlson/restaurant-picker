import os
import json
import pika
from sqlalchemy import create_engine, Column, Integer, String, Float, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Database setup
DATABASE_URI = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Restaurant(Base):
    __tablename__ = 'restaurants3'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    zip = Column(String)
    distance = Column(Float)
    keyword = Column(String)

# Setup RabbitMQ connection
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

channel.queue_declare(queue='analysis_queue', durable=True)

def select_random_restaurant(zip_code, distance, keyword):
    stmt = select(Restaurant).where(Restaurant.zip == zip_code, Restaurant.distance == distance, Restaurant.keyword == keyword).order_by(func.random()).limit(1)  # Using func.random() for random selection
    result = session.execute(stmt).scalars().first()
    return result

def callback(ch, method, properties, body):
    print("Received analysis request")
    data = json.loads(body)
    restaurant = select_random_restaurant(data['zip'], data['distance'], data['keyword'])
    if restaurant:
        print("Selected random restaurant: ", restaurant.name)
        message = json.dumps({
            'name': restaurant.name,
            'address': restaurant.address,
            'latitude': restaurant.latitude,
            'longitude': restaurant.longitude
        })
        send_result_to_frontend(message)
    else:
        print("Failed to retrieve random restaurant")
        message = json.dumps({
            'name': 'Failed to find a restaurant with your search criteria.',
            'address': 'Please try again with expanded search criteria.',
            'latitude': '',
            'longitude': ''
        })
        send_result_to_frontend(message)

def send_result_to_frontend(message):
    channel.basic_publish(
        exchange='',
        routing_key='frontend_queue',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2,)
    )
    print("Sent result to frontend:", message)

channel.basic_consume(queue='analysis_queue', on_message_callback=callback, auto_ack=True)

print('Waiting for analysis requests. To exit press CTRL+C')
channel.start_consuming()
