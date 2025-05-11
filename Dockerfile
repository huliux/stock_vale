FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 将 supervisord.conf 复制到 supervisor 的配置目录
COPY supervisord.conf /etc/supervisor/conf.d/stock_vale_app.conf

EXPOSE 8125
EXPOSE 8501

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/stock_vale_app.conf"]
