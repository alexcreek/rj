FROM python:3.8-buster
WORKDIR /code
COPY . /code
RUN pip3 install pipenv \
  && pipenv install --dev --system
