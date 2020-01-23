FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
RUN apk update && apk add bash py-gunicorn
RUN pip install --no-cache-dir --upgrade pip wheel
RUN mkdir /code
WORKDIR /code

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8080

CMD bash -c "export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.8/site-packages && gunicorn --workers=3 converter:app -b 0.0.0.0:8080"