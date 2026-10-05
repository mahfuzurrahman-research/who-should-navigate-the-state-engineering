FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends r-base-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x run_public_demo.sh run_statistical_demo.sh run_all_demos.sh
CMD ["./run_all_demos.sh"]
