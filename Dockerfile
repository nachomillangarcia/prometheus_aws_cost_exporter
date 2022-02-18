FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV FLASK_APP app.py
ENTRYPOINT [ "flask", "run", "--host=0.0.0.0" ]
CMD []
