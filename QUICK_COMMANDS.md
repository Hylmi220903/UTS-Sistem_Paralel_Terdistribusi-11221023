# 🚀 Quick Commands - Copy & Paste Ready

**File ini berisi semua commands yang siap copy-paste untuk video demo**

---

## �️ QUICK RESET (Before Video Demo)

### Reset Database & Fresh Start
```powershell
# Option 1: Using script (RECOMMENDED)
.\reset_and_start.ps1

# Option 2: Manual reset
Remove-Item "data\dedup_store.db" -Force
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080

# Option 3: Reset only (without starting server)
.\reset_db.ps1
```

---

## �📋 PART 1: Setup & Build

### 1.1 Clean Start
```powershell
# Stop dan hapus container/image lama
docker stop pubsub-aggregator 2>$null
docker rm pubsub-aggregator 2>$null
docker rmi uts-aggregator 2>$null
Remove-Item -Recurse -Force data -ErrorAction SilentlyContinue
```

### 1.2 Build & Run
```powershell
# Build image
docker build -t uts-aggregator .

# Run container
docker run -d --name pubsub-aggregator -p 8080:8080 -v ${PWD}/data:/app/data uts-aggregator

# Check status
docker ps
```

### 1.3 Check Logs
```powershell
# View logs (Ctrl+C to exit)
docker logs -f pubsub-aggregator
```

### 1.4 Health Check
```powershell
# Check health
Invoke-RestMethod -Uri http://localhost:8080/health

# Check root endpoint
Invoke-RestMethod -Uri http://localhost:8080
```

---

## 📊 PART 2: Test Idempotency & Deduplication

### 2.1 Check Initial Stats
```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats
```

### 2.2 Send Event #1 (Unique)
```powershell
$body1 = @{
    topic = "user.login"
    event_id = "evt-demo-001"
    timestamp = "2025-10-24T10:00:00Z"
    source = "auth-service"
    payload = @{
        user_id = 123
        action = "login"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $body1
```

### 2.3 Send Event #2 (Duplicate)
```powershell
$body2 = @{
    topic = "user.login"
    event_id = "evt-demo-001"
    timestamp = "2025-10-24T10:01:00Z"
    source = "auth-service"
    payload = @{
        user_id = 123
        action = "login"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $body2
```

### 2.4 Send Event #3 (Duplicate Again)
```powershell
$body3 = @{
    topic = "user.login"
    event_id = "evt-demo-001"
    timestamp = "2025-10-24T10:02:00Z"
    source = "auth-service"
    payload = @{
        user_id = 123
        action = "login"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $body3
```

### 2.5 Send Event #4 (Different Event)
```powershell
$body4 = @{
    topic = "user.logout"
    event_id = "evt-demo-002"
    timestamp = "2025-10-24T10:03:00Z"
    source = "auth-service"
    payload = @{
        user_id = 123
        action = "logout"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $body4
```

### 2.6 Wait & Check Logs
```powershell
Start-Sleep -Seconds 2
docker logs pubsub-aggregator --tail 20
```

### 2.7 Check Stats After Processing
```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats
```
**Expected:**
- received: 4
- unique_processed: 2
- duplicate_dropped: 2

### 2.8 Query Events
```powershell
# Get all events
Invoke-RestMethod -Uri http://localhost:8080/events

# Get events by topic
Invoke-RestMethod -Uri "http://localhost:8080/events?topic=user.login"
```

---

## 🔄 PART 3: Test Persistence (Restart)

### 3.1 Restart Container
```powershell
# Stop
docker stop pubsub-aggregator

# Start
docker start pubsub-aggregator

# Wait
Start-Sleep -Seconds 3

# Check logs
docker logs pubsub-aggregator --tail 10
```

### 3.2 Check Stats After Restart
```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats
```

### 3.3 Send Duplicate Event After Restart
```powershell
$bodyAfterRestart = @{
    topic = "user.login"
    event_id = "evt-demo-001"
    timestamp = "2025-10-24T11:00:00Z"
    source = "auth-service"
    payload = @{
        user_id = 123
        action = "login_after_restart"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $bodyAfterRestart
```

### 3.4 Check Results
```powershell
# Wait
Start-Sleep -Seconds 2

# Logs (should show "Duplicate event dropped")
docker logs pubsub-aggregator --tail 5

# Stats
Invoke-RestMethod -Uri http://localhost:8080/stats

# Events (should still be only 2)
Invoke-RestMethod -Uri http://localhost:8080/events
```

---

## 🧪 PART 4: Run Unit Tests

### 4.1 Stop Container
```powershell
docker stop pubsub-aggregator
```

### 4.2 Run Tests
```powershell
pytest tests/ -v
```

### 4.3 Run with Coverage (Optional)
```powershell
pytest tests/ --cov=src --cov-report=html
start htmlcov/index.html
```

---

## 🎬 ALTERNATIVE: Use Demo Script

### Run Complete Demo
```powershell
.\demo_test.ps1
```

**Skrip ini otomatis:**
- Kirim 4 events (1 unik, 2 duplikat, 1 unik lagi)
- Tampilkan stats
- Tampilkan events

---

## 🐳 BONUS: Docker Compose Commands

### Start with Docker Compose
```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f aggregator
```

### Test Docker Compose
```powershell
# Health check
Invoke-RestMethod -Uri http://localhost:8080/health

# Send test event
$composeEvent = @{
    topic = "compose.test"
    event_id = "evt-compose-001"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "compose-demo"
    payload = @{ test = "docker-compose" }
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body $composeEvent

# Check stats
Invoke-RestMethod -Uri http://localhost:8080/stats
```

### Stop Docker Compose
```powershell
# Stop services (keep volumes)
docker-compose down

# Stop services and remove volumes (CAUTION!)
docker-compose down -v
```

### View Docker Compose Config
```powershell
# Show config
cat docker-compose.yml

# Validate config
docker-compose config
```

---

## 🧹 CLEANUP

### Clean All
```powershell
# Stop container
docker stop pubsub-aggregator

# Remove container
docker rm pubsub-aggregator

# Remove image (optional)
docker rmi uts-aggregator

# Remove data folder (optional - HATI-HATI!)
Remove-Item -Recurse -Force data -ErrorAction SilentlyContinue
```

---

## 📝 ONE-LINER COMMANDS (For Quick Demo)

### Single Event (One-line)
```powershell
Invoke-RestMethod -Uri http://localhost:8080/publish -Method Post -ContentType "application/json" -Body '{"topic":"test.topic","event_id":"evt-001","timestamp":"2025-10-24T10:00:00Z","source":"test","payload":{"test":"data"}}'
```

### Check Stats (One-line)
```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats | Format-List
```

### Check Events (One-line)
```powershell
Invoke-RestMethod -Uri http://localhost:8080/events | Select-Object count, @{n='events';e={$_.events | Select-Object topic, event_id}}
```

---

## 💡 TIPS

### View Formatted JSON Output
```powershell
Invoke-RestMethod -Uri http://localhost:8080/stats | ConvertTo-Json -Depth 5
```

### Monitor Logs in Real-time
```powershell
docker logs -f pubsub-aggregator
```

### Check Container Status
```powershell
docker ps -a | Select-String pubsub
```

### Quick Restart
```powershell
docker restart pubsub-aggregator; Start-Sleep -Seconds 3; docker logs pubsub-aggregator --tail 10
```

---

**SEMUA COMMANDS SUDAH TESTED DI POWERSHELL! ✅**
