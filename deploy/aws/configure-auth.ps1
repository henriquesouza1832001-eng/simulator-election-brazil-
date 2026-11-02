param(
    [string]$Region = "us-east-2",
    [string]$OriginStackName = "mandato-simulator",
    [string]$EdgeStackName = "mandato-edge-auth"
)

$ErrorActionPreference = "Stop"
$awsCommand = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $awsCommand) {
    $knownPath = Join-Path $env:ProgramFiles "Amazon\AWSCLIV2\aws.exe"
    if (Test-Path $knownPath) { $awsCommand = $knownPath }
}
if (-not $awsCommand) { throw "AWS CLI v2 não está instalado." }

$instanceId = (& $awsCommand cloudformation describe-stack-resources --stack-name $OriginStackName --region $Region `
    --query "StackResources[?ResourceType=='AWS::EC2::Instance'].PhysicalResourceId | [0]" --output text).Trim()
$edgeResponse = & $awsCommand cloudformation describe-stacks --stack-name $EdgeStackName --region $Region --output json
$edgeOutputs = $edgeResponse | ConvertFrom-Json
$outputs = @{}
foreach ($item in $edgeOutputs.Stacks[0].Outputs) { $outputs[$item.OutputKey] = $item.OutputValue }
$secretPath = Join-Path $PSScriptRoot ".origin-secret"
if (-not (Test-Path -LiteralPath $secretPath)) { throw "Não encontrei o segredo de origem local. Rode setup-edge.ps1 nesta mesma cópia do projeto." }
$originSecret = (Get-Content -LiteralPath $secretPath -Raw).Trim()

$envContent = @(
    "ORIGIN_SECRET=$originSecret",
    "COGNITO_REGION=$($outputs.CognitoRegion)",
    "COGNITO_USER_POOL_ID=$($outputs.CognitoUserPoolId)",
    "COGNITO_CLIENT_ID=$($outputs.CognitoClientId)",
    "COGNITO_DOMAIN=$($outputs.CognitoDomain)"
) -join "`n"
$envEncoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($envContent))
$remoteLines = @(
    "set -euo pipefail",
    "cd /opt/mandato/app",
    "git pull --ff-only origin main",
    "printf '%s' '$envEncoded' | base64 -d > .env",
    "set -a; source .env; set +a",
    "chmod 600 .env",
    "docker compose up -d --build",
    "for i in `$(seq 1 25); do",
    '  if curl -fsS -H "X-Origin-Verify: $ORIGIN_SECRET" http://localhost/api/health; then break; fi',
    "  sleep 2",
    "done",
    'curl -fsS -H "X-Origin-Verify: $ORIGIN_SECRET" http://localhost/api/auth/config',
    "docker compose ps"
)
$payload = @{ DocumentName = "AWS-RunShellScript"; InstanceIds = @($instanceId); Parameters = @{ commands = $remoteLines }; Comment = "Ativar HTTPS, autenticacao e isolamento de saves do Mandato" }
$payloadPath = Join-Path $env:TEMP "mandato-configure-auth.json"
[System.IO.File]::WriteAllText($payloadPath, ($payload | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
$commandId = (& $awsCommand ssm send-command --region $Region --cli-input-json "file://$payloadPath" --query "Command.CommandId" --output text).Trim()
Write-Host "Aplicando configuração segura no servidor..."
for ($attempt = 0; $attempt -lt 36; $attempt++) {
    Start-Sleep -Seconds 5
    $status = (& $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId --region $Region --query "Status" --output text).Trim()
    if ($status -eq "Success") {
        & $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId --region $Region --query "StandardOutputContent" --output text
        Write-Host "Pronto. Abra $($outputs.GameUrl) para entrar ou criar a conta."
        exit 0
    }
    if ($status -in @("Failed", "Cancelled", "TimedOut")) {
        & $awsCommand ssm get-command-invocation --command-id $commandId --instance-id $instanceId --region $Region --query "StandardErrorContent" --output text
        throw "A configuração do servidor terminou com status $status."
    }
}
throw "A configuração continua rodando no SSM; consulte o comando $commandId no console AWS."
