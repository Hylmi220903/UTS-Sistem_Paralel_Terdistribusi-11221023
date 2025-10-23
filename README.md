# Pub-Sub Log Aggregator
**UTS Sistem Paralel Terdistribusi - 11221023**

## 📋 Deskripsi Sistem

Sistem Pub-Sub Log Aggregator adalah layanan yang menerima event/log dari publisher dan memprosesnya melalui consumer dengan fitur **idempotent** (tidak memproses ulang event yang sama) dan **deduplication** (mendeteksi dan membuang event duplikat). Seluruh komponen berjalan dalam container Docker.

### Fitur Utama
- ✅ **Idempotent Consumer**: Event dengan (topic, event_id) yang sama hanya diproses sekali
- ✅ **Deduplication**: Deteksi dan pencatatan event duplikat
- ✅ **Persistent Storage**: SQLite database yang tahan terhadap restart
- ✅ **RESTful API**: Endpoint untuk publish, query, dan statistik
- ✅ **Asynchronous Processing**: Menggunakan asyncio.Queue untuk pipeline yang efisien
- ✅ **Docker Support**: Dockerfile dan Docker Compose untuk deployment
- ✅ **Comprehensive Testing**: Unit tests dan integration tests

---

## 🏗️ Arsitektur Sistem

### Diagram Arsitektur

```
┌─────────────┐         ┌──────────────────────────────────┐
│  Publisher  │         │      Aggregator Service          │
│  (External) │         │                                  │
└──────┬──────┘         │  ┌────────────────────────────┐  │
       │                │  │   FastAPI Application      │  │
       │ POST /publish  │  │   - POST /publish          │  │
       └───────────────>│  │   - GET /events?topic=...  │  │
                        │  │   - GET /stats             │  │
                        │  └───────────┬────────────────┘  │
                        │              │                    │
                        │              ▼                    │
                        │  ┌────────────────────────────┐  │
                        │  │   asyncio.Queue            │  │
                        │  │   (In-Memory Pipeline)     │  │
                        │  └───────────┬────────────────┘  │
                        │              │                    │
                        │              ▼                    │
                        │  ┌────────────────────────────┐  │
                        │  │   EventConsumer            │  │
                        │  │   - Idempotency Check      │  │
                        │  │   - Deduplication Logic    │  │
                        │  └───────────┬────────────────┘  │
                        │              │                    │
                        │              ▼                    │
                        │  ┌────────────────────────────┐  │
                        │  │   DedupStore (SQLite)      │  │
                        │  │   - Processed Events       │  │
                        │  │   - (topic, event_id)      │  │
                        │  └────────────────────────────┘  │
                        └──────────────────────────────────┘
```

### Komponen Sistem

#### 1. **FastAPI Application** (`src/main.py`)
- Entry point untuk menerima HTTP requests
- Validasi schema event menggunakan Pydantic
- Routing ke consumer untuk processing asynchronous

#### 2. **EventConsumer** (`src/consumer.py`)
- Membaca event dari asyncio.Queue
- Melakukan idempotency check sebelum processing
- Menyimpan event yang unik ke DedupStore
- Menghitung statistik (received, processed, dropped)

#### 3. **DedupStore** (`src/dedup_store.py`)
- Persistent storage menggunakan SQLite
- Menyimpan event yang telah diproses
- UNIQUE constraint pada (topic, event_id) untuk idempotency
- Index untuk performa query yang cepat

#### 4. **Event Model** (`src/models.py`)
- Pydantic models untuk validasi data
- Schema: `{topic, event_id, timestamp, source, payload}`

---

## 🔑 Keputusan Desain

### 1. Idempotency
**Implementasi**: Menggunakan UNIQUE constraint di SQLite pada kolom (topic, event_id)

**Alasan**:
- Database-level constraint memastikan idempotency bahkan dalam race condition
- Tidak perlu locking mechanism yang kompleks
- Atomic operation di database level

**Trade-off**:
- Setiap event memerlukan database lookup
- Sedikit overhead untuk I/O ke disk
- ✅ Keuntungan: Reliability dan data consistency yang tinggi

### 2. Dedup Store (SQLite)
**Implementasi**: SQLite embedded database di `/app/data/dedup_store.db`

**Alasan**:
- Persistent storage yang tahan restart container
- Tidak memerlukan external database server (sesuai requirement "lokal")
- ACID compliance untuk data integrity
- Lightweight dan mudah di-backup

