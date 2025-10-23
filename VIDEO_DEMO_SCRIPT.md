# 🎥 Skrip Video Demo (5-8 Menit)
**Panduan Singkat untuk Video YouTube - UTS Sistem Terdistribusi**

---

## 📋 CHECKLIST POIN PENILAIAN

### Video Demo Wajib (10 poin):
- ✅ Build image dan jalankan container
- ✅ Kirim event duplikat (simulasi at-least-once) dan tunjukkan idempotency + dedup bekerja
- ✅ Periksa `GET /events` dan `GET /stats` sebelum/sesudah pengiriman duplikat
- ✅ Restart container dan tunjukkan dedup store persisten mencegah reprocessing
- ✅ Ringkas arsitektur dan keputusan desain (singkat, 30-60 detik)

---

## 🎬 SKRIP DEMO

### **[00:00-01:00] PART 1: Intro & Build Image**

**Yang Ditampilkan:**
```powershell
# 1. Tunjukkan struktur project
dir

# Output yang diharapkan:
# src/          <- source code
# tests/        <- unit tests
# Dockerfile    <- container definition
# requirements.txt
```

**Narasi:**
> "Halo, saya akan demo Pub-Sub Log Aggregator untuk UTS Sistem Terdistribusi.
> Sistem ini menerima event dari publisher dan memproses dengan fitur idempotency dan deduplication.
> Mari kita mulai dengan build Docker image."

```powershell
# 2. Build Docker image
docker build -t uts-aggregator .
```

**Narasi saat build:**
> "Dockerfile menggunakan Python 3.11-slim, install dependencies dari requirements.txt,
> dan menjalankan sebagai non-root user untuk security."

---

### **[01:00-02:00] PART 2: Run Container**

**Yang Ditampilkan:**
```powershell
# 1. Jalankan container
docker run -d --name pubsub-aggregator -p 8080:8080 -v ${PWD}/data:/app/data uts-aggregator

# 2. Cek container running
docker ps

# 3. Lihat logs
docker logs -f pubsub-aggregator
# Tekan Ctrl+C setelah melihat "Application started successfully"
```

**Narasi:**
> "Container berjalan di port 8080 dengan volume mounting untuk persistent storage.
> Logs menunjukkan FastAPI server dan EventConsumer sudah aktif."

```powershell
# 4. Test health check
curl http://localhost:8080/health

# 5. Cek root endpoint
curl http://localhost:8080
```

**Narasi:**
> "API sudah responsif. Kita punya 3 endpoint utama:
> POST /publish untuk terima event,
> GET /events untuk query event,
> GET /stats untuk statistik sistem."

---

### **[02:00-04:00] PART 3: Test Idempotency & Deduplication**

**Yang Ditampilkan:**

**3.1 Cek Stats Awal**
```powershell
# Stats sebelum ada event
curl http://localhost:8080/stats
```

**Narasi:**
> "Stats awal: received=0, unique_processed=0, duplicate_dropped=0."

**3.2 Kirim Event Pertama**
```powershell
# Event unik pertama
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-24T10:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "action": "login"}
  }'
```

**Narasi:**
> "Kirim event pertama dengan topic 'user.login' dan event_id 'evt-demo-001'.
> Response: status accepted, event masuk ke queue."

**3.3 Kirim Event Duplikat (Simulasi At-Least-Once)**
```powershell
# Event SAMA lagi (duplikat)
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-24T10:01:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "action": "login"}
  }'
```

**Narasi:**
> "Kirim event yang SAMA lagi dengan event_id yang sama.
> Ini mensimulasikan at-least-once delivery: publisher retry mengirim ulang karena network issue.
> API tetap return 200 OK karena menerima semua event."

**3.4 Kirim Event Duplikat Lagi (ke-3)**
```powershell
# Duplikat ke-3
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-24T10:02:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "action": "login"}
  }'
```

**Narasi:**
> "Kirim lagi event yang sama untuk ketiga kalinya."

**3.5 Kirim Event Berbeda**
```powershell
# Event unik kedua (event_id berbeda)
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.logout",
    "event_id": "evt-demo-002",
    "timestamp": "2025-10-24T10:03:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "action": "logout"}
  }'
```

**Narasi:**
> "Kirim event kedua dengan event_id berbeda (evt-demo-002)."

