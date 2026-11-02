# AWS EC2 deploy

This stack creates a small EC2 host, an isolated VPC, an encrypted persistent
root volume, and a security group that allows HTTP only from the public IPv4
detected on the machine running the script. It does not open SSH; the instance
has an SSM role for administration from the AWS console.

The instance clones the public `main` branch from GitHub and starts the existing
Docker Compose app. It serves plain HTTP on port 80, so it is intended for
single-user access behind the IP allowlist. If your public IP changes, update
the `AllowedClientCidr` parameter in the stack to the new address plus `/32`.

## Deploy

1. Create/activate the AWS account and authenticate AWS CLI v2 locally.
2. From this directory run:

   ```powershell
   .\deploy.ps1 -Region us-east-1 -InstanceType t3.small
   ```

3. Wait for CloudFormation to finish, then open the `GameUrl` stack output.
   The first Docker build can take several minutes. If startup fails, inspect
   `/var/log/cloud-init-output.log` through Systems Manager Session Manager.

The SQLite save is stored in a Docker volume on the encrypted EC2 root EBS
volume. `DeleteOnTermination` is disabled for that volume; deleting the stack
does not automatically remove the disk, so delete or snapshot it deliberately.

The project database is not uploaded from the developer machine. The instance
starts with a fresh game save. Create independent backups after first launch.