**Alternatif yang dipertimbangkan**:
- ❌ In-memory dict: Tidak persist setelah restart
- ❌ File JSON/LMDB: Kurang atomic, perlu manual locking
- ✅ SQLite: Balance antara simplicity dan reliability

### 3. Ordering & Total Ordering
**Implementasi**: Event diproses dalam urutan FIFO dari asyncio.Queue

**Penjelasan**:
- asyncio.Queue memastikan FIFO ordering untuk single consumer
- Timestamp disimpan untuk reference, tapi tidak digunakan untuk ordering
- Total ordering tidak dibutuhkan karena idempotency: hasil sama regardless of order

**Skenario**:
```
Event A (timestamp: T1) arrives first
Event B (timestamp: T2) arrives second (T2 < T1)
→ Processed: A, then B (FIFO)
→ Result: Both processed once (idempotent)
```

### 4. At-Least-Once Delivery
**Implementasi**: Publisher menerima HTTP 200 OK sebelum event diproses

**Simulasi**:
```python
1. POST /publish → Event masuk queue → Return 200 OK
2. Consumer mengambil dari queue
3. Jika consumer crash sebelum store → Event hilang
4. Publisher retry → Event masuk lagi (duplikat)
5. Dedup store mendeteksi → Duplicate dropped
```

**Reliability**:
- Event di queue bisa hilang jika container crash
- Publisher harus implement retry logic
- Dedup store memastikan duplikat tidak diproses ulang

### 5. Crash Tolerance
**Implementasi**:
```python
def test_persistence_after_restart():
    # Store event
    store1.store_event(event)
    
    # Simulasi restart (new instance)
    store2 = DedupStore(same_db_path)
    
    # Event masih tercatat
    assert store2.is_duplicate(topic, event_id)
```

**Mekanisme**:
- SQLite database di persistent volume (`./data:/app/data`)
- Setelah restart, DedupStore membaca dari database yang sama
- Event yang sudah diproses tidak diproses ulang

### 6. Failure Modes & Mitigasi

| Failure Mode | Dampak | Mitigasi |
|--------------|--------|----------|
| Container crash | Event di queue hilang | Publisher retry + dedup |
| Database corruption | Data loss | Backup volume, SQLite WAL mode |
| Duplicate flood | Resource exhaustion | Early dedup check (is_duplicate) |
| Out-of-order events | No issue | Idempotency ensures correctness |

---

## 📊 Performance & Scalability

### Skala Uji
- **Target**: >= 5000 events dengan >= 20% duplikasi
- **Hasil Test**: Sistem responsive, semua event diproses
- **Latency**: ~0.01s per event (dengan simulasi processing)

### Bottleneck
1. **SQLite Write**: Single-threaded writes
   - Mitigasi: Use WAL mode, batch processing
2. **asyncio.Queue**: In-memory, bounded size
   - Mitigasi: Backpressure handling, monitoring

### Optimasi (Opsional untuk Production)
```python
# Bloom Filter untuk fast negative lookup
if not bloom_filter.might_contain(event_id):
    # Definitely not duplicate, skip DB check
    
# Batch writes
async def batch_store(events):
    with conn:
        conn.executemany(...)
```

---

## 🔌 API Documentation

### 1. POST /publish
**Deskripsi**: Menerima event dari publisher

**Request Body**:
```json
{
  "topic": "user.login",
  "event_id": "evt-12345",
  "timestamp": "2025-10-22T10:30:00Z",
  "source": "auth-service",
  "payload": {
    "user_id": 123,
    "ip": "192.168.1.1"
  }
}
```

**Response**:
```json
{
  "status": "accepted",
  "message": "Event diterima dan akan diproses",
  "event_id": "evt-12345",
  "received_at": "2025-10-22T10:30:01.123456Z"
}
```

**Status Codes**:
- `200 OK`: Event diterima
- `422 Unprocessable Entity`: Validasi gagal

### 2. GET /events?topic={topic}
**Deskripsi**: Mengambil daftar event yang telah diproses

**Query Parameters**:
- `topic` (optional): Filter by topic
- `limit` (optional, default=100): Max events to return

**Response**:
```json
{
  "topic": "user.login",
  "count": 2,
  "events": [
    {
      "topic": "user.login",
      "event_id": "evt-12345",
      "timestamp": "2025-10-22T10:30:00Z",
      "source": "auth-service",
      "payload": {"user_id": 123},
      "processed_at": "2025-10-22T10:30:01.234567Z"
    }
  ]
}
```

