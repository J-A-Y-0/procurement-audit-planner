# Web application

This application runs the Skills + Agents workflow as a browser service. Anthropic generates a new risk assessment, audit plan, independent challenges and QA interpretation for each run. The original Python tools calculate figures and samples and validate the resulting papers. Scope decisions and final sign-off are separate human steps.

## Run locally

Use Python 3.12 with Poppler (`pdftotext` and `pdfinfo`) on PATH.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-web.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env; keep this file private.
.venv/bin/python -m webapp
```

Open `http://localhost:8000`. The key stays on the server and is excluded from Git, generated papers and downloads. The default model is `claude-haiku-5-5`. ChatGPT and Claude membership logins are not required. The assignment does not require submission of an API key.

## Review workflow

The home page links to a public, read-only completed example at `/example/`. It preserves the signed package from live run `a88c49fe9b8c44ef88449cc258ce9b89`; viewing or downloading it does not call the model or create a run. New reviews keep their own blank decisions, signatures and browser-session isolation.

1. Start a review using the nine supplied public source files. The service copies evidence into an isolated run directory, recomputes payment analyses and verifies the cached source quotations.
2. Claude generates a cited risk register. Read the register and supporting evidence, then approve, amend inclusion or reject every risk. Rejection needs a reason. Enter the reviewer's name and date; approvals begin blank.
3. The planner creates a scoped plan. The challenger sends specific review points and verifies the planner's responses. Python builds the papers and payment samples. QA executes quote, number, trace and sample checks and returns failures to the planner for bounded correction.
4. Read the working papers, checks and any points reserved for the auditor. Sign off or return the pack with revision comments. A return triggers a new team revision. A signed-off run exposes the final ZIP.

Approving all risks fills the scope form; submitting it is a separate decision. No model can sign off. If every risk is excluded, the service records the decision without creating a plan. Failed or incomplete model responses block the run. API calls are not silently retried; artifact repair and review rounds are bounded.

## Evidence and AI roles

The application is limited to the supplied dataset. It reuses the verified `rules.json` and `history.json` extraction cache and checks their quotations against the same source files again. It does not claim to extract those documents afresh. Cleaning, seven payment analyses, self-checks, scoring, sample selection and four final checks execute again. The model receives all aggregate metrics and the first three cases of each ranked example list, preserving their original indices. Per-payment row-ID arrays and repeated payment tables are omitted from its context to reduce cost. Full lists and papers remain available to Python and the auditor; the challenger also receives exact sample counts and amount bounds computed from every selected row. Risk ratings, planning text, challenges and QA interpretation are new model outputs; earlier judgments, approvals and signatures are not copied into live runs.

The role and skill instructions are read from `.claude/agents/` and `.claude/skills/`. The server coordinates messages, restricts file ownership, runs the tools and enforces both human gates. Model-call receipts and team messages are included with the run's evidence. Documents identify procurement indicators for future fieldwork, rather than established breaches or losses. Scope amendments in the browser change inclusion; changing risk scores requires a new assessment.

The API constrains each role's response to a JSON schema, and the server checks that structure before the original audit validators run. A correctly formatted response still needs to pass the evidence, calculation and review checks.

## Deployment and operating limits

`Dockerfile` and `compose.yaml` provide deployment configuration. Docker includes Python and Poppler. Run one server process; the filesystem store and executor are designed for one process. Use HTTPS with `AUDIT_SECURE_COOKIE=1`, set `ANTHROPIC_API_KEY` in hosting secrets, and provide a writable `AUDIT_DATA_DIR`. The health endpoint is `/healthz`; the service honors `PORT`.

```sh
docker compose up --build -d
```

Compose uses a persistent named volume. Without a database, preserve the parent of `AUDIT_DATA_DIR`, containing both runs and `api-budget.json`. When `DATABASE_URL` is set, Postgres stores run records, working-paper checkpoints at human gates, and the API budget instead. On startup, the service restores these checkpoints to its local workspace. Database errors block processing rather than falling back to an empty budget. Docker is unavailable locally; the public hosting build is a separate acceptance check.

`render.yaml` uses **Render Free** for both the Docker web service and Postgres, with no paid disk. It connects to the database over Render's private network and blocks external database connections. Supply `ANTHROPIC_API_KEY` as a private hosting environment variable. Both resources must display Free before deployment; no payment method is needed. Automatic deployment is disabled. The database permits one application process at a time: suspend the old web service before manually redeploying an existing installation, then resume it after selecting the new commit.

Render's free web service sleeps after 15 minutes without traffic and can take about a minute to wake. Its local filesystem is temporary, so Postgres checkpoints preserve waiting and signed-off runs and budget reservations. **Free Render Postgres expires 30 days after creation.** Download the final pack and retain the source repository; the hosted demonstration must be accessed before the database expires. These are [Render's free-tier limits](https://render.com/docs/free), not assignment requirements. No background keep-alive service is used.

Browser sessions can access only their own runs. Keep the session cookie to return to a run; there is no account recovery. Processing interrupted by a restart is marked failed, while waiting and completed runs survive when storage persists. The store permits 100 runs; operators archive old runs when needed. Only one live generation job starts at a time, with twelve new live runs allowed by default (`AUDIT_LIVE_RUN_LIMIT`). A plan can be returned for revision up to three times.

The default application API allowance is **USD 3.00** (`AUDIT_API_BUDGET_USD`). Before generation, the service counts tokens and reserves a conservative input cost plus the full output allowance. Completed usage updates the ledger; uncertain interrupted requests retain their reservation. With Postgres, this ledger survives web-service restarts. This guard is specific to this installation and does not read the Anthropic account balance or cover other applications. A new installation starts a separate allowance: account for previous usage when choosing its cap. Budget control permits only the configured Haiku model; no automatic upgrade occurs.

## Verify and submit

```sh
.venv/bin/python -m pytest -q
```

Offline tests substitute provider responses while executing the real tools and exercising human gates, scope changes, revisions, QA correction, evidence references, browser-session isolation, safe documents and API budget enforcement. A real Anthropic end-to-end run and an independent public HTTPS browser run are separate acceptance checks.

Submit this GitHub repository URL and the independently deployed website URL required by the assignment. A localhost address does not satisfy the deployment requirement.