**3.6 Tunggu & Cek Logs**
```powershell
# Tunggu processing
Start-Sleep -Seconds 2

# Lihat logs
docker logs pubsub-aggregator --tail 20
```

**Narasi:**
> "Di logs, kita bisa lihat:
> - Event processed: evt-demo-001 (hanya 1x)
> - Duplicate event dropped: evt-demo-001 (2x)
> - Event processed: evt-demo-002
> Ini menunjukkan IDEMPOTENCY bekerja!"

**3.7 Cek Stats Setelah Processing**
```powershell
curl http://localhost:8080/stats
```

**Narasi:**
> "Stats sekarang:
> - received: 4 (4 event masuk ke queue)
> - unique_processed: 2 (hanya 2 event unik disimpan)
> - duplicate_dropped: 2 (2 duplikat dibuang)
> - topics: ['user.login', 'user.logout']
> 
> DEDUPLICATION BERHASIL! Event dengan (topic, event_id) yang sama hanya diproses sekali."

**3.8 Query Events**
```powershell
# Get semua events
curl http://localhost:8080/events

# Get events by topic
curl "http://localhost:8080/events?topic=user.login"
```

**Narasi:**
> "GET /events mengembalikan hanya 2 event unik yang tersimpan.
> Filter by topic juga berfungsi."

---

### **[04:00-06:00] PART 4: Test Persistence (Restart Container)**

**Yang Ditampilkan:**

**4.1 Restart Container**
```powershell
# Stop container
docker stop pubsub-aggregator

# Start lagi
docker start pubsub-aggregator

# Tunggu startup
Start-Sleep -Seconds 3

# Cek logs
docker logs pubsub-aggregator --tail 10
```

**Narasi:**
> "Sekarang saya restart container untuk simulasi crash atau deployment baru.
> Logs menunjukkan aplikasi startup kembali dengan database yang sama."

**4.2 Cek Stats Setelah Restart**
```powershell
curl http://localhost:8080/stats
```

**Narasi:**
> "Perhatikan: stats di-reset karena in-memory counter,
> TAPI dedup store masih menyimpan record event yang sudah diproses."

**4.3 Kirim Event Duplikat Setelah Restart**
```powershell
# Kirim evt-demo-001 LAGI setelah restart
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json" `
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-24T11:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": 123, "action": "login_after_restart"}
  }'
```

**Narasi:**
> "Kirim event evt-demo-001 lagi SETELAH restart.
> Event ini sudah diproses SEBELUM restart."

**4.4 Cek Logs & Stats**
```powershell
# Tunggu
Start-Sleep -Seconds 2

# Logs
docker logs pubsub-aggregator --tail 5

# Stats
curl http://localhost:8080/stats
```

**Narasi:**
> "Logs menunjukkan: 'Duplicate event dropped'!
> Stats: duplicate_dropped bertambah.
> 
> INI MEMBUKTIKAN PERSISTENCE BEKERJA!
> Database SQLite di volume /app/data masih menyimpan record event lama.
> Event yang sudah diproses sebelum restart TIDAK diproses ulang.
> 
> Ini penting untuk CONSISTENCY: setelah crash dan restart,
> sistem masih ingat event mana yang sudah diproses."

**4.5 Query Events (Masih Ada)**
```powershell
curl http://localhost:8080/events
```

**Narasi:**
> "Events yang diproses sebelum restart masih ada di database.
> Hanya 2 event tersimpan, bukan 3 atau lebih."

---

### **[06:00-07:30] PART 5: Arsitektur & Keputusan Desain**

**Yang Ditampilkan:** (bisa pakai diagram atau live code editor)

**Narasi:**
> "Mari saya jelaskan arsitektur singkat:
> 
> **Flow Event:**
> 1. Publisher → POST /publish → FastAPI → Validation (Pydantic)
> 2. Event masuk ke asyncio.Queue (in-memory pipeline)
> 3. EventConsumer memproses dari queue secara async
> 4. Check: is_duplicate(topic, event_id) di SQLite
> 5. Jika belum ada → store_event(), jika sudah ada → drop
> 
> **Idempotency:**
> - Key: (topic, event_id)
> - UNIQUE constraint di database
> - Guarantees: event sama tidak diproses ulang
> 
> **Deduplication:**
> - SQLite database dengan UNIQUE constraint
> - Cek sebelum processing, atomic operation
> - Handle race condition dengan IntegrityError
> 
> **Persistence:**
> - SQLite database di volume /app/data
> - Docker volume mounting: ./data:/app/data
> - Data tahan restart dan crash
> 
> **Ordering:**
> - FIFO dari asyncio.Queue
> - Total ordering tidak dibutuhkan karena idempotency
> 
> **At-Least-Once:**
> - API return 200 sebelum processing selesai
> - Publisher bisa retry → duplikat masuk
> - Dedup store handle duplikat
> 
> **Keputusan Desain:**
> - SQLite: balance antara simplicity dan reliability
> - asyncio.Queue: efficient in-memory pipeline
> - Non-root user di Docker: security best practice"

---

### **[07:30-08:00] PART 6: Unit Tests & Closing**

**Yang Ditampilkan:**
```powershell
# Stop container dulu
docker stop pubsub-aggregator

