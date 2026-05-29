FROM python:3.10-slim

WORKDIR /app

COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/sandbox /app/zhu_hun/zhu_hun_output

EXPOSE 8000

CMD ["python", "api_server.py"]