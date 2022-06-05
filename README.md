# transaction-service

API сервис для проведения транзакций с отправкой уведомлений брокеру сообщений.

### Локальное развертывание проекта
1. Создание виртуального окружения
```
python3.10 -m venv /path/to/project/venv
```
2. Активация виртуального окружения
```
source /path/to/project/venv/bin/activate
```
3. Установка зависимостей
```
pip install --upgrade pip
pip install -r requirements.txt
```
4. Конфигурация .env файла
Необходимо создать `.env` файл по примеру `example.env` и назначить переменным `DATABASE_URL`, `RMQ_HOST` и `RMQ_PORT` значения для корректного взаимодействия с Postgres и RabbitMQ.
4. Запуск сервера
```
flask run
```