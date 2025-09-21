@echo off
echo 配置DeepSeek API环境变量...

set LLM_API_KEY=sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK
set LLM_ENDPOINT=https://www.chataiapi.com/v1/chat/completions
set LLM_MODEL=deepseek-v3-250324

echo 当前会话中的环境变量已设置：
echo LLM_API_KEY=%LLM_API_KEY%
echo LLM_ENDPOINT=%LLM_ENDPOINT%
echo LLM_MODEL=%LLM_MODEL%

echo.
echo 注意：这些环境变量只在当前命令行会话中有效。
echo 要永久设置，请运行: setup_deepseek_api_permanent.bat
pause
