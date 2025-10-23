# Step-by-Step Guide: Menjalankan Pub-Sub Log Aggregator
**Panduan Lengkap untuk Pemula**

---

## 📚 Penjelasan Konsep Pub-Sub

### Apa itu Pub-Sub?

**Pub-Sub** (Publisher-Subscriber) adalah pola komunikasi di mana:
- **Publisher**: Pengirim event/message (tidak tahu siapa yang menerima)
- **Subscriber/Consumer**: Penerima event/message (tidak tahu siapa yang mengirim)
- **Topic**: Kategori/channel untuk mengelompokkan event

**Analogi**: Seperti berlangganan channel YouTube
- Publisher = YouTuber yang upload video
- Subscriber = Kamu yang berlangganan
- Topic = Channel/kategori (Gaming, Education, dll)

### Apa itu Idempotency?

**Idempotent** = Operasi yang bisa dilakukan berkali-kali dengan hasil yang sama

**Contoh**:
```
Event A dikirim 3 kali → Hanya diproses 1 kali
Event B dikirim 1 kali → Diproses 1 kali
```

**Kenapa penting?**
- Network bisa gagal → Publisher retry mengirim event
- Event duplikat bisa masuk sistem
- Idempotency memastikan event yang sama tidak diproses ulang

### Apa itu Deduplication?

**Deduplication** = Mendeteksi dan membuang data duplikat

**Cara kerja di sistem ini**:
1. Event datang dengan (topic, event_id)
2. Cek di database: apakah (topic, event_id) sudah ada?
3. Jika sudah ada → Buang (duplicate_dropped++)
4. Jika belum ada → Proses dan simpan (unique_processed++)

---

## 🛠️ Persiapan Awal

### 1. Pastikan Sudah Terinstall

**Windows**:
```powershell
# Cek Python
python --version  # Harus >= 3.11

# Cek Docker
docker --version

# Cek Docker Compose
docker-compose --version
```

**Jika belum ada**:
- Python: Download dari https://www.python.org/downloads/
- Docker Desktop: Download dari https://www.docker.com/products/docker-desktop/

### 2. Buka Terminal/PowerShell

```powershell
# Navigasi ke folder project
cd "C:\DATA\ITK\SEMESTER 7\SISTEM TERDISTRIBUSI\UTS\UTS-Sistem_Paralel_Terdistribusi-11221023-Code"
```

### 3. Verifikasi File Project

```powershell
# List file yang ada
dir

# Harus ada:
# - src/
# - tests/
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - README.md
```

---

## 🚀 Cara 1: Menjalankan dengan Python (Tanpa Docker)

### Step 1: Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt
```

**Penjelasan**:
- `pip` = Package manager untuk Python
- `requirements.txt` = Daftar library yang dibutuhkan
- Install: FastAPI, uvicorn, pydantic, pytest, dll

### Step 2: Jalankan Aplikasi

```powershell
# Jalankan server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

**Penjelasan**:
- `uvicorn` = Web server untuk FastAPI
- `src.main:app` = Import app dari file src/main.py
- `--host 0.0.0.0` = Accept connections dari semua IP
- `--port 8080` = Jalankan di port 8080
- `--reload` = Auto-restart saat ada perubahan code

**Output yang diharapkan**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Step 3: Test Aplikasi

**Buka browser baru**, akses: http://localhost:8080

Akan muncul JSON response:
```json
{
  "service": "Pub-Sub Log Aggregator",
  "version": "1.0.0",
  "status": "running"
}
```

✅ **Aplikasi berhasil berjalan!**

---

## 🐳 Cara 2: Menjalankan dengan Docker (Recommended)

### Step 1: Build Docker Image

```powershell
# Build image dari Dockerfile
docker build -t uts-aggregator .
```

**Penjelasan**:
- `docker build` = Perintah untuk membuat image
- `-t uts-aggregator` = Nama image (tag)
- `.` = Context directory (current folder)

**Proses yang terjadi**:
1. Download base image (python:3.11-slim)
2. Copy requirements.txt
3. Install Python packages
4. Copy source code
5. Set user, permissions, dll
6. Create image

