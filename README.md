# BerlinBite ✳

Search a real Berlin restaurant, confirm the place, and plan your evening with “Tonight at a Glance.” A small FastAPI application and a responsive vanilla-JavaScript frontend travel together in one Docker image.

## Status — 24 September 2026

Source implementation is present and the local server was successfully started by the user at http://127.0.0.1:8000. All 12 API, adapter and scoring tests passed in the installed Python 3.13 environment. No live API credentials have been supplied. Docker execution, Terraform provider validation and AWS deployment remain unverified because this authoring session restricts the required access. The GitHub connector rejected writes despite account-level push permission.

Verified: all 12 automated tests, Python compilation, JavaScript syntax and Terraform formatting/parser checks. See `docs/VALIDATION.md`. Portfolio documents remain drafts until live-data, visual and deployment evidence is added.

## Run locally

Python 3.12+ is required. On macOS, from this directory:

```bash
python3 scripts/configure_keys.py
bash start.command
```

The first command accepts both keys as hidden input. It writes `.env` with owner-only permissions. Never put keys in GitHub, chat, frontend JavaScript, screenshots or Terraform variables. The launcher creates a virtual environment, installs dependencies, runs tests, and starts the app at **http://127.0.0.1:8000**. A dependency or test failure stops startup so it can be fixed first.

Google Cloud: enable **Places API (New)**, billing and an API key restricted to that API. The key belongs to the backend. For OpenAI, use an API project key with billing and model access. `OPENAI_MODEL` is configurable. API billing is separate from a ChatGPT subscription.

If no Google key is present, searches return an explicit 503 setup message. The app never fabricates restaurant results. Without an OpenAI key, factual Google search still works; the app labels the fixed general advice instead of claiming AI generation. Restart after changing `.env`.

## Docker — the same app

```bash
cp .env.example .env  # only if .env does not already exist
python3 scripts/configure_keys.py
docker compose up --build
```

Open http://127.0.0.1:8000. The image runs as a non-root user; Compose limits host exposure to localhost, drops capabilities and uses a read-only filesystem. `.dockerignore` excludes credentials and Terraform state.

## Experience and data

1. Search by restaurant name or craving, within the Berlin bounding rectangle.
2. Select a result; Google details are fetched on demand.
3. Choose a Berlin-local visit time, up to seven days ahead.
4. Read crowd estimate, editorial quick take when available, language/booking uncertainty, current weather, and general advice.
5. Save a place ID locally and fetch fresh details when reopening it.

Google is the source for restaurant details. We request explicit field masks and show attribution. Editorial summaries are displayed as supplied; Google reviews and restaurant content are **not sent to OpenAI**. The AI receives only our generic time heuristic. This is intentionally not an AI review summarizer. Staff English ability and reservation availability are not verified and are never inferred from location or translated reviews.

Crowd estimates are simple, unvalidated rules: base 25, +35 dinner (18–20:59), +20 lunch (12–13:59), +20 Friday/Saturday. Quiet <40, Moderate 40–64, Busy >=65. These values express a heuristic, not measured occupancy, probabilities or a trained ML model. Weather is current weather and does not influence this score. Open-Meteo’s free endpoint is for qualifying noncommercial use; revisit licensing before commercial operation.

## Structure

- `frontend/`: responsive interface, accessible states, local place-ID list, privacy and terms pages.
- `backend/app/main.py`: HTTP routes, input validation, safe errors, security headers and basic rate limiting.
- `backend/app/services/`: separate Google, Open-Meteo and OpenAI adapters; swap a provider here rather than rewriting the UI.
- `backend/app/scoring.py`: explainable Berlin-time heuristic.
- `backend/tests/`: scoring, validation, missing-key, rate-limit and adapter-error tests. Fixtures exist only in tests.
- `terraform/`: reproducible AWS resources, with application deployment disabled until an image and secret values exist.
- `scripts/`: hidden-input local/cloud key configuration.
- `docs/`: architecture, deployment, validation and portfolio drafts.

## API

| Route | Purpose |
|---|---|
| GET `/api/health` | Process health, no provider calls |
| GET `/api/config` | Credential-presence booleans, never values |
| GET `/api/search?q=...` | Live restaurant search |
| GET `/api/places/{id}` | Live details |
| POST `/api/insight` | `{ "place_id": "...", "visit_at": "ISO timestamp with offset" }` |
| GET `/api/docs` | OpenAPI interactive documentation |

The local rate limiter is per process and ignores untrusted forwarded headers. AWS WAF provides the distributed public-facing limit. Rate limits reduce abuse but do not guarantee a spending ceiling.

## Architecture and decisions

AWS target: CloudFront HTTPS + WAF → Application Load Balancer → ECS Fargate tasks in two availability zones → external HTTPS APIs. ECR stores the image; Secrets Manager stores API keys; CloudWatch collects logs and an error alarm. Terraform creates these resources. App Runner was considered but is closed to new customers; standard ECS makes networking and availability decisions explicit for the portfolio.

Two tasks are the availability baseline; CPU scaling permits up to four. Tasks use public IPs for outbound API calls without NAT Gateway costs, but inbound traffic is allowed only from the load balancer. CloudFront-origin access is limited by AWS’s managed prefix list plus a random origin header. **Limitation: CloudFront-to-ALB uses HTTP**; viewer-to-CloudFront and third-party API traffic use HTTPS. For end-to-end TLS, configure a domain and ACM certificate on the ALB before production. The random origin header is stored in Terraform state, so protect state. API keys are written separately and never enter Terraform state.

A database is deliberately omitted: only device-local saved IDs are needed. This reduces cost and operational complexity but lists do not sync between devices. Frontend assets share the app container for portability; a future S3 origin could offload assets without changing API contracts. See `docs/DEPLOYMENT.md` before creating AWS resources.

## Tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest backend/tests -q
terraform -chdir=terraform init
terraform -chdir=terraform validate
```

Direct dependencies are pinned to the locally tested versions. requirements-lock.txt records the complete tested Python environment. Docker uses Python 3.13 to match local testing; Linux container verification remains pending.

## Portfolio and responsible use

Documentation explains what each component does, why it was selected, alternatives, limitations and verification status. Cloud implementation is the assessment focus. The student must review, understand and adapt all generated code and comply with their institution’s AI-use rules. Do not claim tests, deployment, tutor feedback or measurements that did not happen. Do not upload the assignment or tutor PDFs to the public repository. The privacy page requires operator-specific details before public launch.

## References

- [Google Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search)
- [Google Places policies](https://developers.google.com/maps/documentation/places/web-service/policies)
- [OpenAI Responses](https://developers.openai.com/api/docs/guides/text)
- [Open-Meteo documentation](https://open-meteo.com/en/docs)
- [AWS App Runner availability change](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)
- [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
