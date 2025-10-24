# 🗑️ Cara Reset/Hapus Data Database

Database disimpan di: `data/dedup_store.db` (SQLite)

---

## ⚡ Quick Reset (RECOMMENDED untuk Video Demo)

### Option 1: Script PowerShell (Paling Mudah)
```powershell
# Reset database saja
.\reset_db.ps1

# Reset + Start server langsung
.\reset_and_start.ps1
```

### Option 2: Manual Single Command
```powershell
# Hapus database
Remove-Item "data\dedup_store.db" -Force

# Start server (database baru otomatis dibuat)
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

---

## 📝 Metode Lengkap

### Metode 1: Stop Server → Hapus Database → Start Lagi

**Step-by-step:**

1. **Stop server yang sedang berjalan**
   ```powershell
   # Tekan Ctrl+C di terminal yang menjalankan uvicorn
   ```

2. **Hapus file database**
   ```powershell
   Remove-Item "data\dedup_store.db" -Force
   ```

3. **Start server lagi** (database baru akan dibuat otomatis)
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080
   ```

---

### Metode 2: Gunakan Python Script

```powershell
.\.venv\Scripts\python.exe reset_db.py
```

Script akan:
- Check apakah database ada
- Hapus semua records di tabel `events`
- Tampilkan jumlah data yang dihapus

---

### Metode 3: Manual dengan SQLite Command

```powershell
# Gunakan sqlite3 CLI (jika installed)
sqlite3 data/dedup_store.db "DELETE FROM events;"

# Atau gunakan DB Browser for SQLite (GUI)
```

---

### Metode 4: Reset via Docker

```powershell
# Stop container
docker stop pubsub-aggregator

# Hapus volume/data
Remove-Item -Recurse -Force data

# Restart container
docker start pubsub-aggregator
```

---

## ✅ Verification

Setelah reset, cek stats untuk verify:

```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats
```

**Expected output (data kosong):**
```json
{
  "received": 0,
  "unique_processed": 0,
  "duplicate_dropped": 0,
  "topics": [],
  "uptime": 0.123
}
```

---

## 🎬 For Video Demo

**Sebelum merekam video, SELALU reset database:**

```powershell
# Stop server (Ctrl+C)
# Jalankan:
.\reset_and_start.ps1
```

Ini memastikan:
- ✅ Data fresh dan bersih
- ✅ Stats dimulai dari 0
- ✅ Demo lebih clean dan professional

---

## 📂 File Locations

- **Database:** `data/dedup_store.db` (24 KB typical size)
- **Reset Script (PowerShell):** `reset_db.ps1`
- **Reset + Start Script:** `reset_and_start.ps1`
- **Reset Script (Python):** `reset_db.py`

---

## 🚨 Troubleshooting

**Problem:** "Cannot access file (used by another process)"

**Solution:**
```powershell
# Stop server dulu dengan Ctrl+C
# Tunggu 2-3 detik
# Baru jalankan reset
Remove-Item "data\dedup_store.db" -Force
```

**Problem:** "Database not found"

**Solution:**
```powershell
# Normal! Database akan dibuat otomatis saat server start
# Just start the server:
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

