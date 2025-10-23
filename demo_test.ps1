# Demo Test Script - Pub-Sub Log Aggregator
# Script untuk Video Demo - Menunjukkan Idempotency & Deduplication

Write-Host "=== Pub-Sub Log Aggregator Demo ===" -ForegroundColor Green
Write-Host "Demonstrasi Idempotency & Deduplication" -ForegroundColor Gray
Write-Host ""

# Function untuk kirim event
function Send-Event {
    param(
        [string]$Topic,
        [string]$EventId,
        [hashtable]$Payload,
        [string]$Description
    )
    
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $body = @{
        topic = $Topic
        event_id = $EventId
        timestamp = $timestamp
        source = "demo-script"
        payload = $Payload
    } | ConvertTo-Json -Compress
    
    Write-Host $Description -ForegroundColor Cyan
    Write-Host "  Topic: $Topic | Event ID: $EventId" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Method POST -Uri "http://localhost:8080/publish" `
            -Headers @{"Content-Type"="application/json"} -Body $body
        Write-Host "  Response: $($response.status) - $($response.message)" -ForegroundColor Yellow
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# Test 1: Send event unik pertama
Write-Host "[Test 1] Kirim Event UNIK Pertama" -ForegroundColor Magenta
Send-Event -Topic "user.login" -EventId "evt-demo-001" `
    -Payload @{user_id=123; action="login"; ip="192.168.1.1"} `
    -Description "Event pertama dengan event_id 'evt-demo-001'"

Start-Sleep -Seconds 2

# Test 2: Send duplicate event (ke-1)
Write-Host "[Test 2] Kirim Event DUPLIKAT (sama dengan Test 1)" -ForegroundColor Magenta
Send-Event -Topic "user.login" -EventId "evt-demo-001" `
    -Payload @{user_id=123; action="login"; ip="192.168.1.1"} `
    -Description "Event DUPLIKAT - event_id sama dengan event pertama"

Start-Sleep -Seconds 2

# Test 3: Send duplicate event lagi (ke-2)
Write-Host "[Test 3] Kirim Event DUPLIKAT Lagi" -ForegroundColor Magenta
Send-Event -Topic "user.login" -EventId "evt-demo-001" `
    -Payload @{user_id=123; action="login"} `
    -Description "Event DUPLIKAT lagi - event_id masih sama"

Start-Sleep -Seconds 2

# Test 4: Send event berbeda
Write-Host "[Test 4] Kirim Event UNIK Kedua (event_id berbeda)" -ForegroundColor Magenta
Send-Event -Topic "user.logout" -EventId "evt-demo-002" `
    -Payload @{user_id=123; action="logout"} `
    -Description "Event baru dengan event_id 'evt-demo-002'"

Start-Sleep -Seconds 2

# Test 5: Check stats
Write-Host "[Test 5] Cek Statistik Sistem" -ForegroundColor Magenta
Write-Host "Mengambil stats dari GET /stats..." -ForegroundColor Gray
try {
    $stats = Invoke-RestMethod -Method GET -Uri "http://localhost:8080/stats"
    Write-Host ""
    Write-Host "=== STATISTIK SISTEM ===" -ForegroundColor Green
    Write-Host "  Received:          $($stats.received) events" -ForegroundColor White
    Write-Host "  Unique Processed:  $($stats.unique_processed) events" -ForegroundColor Green
    Write-Host "  Duplicate Dropped: $($stats.duplicate_dropped) events" -ForegroundColor Red
    Write-Host "  Topics:            $($stats.topics -join ', ')" -ForegroundColor Cyan
    Write-Host "  Uptime:            $([math]::Round($stats.uptime, 2)) seconds" -ForegroundColor Gray
    Write-Host ""
    
    # Kalkulasi duplicate rate
    $dupRate = [math]::Round(($stats.duplicate_dropped / $stats.received) * 100, 2)
    Write-Host "  Duplicate Rate:    $dupRate%" -ForegroundColor Yellow
    Write-Host ""
} catch {
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Get events
Write-Host "[Test 6] Cek Events yang Tersimpan" -ForegroundColor Magenta
Write-Host "Mengambil events dari GET /events..." -ForegroundColor Gray
try {
    $events = Invoke-RestMethod -Method GET -Uri "http://localhost:8080/events?limit=10"
    Write-Host ""
    Write-Host "=== EVENTS TERSIMPAN ===" -ForegroundColor Green
    Write-Host "  Total: $($events.count) events" -ForegroundColor White
    Write-Host ""
    foreach ($event in $events.events) {
        Write-Host "  ✓ $($event.topic) : $($event.event_id)" -ForegroundColor Cyan
        Write-Host "    Processed at: $($event.processed_at)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== Demo Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Untuk melihat logs container, jalankan:" -ForegroundColor Yellow
Write-Host "  docker logs pubsub-aggregator --tail 20" -ForegroundColor White
Write-Host ""
Write-Host "Expected Results:" -ForegroundColor Cyan
Write-Host "  - Received: 4 (4 events dikirim)" -ForegroundColor Gray
Write-Host "  - Unique Processed: 2 (evt-demo-001 dan evt-demo-002)" -ForegroundColor Gray
Write-Host "  - Duplicate Dropped: 2 (evt-demo-001 dikirim 3x, jadi 2 duplikat)" -ForegroundColor Gray
