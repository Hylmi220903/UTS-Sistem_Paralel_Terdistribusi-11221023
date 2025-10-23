# Quick Start Guide - Pub-Sub Log Aggregator

## 🚀 Cara Tercepat Menjalankan Sistem

### Option 1: Docker (Recommended)

```powershell
# 1. Build image
docker build -t uts-aggregator .

# 2. Run container
docker run -d --name pubsub-aggregator -p 8080:8080 -v ${PWD}/data:/app/data uts-aggregator

# 3. Check health
curl http://localhost:8080/health

# 4. Run demo
.\demo_test.ps1
```

### Option 2: Docker Compose (Bonus)

```powershell
# 1. Start all services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f aggregator

# 4. Run demo
.\demo_test.ps1

# 5. Stop services
docker-compose down
```

### Option 3: Python Langsung

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# 3. Run demo (di terminal baru)
.\demo_test.ps1
```

---

## 🧪 Run Tests

```powershell
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Open coverage report
start htmlcov/index.html
```

---

## 📋 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/publish` | POST | Publish event |
| `/events?topic={topic}` | GET | Get processed events |
| `/stats` | GET | Get statistics |

---

## 📊 Example Requests

### Publish Event

```powershell
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-22T10:30:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123}
  }'
```

### Get Stats

```powershell
curl http://localhost:8080/stats
```

### Get Events

```powershell
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

---

## 📁 Project Structure

```
UTS-Sistem_Paralel_Terdistribusi-11221023-Code/
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # Pydantic models
│   ├── consumer.py               # Event consumer
│   └── dedup_store.py            # SQLite dedup store
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_aggregator.py        # Core tests
│   └── test_api.py               # API tests
├── data/                         # Database (runtime)
├── Dockerfile                    # Container image
├── docker-compose.yml            # Multi-service (bonus)
├── requirements.txt              # Dependencies
├── .gitignore                    # Git ignore
├── demo_test.ps1                 # Demo script
├── README.md                     # Full documentation
├── StepByStep.md                 # Tutorial lengkap
├── SUBMISSION_CHECKLIST.md       # Checklist poin
└── QUICKSTART.md                 # This file
```

---

## 🔍 Key Features

✅ **Idempotent Consumer**: Event dengan (topic, event_id) sama hanya diproses sekali  
✅ **Deduplication**: Deteksi dan buang event duplikat  
✅ **Persistent Storage**: SQLite database tahan restart  
✅ **Async Processing**: asyncio.Queue pipeline  
✅ **Docker Support**: Dockerfile + Docker Compose  
✅ **Comprehensive Tests**: 15+ unit & integration tests  
✅ **Complete Documentation**: README, StepByStep, Checklist  

---

## 📖 Documentation

- **README.md**: Arsitektur lengkap, design decisions, API docs
- **StepByStep.md**: Tutorial step-by-step untuk pemula
- **SUBMISSION_CHECKLIST.md**: Mapping requirement ke implementation
- **QUICKSTART.md**: This file - quick reference

---

## ❓ Troubleshooting

**Port sudah digunakan?**
```powershell
docker run -p 8081:8080 ...  # Use different port
```

**Tests gagal import?**
```powershell
$env:PYTHONPATH = "$PWD"
pytest tests/ -v
```

**Database locked?**
```powershell
docker stop pubsub-aggregator
Remove-Item data/dedup_store.db-journal
docker start pubsub-aggregator
```

---

## 📞 Support

- Check logs: `docker logs -f pubsub-aggregator`
- View stats: `curl http://localhost:8080/stats`
- Health check: `curl http://localhost:8080/health`

---

**NIM**: 11221023  
**Mata Kuliah**: Sistem Paralel Terdistribusi  
**Tahun**: 2025