### 3. GET /stats
**Deskripsi**: Mendapatkan statistik sistem

**Response**:
```json
{
  "received": 1000,
  "unique_processed": 850,
  "duplicate_dropped": 150,
  "topics": ["user.login", "user.logout", "payment.success"],
  "uptime": 3600.5
}
```

**Metrics Explained**:
- `received`: Total event yang masuk ke queue
- `unique_processed`: Event unik yang disimpan ke store
- `duplicate_dropped`: Event duplikat yang dibuang
- `topics`: List topic yang ada di sistem
- `uptime`: Waktu sistem berjalan (seconds)

---

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t uts-aggregator .
```

### Run Container
```bash
docker run -p 8080:8080 -v ${PWD}/data:/app/data uts-aggregator
```

### Docker Compose (Bonus)
```bash
docker-compose up -d
```

**Docker Compose Features**:
- ✅ Service aggregator dengan persistent volume
- ✅ Internal network untuk isolasi
- ✅ Health check configuration
- ✅ Restart policy
- ✅ Non-root user untuk security

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/test_aggregator.py -v
```

### Run API Tests
```bash
pytest tests/test_api.py -v
```

### Test Coverage
```bash
pytest --cov=src --cov-report=html
```

**Test Scenarios**:
1. ✅ Dedup detection (same topic + event_id)
2. ✅ Persistence after restart
3. ✅ Schema validation
4. ✅ GET endpoints consistency
5. ✅ Stress test (5000+ events, 20% duplicate)
6. ✅ API integration tests

---

## 📈 Monitoring & Observability

### Logging
```python
# Setiap event processing dicatat
logger.info(f"Event processed: {topic}:{event_id}")
logger.info(f"Duplicate event dropped: {topic}:{event_id}")
```

### Metrics (GET /stats)
- Track duplicate rate: `duplicate_dropped / received`
- Monitor topics: Detect anomaly dalam topic distribution
- Uptime: Verify system stability

### Health Check
```bash
curl http://localhost:8080/health
```

---

## 🔐 Security Considerations

1. **Non-root User**: Container runs as `appuser`
2. **No External Dependencies**: All running locally
3. **Input Validation**: Pydantic schema validation
4. **SQL Injection**: Protected by parameterized queries

---

## 📦 Project Structure

```
UTS-Sistem_Paralel_Terdistribusi-11221023-Code/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── consumer.py          # EventConsumer logic
│   └── dedup_store.py       # SQLite dedup store
├── tests/
│   ├── test_aggregator.py   # Unit tests
│   └── test_api.py          # API integration tests
├── data/                    # SQLite database (created at runtime)
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-service orchestration (bonus)
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── StepByStep.md           # Tutorial lengkap
└── SUBMISSION_CHECKLIST.md # Checklist poin nilai
```

---

## 📚 Referensi

### Konsep Teori (Bab 1-7, Tanenbaum)
1. **Bab 1**: Pub-Sub pattern untuk decoupling publisher-consumer
2. **Bab 2**: Client-server architecture, RESTful API
3. **Bab 3**: At-least-once delivery semantics, idempotency
4. **Bab 4**: Topic-based routing, event naming scheme
5. **Bab 5**: Event timestamp + monotonic counter untuk ordering
6. **Bab 6**: Retry mechanism, backoff, durable storage
7. **Bab 7**: Idempotency + dedup untuk consistency

### Teknologi
- **FastAPI**: Modern Python web framework
- **asyncio**: Asynchronous I/O untuk concurrency
- **SQLite**: Embedded database untuk persistence
- **Docker**: Containerization
- **pytest**: Testing framework

---

## 🎯 Kesimpulan

Sistem ini mengimplementasikan **Pub-Sub log aggregator** dengan fokus pada:
- **Reliability**: Persistent storage, crash tolerance
- **Correctness**: Idempotency, deduplication
- **Observability**: Logging, metrics, health checks
- **Simplicity**: Minimal dependencies, clear architecture

Suitable untuk production environment dengan traffic moderate (ribuan events/detik) dan requirements high data integrity.

---

## 👤 Informasi

**NIM**: 11221023  
**Mata Kuliah**: Sistem Paralel Terdistribusi  
**Ujian**: UTS Take-Home  
**Tahun**: 2025

---

## 📝 Lisensi

Proyek ini dibuat untuk keperluan akademik.
