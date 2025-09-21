# DeepSeek API 配置脚本
Write-Host "配置DeepSeek API环境变量..." -ForegroundColor Green

# 临时设置环境变量（当前会话）
$env:LLM_API_KEY = "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK"
$env:LLM_ENDPOINT = "https://www.chataiapi.com/v1/chat/completions"
$env:LLM_MODEL = "deepseek-v3-250324"

Write-Host "当前会话中的环境变量已设置：" -ForegroundColor Yellow
Write-Host "LLM_API_KEY=$env:LLM_API_KEY" -ForegroundColor Cyan
Write-Host "LLM_ENDPOINT=$env:LLM_ENDPOINT" -ForegroundColor Cyan
Write-Host "LLM_MODEL=$env:LLM_MODEL" -ForegroundColor Cyan

Write-Host "`n要永久设置环境变量，请运行:" -ForegroundColor Yellow
Write-Host ".\setup_deepseek_api_permanent.ps1" -ForegroundColor White
