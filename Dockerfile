FROM python:3.9.1-buster

EXPOSE 8000
# This is the root of the Django app
RUN mkdir -p /var/app
WORKDIR /var/app
# No venv used here, everything is installed into the root environment
ADD requirements.txt /var
RUN pip install -r /var/requirements.txt
ENTRYPOINT ["python", "/var/app/manage.py"]
