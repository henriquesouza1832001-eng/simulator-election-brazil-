param(
    [string]$Region = "us-east-2",
    [string]$StackName = "mandato-simulator"
)

$ErrorActionPreference = "Stop"
$templatePath = Join-Path $PSScriptRoot "template.yaml"
$awsCommand = (Get-Command aws -ErrorAction SilentlyContinue).Source

if (-not $awsCommand) {
    $knownPath = Join-Path $env:ProgramFiles "Amazon\AWSCLIV2\aws.exe"
    if (Test-Path $knownPath) { $awsCommand = $knownPath }
}
if (-not $awsCommand) {
    throw "AWS CLI v2 is not installed. Install it and authenticate before updating the stack."
}

& $awsCommand sts get-caller-identity --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Authenticate the AWS CLI on this machine before updating the stack."
}

& $awsCommand cloudformation validate-template `
    --template-body "file://$templatePath" `
    --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "CloudFormation template validation failed; the stack was not changed."
}

$stackStatus = & $awsCommand cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].StackStatus" `
    --output text
if ($LASTEXITCODE -ne 0) {
    throw "Could not find stack '$StackName' in $Region. No stack was created."
}

$allowedStatuses = @("CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE")
if ($stackStatus.Trim() -notin $allowedStatuses) {
    throw "The stack is in '$stackStatus'. Resolve that state before applying this update."
}

$updateArgs = @(
    "cloudformation", "update-stack",
    "--stack-name", $StackName,
    "--template-body", "file://$templatePath",
    "--parameters",
    "ParameterKey=AllowedClientCidr,UsePreviousValue=true",
    "ParameterKey=InstanceType,UsePreviousValue=true",
    "ParameterKey=LatestAmiId,UsePreviousValue=true",
    "--capabilities", "CAPABILITY_IAM",
    "--region", $Region
)
$updateOutput = & $awsCommand @updateArgs 2>&1
$updateExitCode = $LASTEXITCODE
$updateMessage = $updateOutput -join [Environment]::NewLine

if ($updateExitCode -ne 0) {
    if ($updateMessage -match "No updates are to be performed") {
        Write-Host "Stack '$StackName' is already up to date."
        exit 0
    }
    throw "CloudFormation rejected the update:`n$updateMessage"
}

Write-Host "Update started. The current instance and parameters will be preserved."
& $awsCommand cloudformation wait stack-update-complete --stack-name $StackName --region $Region
if ($LASTEXITCODE -ne 0) {
    $failedStatus = & $awsCommand cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region `
        --query "Stacks[0].StackStatus" `
        --output text
    throw "The update did not complete successfully (status: $failedStatus). Check the stack events in CloudFormation."
}

& $awsCommand cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs[?OutputKey=='WeeklyBackupBucket' || OutputKey=='WeeklyBackupScheduleUtc'].[OutputKey,OutputValue]" `
    --output table
if ($LASTEXITCODE -ne 0) {
    throw "The stack updated, but its backup outputs could not be read."
}
