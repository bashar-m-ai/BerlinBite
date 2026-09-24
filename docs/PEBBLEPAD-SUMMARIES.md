# Draft text-box summaries

## Phase 1 (under 200 words)

BerlinBite is a proposed cloud application for restaurant discovery and evening planning in Berlin. Users search real restaurant data, confirm a place, inspect clearly labelled planning information and save place identifiers locally. A portable FastAPI application and frontend run in one Docker image. The proposed AWS architecture uses CloudFront, WAF, an Application Load Balancer and ECS Fargate across two availability zones, supported by ECR, Secrets Manager and CloudWatch. Terraform describes the infrastructure. The design prioritizes reproducibility, explicit security and availability tradeoffs, and manageable scope. Crowd labels are transparent, unvalidated time heuristics, not live occupancy or a trained model. The concept PDF includes the architectural rationale and diagram. Deployment and live-data verification remain pending.

## Phase 2 (under 200 words)

The FastAPI backend, responsive frontend, live Google Places adapter, current-weather adapter and optional OpenAI general-advice adapter have been implemented. The local application starts successfully, and all 12 automated API, adapter and scoring tests pass. JavaScript syntax and Terraform format checks also pass. Keys remain private and restaurant results are never fabricated. Docker build/runtime checks and Terraform provider validation pass. Live API calls and AWS deployment are not yet verified. The development presentation explains the implementation, alternatives, security controls and remaining work. Next steps are private key configuration, visual and live-data testing, a reviewed AWS permission/cost plan, deployment and collection of actual evidence. This is a development-stage summary and must be updated after those steps.
