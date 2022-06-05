"""Transaction service API."""
import pika
from flask import jsonify, request

import errors
from app import app, db, rmq_channel
from orm import Client, Transaction, TransactionCategory, TransactionStatus

MESSAGE_TEMPLATE = (
    '[INFO] Transaction #{trans_id}:\n'
    '* amount: {amount}\n'
    '* client_id: {client_id}\n'
    '* category: {category}\n'
    '* status: {status}'
)


@app.get('/')
def index():
    """Get root URL.

    Returns:
        Service's name.
    """
    return 'Transaction service API', 200


@app.get('/client/<int:client_id>')
def client_balance(client_id):
    """Get clients balance.

    Args:
        client_id(int): Client identifier.

    Returns:
        Client's balance. If client is not found returns 404.
    """
    client = Client.query.get(client_id)
    db.session.commit()

    if not client:
        return errors.error_response(
            status_code=404, message='Client is not found.'
        )

    response = jsonify({'balance': round(client.balance, 2)})
    response.status_code = 200
    return response


@app.post('/client')
def create_client():
    """Create client.

    Args:
        fullname(str): Client's fullname.

    Returns:
        Client's identifier.
    """
    fullname = request.json.get('fullname')

    if not isinstance(fullname, str):
        return errors.bad_request(
            message='Invalid fullname type.'
        )

    client = Client(fullname=fullname)

    db.session.add(client)
    db.session.commit()

    response = jsonify({'client_id': client.id})
    response.status_code = 200
    return response


@app.post('/client/<int:client_id>/deposit')
def deposit(client_id):
    """Deposit funds to the client's balance.

    Args:
        client_id (int): Client identifier.
        amount (int | float): Funds amount to deposit.
    """
    client = Client.query.get(client_id)
    db.session.commit()

    if not client:
        return errors.error_response(
            status_code=404, message='Client is not found.'
        )

    amount = request.json.get('amount')

    if not isinstance(amount, int | float):
        return errors.bad_request(
            message='Invalid amount type.'
        )

    client.balance += amount

    transaction = Transaction(
        amount=amount,
        client_id=client_id,
        category=TransactionCategory.DEPOSIT.value,
        status=TransactionStatus.SUCCESS.value
    )
    db.session.add(transaction)
    db.session.commit()

    # Define RabbitMQ queue.
    rmq_channel.queue_declare(queue=str(client.id), durable=True)

    # Send message to RabbitMQ.
    message = MESSAGE_TEMPLATE.format(
        trans_id=transaction.id,
        amount=amount,
        client_id=client_id,
        category=TransactionCategory.DEPOSIT.name,
        status=TransactionStatus.SUCCESS.name
    )
    rmq_channel.basic_publish(
        exchange='',
        routing_key=str(client.id),
        body=message
    )

    response = jsonify({'message': 'Deposit completed.'})
    response.status_code = 200
    return response


@app.post('/client/<int:client_id>/withdraw')
def withdraw(client_id):
    """Withdraw funds from the client's balance.

    Args:
        client_id (int): Client identifier.
        amount (int | float): Funds amount to withdraw.
    """
    client = Client.query.get(int(client_id))
    db.session.commit()

    if not client:
        return errors.error_response(
            status_code=404, message='Client is not found.'
        )

    amount = request.json.get('amount')

    if not isinstance(amount, int | float):
        return errors.bad_request(
            message='Invalid amount type.'
        )

    amount = round(amount, 2)

    # Create Transaction record in database.
    transaction = Transaction(
        amount=amount,
        category=TransactionCategory.WITHDRAW.value,
        client_id=client.id
    )
    db.session.add(transaction)
    db.session.commit()

    # Define RabbitMQ queue.
    rmq_channel.queue_declare(queue=str(client.id), durable=True)

    # Balance is not enough to withdraw amount.
    if client.balance < amount:
        transaction.status = TransactionStatus.FAILURE.value
        db.session.commit()

        message = MESSAGE_TEMPLATE.format(
            trans_id=transaction.id,
            amount=amount,
            client_id=client_id,
            category=TransactionCategory.WITHDRAW.name,
            status=TransactionStatus.FAILURE.name
        )
        rmq_channel.basic_publish(
            exchange='',
            routing_key=str(client.id),
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        return errors.bad_request(
            message='Insufficient funds to withdraw.'
        )

    client.balance -= amount
    transaction.status = TransactionStatus.SUCCESS.value
    db.session.commit()

    # Send message to RabbitMQ.
    message = MESSAGE_TEMPLATE.format(
        trans_id=transaction.id,
        amount=amount,
        client_id=client_id,
        category=TransactionCategory.WITHDRAW.name,
        status=TransactionStatus.SUCCESS.name
    )
    rmq_channel.basic_publish(
        exchange='',
        routing_key=str(client.id),
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    response = jsonify({'message': 'Withdraw completed.'})
    response.status_code = 200
    return response
