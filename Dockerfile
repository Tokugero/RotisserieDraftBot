FROM python:3.6.8-stretch

ADD cubebot.py /
ADD requirements.txt /
ADD functions /functions/

RUN pip install -r requirements.txt

CMD [ "python", "./cubebot.py" ]
