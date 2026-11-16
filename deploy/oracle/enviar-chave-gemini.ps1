# Envia a chave do Gemini do seu PC (backend\.env) para o servidor da Oracle, sem digitar e sem exibir a chave.
# Uso (PowerShell, na raiz do projeto):  powershell -ExecutionPolicy Bypass -File deploy\oracle\enviar-chave-gemini.ps1
# A chave viaja pelo SSH (entrada padrão), é gravada em /opt/quatroanos/.env (permissão 600) e a API é recriada.
param(
    [string]$Servidor = 'ubuntu@163.176.55.130',
    [string]$ChaveSsh = (Join-Path $HOME '.ssh\oracle_a2'),
    [string]$Recursos = 'interpretar,mapear'
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)  # sem BOM no texto enviado ao SSH
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$arquivo = Join-Path $raiz 'backend\.env'
if (-not (Test-Path $arquivo)) { throw "Não achei $arquivo. Rode antes backend\scripts\configurar_gemini.ps1." }

function Ler([string]$nome) {
    $linha = Get-Content $arquivo | Where-Object { $_ -match "^$nome=" } | Select-Object -First 1
    if ($linha) { return ($linha -replace "^$nome=", '').Trim().Trim('"').Trim("'") }
    return ''
}
$chave = Ler 'GEMINI_API_KEY'
$modelo = Ler 'GEMINI_MODEL'
if ($chave -notmatch '^[A-Za-z0-9._-]{20,}$') { throw 'GEMINI_API_KEY ausente ou com formato inesperado em backend\.env.' }
if (-not $modelo) { $modelo = 'gemini-3.1-flash-lite' }
if ($modelo -notmatch '^[A-Za-z0-9._-]{3,80}$') { throw 'GEMINI_MODEL com formato inesperado.' }
if ($Recursos -notmatch '^[a-z,]+$') { throw 'Recursos inválidos.' }

$ssh = @('-i', $ChaveSsh, '-o', 'ConnectTimeout=20', '-o', 'BatchMode=yes', $Servidor)

# Script remoto: vai por stdin (a chave não aparece na linha de comando nem na lista de processos).
$remoto = @"
set -e
f=/opt/quatroanos/.env
grep -v -E '^(GEMINI_API_KEY|GEMINI_MODEL|GEMINI_RECURSOS)=' "`$f" > "`$f.novo"
printf 'GEMINI_API_KEY=%s\nGEMINI_MODEL=%s\nGEMINI_RECURSOS=%s\n' '$chave' '$modelo' '$Recursos' >> "`$f.novo"
chmod 600 "`$f.novo"
mv "`$f.novo" "`$f"
echo gravado
"@ -replace "`r", ''
$remoto | & ssh @ssh 'sudo bash -s'
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gravar no servidor.' }

Write-Host 'Recriando a API para ler a nova configuração...'
& ssh @ssh 'quatro-dc up -d api'
if ($LASTEXITCODE -ne 0) { throw 'Falha ao recriar a API.' }

Write-Host 'Conferindo dentro do contêiner (sem mostrar a chave)...'
& ssh @ssh "sudo docker exec quatroanos-api-1 sh -c 'test -n `"`$GEMINI_API_KEY`" && echo chave-presente || echo chave-AUSENTE; echo modelo=`$GEMINI_MODEL; echo recursos=`$GEMINI_RECURSOS'"
Write-Host 'Pronto.'