**Output akhir**: 
```
Successfully built abc123def456
Successfully tagged uts-aggregator:latest
```

### Step 2: Run Container

```powershell
# Run container dengan volume mounting
docker run -d `
  --name pubsub-aggregator `
  -p 8080:8080 `
  -v ${PWD}/data:/app/data `
  uts-aggregator
```

**Penjelasan**:
- `-d` = Detached mode (run in background)
- `--name` = Nama container
- `-p 8080:8080` = Port mapping (host:container)
- `-v ${PWD}/data:/app/data` = Mount volume untuk persistent data
- `uts-aggregator` = Image yang digunakan

**Cek container running**:
```powershell
docker ps
```

Output:
```
CONTAINER ID   IMAGE             STATUS         PORTS
abc123         uts-aggregator    Up 10 seconds  0.0.0.0:8080->8080/tcp
```

### Step 3: View Logs

```powershell
# Lihat logs container
docker logs -f pubsub-aggregator
```

**Penjelasan**:
- `logs` = Tampilkan log output
- `-f` = Follow mode (real-time)

Output:
```
INFO:     Started server process
INFO:     EventConsumer started
INFO:     Application started successfully
```

**Tekan Ctrl+C untuk exit dari log view**

### Step 4: Test Container

```powershell
# Cek health
curl http://localhost:8080/health

# Atau buka browser
start http://localhost:8080
```

---

## 🐳 Cara 3: Menjalankan dengan Docker Compose (Bonus)

### Step 1: Start Services

```powershell
# Start all services
docker-compose up -d
```

**Penjelasan**:
- `docker-compose` = Orchestration tool untuk multiple containers
- `up` = Start services
- `-d` = Detached mode

**Proses yang terjadi**:
1. Create network (pubsub-network)
2. Build/pull images
3. Create volumes (./data)
4. Start containers (aggregator, publisher)

**Output**:
```
Creating network "pubsub-network"
Creating pubsub-aggregator ... done
Creating pubsub-publisher  ... done
```

### Step 2: Check Status

```powershell
# Lihat semua services
docker-compose ps
```

Output:
```
Name                  Command               State    Ports
----------------------------------------------------------------
pubsub-aggregator     python -m uvicorn ...        Up     0.0.0.0:8080->8080/tcp
pubsub-publisher      python -c print...           Exit 0
```

### Step 3: View Logs

```powershell
# Logs dari semua services
docker-compose logs -f

# Logs dari specific service
docker-compose logs -f aggregator
```

### Step 4: Stop Services

```powershell
# Stop semua services
docker-compose down

# Stop dan hapus volumes
docker-compose down -v
```

---

## 🧪 Testing Sistem

### Test 1: Publish Event Pertama

**Buka terminal baru**, jalankan:

```powershell
# Kirim event via curl
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-22T10:30:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "ip": "192.168.1.1"}
  }'
```

**Response yang diharapkan**:
```json
{
  "status": "accepted",
  "message": "Event diterima dan akan diproses",
  "event_id": "evt-001",
  "received_at": "2025-10-22T10:30:01.123456Z"
}
```

✅ **Event berhasil diterima!**

### Test 2: Kirim Event Duplikat

**Kirim event yang sama lagi**:

```powershell
# Event dengan event_id yang sama
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-22T10:31:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "ip": "192.168.1.1"}
  }'
```

**Response**: Masih `"status": "accepted"` (API menerima semua event)

**Tapi** cek di logs:
```powershell
docker logs pubsub-aggregator
```

Akan muncul:
```
INFO: Duplicate event dropped: user.login:evt-001
```

✅ **Deduplication berfungsi!**

### Test 3: Cek Statistik

```powershell
curl http://localhost:8080/stats
```

**Response**:
```json
{
  "received": 2,
  "unique_processed": 1,
  "duplicate_dropped": 1,
  "topics": ["user.login"],
  "uptime": 125.5
}
```

**Penjelasan**:
- `received: 2` = 2 event masuk ke queue
- `unique_processed: 1` = 1 event unik disimpan
- `duplicate_dropped: 1` = 1 event duplikat dibuang

✅ **Idempotency berfungsi!**

