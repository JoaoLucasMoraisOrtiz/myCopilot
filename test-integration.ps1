Write-Host "Testando integracao OpenCode + Modelo Local..." -ForegroundColor Cyan
Write-Host ""

$env:MODELS_DEV_API_JSON = "$PSScriptRoot\local-model-config.json"
$env:PHI_LOCAL_API_KEY = "unused"

Write-Host "Variaveis configuradas" -ForegroundColor Green
Write-Host ""

Write-Host "1. Verificando API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   API respondendo: $($response.status)" -ForegroundColor Green
    if ($response.model_loaded) {
        Write-Host "   Modelo carregado" -ForegroundColor Green
    }
}
catch {
    Write-Host "   API nao esta rodando!" -ForegroundColor Red
    Write-Host "   Execute 'python api.py' em outro terminal" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "2. Testando carregamento de providers..." -ForegroundColor Yellow
bun run test-phi-local.ts
