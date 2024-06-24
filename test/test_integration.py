import json
import pytest
from src.data_collector import session, Base, engine, Restaurant
from src.app import app as flask_app
from pika import BlockingConnection, ConnectionParameters
from sqlalchemy import create_engine
from factory.alchemy import SQLAlchemyModelFactory
from factory import Faker

# Setup Factory for test data
class RestaurantFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Restaurant
        sqlalchemy_session = session

    name = Faker('company')
    address = Faker('address')
    latitude = Faker('latitude')
    longitude = Faker('longitude')
    zip = Faker('zipcode')
    distance = 1609.34
    keyword = 'pizza'

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    Base.metadata.create_all(engine)

    yield flask_app

@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='module')
def rabbitmq():
    """Fixture to run RabbitMQ during tests."""
    connection = BlockingConnection(ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    yield channel
    connection.close()

def test_full_application_flow(client, rabbitmq):
    # Post data to Flask to initiate the process
    response = client.post('/', data={'zip': '10001', 'distance': '1', 'keyword': 'pizza'})
    assert response.status_code == 302  # Assuming redirection after post

    # Simulate RabbitMQ message handling as would be triggered by the Flask app
    restaurant = RestaurantFactory()
    session.commit()

    # Publishing a message to RabbitMQ which should be picked up by the data collector
    message = json.dumps({'zip': restaurant.zip, 'distance': restaurant.distance, 'keyword': restaurant.keyword})
    rabbitmq.basic_publish(exchange='',
                           routing_key='task_queue',
                           body=message)

    # Assuming there's a slight delay for message handling
    import time
    time.sleep(1)

    # Now check if the data has been processed correctly
    response = client.get('/results')
    assert b'Test Restaurant' in response.data  # Check if the test restaurant's data is displayed

# Run tests
if __name__ == '__main__':
    pytest.main()
