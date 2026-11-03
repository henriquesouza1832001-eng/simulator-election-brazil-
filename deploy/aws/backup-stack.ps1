param(
    [string]$Region = "us-east-2",
    [string]$OriginStackName = "mandato-simulator",
    [string]$BackupStackName = "mandato-weekly-backups",
    [switch]$PreviewOnly
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
if (-not $awsCommand) { throw "AWS CLI v2 is not installed. Authenticate before creating the backup stack." }

& $awsCommand sts get-caller-identity --region $Region --output json | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Authenticate the AWS CLI before continuing." }

$originStatus = & $awsCommand cloudformation describe-stacks --stack-name $OriginStackName --region $Region --query "Stacks[0].StackStatus" --output text
if ($LASTEXITCODE -ne 0 -or $originStatus.Trim() -notin @("CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE")) {
    throw "The existing game stack '$OriginStackName' is unavailable or not stable. No resources were changed."
}

$resourceOutput = & $awsCommand cloudformation describe-stack-resources --stack-name $OriginStackName --region $Region --output json
if ($LASTEXITCODE -ne 0) { throw "Could not read resources from '$OriginStackName'." }
$resources = ($resourceOutput | ConvertFrom-Json).StackResources
$gameInstance = $resources | Where-Object LogicalResourceId -eq "GameInstance" | Select-Object -First 1
$instanceRole = $resources | Where-Object LogicalResourceId -eq "InstanceRole" | Select-Object -First 1
if (-not $gameInstance -or $gameInstance.PhysicalResourceId -notmatch '^i-[0-9a-f]+$') { throw "Could not resolve the existing game EC2 instance." }
if (-not $instanceRole -or $instanceRole.PhysicalResourceId -notmatch '^[A-Za-z0-9+=,.@_-]{1,64}$') { throw "Could not resolve the existing EC2 instance role." }

$templatePath = Join-Path $PSScriptRoot "backup-template.yaml"
& $awsCommand cloudformation validate-template --template-body "file://$templatePath" --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Backup CloudFormation validation failed; no stack was changed." }

$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$backupProbe = & $awsCommand cloudformation describe-stacks --stack-name $BackupStackName --region $Region --output json 2>$null
$backupProbeExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorAction
$backupStackExists = $backupProbeExitCode -eq 0
$changeSetType = if ($backupStackExists) { "UPDATE" } else { "CREATE" }
if ($backupStackExists) {
    $backupStatus = ($backupProbe | ConvertFrom-Json).Stacks[0].StackStatus
    if ($backupStatus -notin @("CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE")) {
        throw "Backup stack '$BackupStackName' is in '$backupStatus'. Resolve that state before retrying."
    }
}

$changeSetName = "weekly-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$createArgs = @(
    "cloudformation", "create-change-set",
    "--stack-name", $BackupStackName,
    "--change-set-name", $changeSetName,
    "--change-set-type", $changeSetType,
    "--template-body", "file://$templatePath",
    "--parameters",
    "ParameterKey=InstanceId,ParameterValue=$($gameInstance.PhysicalResourceId)",
    "ParameterKey=InstanceRoleName,ParameterValue=$($instanceRole.PhysicalResourceId)",
    "--capabilities", "CAPABILITY_IAM",
    "--description", "Weekly SQLite backup resources for the existing game instance only.",
    "--tags", "Key=Project,Value=mandato-simulator",
    "--region", $Region,
    "--query", "Id",
    "--output", "text"
)
$changeSetArn = & $awsCommand @createArgs
if ($LASTEXITCODE -ne 0 -or -not $changeSetArn) { throw "Could not create the backup change set." }

for ($attempt = 0; $attempt -lt 60; $attempt++) {
    $changeSetOutput = & $awsCommand cloudformation describe-change-set --change-set-name $changeSetName --stack-name $BackupStackName --region $Region --output json
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect the backup change set '$changeSetName'." }
    $changeSet = $changeSetOutput | ConvertFrom-Json
    if ($changeSet.Status -in @("CREATE_COMPLETE", "FAILED")) { break }
    Start-Sleep -Seconds 5
}

if ($changeSet.Status -eq "FAILED") {
    if ($changeSet.StatusReason -match "didn't contain changes|No updates are to be performed") {
        Write-Host "Backup stack '$BackupStackName' is already up to date."
        exit 0
    }
    throw "Backup change set failed validation: $($changeSet.StatusReason)"
}
if ($changeSet.Status -ne "CREATE_COMPLETE") { throw "Backup change set is still in '$($changeSet.Status)' after five minutes." }

$unexpectedInstanceChange = @($changeSet.Changes | Where-Object { $_.ResourceChange.ResourceType -eq "AWS::EC2::Instance" })
if ($unexpectedInstanceChange.Count -gt 0) { throw "Refusing to proceed: the separate backup stack unexpectedly contains an EC2 instance change." }

Write-Host "Proposed backup stack changes (the existing EC2 instance is not in this stack):"
$changeSet.Changes | ForEach-Object {
    Write-Host ("  {0,-8} {1,-28} {2}" -f $_.ResourceChange.Action, $_.ResourceChange.LogicalResourceId, $_.ResourceChange.ResourceType)
}
Write-Host "Change set: $changeSetName"
if ($PreviewOnly) {
    Write-Host "Preview only; no AWS resources were created or updated."
    exit 0
}

& $awsCommand cloudformation execute-change-set --change-set-name $changeSetName --stack-name $BackupStackName --region $Region
if ($LASTEXITCODE -ne 0) { throw "Could not execute the reviewed backup change set." }
if ($changeSetType -eq "CREATE") {
    & $awsCommand cloudformation wait stack-create-complete --stack-name $BackupStackName --region $Region
} else {
    & $awsCommand cloudformation wait stack-update-complete --stack-name $BackupStackName --region $Region
}
if ($LASTEXITCODE -ne 0) { throw "Backup stack deployment did not complete. Inspect CloudFormation events before retrying." }

& $awsCommand cloudformation describe-stacks --stack-name $BackupStackName --region $Region --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" --output table
