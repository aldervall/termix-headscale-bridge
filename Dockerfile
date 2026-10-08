FROM python:3-slim
WORKDIR /app
COPY adapter.py /app/adapter.py
EXPOSE 8091
CMD ["python3", "/app/adapter.py"]
