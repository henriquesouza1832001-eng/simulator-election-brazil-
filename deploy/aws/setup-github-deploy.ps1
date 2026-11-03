param(
    [string]$Region = "us-east-2",
    [string]$OriginStackName = "mandato-simulator",
    [string]$DeployStackName = "mandato-github-deploy",
    [string]$Repository = "henriquesouza1832001-eng/simulator-election-brazil-",
    [switch]$SkipDispatch
)

$ErrorActionPreference = "Stop"
$awsCommand = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $awsCommand) {
    $knownPaths = @(
        (Join-Path $env:ProgramFiles "Amazon\AWSCLIV2\aws.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Amazon\AWSCLIV2\aws.exe")
    )
    $awsCommand = $knownPaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $awsCommand) {
    throw "AWS CLI v2 não está instalado. Instale e autentique a CLI antes de configurar o deploy."
}

$ghCommand = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $ghCommand) { throw "GitHub CLI não está instalado. Instale e autentique com gh auth login." }
& $ghCommand auth status --hostname github.com | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Autentique a GitHub CLI e tente novamente. A AWS ainda não foi alterada." }
& $ghCommand repo view $Repository --json nameWithOwner | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Não consegui acessar o repositório $Repository com a GitHub CLI. A AWS ainda não foi alterada." }
$repositoryJson = & $ghCommand api "repos/$Repository"
if ($LASTEXITCODE -ne 0) { throw "Não consegui ler a identificação do repositório. A AWS ainda não foi alterada." }
$repositoryInfo = $repositoryJson | ConvertFrom-Json
$oidcJson = & $ghCommand api "repos/$Repository/actions/oidc/customization/sub"
if ($LASTEXITCODE -ne 0) { throw "Não consegui verificar a configuração OIDC do repositório. A AWS ainda não foi alterada." }
$oidcSettings = $oidcJson | ConvertFrom-Json
if (-not $oidcSettings.use_default -or -not $oidcSettings.use_immutable_subject) {
    throw "O template de deploy exige o subject OIDC padrão imutável. Ative essa opção nas configurações OIDC do repositório antes de continuar."
}

$identityJson = & $awsCommand sts get-caller-identity --region $Region --output json
if ($LASTEXITCODE -ne 0) { throw "Autentique a AWS CLI antes de configurar o deploy." }
$identity = $identityJson | ConvertFrom-Json
Write-Host "Conta AWS autenticada: $($identity.Account) · $($identity.Arn)"

$instanceId = (& $awsCommand cloudformation describe-stack-resources `
    --stack-name $OriginStackName `
    --region $Region `
    --query "StackResources[?ResourceType=='AWS::EC2::Instance'].PhysicalResourceId | [0]" `
    --output text).Trim()
if ($LASTEXITCODE -ne 0 -or $instanceId -notmatch '^i-[a-f0-9]+$') {
    throw "Não encontrei uma instância EC2 na stack '$OriginStackName' em $Region. Nenhuma role foi criada."
}

$providersJson = & $awsCommand iam list-open-id-connect-providers --output json
if ($LASTEXITCODE -ne 0) { throw "Não foi possível consultar os provedores OIDC existentes. Nenhuma role foi criada." }
$provider = (($providersJson | ConvertFrom-Json).OpenIDConnectProviderList |
    Where-Object { $_.Arn.EndsWith('/token.actions.githubusercontent.com') } |
    Select-Object -First 1).Arn

$stackProbe = & $awsCommand cloudformation describe-stacks --stack-name $DeployStackName --region $Region --output json 2>$null
$deployStackExists = $LASTEXITCODE -eq 0
$stackOwnsProvider = $false
if ($deployStackExists) {
    $stackResources = & $awsCommand cloudformation describe-stack-resources --stack-name $DeployStackName --region $Region --output json
    if ($LASTEXITCODE -ne 0) { throw "Não consegui conferir os recursos da stack '$DeployStackName'. Nenhuma stack foi alterada." }
    $stackOwnsProvider = [bool](($stackResources | ConvertFrom-Json).StackResources |
        Where-Object { $_.LogicalResourceId -eq "GitHubOidcProvider" })
}

$templatePath = Join-Path $PSScriptRoot "github-actions-role.yaml"
& $awsCommand cloudformation validate-template --template-body "file://$templatePath" --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { throw "A validação do template da role falhou. Nenhuma stack foi alterada." }

$deployArgs = @(
    "cloudformation", "deploy",
    "--template-file", $templatePath,
    "--stack-name", $DeployStackName,
    "--region", $Region,
    "--capabilities", "CAPABILITY_NAMED_IAM",
    "--parameter-overrides",
    "InstanceId=$instanceId",
    "GitHubOwner=$($repositoryInfo.owner.login)",
    "GitHubOwnerId=$($repositoryInfo.owner.id)",
    "GitHubRepository=$($repositoryInfo.name)",
    "GitHubRepositoryId=$($repositoryInfo.id)",
    "--tags", "Project=mandato-simulator"
)
if ($provider -and -not $stackOwnsProvider) { $deployArgs += "ExistingOidcProviderArn=$provider" }
Write-Host "Criando/atualizando a role de deploy para a instância $instanceId..."
& $awsCommand @deployArgs
if ($LASTEXITCODE -ne 0) { throw "A stack IAM não terminou com sucesso. Confira os eventos de '$DeployStackName' no CloudFormation." }

$roleArn = (& $awsCommand cloudformation describe-stacks `
    --stack-name $DeployStackName `
    --region $Region `
    --query "Stacks[0].Outputs[?OutputKey=='GitHubDeployRoleArn'].OutputValue | [0]" `
    --output text).Trim()
if ($LASTEXITCODE -ne 0 -or $roleArn -notmatch '^arn:aws:iam::[0-9]{12}:role/mandato-github-deploy$') {
    throw "A stack não retornou o ARN esperado da role. A variável do GitHub não foi alterada."
}

& $ghCommand variable set AWS_DEPLOY_ROLE_ARN --body $roleArn --repo $Repository
if ($LASTEXITCODE -ne 0) { throw "A role foi criada, mas não consegui gravar AWS_DEPLOY_ROLE_ARN. Confira gh auth status e as permissões do repositório." }
Write-Host "Role cadastrada como variável do repositório $Repository. Nenhuma chave AWS foi enviada ao GitHub."

if (-not $SkipDispatch) {
    & $ghCommand workflow run aws-deploy.yml --repo $Repository --ref main
    if ($LASTEXITCODE -ne 0) { throw "A role e a variável estão prontas, mas não consegui disparar o workflow." }
    Write-Host "Deploy disparado. Acompanhe 'Build and deploy Mandato' na aba Actions do GitHub."
} else {
    Write-Host "Configuração concluída. O próximo push na main fará o deploy automaticamente."
}
