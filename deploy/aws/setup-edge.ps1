param(
    [string]$Region = "us-east-2",
    [string]$OriginStackName = "mandato-simulator",
    [string]$EdgeStackName = "mandato-edge-auth"
)

$ErrorActionPreference = "Stop"
$templatePath = Join-Path $PSScriptRoot "edge-template.yaml"
$awsCommand = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $awsCommand) {
    $knownPath = Join-Path $env:ProgramFiles "Amazon\AWSCLIV2\aws.exe"
    if (Test-Path $knownPath) { $awsCommand = $knownPath }
}
if (-not $awsCommand) { throw "AWS CLI v2 não está instalado." }

& $awsCommand sts get-caller-identity --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Autentique a AWS CLI antes de continuar." }

$instanceId = (& $awsCommand cloudformation describe-stack-resources --stack-name $OriginStackName --region $Region `
    --query "StackResources[?ResourceType=='AWS::EC2::Instance'].PhysicalResourceId | [0]" --output text).Trim()
$securityGroupId = (& $awsCommand cloudformation describe-stack-resources --stack-name $OriginStackName --region $Region `
    --query "StackResources[?ResourceType=='AWS::EC2::SecurityGroup'].PhysicalResourceId | [0]" --output text).Trim()
$originDns = (& $awsCommand ec2 describe-instances --instance-ids $instanceId --region $Region `
    --query "Reservations[0].Instances[0].PublicDnsName" --output text).Trim()
$prefixListId = (& $awsCommand ec2 describe-managed-prefix-lists --region $Region `
    --filters "Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing" `
    --query "PrefixLists[0].PrefixListId" --output text).Trim()
if (-not $instanceId -or -not $securityGroupId -or -not $originDns -or -not $prefixListId) {
    throw "Não consegui localizar o host, o grupo de segurança ou a lista de prefixos do CloudFront."
}

$secretPath = Join-Path $PSScriptRoot ".origin-secret"
if (Test-Path -LiteralPath $secretPath) {
    $originSecret = (Get-Content -LiteralPath $secretPath -Raw).Trim()
} else {
    $secretBytes = New-Object byte[] 32
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $random.GetBytes($secretBytes)
    $random.Dispose()
    $originSecret = [BitConverter]::ToString($secretBytes).Replace("-", "").ToLowerInvariant()
    [System.IO.File]::WriteAllText($secretPath, $originSecret)
}

Write-Host "Host de origem: $instanceId"
Write-Host "Publicando camada HTTPS e cadastro Cognito; os saves SQLite ficam no host atual."
& $awsCommand cloudformation deploy `
    --template-file $templatePath `
    --stack-name $EdgeStackName `
    --region $Region `
    --parameter-overrides "OriginDomainName=$originDns" "OriginSecurityGroupId=$securityGroupId" "OriginFacingPrefixListId=$prefixListId" "OriginSharedSecret=$originSecret" `
    --tags Project=mandato-simulator
if ($LASTEXITCODE -ne 0) { throw "A implantação da camada HTTPS não terminou." }

& $awsCommand cloudformation describe-stacks --stack-name $EdgeStackName --region $Region `
    --query "Stacks[0].Outputs" --output table
Write-Host "Próximo passo: executar configure-auth.ps1 para aplicar os valores públicos do Cognito no servidor."
