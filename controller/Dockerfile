FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y pyinstaller

EXPOSE 5000

CMD ["python", "app.py"]
