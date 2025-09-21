@echo off
echo 永久配置DeepSeek API环境变量...

setx LLM_API_KEY "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK"
setx LLM_ENDPOINT "https://www.chataiapi.com/v1/chat/completions"
setx LLM_MODEL "deepseek-v3-250324"

echo.
echo ✅ 环境变量已永久设置！
echo 请重新启动命令行或重启电脑以使环境变量生效。
echo.
echo 设置的环境变量：
echo LLM_API_KEY=sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK
echo LLM_ENDPOINT=https://api.deepseek.com/v1/chat/completions  
echo LLM_MODEL=deepseek-chat
echo.
pause
