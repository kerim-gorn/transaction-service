"""SQLAlchemy ORM classes."""
from enum import Enum

from sqlalchemy.sql import func

from app import db


class TransactionStatus(Enum):
    """Enum for status of ORM model Transaction."""

    FAILURE = -1,
    IN_PROGRESS = 0,
    SUCCESS = 1


class TransactionCategory(Enum):
    """Enum for categories of ORM model Transaction."""

    DEPOSIT = 1,
    WITHDRAW = 2


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, default=TransactionStatus.IN_PROGRESS.value)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    client_id = db.Column(
        db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE')
    )


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String, nullable=False)
    balance = db.Column(db.Float, default=0)
    transaction = db.relationship(
        Transaction,
        backref='client',
        passive_deletes=True
    )
