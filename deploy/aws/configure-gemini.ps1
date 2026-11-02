param(
    [string]$Region = "us-east-2",
    [string]$StackName = "mandato-simulator",
    [string]$ParameterName = "/mandato/production/gemini-api-key"
)

$ErrorActionPreference = "Stop"
$awsCommand = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $awsCommand) {
    $knownPath = Join-Path $env:ProgramFiles "Amazon\AWSCLIV2\aws.exe"
    if (Test-Path $knownPath) { $awsCommand = $knownPath }
}
if (-not $awsCommand) { throw "AWS CLI v2 não está instalado nesta máquina." }
if ($Region -notmatch '^[a-z0-9-]+$') { throw "Região AWS inválida." }
if ($ParameterName -notmatch '^/[A-Za-z0-9/_-]{1,200}$') { throw "Nome de parâmetro AWS inválido." }

& $awsCommand sts get-caller-identity --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Autentique a AWS CLI antes de continuar." }

$instanceId = (& $awsCommand cloudformation describe-stack-resources --stack-name $StackName --region $Region `
    --query "StackResources[?ResourceType=='AWS::EC2::Instance'].PhysicalResourceId | [0]" --output text).Trim()
if (-not $instanceId -or $instanceId -eq "None") { throw "Não encontrei a instância EC2 na stack $StackName." }

$pythonPayload = @'
python3 - "$secret_file" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
parameter = record.get("Parameter", {})
if parameter.get("Type") != "SecureString":
    raise SystemExit("O parâmetro deve ser criado como SecureString.")
key = parameter.get("Value", "").strip()
if not key or len(key) > 512 or re.search(r"[\r\n\x00]", key):
    raise SystemExit("O parâmetro Gemini está vazio ou em formato inválido.")

target = Path("/opt/mandato/app/.gemini.env")
target.write_text(f"GEMINI_API_KEY={key}\nGEMINI_MODEL=gemini-3.8-flash\n", encoding="utf-8")
os.chmod(target, 0o600)
PY
'@

$remoteLines = @(
    "set -euo pipefail",
    "cd /opt/mandato/app",
    "git pull --ff-only origin main",
    "umask 077",
    'secret_file="$(mktemp)"',
    'trap ''rm -f "$secret_file"'' EXIT',
    "aws ssm get-parameter --region $Region --name $ParameterName --with-decryption --output json > `"`$secret_file`"",
    $pythonPayload,
    "docker compose up -d --build api",
    "docker compose exec -T api python -c 'import os,sys; sys.exit(0 if os.getenv(`"GEMINI_API_KEY`") else 1)'",
    "echo 'Gemini configurado no contêiner da API.'",
    "docker compose ps api"
)

$payload = @{
    DocumentName = "AWS-RunShellScript"
    InstanceIds = @($instanceId)
    Parameters = @{ commands = $remoteLines }
    Comment = "Configurar a chave Gemini a partir do Parameter Store"
}
$payloadPath = Join-Path $env:TEMP "mandato-configure-gemini.json"
[System.IO.File]::WriteAllText($payloadPath, ($payload | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
$commandId = (& $awsCommand ssm send-command --region $Region --cli-input-json "file://$payloadPath" `
    --query "Command.CommandId" --output text).Trim()
Write-Host "Lendo o segredo do Parameter Store e atualizando apenas a API; a chave não será exibida."

for ($attempt = 0; $attempt -lt 36; $attempt++) {
    Start-Sleep -Seconds 5
    $status = (& $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId `
        --region $Region --query "Status" --output text).Trim()
    if ($status -eq "Success") {
        & $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId `
            --region $Region --query "StandardOutputContent" --output text
        Write-Host "Configuração concluída. A primeira prévia de medida confirma a chamada ao Gemini; falhas do serviço usam o interpretador local."
        exit 0
    }
    if ($status -in @("Failed", "Cancelled", "TimedOut")) {
        & $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId `
            --region $Region --query "StandardErrorContent" --output text
        throw "A configuração do Gemini terminou com status $status."
    }
}

throw "A configuração continua rodando no SSM; consulte o comando $commandId no console AWS."
