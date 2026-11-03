# AWS deployment

The game runs on an encrypted EC2 volume. Keep the original `mandato-simulator`
stack intact: it owns the persistent SQLite volume and the running game host.
The separate `mandato-edge-auth` stack adds CloudFront HTTPS, Cognito accounts,
and a security-group rule for CloudFront's origin-facing network. The web origin
checks a random shared header so another CloudFront distribution cannot reuse it.
The optional `mandato-weekly-backups` stack attaches scoped S3 access to the
existing instance role and adds a scheduled SSM association; it never modifies
the EC2 resource. Each template documents its deployment boundary here.

## First setup

1. Authenticate AWS CLI v2 in `us-east-2`.
2. Deploy the EC2 stack if it does not exist:

   ```powershell
   .\deploy.ps1 -Region us-east-2 -InstanceType t3.small
   ```

3. Publish the repository's current `main` branch. The game host pulls it during
   the next update.
4. Add HTTPS, account login, and the CloudFront-only ingress rule:

   ```powershell
   .\setup-edge.ps1 -Region us-east-2
   ```

5. Apply the Cognito identifiers and origin secret to the existing host through
   Systems Manager:

   ```powershell
   .\configure-auth.ps1 -Region us-east-2
   ```

6. Open the `GameUrl` output from `mandato-edge-auth`. The browser uses Cognito
   SRP authentication for email/password and the app client has no client secret.
   New accounts are auto-confirmed by a pre-sign-up Lambda without marking the
   email as verified. Players can optionally verify it in **Conta** to enable
   password recovery. This tradeoff matches the single-player prototype; enable
   verified email or an administrator approval flow before opening registration
   to a public audience.

The random origin secret is saved in the ignored local file `.origin-secret`.
Keep it in the same trusted deployment workspace for future updates. Never add
it to GitHub or paste it in chat. The server receives it over Systems Manager;
the CloudFront origin sends it on every request.

## Player data and operations

Player identity comes from the verified Cognito token `sub`; the API never trusts
a player ID from the browser. Game state, actions, and learning corrections are
partitioned by that identity. The database is a Docker volume on the encrypted
EC2 root disk and remains separate from Cognito. Back up the SQLite file before
changing either stack. The edge stack retains the Cognito user pool on deletion.

No SSH port is open. Manage the instance through Session Manager. The original
stack's ingress still contains the creator's IPv4 allowlist; the app's origin
header rejects direct requests after `configure-auth.ps1` runs. The added
CloudFront ingress allows HTTPS visitors to reach the site without opening the
origin to arbitrary networks.

## Backups

Weekly recovery lives in the separate `mandato-weekly-backups` CloudFormation
stack. It deliberately does not update the main `mandato-simulator` stack:
CloudFormation reports the main stack's EC2 `UserData` as a conditional
replacement, so keep backup resources separate from the persistent game host.

Preview the new stack before applying it:

```powershell
.\backup-stack.ps1 -Region us-east-2 -PreviewOnly
```

The script resolves the existing EC2 instance and role from
`mandato-simulator`, validates the backup template, and creates a change set.
It refuses any plan containing an EC2 instance change. Review the printed
resource plan; run the same command without `-PreviewOnly` to create the backup
bucket and schedule.

A consistent SQLite snapshot then runs every Sunday at 13:00 UTC (10:00 in
Brasília) through Systems Manager State Manager. It uses Python's SQLite backup
API from the API container, verifies the core save tables and `PRAGMA
integrity_check`, saves the upload temporarily under
`/opt/mandato/backups/weekly`, and sends it to the private S3 bucket. A failed
upload leaves its local copy for recovery; successful runs prune local copies
older than 35 days.

The bucket blocks public access, enforces TLS, uses S3-managed server-side
encryption, and has versioning. S3 Lifecycle expires weekly snapshots after 90
days, then removes noncurrent versions and expired delete markers; incomplete
multipart uploads are aborted after seven days. The EC2 role can read and write
objects only under `weekly/`; the application container receives no AWS
credentials. The bucket is retained if the stack is deleted, so delete it only
after intentionally transferring or removing its backups.

The first automatic upload occurs at the next scheduled Sunday run. Run the
SSM association once manually after deployment to verify the upload before
relying on the weekly schedule.

