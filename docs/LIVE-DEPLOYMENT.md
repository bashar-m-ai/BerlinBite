# Verified AWS deployment

URL: https://d2siyf6buflqzp.cloudfront.net

Verified 24 September 2026: homepage 200, health 200, Google search 200, restaurant details 200 with website present, insight 200 with AI-generated general advice. Two desired ECS tasks, two running, none pending. Image tag v2.

Terraform provisioned the infrastructure. CloudFront cache policy ID was corrected during deployment and required IAM reads were added. The task definition was reused after the initial lookup permission failure.

User reviewed the local interface; no automated browser visual or load test is claimed. Google/OpenAI charges are separate from AWS credits. AWS uses the account's eligible credits; keep track of the remaining balance. Origin traffic from CloudFront to ALB is HTTP, as documented.
