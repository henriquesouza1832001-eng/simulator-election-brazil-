param(
    [string]$Region = "us-east-2",
    [string]$StackName = "mandato-simulator",
    [string]$InstanceId,
    [switch]$Disable
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
if (-not $awsCommand) { throw "AWS CLI v2 is required. Authenticate to the game account before continuing." }

& $awsCommand sts get-caller-identity --region $Region --output json | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Authenticate the AWS CLI before changing the game host." }
if (-not $InstanceId) {
    $InstanceId = (& $awsCommand cloudformation describe-stack-resources `
        --stack-name $StackName `
        --region $Region `
        --query "StackResources[?LogicalResourceId=='GameInstance'].PhysicalResourceId | [0]" `
        --output text).Trim()
    if ($LASTEXITCODE -ne 0 -or $InstanceId -notmatch '^i-[a-f0-9]+$') {
        throw "Could not resolve the game instance from '$StackName'. No change was sent."
    }
}

if ($Disable) {
    $commands = @(
        "sudo systemctl disable --now mandato-auto-deploy.timer",
        "sudo systemctl is-active mandato-auto-deploy.timer || true"
    )
} else {
    $commands = @(
        "set -euo pipefail",
        "test -x /opt/mandato/app/deploy/aws/auto-deploy-check.sh",
        "install -m 0644 /opt/mandato/app/deploy/aws/mandato-auto-deploy.service /etc/systemd/system/mandato-auto-deploy.service",
        "install -m 0644 /opt/mandato/app/deploy/aws/mandato-auto-deploy.timer /etc/systemd/system/mandato-auto-deploy.timer",
        "install -d -m 0700 /var/lib/mandato",
        "if [ ! -s /var/lib/mandato/auto-deploy-last-checked ]; then git -C /opt/mandato/app rev-parse HEAD > /var/lib/mandato/auto-deploy-last-checked; chmod 600 /var/lib/mandato/auto-deploy-last-checked; fi",
        "systemctl daemon-reload",
        "systemctl enable --now mandato-auto-deploy.timer",
        "systemctl is-enabled mandato-auto-deploy.timer",
        "systemctl is-active mandato-auto-deploy.timer"
    )
}

$inputPath = Join-Path $env:TEMP ("mandato-auto-deploy-" + [guid]::NewGuid().ToString("N") + ".json")
$payload = @{
    DocumentName = "AWS-RunShellScript"
    InstanceIds = @($InstanceId)
    Comment = if ($Disable) { "Disable Mandato automatic deployment timer" } else { "Install Mandato CI-gated automatic deployment timer" }
    Parameters = @{ commands = $commands }
} | ConvertTo-Json -Depth 6 -Compress
[System.IO.File]::WriteAllText($inputPath, $payload, [System.Text.UTF8Encoding]::new($false))
try {
    $sendResult = & $awsCommand ssm send-command --region $Region --cli-input-json ("file://" + $inputPath) --output json
    if ($LASTEXITCODE -ne 0) { throw "SSM could not send the host configuration command." }
    $commandId = ($sendResult | ConvertFrom-Json).Command.CommandId
    if (-not $commandId) { throw "SSM did not return a command ID." }
    Write-Host "SSM command: $commandId"
    & $awsCommand ssm wait command-executed --region $Region --command-id $commandId --instance-id $InstanceId
    $status = & $awsCommand ssm get-command-invocation --region $Region --command-id $commandId --instance-id $InstanceId --query Status --output text
    if ($LASTEXITCODE -ne 0) { throw "Could not read the SSM command result." }
    if ($status.Trim() -ne "Success") {
        throw "Host configuration ended with status '$($status.Trim())'. Read its details with AWS Systems Manager Run Command."
    }
    Write-Host "Automatic deployment timer is enabled and active on $InstanceId."
} finally {
    Remove-Item -LiteralPath $inputPath -Force -ErrorAction SilentlyContinue
}
