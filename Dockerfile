FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONIOENCODING=utf8

CMD [ "python", "-u", "./skilift_checker.py" ]
