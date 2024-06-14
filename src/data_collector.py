import os
import json
import pika
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # This will load the environment variables from the .env file

# Database setup
DATABASE_URI = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URI)
Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# RabbitMQ setup
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

def callback(ch, method, properties, body):
    data = json.loads(body)
    print("Received data:", data)
    fetch_and_store(data['distance'], data['food_type'])

def fetch_and_store(distance, food_type):
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    endpoint_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius={distance}&type=restaurant&keyword={food_type}&key={GOOGLE_API_KEY}"
    res = requests.get(endpoint_url)
    results = res.json().get('results', [])
    for result in results:
        restaurant = Restaurant(
            name=result['name'],
            address=result.get('vicinity', ''),
            latitude=result['geometry']['location']['lat'],
            longitude=result['geometry']['location']['lng']
        )
        session.add(restaurant)
    session.commit()
    print("Restaurants stored to DB")

channel.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
