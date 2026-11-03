# AWS deployment

The game runs on an encrypted EC2 volume. Keep the original `mandato-simulator`
stack intact: it owns the persistent SQLite volume and the running game host.
The separate `mandato-edge-auth` stack adds CloudFront HTTPS, Cognito accounts,
and a security-group rule for CloudFront's origin-facing network. The web origin
checks a random shared header so another CloudFront distribution cannot reuse it.
The templates point back to this guide for their shared deployment rationale and
the invariants that keep the database and origin protected.

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

A consistent manual SQLite backup can be made over Session Manager with Python's
SQLite backup API. The previous deployment stores snapshots under
`/opt/mandato/backups`. A scheduled copy to a separate S3 bucket with lifecycle
and restore verification remains a follow-up before inviting other players.
The automatic deploy keeps the 30 newest pre-deploy snapshots on the same
encrypted EC2 volume; that protects deployments but is not an off-host backup.

## Automatic GitHub deployment

`.github/workflows/aws-deploy.yml` builds the browser app and runs the existing
API checks on changes to game code. On `main`, it deploys through Systems
Manager Run Command, creates a consistent SQLite backup on the host, rebuilds
the Docker Compose services, checks the API, and restores the previous code if
the health check fails. GitHub Actions receives temporary AWS credentials via
OIDC; no AWS access key is stored in the repository.

One-time account setup:

1. In CloudFormation (`us-east-2`), create a stack from
   `deploy/aws/github-actions-role.yaml`. The repository's immutable GitHub
   owner/repository IDs and the current EC2 instance ID are prefilled. If the
   IAM OIDC provider for `token.actions.githubusercontent.com` already exists,
   set `ExistingOidcProviderArn` to its ARN; otherwise leave it blank.
2. Copy the stack output `GitHubDeployRoleArn`.
3. In GitHub, open **Settings → Secrets and variables → Actions → Variables**
   and create `AWS_DEPLOY_ROLE_ARN` with that output. It is an ARN, not a
   secret credential.
4. Re-run the latest **Build and deploy Mandato** workflow, or push the next
   change to `main`. The workflow can also be started manually from **Actions**.

The role trusts only this repository's `main` ref. Its policy can send the
`AWS-RunShellScript` document only to the Mandato EC2 instance and read that
command's result. The workflow serializes deployments so two builds cannot
replace each other at the same time. If the role variable is absent, the build
still completes and GitHub reports that AWS setup is pending.

## Gemini text interpretation

The FastAPI server calls Gemini. The key stays on the server and is never sent
to the browser or stored in Git. If Gemini is unavailable, the API uses the
local interpreter; deterministic game rules still calculate the effects.

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
