# AWS deployment runbook — not executed

## Review before creating resources

The current `berlinbite-dev` login has sign-in permission only. An administrator must grant a scoped deployment policy for the resources defined here: EC2 networking, ECS/Fargate, ECR, ELBv2, CloudFront, WAFv2, CloudWatch Logs/alarms, Application Auto Scaling, Secrets Manager and project IAM roles. `iam:PassRole` must be limited to `berlinbite-execution` and ECS tasks. Service-linked role creation may also be necessary. Do not attach blanket AdministratorAccess just to suppress errors. Verify the exact Terraform plan with a suitably scoped deployment role before applying.

Deployment is paused until the user approves the concrete plan, expected costs and public exposure. This runbook is not authorization to apply it.

## Costs and security tradeoffs

This is an always-on two-task baseline, not a free-tier promise. Budget for two 0.25-vCPU/0.5-GB Fargate tasks, load balancer hours and capacity, public IPv4 addresses, WAF ACL/rule/requests, ECR, two secrets, logs, CloudFront/transfer, and separately Google/OpenAI calls. Calculate a current regional estimate using the AWS Pricing Calculator before approval. Reducing `min_tasks` to 1 saves compute but loses the two-task availability baseline. Public subnets avoid NAT Gateway charges. Resource costs begin during the first bootstrap apply even though the app is disabled.

The viewer URL uses CloudFront HTTPS. The origin hop uses HTTP and must be upgraded with a domain and ACM ALB certificate if end-to-end encryption is required. ALB ingress is restricted to CloudFront prefix ranges and a per-deployment origin header. WAF rate limits requests by viewer IP; app-level rate limits are only a backstop. This does not impose a hard provider spending cap. Set provider quotas/billing alerts independently.

## Authentication compatibility

Use the named profile. If the installed Terraform AWS SDK cannot read `aws login` profiles, configure a separate process profile without exposing credentials:

```bash
aws configure set credential_process 'aws configure export-credentials --profile berlinbite --format process' --profile berlinbite-terraform
aws configure set region eu-central-1 --profile berlinbite-terraform
export AWS_PROFILE=berlinbite-terraform
```

Do not run the export-credentials command by itself; it prints credentials. Never copy those into Terraform files.

## Bootstrap, secrets and image

From the repository root, after review and approval:

```bash
terraform -chdir=terraform init
terraform -chdir=terraform validate
terraform -chdir=terraform plan -out=bootstrap.tfplan
terraform -chdir=terraform apply bootstrap.tfplan
python3 scripts/store_aws_secrets.py
```

Bootstrap creates the infrastructure but no ECS application tasks (`deploy_app=false`). Copy the ECR repository URL from `terraform -chdir=terraform output -raw repository_url`. Substitute it below, and replace `REGISTRY` with the hostname part of that URL:

```bash
aws ecr get-login-password --profile berlinbite --region eu-central-1 | docker login --username AWS --password-stdin REGISTRY
docker buildx build --platform linux/amd64 -t REPOSITORY_URL:v1 --push .
terraform -chdir=terraform plan -var='deploy_app=true' -var='image_tag=v1' -out=deploy.tfplan
terraform -chdir=terraform apply deploy.tfplan
terraform -chdir=terraform output -raw app_url
```

Tags are immutable. Use a fresh version for each release and keep the previous one for rollback. The image must exist and both secrets must have values before enabling app tasks. Save `deploy_app=true` and the selected tag in an ignored `terraform.tfvars` for later plans, so a default plan does not propose removing the service.

## Verify before declaring completion

- Wait for ECS service stability and healthy ALB targets.
- Open the HTTPS output URL on desktop and mobile.
- Confirm `/api/health` responds and HTTP redirects to HTTPS.
- Search for a real Berlin restaurant and confirm the selected address.
- Test unavailable Google/OpenAI credentials and provider timeouts safely.
- Confirm unknown language/reservation data remains labelled unknown.
- Save and reopen a place; verify only IDs are stored in local storage.
- Inspect CloudWatch errors and verify the alarm. No notification destination is configured yet.
- Capture actual screenshots and outputs for the portfolio. Record timestamps and deployment version.
- Complete operator identity/contact/privacy details before public launch.

## Rotation, rollback and cleanup

Rotate API keys through Secrets Manager using the script, then force a new ECS deployment so tasks load the new values. Roll back by redeploying a known-good immutable image tag.

Review `terraform plan -destroy` before cleanup. ECR refuses deletion while images remain; deliberately remove only this project's images after retaining any needed evidence. Secrets have a recovery window. Local Terraform state contains infrastructure identifiers and the origin header; keep it private. For shared work, migrate to an encrypted, access-controlled remote state backend with locking.