# Run unit tests
pytest tests/ -v
```

**Narasi:**
> "Sistem sudah dilengkapi unit tests:
> - test_duplicate_detection
> - test_persistence_after_restart
> - test_high_volume_events (5000+ events, 20% duplikasi)
> - test_api endpoints
> 
> Semua tests PASS, membuktikan sistem robust dan reliable.
> 
> **Kesimpulan:**
> Sistem Pub-Sub Log Aggregator ini mengimplementasikan:
> ✅ Idempotent consumer
> ✅ Deduplication dengan SQLite
> ✅ Persistent storage tahan restart
> ✅ At-least-once delivery handling
> ✅ Docker containerization
> 
> Terima kasih sudah menonton! Link repository dan dokumentasi ada di deskripsi."

**Cleanup:**
```powershell
# Cleanup (optional, untuk demo saja)
docker rm pubsub-aggregator
docker rmi uts-aggregator
```

---

## 📝 TIPS RECORDING

### Persiapan:
1. **Bersihkan terminal history**
2. **Zoom terminal font** agar mudah dibaca
3. **Persiapkan script di notepad** untuk copy-paste
4. **Test run dulu** untuk memastikan semua berjalan
5. **Close aplikasi lain** untuk menghindari notifikasi

### Recording Software:
- **OBS Studio** (free, recommended)
- **ShareX** (Windows)
- **Zoom** (record meeting)
- **Loom** (web-based)

### Audio:
- Gunakan **microphone yang jelas**
- **Ruangan tenang**, hindari background noise
- **Speak clearly** dengan pace yang tidak terlalu cepat
- **Pause sebentar** sebelum lanjut step berikutnya

### Visual:
- **Full screen terminal** atau split dengan code editor
- **Highlight important output** dengan pointer mouse
- **Zoom in** saat menunjukkan detail
- **Tunjukkan URL di browser** (http://localhost:8080) jika perlu

### Editing (Optional):
- Cut bagian yang tidak perlu (build yang lama, loading, dll)
- Tambahkan **text overlay** untuk poin penting
- Tambahkan **timestamp** di deskripsi video
- Speed up bagian yang repetitive (2x speed)

---

## 📌 TIMESTAMP UNTUK DESKRIPSI VIDEO

Salin ini ke deskripsi YouTube:

```
🎯 Timestamps:
00:00 - Intro & Struktur Project
01:00 - Build Docker Image
02:00 - Run Container & Health Check
03:00 - Test Idempotency & Deduplication
05:00 - Test Persistence (Restart Container)
07:00 - Arsitektur & Keputusan Desain
08:00 - Unit Tests & Closing

📂 Repository: [Link GitHub Anda]
📄 Dokumentasi Lengkap: README.md
📝 Laporan: report.pdf

#SistemTerdistribusi #PubSub #Idempotency #Docker #FastAPI
```

---

## ✅ CHECKLIST SEBELUM RECORDING

- [ ] Docker Desktop running
- [ ] Data folder kosong (untuk fresh demo)
- [ ] Terminal font size cukup besar
- [ ] Background applications closed
- [ ] Microphone tested
- [ ] Script siap di notepad
- [ ] Recording software ready
- [ ] Internet connection stable (untuk push ke GitHub)

---

**SEMANGAT RECORDING! 🎥🚀**
