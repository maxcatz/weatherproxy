# WeatherProxy API

A FastAPI-based weather proxy service that caches geolocation and weather data in Redis.

## Features

- Cache city geolocation and weather data in Redis
- Retry requests to external APIs with exponential backoff
- Expose a simple `/weather?city=<city_name>` endpoint
- Logging and metrics for requests

## Installation && Local Run/Testing

### 1. Clone the repository

```bash
git clone git@github.com:maxcatz/weatherproxy.git
cd weatherproxy
```
 ### 2. Create a virtual environment and install dependencies   
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 3. Set environment variables
```bash
export PYTHONPATH=.
export REDIS_URL="redis://localhost:6379"
```
### 4. Redis
Ensure you have local instance of redis available on port 6379
Or start redis in docker 
```bash
docker run --name my-redis -p 6379:6379 -d redis:7-alpine
```

### 5. Run FastAPI locally
```bash
python app/main.py
```
API available at http://127.0.0.1:8000

### 6. Run unit tests
```bash
pytest -v tests/
```



## Quick Start with Docker 

### 1. Build Docker images
```bash
docker-compose build
```

### 2. Start containers
```bash
docker-compose up
```
API available at http://localhost:8000

Redis runs internally at redis://redis:6379 for the API container

3. Stop and remove containers
```bash
docker-compose down
```
## Improvements

- **Type Validation from External APIs:** Implement robust validation to ensure data received from external APIs is correctly typed and handled safely.
- **Metrics API to Prometheus:** Expose key application metrics to Prometheus for monitoring and alerting.
- **Testing:** Increase test coverage and add edge case tests.
