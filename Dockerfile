FROM python:bullseye

RUN apt-get update

WORKDIR /babyagi

COPY . /babyagi

RUN pip install -r requirements.txt

CMD ["python", "-u", "babyagi.py"]
