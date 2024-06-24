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
    __tablename__ = 'restaurants3'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    zip = Column(String)
    distance = Column(Float)
    keyword = Column(String)

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
    fetch_and_store(data['zip'], data['distance'], data['keyword'])

def geocode_zip(zip_code):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": zip_code, "key": os.getenv('GOOGLE_API_KEY')}
    response = requests.get(base_url, params=params)
    results = response.json()
    if results['status'] == 'OK':
        location = results['results'][0]['geometry']['location']
        #print("successful geocoding")
        return location['lat'], location['lng']
    else:
        return None, None  # Handle no result or error appropriately

def fetch_and_store(zip_code, distance, keyword):
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    lat, long = geocode_zip(zip_code)
    loc = str(lat) + "," + str(long)
    #endpoint_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius={distance}&type=restaurant&keyword={food_type}&key={GOOGLE_API_KEY}"
    endpoint_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={loc}&radius={distance}&type=restaurant&keyword={keyword}&key={GOOGLE_API_KEY}"
    res = requests.get(endpoint_url)
    results = res.json().get('results', [])
    for result in results:
        restaurant = Restaurant(
            name=result['name'],
            address=result.get('vicinity', ''),
            latitude=result['geometry']['location']['lat'],
            longitude=result['geometry']['location']['lng'],
            zip=zip_code,
            distance=distance,
            keyword=keyword
        )
        #print("Inserting restaurant: ", restaurant)
        session.add(restaurant)
    session.commit()
    print("Restaurants stored to DB")
    send_info_to_analyzer(zip_code, distance, keyword)

def send_info_to_analyzer(zip_code, distance, keyword):
    connection_ = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel_ = connection_.channel()
    channel_.queue_declare(queue='analysis_queue', durable=True)

    # Send the message
    message = json.dumps({'zip': zip_code, 'distance': distance, 'keyword': keyword})
    channel_.basic_publish(
        exchange='',
        routing_key='analysis_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    print(" [x] Sent %r" % message)
    connection_.close()

channel.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
