@echo off
chcp 65001 >nul
title Quatro Anos - iniciar o jogo
cd /d "%~dp0"
echo.
echo  QUATRO ANOS - simulador politico do Brasil
echo  ------------------------------------------
echo  Iniciando o motor (porta 8000) e a tela (porta 5179)...
echo.
rem lista de partidas propria do jogador: nao mistura com as partidas de teste do desenvolvimento
set LOCAL_PLAYER_ID=jogador
rem a chave do Gemini (opcional) fica em backend\.env; sem ela o jogo usa a leitura local de textos
start "Quatro Anos - motor" /min cmd /c "cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
start "Quatro Anos - tela" /min cmd /c "npx vite --port 5179"
echo  Aguardando o jogo subir (cerca de 15 segundos)...
timeout /t 15 /nobreak >nul
start "" http://localhost:5179/
echo.
echo  O jogo abriu no navegador: http://localhost:5179/
echo  Para encerrar, feche as duas janelas minimizadas "Quatro Anos".
echo  Roteiro de teste: docs\ROTEIRO_PLAYTEST.md
echo.
pause
