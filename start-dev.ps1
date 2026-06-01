Write-Host "=== Démarrage de l'environnement de développement ===" -ForegroundColor Cyan

Write-Host "[1/3] Démarrage des services Docker (postgres, backend, monitoring)..." -ForegroundColor Yellow
docker compose up -d postgres backend prometheus grafana alertmanager nginx elasticsearch logstash

Write-Host "[2/3] Attente du backend..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "[3/3] Démarrage du service ML local..." -ForegroundColor Yellow
$mlProc = Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "-m uvicorn api.main:app --port 8000" -WorkingDirectory "$PSScriptRoot\ml" -PassThru

Write-Host "=== TOUT EST PRET ===" -ForegroundColor Green
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Green
Write-Host "ML:       http://localhost:8000" -ForegroundColor Green
Write-Host "Postgres: localhost:5433" -ForegroundColor Green
Write-Host "Grafana:  http://localhost:3000" -ForegroundColor Green
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Green
Write-Host "Nginx:    http://localhost:8080" -ForegroundColor Green
Write-Host "Elasticsearch: http://localhost:9200" -ForegroundColor Green
Write-Host ""
Write-Host "Pour arreter: docker compose down" -ForegroundColor Magenta
