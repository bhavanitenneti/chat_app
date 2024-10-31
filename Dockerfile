FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt /app/
RUN apt-get update && apt-get install -y mariadb-client \
    && pip install --trusted-host pypi.python.org -r requirements.txt

COPY wait-for-it.sh /app/
RUN chmod +x wait-for-it.sh

COPY . /app

EXPOSE 5000

CMD ["./wait-for-it.sh", "mysql", "--", "python", "app.py"]

