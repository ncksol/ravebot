FROM python:3

WORKDIR /home/user/app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD python main.py