To restore from Session Manager, list available files with
`aws s3 ls s3://<bucket-from-CloudFormation-output>/weekly/ --region us-east-2`,
then run:

```bash
sudo bash /opt/mandato/app/deploy/aws/restore-weekly-backup.sh \
  s3://<bucket-from-CloudFormation-output>/weekly/game-<timestamp>.sqlite3
```

The script verifies database integrity and required save tables, makes a consistent pre-restore copy,
stops the API only for the replacement, and restarts it afterward. Keep the
pre-restore file until the game has loaded correctly. This same S3 object can be
downloaded before moving the game to a different host.

The automatic deploy also keeps the 30 newest pre-deploy snapshots on the same
encrypted EC2 volume; those protect code updates but are not off-host backups.
The S3 cost depends mainly on the database size and the 90-day retained volume,
plus one upload request per week. Check actual storage and request charges in
AWS Billing; the [S3 pricing page](https://aws.amazon.com/s3/pricing/) lists the
current pricing dimensions. The weekly snapshots remain in S3 Standard for
immediate recovery, without Glacier retrieval delays or lifecycle transition
charges.

## Automatic GitHub deployment

`.github/workflows/aws-deploy.yml` builds the browser app and runs the existing
API checks on changes to game code. On `main`, it deploys through Systems
Manager Run Command, creates a consistent SQLite backup on the host, rebuilds
the Docker Compose services, checks the API, and restores the previous code if
the health check fails. GitHub Actions receives temporary AWS credentials via
OIDC; no AWS access key is stored in the repository.

One-time account setup:

Run this one-time setup from an authenticated local shell with AWS CLI v2 and
GitHub CLI:

```powershell
.\deploy\aws\setup-github-deploy.ps1 -Region us-east-2
```

The script finds the current EC2 instance in `mandato-simulator`, reuses the
GitHub OIDC provider if one already exists, creates or updates the restricted
CloudFormation role, stores its ARN in the repository variable
`AWS_DEPLOY_ROLE_ARN`, and dispatches the first deployment. Use
`-SkipDispatch` to configure the connection without deploying immediately.
The script never sends AWS keys to GitHub; the ARN is an identifier, not a
credential. To perform the steps manually instead, create a stack from
`deploy/aws/github-actions-role.yaml`, copy its `GitHubDeployRoleArn` output,
and add it under **Settings → Secrets and variables → Actions → Variables**.

The role trusts only this repository's `main` ref. Its policy can send the
`AWS-RunShellScript` document only to the Mandato EC2 instance and read that
command's result. The workflow serializes deployments so two builds cannot
replace each other at the same time. If the role variable is absent, the build
still completes and GitHub reports that AWS setup is pending.

## Gemini text interpretation

The FastAPI server calls Gemini. The key stays on the server and is never sent
to the browser or stored in Git. If Gemini is unavailable, the API uses the
local interpreter; deterministic game rules still calculate the effects.
In production on 3 November 2026, `/api/health` reports `local-fallback` because
no Gemini key is configured. The decision screen now labels this state as
**Motor local** and changes to **Gemini configurado** when the server has a key;
neither label claims that a particular request succeeded.

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
   Restrict it to the Gemini API when that option is available. Do not put the
   key in GitHub or send it in chat.
2. In AWS Console, open **Systems Manager → Parameter Store → Create parameter**.
   Use `/mandato/production/gemini-api-key` as the name, **SecureString** as the
   type, **Standard** as the tier, and the default `alias/aws/ssm` encryption
   key. Standard parameters have no monthly storage charge.
3. Publish the updated `main` branch, then run this from PowerShell with AWS CLI
   authenticated to the account:

   ```powershell
   .\configure-gemini.ps1 -Region us-east-2
   ```

The script retrieves the parameter on EC2, writes an ignored `.gemini.env` file
with owner-only permissions, rebuilds only the API container, and does not print
the key. The `/api/health` route reports whether a key is configured; the first
measure preview confirms that the Gemini API call works.

The instance already uses AWS's `AmazonSSMManagedInstanceCore` policy, which
permits the instance to read SSM parameters. That existing policy is broader
than this Gemini parameter, so keep other secrets out of Parameter Store in
this account. Before opening the server to other users or workloads, replace
that broad read permission with a policy scoped to this parameter.
