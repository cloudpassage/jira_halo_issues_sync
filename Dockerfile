FROM python:3

LABEL author="Thomas.Miller@fidelissecurity.com"

WORKDIR /usr/src/app

COPY ./ .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "application.py"]