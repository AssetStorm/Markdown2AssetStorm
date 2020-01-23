FROM debian:stable-slim
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -y upgrade && \
apt-get -y install python3 python3-pip bash gunicorn3 pandoc
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel
RUN mkdir /code
WORKDIR /code

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8080

CMD bash -c "export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.8/site-packages && gunicorn3 --workers=3 converter:app -b 0.0.0.0:8080"