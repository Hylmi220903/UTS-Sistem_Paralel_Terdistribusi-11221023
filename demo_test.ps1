# Sample Test Script - Demo Pub-Sub Log Aggregator
# Gunakan script ini untuk demonstrasi cepat

Write-Host "=== Pub-Sub Log Aggregator Demo ===" -ForegroundColor Green
Write-Host ""

# Function untuk kirim event
function Send-Event {
    param(
        [string]$Topic,
        [string]$EventId,
        [hashtable]$Payload
    )
    
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $body = @{
        topic = $Topic
        event_id = $EventId
        timestamp = $timestamp
        source = "demo-script"
        payload = $Payload
    } | ConvertTo-Json
    
    Write-Host "Sending event: $Topic : $EventId" -ForegroundColor Cyan
    $response = Invoke-RestMethod -Method POST -Uri "http://localhost:8080/publish" `
        -Headers @{"Content-Type"="application/json"} -Body $body
    Write-Host "Response: $($response.status)" -ForegroundColor Yellow
    Write-Host ""
}

# Test 1: Send normal event
Write-Host "Test 1: Sending normal event" -ForegroundColor Magenta
Send-Event -Topic "user.login" -EventId "evt-demo-001" -Payload @{user_id=123; ip="192.168.1.1"}

Start-Sleep -Seconds 1

# Test 2: Send duplicate event
Write-Host "Test 2: Sending duplicate event (same event_id)" -ForegroundColor Magenta
Send-Event -Topic "user.login" -EventId "evt-demo-001" -Payload @{user_id=123; ip="192.168.1.1"}

Start-Sleep -Seconds 1

# Test 3: Send different event
Write-Host "Test 3: Sending different event" -ForegroundColor Magenta
Send-Event -Topic "user.logout" -EventId "evt-demo-002" -Payload @{user_id=123}

Start-Sleep -Seconds 1

# Test 4: Check stats
Write-Host "Test 4: Checking statistics" -ForegroundColor Magenta
$stats = Invoke-RestMethod -Method GET -Uri "http://localhost:8080/stats"
Write-Host "Statistics:" -ForegroundColor Green
Write-Host "  Received: $($stats.received)"
Write-Host "  Unique Processed: $($stats.unique_processed)"
Write-Host "  Duplicate Dropped: $($stats.duplicate_dropped)"
Write-Host "  Topics: $($stats.topics -join ', ')"
Write-Host "  Uptime: $([math]::Round($stats.uptime, 2)) seconds"
Write-Host ""

# Test 5: Get events
Write-Host "Test 5: Getting processed events" -ForegroundColor Magenta
$events = Invoke-RestMethod -Method GET -Uri "http://localhost:8080/events?limit=10"
Write-Host "Total events retrieved: $($events.count)" -ForegroundColor Green
foreach ($event in $events.events) {
    Write-Host "  - $($event.topic) : $($event.event_id) (processed at $($event.processed_at))"
}
Write-Host ""

Write-Host "=== Demo Complete ===" -ForegroundColor Green
Write-Host "Check logs: docker logs pubsub-aggregator" -ForegroundColor Yellow
