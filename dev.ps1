param([switch], [switch], [switch]False)

if (False) {
    Write-Host "Script de Desarrollo - Tracking API" -ForegroundColor Cyan
    Write-Host "  -Docker    Iniciar con Docker Compose"
    Write-Host "  -API       Iniciar solo la API"
    exit 0
}

if () {
    Write-Host "Iniciando con Docker..." -ForegroundColor Blue
    docker-compose up -d
    Write-Host "API: http://localhost:8000" -ForegroundColor Green
    Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Green
} elseif () {
    Write-Host "Iniciando API..." -ForegroundColor Blue
    if (!(Test-Path "venv")) {
        python -m venv venv
    }
    & venv\Scripts\Activate.ps1
    pip install -r requirements-dev.txt
    python -m uvicorn src.main:app --reload
} else {
    Write-Host "Usa: .\dev.ps1 -Docker o .\dev.ps1 -API"
}
