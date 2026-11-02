# AWS deployment

The game runs on an encrypted EC2 volume. Keep the original `mandato-simulator`
stack intact: it owns the persistent SQLite volume and the running game host.
The separate `mandato-edge-auth` stack adds CloudFront HTTPS, Cognito accounts,
and a security-group rule for CloudFront's origin-facing network. The web origin
checks a random shared header so another CloudFront distribution cannot reuse it.

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

6. Open the `GameUrl` output from `mandato-edge-auth`. The browser's login uses
   Cognito's authorization-code flow with PKCE. The public app client has no
   client secret.

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
