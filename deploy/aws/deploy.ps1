param(
    [string]$Region = "us-east-1",
    [ValidateSet("t3.micro", "t3.small")]
    [string]$InstanceType = "t3.small",
    [string]$StackName = "mandato-simulator"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$templatePath = Join-Path $PSScriptRoot "template.yaml"

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI v2 não está instalado. Instale-o e autentique sua conta antes de executar este script."
}

try {
    aws sts get-caller-identity --region $Region | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "AWS CLI sem sessão autenticada." }
} catch {
    throw "Autentique a AWS CLI nesta máquina antes do deploy. Nenhuma chave deve ser colada no chat. Detalhe: $_"
}

$clientIp = (Invoke-RestMethod -Uri "https://checkip.amazonaws.com").Trim()
if ($clientIp -notmatch '^(\d{1,3}\.){3}\d{1,3}$') {
    throw "Não consegui detectar o IPv4 público desta conexão."
}
$allowedCidr = "$clientIp/32"

Write-Host "Stack: $StackName"
Write-Host "Região: $Region"
Write-Host "Instância: $InstanceType"
Write-Host "Acesso HTTP permitido somente para: $allowedCidr"
Write-Host "O jogo será clonado do GitHub durante a inicialização da instância."

aws cloudformation deploy `
    --template-file $templatePath `
    --stack-name $StackName `
    --region $Region `
    --parameter-overrides "AllowedClientCidr=$allowedCidr" "InstanceType=$InstanceType" `
    --capabilities CAPABILITY_IAM `
    --tags Project=mandato-simulator
if ($LASTEXITCODE -ne 0) { throw "O deploy do CloudFormation falhou." }

aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs" `
    --output table
