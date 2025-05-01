FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y zip binutils && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

EXPOSE 5000

CMD ["python", "app.py"]
