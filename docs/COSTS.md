# AWS cost worksheet — estimate, not a spending cap

Checked 24 September 2026 against AWS public Frankfurt price-list data. Assumes Linux x86 Fargate, 730 hours/month, two tasks, 0.25 vCPU and 0.5 GB per task, one ALB, two task public IPv4 addresses and at least two ALB public IPv4 addresses. Taxes, credits and currency conversion are excluded.

| Component | Calculation | Monthly USD |
|---|---|---:|
| Fargate vCPU | 2 × 0.25 × 730 × $0.04656 | 16.99 |
| Fargate memory | 2 × 0.5 × 730 × $0.00511 | 3.73 |
| ALB base | 730 × $0.027 | 19.71 |
| Public IPv4 baseline | 4 × 730 × $0.005 | 14.60 |
| WAF ACL + one rule | $5 + $1 | 6.00 |
| Subtotal of listed baseline items | Rounded | **61.03** |

Additional charges: ALB capacity ($0.008 per LCU-hour), WAF requests, Secrets Manager, CloudWatch, ECR image storage, CloudFront and data transfer, plus Google Places and OpenAI usage. More tasks/IPs during scaling and rolling deployments increase costs. This subtotal is therefore **not the final monthly bill**. AWS credits, if eligible, can offset costs but are not assumed.

Public price-list sources:
- https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/eu-central-1/index.json
- https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/eu-central-1/index.json
- https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/eu-central-1/index.json
- https://aws.amazon.com/waf/pricing/

This architecture is designed for explicit availability and infrastructure visibility, not minimum hosting cost. For a short assessment demonstration, operating time can be limited and resources removed after preserving evidence. Reducing the baseline to one task reduces cost but weakens availability. Consider an alternative deployment architecture if an ongoing ~$61-plus baseline is unsuitable. No resources have been created or spending approved.
