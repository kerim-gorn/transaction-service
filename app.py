"""Flask application of transaction service."""
import os

import pika
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set RabbitMQ connection.
rmq_channel = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.environ.get('RMQ_HOST'),
        port=os.environ.get('RMQ_PORT'),
        heartbeat=600
    )
).channel()

db.init_app(app)
migrate.init_app(app, db)

import api