### Test 4: Query Events

```powershell
# Get semua events
curl http://localhost:8080/events

# Get events by topic
curl "http://localhost:8080/events?topic=user.login"
```

**Response**:
```json
{
  "topic": "user.login",
  "count": 1,
  "events": [
    {
      "topic": "user.login",
      "event_id": "evt-001",
      "timestamp": "2025-10-22T10:30:00Z",
      "source": "auth-service",
      "payload": {"user_id": 123, "ip": "192.168.1.1"},
      "processed_at": "2025-10-22T10:30:01.234567Z"
    }
  ]
}
```

✅ **Query berfungsi!**

### Test 5: Stress Test (5000+ Events)

**Buat script untuk kirim banyak event**:

```powershell
# Simpan ke file test_stress.ps1
@"
for (`$i = 1; `$i -le 5000; `$i++) {
    `$eventId = "evt-`$i"
    if (`$i % 5 -eq 0) {
        # Buat duplikat (20%)
        `$eventId = "evt-`$(`$i-1)"
    }
    
    `$body = @{
        topic = "stress.test"
        event_id = `$eventId
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        source = "stress-test"
        payload = @{index = `$i}
    } | ConvertTo-Json
    
    curl -X POST http://localhost:8080/publish `
      -H "Content-Type: application/json" `
      -d `$body -s | Out-Null
    
    if (`$i % 500 -eq 0) {
        Write-Host "Sent `$i events..."
    }
}
Write-Host "Done! Sent 5000 events."
"@ | Out-File test_stress.ps1

# Jalankan script
.\test_stress.ps1
```

**Tunggu beberapa detik**, lalu cek stats:

```powershell
curl http://localhost:8080/stats
```

**Expected**:
```json
{
  "received": 5000,
  "unique_processed": 4000,
  "duplicate_dropped": 1000,
  ...
}
```

✅ **Sistem handle 5000+ events dengan 20% duplikasi!**

---

## 🔄 Test Persistence (Restart Container)

### Step 1: Cek Data Sebelum Restart

```powershell
curl http://localhost:8080/stats
```

Note down `unique_processed` value.

### Step 2: Restart Container

```powershell
# Stop container
docker stop pubsub-aggregator

# Start lagi
docker start pubsub-aggregator

# Tunggu beberapa detik
Start-Sleep -Seconds 5
```

### Step 3: Kirim Event Duplikat

```powershell
# Kirim event yang sudah ada sebelum restart
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-22T11:00:00Z",
    "source": "auth-service",
    "payload": {"test": "after_restart"}
  }'
```

### Step 4: Verify Persistence

```powershell
curl http://localhost:8080/stats
```

**Expected**: 
- `duplicate_dropped` bertambah
- Event `evt-001` masih dikenali sebagai duplikat

✅ **Persistent storage berfungsi!** (Event yang sudah diproses sebelum restart masih tercatat)

---

## 🧪 Menjalankan Unit Tests

### Step 1: Install Test Dependencies

```powershell
pip install -r requirements.txt
```

### Step 2: Run Tests

```powershell
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_aggregator.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Output yang diharapkan**:
```
tests/test_aggregator.py::TestDedupStore::test_store_initialization PASSED
tests/test_aggregator.py::TestDedupStore::test_store_event PASSED
tests/test_aggregator.py::TestDedupStore::test_duplicate_detection PASSED
...
======================== 20 passed in 5.23s =========================
```

### Step 3: View Coverage Report

```powershell
# Open HTML report
start htmlcov/index.html
```

✅ **Semua tests pass!**

---

## 📊 Monitoring Sistem

### View Real-time Logs

```powershell
# Docker logs
docker logs -f pubsub-aggregator

# Akan menampilkan:
# - Event received
# - Event processed
# - Duplicate dropped
```

### Check Health

```powershell
# Health endpoint
curl http://localhost:8080/health

# Expected
{"status": "healthy", "timestamp": "..."}
```

### Monitor Stats

```powershell
# Script untuk monitor stats setiap 5 detik
while ($true) {
    Clear-Host
    Write-Host "=== Stats ===" -ForegroundColor Green
    curl http://localhost:8080/stats 2>$null | ConvertFrom-Json | Format-List
    Start-Sleep -Seconds 5
}
```

---

## 🛑 Stopping Sistem

### Docker Run

```powershell
# Stop container
docker stop pubsub-aggregator

# Remove container
docker rm pubsub-aggregator
```

### Docker Compose

```powershell
# Stop services
docker-compose down

# Stop dan hapus volumes (HATI-HATI: data hilang)
docker-compose down -v
```

### Python Langsung

```powershell
# Tekan Ctrl+C di terminal yang menjalankan uvicorn
```

---

## ❓ Troubleshooting

### Problem: Port 8080 sudah digunakan

**Error**: `Address already in use`

**Solution**:
```powershell
# Cari process yang menggunakan port 8080
netstat -ano | findstr :8080

# Kill process (ganti PID dengan hasil di atas)
taskkill /PID <PID> /F

# Atau gunakan port lain
docker run -p 8081:8080 ...
```

### Problem: Docker build gagal

**Error**: `Cannot connect to Docker daemon`

**Solution**:
1. Pastikan Docker Desktop running
2. Restart Docker Desktop
3. Run as Administrator

### Problem: Import error saat run tests

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```powershell
# Set PYTHONPATH
$env:PYTHONPATH = "$PWD"
pytest tests/ -v
```

### Problem: Database locked

**Error**: `database is locked`

**Solution**:
```powershell
# Stop semua containers
docker stop pubsub-aggregator

# Delete lock file
Remove-Item data/dedup_store.db-journal -ErrorAction SilentlyContinue

# Restart
docker start pubsub-aggregator
```

### Problem: Logs tidak muncul

**Solution**:
```powershell
# Set environment variable
docker run -e PYTHONUNBUFFERED=1 ...
```

---

## 📝 Checklist Testing

Sebelum submit, pastikan semua ini sudah dicek:

- [ ] Build Docker image berhasil
- [ ] Container berjalan dan healthy
- [ ] POST /publish menerima event
- [ ] Duplikat terdeteksi (cek logs)
- [ ] GET /stats menampilkan data benar
- [ ] GET /events mengembalikan event
- [ ] Restart container, data persist
- [ ] Unit tests pass
- [ ] Stress test (5000 events) berhasil
- [ ] Docker Compose berjalan

---

## 🎓 Penjelasan untuk Laporan

### Cara Kerja Sistem

**1. Event Flow:**
```
Publisher → POST /publish → FastAPI → Validation (Pydantic)
                                    ↓
                            asyncio.Queue.put()
                                    ↓
                            EventConsumer.start()
                                    ↓
                            Check: is_duplicate?
                            ├─ Yes → drop (duplicate_dropped++)
                            └─ No  → store (unique_processed++)
                                    ↓
                            DedupStore (SQLite)
```

**2. Idempotency:**
- Key: `(topic, event_id)`
- UNIQUE constraint di database
- Cek sebelum processing: `is_duplicate(topic, event_id)`
- Store jika belum ada: `store_event(event)`

**3. Persistence:**
- SQLite database di `/app/data/dedup_store.db`
- Volume mount: `./data:/app/data`
- Setelah restart, database tetap ada
- Event yang sudah diproses masih tercatat

**4. At-Least-Once:**
- Publisher dapat HTTP 200 sebelum processing
- Jika crash sebelum store → event hilang
- Publisher retry → duplikat masuk
- Dedup store handle duplikat

---

## 🚀 Next Steps

1. **Untuk Demo Video**: 
   - Record saat build image
   - Jalankan container
   - Test publish event + duplicate
   - Show stats dan events
   - Restart dan test persistence

2. **Untuk Laporan**:
   - Screenshot architecture diagram
   - Screenshot stats sebelum/sesudah stress test
   - Jelaskan design decisions (lihat README.md)

3. **Bonus Points**:
   - Docker Compose sudah ada ✅
   - Unit tests comprehensive ✅
   - Documentation lengkap ✅

---

**Selamat Mengerjakan! 🎉**

Jika ada pertanyaan, cek README.md atau comment di source code untuk detail lebih lanjut.
