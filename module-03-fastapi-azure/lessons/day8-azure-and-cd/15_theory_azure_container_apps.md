# Day 8 — Parking the Truck: Azure Container Apps & CD

**Time:** ~3 h · **Prerequisite:** Day 7 (you can build an image), Module 2 Day 8 (GitHub Actions)

You have a food truck. Today you park it somewhere the public can reach, and then you make the
parking happen **by itself** every time you merge to `main`.

> 💳 **Before you start:** work through **[docs/AZURE_SETUP_GUIDE.md](../../../docs/AZURE_SETUP_GUIDE.md)**
> first. It covers creating the account *with spending limits*, and this module's one genuinely
> non-free component. Do not skip the budget alert.

---

## 🧠 Before you read — predict first

1. Your image runs on your laptop. What are the *minimum* pieces of cloud infrastructure needed for
   a stranger to open it in a browser?
2. Your CI needs permission to deploy to Azure. The obvious approach is a password in a GitHub
   secret. What's wrong with that, and what would be better?
3. Nobody uses your demo API for three weeks. What should it cost?

---

## 1. Where a container can run, and why we chose this

| Option | What you manage | Verdict for this course |
|---|---|---|
| A VM you rent | OS, patches, Docker, restarts, TLS, scaling | Too much. You'd spend the module on Linux admin |
| Kubernetes (AKS) | Cluster, nodes, YAML, ingress controllers | Powerful, enormous. A rabbit hole for a solo learner |
| **Azure Container Apps** | **Just your image** | ✅ **This** |
| Azure App Service | Similar, older, less container-native | Fine, but less transferable |

Azure Container Apps is **serverless containers**: you hand over an image and a port, and the
platform does TLS, a public URL, load balancing, rolling updates, and scaling — including scaling to
**zero** when nobody is asking.

The festival ground: you don't buy land and build a kitchen. You rent a pitch, drive the truck on,
and the organiser turns the lights on when customers arrive and off when they don't. You're billed
for the hours you actually served.

Kubernetes runs underneath, and you never see it. That's the point.

---

## 2. The four pieces

Prediction question 1, answered:

```
Resource Group                     a folder holding everything, so you can delete it all at once
 ├── Container Registry (ACR)      the depot: where your image is stored
 └── Container Apps Environment    the festival ground: shared network + logging
      └── Container App            your truck, with a public URL
```

| Piece | Analogy | Why it exists |
|---|---|---|
| **Resource Group** | A folder | Azure billing and deletion work per group. `az group delete` removes everything |
| **Container Registry** | The depot | Azure needs to pull your image from somewhere it trusts |
| **Environment** | The festival ground | Shared network and log workspace for one or more apps |
| **Container App** | Your truck | The running thing, with a URL and a scaling rule |

Create a resource group **per project**. That way teardown is one command and cannot miss anything —
the single most valuable habit for not being surprised by a bill.

---

## 3. 💸 What this actually costs

Be precise here, because "free tier" is doing a lot of work in most tutorials.

### Container Apps: genuinely free at this scale

Per subscription, per calendar month, Microsoft gives you free:

| Resource | Free each month |
|---|---|
| vCPU time | 180,000 vCPU-seconds |
| Memory time | 360,000 GiB-seconds |
| Requests | 2,000,000 |

Your demo API at 0.25 vCPU / 0.5 GiB, handling occasional traffic, uses a rounding error of that.
And with `--min-replicas 0`, Microsoft's billing documentation is explicit: *"When a revision is
scaled to zero replicas, no resource consumption charges are incurred."*

Prediction question 3: **an idle scale-to-zero app costs nothing for compute.** The trade is a
**cold start** — the first request after idling waits a few seconds for a container to boot. For a
portfolio demo that's a fine trade; mention it in your README so a recruiter clicking the link isn't
confused by a slow first load.

### 🚨 The Container Registry is not free

**Azure Container Registry has three SKUs — Basic, Standard, Premium — and no free tier.** Basic
lists at **$0.1666 per day**, which is roughly **$5 per month** (about €5; Azure's euro price list
is separate, so treat this as approximate). It bills whether or not your app is running.

This is the one recurring cost in the whole course, and it is why the setup guide insists on a
budget alert and why the last section of this page is about deleting things.

The new-account **$200 credit covers it for 30 days**. After that, if you want the deployment to
stay live for a job hunt, budget about €5/month — or tear it down and redeploy from your repo in
about ten minutes when someone asks to see it, which costs nothing and is itself a demonstrable
skill.

> 🎯 **Remember this** — Container Apps at demo scale: **free**, and truly zero when idle.
> The registry: **~€5/month, always**. Delete the resource group when you're done.

---

## 4. Deploying by hand, once

Course principle: **hard way first**. Automate only what you have already done manually, or you're
debugging a black box.

```bash
# 0. names (lowercase, globally unique for the registry)
RG=rg-insight-api
LOC=westeurope
ACR=insightapi$RANDOM          # 5-50 alphanumeric chars, globally unique
APP=insight-api
ENVNAME=env-insight-api

# 1. log in and prepare
az login
az account set --subscription "<your subscription name>"
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

# 2. the folder
az group create --name $RG --location $LOC

# 3. the depot
az acr create --resource-group $RG --name $ACR --sku Basic --location $LOC

# 4. build the image IN THE CLOUD (no local Docker needed)
az acr build --registry $ACR --image $APP:v1 .

# 5. the festival ground
az containerapp env create --name $ENVNAME --resource-group $RG --location $LOC

# 6. the truck
az containerapp create \
  --name $APP \
  --resource-group $RG \
  --environment $ENVNAME \
  --image $ACR.azurecr.io/$APP:v1 \
  --registry-server $ACR.azurecr.io \
  --ingress external \
  --target-port 8000 \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.25 --memory 0.5Gi \
  --query properties.configuration.ingress.fqdn --output tsv
```

Key flags:

| Flag | Meaning |
|---|---|
| `az acr build` | **Builds the image on Azure's machines** and pushes it. No local Docker at all |
| `--ingress external` | Give it a public URL. `internal` = reachable only inside the environment |
| `--target-port 8000` | The port **your container listens on** — must match your Dockerfile's `CMD` |
| `--min-replicas 0` | Scale to zero when idle. This is the free-when-unused switch |
| `--max-replicas 3` | Ceiling. Protects you from a traffic spike becoming a bill |
| `--cpu 0.25 --memory 0.5Gi` | Smallest useful size. CPU 0.25–2.0, memory 0.5–4.0 Gi |
| `--query ...ingress.fqdn -o tsv` | Print just the public hostname |

Step 4 is worth pausing on. `az acr build` uploads your build context and builds it **on Azure**,
which means a learner on a slow laptop, or a machine without Docker at all, can still ship. It's the
same Dockerfile you wrote yesterday.

The last command prints something like
`insight-api.happyhill-70162bb9.westeurope.azurecontainerapps.io`. Open `https://<that>/docs` and
your API is on the public internet, with a TLS certificate you did not configure.

To ship a new version:

```bash
az acr build --registry $ACR --image $APP:v2 .
az containerapp update --name $APP --resource-group $RG --image $ACR.azurecr.io/$APP:v2
```

⚠️ Use a **new tag** each time. Re-pushing `:latest` does not reliably produce a new revision,
because nothing about the requested image changed as far as Azure can tell. Day 7's rule — deploy
commit SHAs — is enforced here by the platform.

### Secrets

Never bake a connection string into an image (Day 7: layers are permanent).

```bash
az containerapp secret set --name $APP --resource-group $RG \
  --secrets db-url="postgresql+psycopg2://user:pass@host:5432/db"

az containerapp update --name $APP --resource-group $RG \
  --set-env-vars DATABASE_URL=secretref:db-url
```

| Token | Meaning |
|---|---|
| `secret set` | Stores an encrypted value on the app |
| `DATABASE_URL=secretref:db-url` | The env var's value is *a reference to* the secret, not the secret |
| `secretref:` | Literally that prefix, then the secret's name |

Two gotchas: **secret names are capped at 20 characters**, and changing a secret does **not** create
a new revision — existing revisions keep the old value until you deploy or restart one.

Day 4's `Settings` reads `DATABASE_URL` from the environment, so the app needs no change at all.
Environment beats `.env` beats default: same image, different environment, different configuration.

> 🎯 **Remember this** — `az acr build` builds in the cloud. New tag for every deploy. Secrets are
> injected as environment variables via `secretref:`, never baked into the image.

---

## 5. Continuous deployment, and the password problem

Prediction question 2. The old approach — `az ad sp create-for-rbac --sdk-auth`, paste the JSON into
a GitHub secret — has real problems:

- It is a **long-lived credential**. It works until someone remembers to rotate it, which is never.
- If it leaks (a log, a fork, a screen share), the attacker has your subscription until you notice.
- The `--sdk-auth` flag is **deprecated** and Microsoft's own docs discourage the pattern.

### OIDC: a visitor badge instead of a copied key

**OIDC** (OpenID Connect) federation removes the stored secret entirely.

1. GitHub Actions mints a short-lived, signed token describing *this exact workflow run*: this
   repository, this branch, this event.
2. The workflow presents it to Microsoft Entra ID.
3. Entra checks it against a **federated credential** you registered: "I trust tokens from GitHub
   that say they're from `my-org/my-repo` on branch `main`."
4. Entra returns an Azure access token valid for minutes.

Nothing secret is ever stored in GitHub. The three values you do store —
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` — are identifiers, not passwords. They
are useless without a token from the exact repository and branch you named.

A copied key versus a visitor badge that is issued on arrival, names the visitor, and expires the
same day.

```bash
# 1. app registration
APP_ID=$(az ad app create --display-name "gh-actions-insight-api" --query appId -o tsv)
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)

# 2. service principal
az ad sp create --id "$APP_ID"
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# 3. permission, scoped to ONE resource group - not the subscription
az role assignment create \
  --assignee-object-id "$SP_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/$RG

# 4. the trust relationship
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters credential.json
```

🚩 **`--id` in step 4 wants the *object* ID, not the client/app ID.** `az ad app create` returns
both, they look alike, and swapping them is the single most common failure in every walkthrough of
this. `appId` = client ID (goes in the GitHub secret); `id` = object ID (goes here).

Note step 3's `--scope`: the resource **group**, not the subscription. A leaked identity should be
able to touch one project, not everything you own.

### 🚨 The 2026 change nobody's blog post has caught up with

`credential.json` contains a `subject` that must match the token GitHub sends, **exactly**.

Until recently that subject looked like:

```
repo:my-org/my-repo:ref:refs/heads/main
```

**On 15 July 2026 GitHub changed to immutable subject claims.** Names can be renamed, so GitHub now
embeds the numeric owner and repository IDs:

```
repo:my-org@123456/my-repo@456789:ref:refs/heads/main
```

| | Subject format |
|---|---|
| Repos created **before** 15 Jul 2026 | `repo:owner/repo:ref:refs/heads/main` (unless opted in) |
| Repos created **after** 15 Jul 2026 | `repo:owner@<ownerId>/repo@<repoId>:ref:refs/heads/main` |
| Renamed or transferred after that date | **Switches to immutable automatically** |

**Your project repository will be brand new, so you need the immutable format.**

And here is why this matters more than a footnote — Microsoft's own documentation warns, verbatim:

> "If you accidentally add the incorrect external workload information in the *subject* setting the
> federated identity credential is created successfully without error. The error does not become
> apparent until the token exchange fails."

**A wrong subject produces no error when you create it.** You find out later, from a failing
workflow, with a message that does not mention the subject. If your deploy job fails to log in,
suspect this first. Wildcards are not supported in `subject`, and you may register up to 20
credentials per app — so a branch and an environment need one each.

```json
{
  "name": "gh-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:my-org@123456/my-repo@456789:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}
```

The setup guide shows how to read your actual owner and repository IDs so you don't have to guess.

> 🎯 **Remember this** — OIDC = visitor badge, not copied key. Object ID ≠ client ID. **A wrong
> `subject` fails silently**, and new repos need the `owner@id/repo@id` format.

---

## 6. The deploy workflow

```yaml
name: CD

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write        # REQUIRED: lets the runner mint an OIDC token
  contents: read         # for actions/checkout

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Azure (OIDC, no password)
        uses: azure/login@v3
        with:
          client-id:       ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id:       ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Build the image in the cloud
        run: az acr build --registry ${{ vars.ACR_NAME }} --image insight-api:${{ github.sha }} .

      - name: Roll out the new revision
        run: |
          az containerapp update \
            --name insight-api \
            --resource-group ${{ vars.AZURE_RG }} \
            --image ${{ vars.ACR_NAME }}.azurecr.io/insight-api:${{ github.sha }}

      - name: Show the live URL
        run: |
          az containerapp show --name insight-api --resource-group ${{ vars.AZURE_RG }} \
            --query properties.configuration.ingress.fqdn --output tsv
```

| Line | Why |
|---|---|
| `branches: [main]` | Deploy only from `main`. Feature branches run CI, not CD |
| `workflow_dispatch` | A manual "Run workflow" button, as in Module 2's `pipeline.yml` |
| `permissions: id-token: write` | **Mandatory for OIDC.** Without it the runner cannot mint a token and login fails |
| `azure/login@v3` | Current major. `v1` is end-of-life; `v2` is security fixes only |
| `${{ github.sha }}` | The commit SHA as the image tag — Day 7's rule, enforced |
| `${{ vars.X }}` | Repository **variables** for non-secret config; `secrets.X` for the identifiers |

⚠️ Microsoft's own Container Apps + GitHub Actions page still shows `azure/login@v1` with an
`AZURE_CREDENTIALS` JSON blob. That page is stale. Use `v3` with OIDC.

### CI and CD are different jobs

Module 2 taught the bouncer (`ci.yml`) and the night shift (`pipeline.yml`). Add the **delivery
driver**:

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | every push and PR | ruff + pytest. **The gate** |
| `cd.yml` | push to `main` only | build, push, deploy |

Make CD depend on CI passing, so a red test can never reach production:

```yaml
jobs:
  test:
    uses: ./.github/workflows/ci.yml     # reuse, don't duplicate
  deploy:
    needs: test                          # only runs if `test` succeeded
    runs-on: ubuntu-latest
```

`needs:` is the whole safety mechanism. Without it the two jobs race, and a broken build deploys
while the tests are still running.

---

## 7. Revisions and rollback

Every `containerapp update` creates a **revision** — an immutable snapshot of image plus
configuration.

```bash
az containerapp revision list --name $APP --resource-group $RG --output table
az containerapp revision activate --revision <older-revision-name> --resource-group $RG
```

Rolling back is activating the previous revision. Seconds, not a rebuild. This is why immutable
image tags matter: `insight-api:a3f9c21` is a specific, reproducible artifact, whereas rolling back
to "latest" is meaningless.

Logs:

```bash
az containerapp logs show --name $APP --resource-group $RG --follow
```

Your uvicorn output, streamed. Same as `docker logs -f`, one layer up.

---

## 8. 🧹 Tearing down

The habit that keeps this course inside its budget:

```bash
az group delete --name $RG --yes --no-wait
```

Everything in the group — registry, environment, app, logs — is destroyed. `--yes` skips the
confirmation, `--no-wait` returns immediately.

Because the whole deployment is scripted, tearing down is not losing your work. Your repository
still builds and deploys in about ten minutes. **"I can rebuild my entire production environment
from a repository in ten minutes" is a stronger interview answer than "it's still running."**

After deleting, check the portal's Cost Analysis view once a few days later. Confirming a bill is
actually zero is part of the skill.

> 🎯 **Remember this** — one resource group per project means teardown is one command. Scripted
> infrastructure means teardown is not a loss.

---

## 🔁 Spaced review

<details>
<summary>1. (Day 7) Your app runs locally in Docker but Azure reports the container as unhealthy and never serves traffic. Name three likely causes.</summary>

1. **Uvicorn is bound to `127.0.0.1`.** Inside the container, nothing external can reach it. Needs
   `--host 0.0.0.0`.
2. **`--target-port` doesn't match** the port in the Dockerfile's `CMD`. Azure probes 8000 while
   uvicorn listens on 80.
3. **The app crashes at startup** — most often Day 4's `Settings` failing because `DATABASE_URL`
   wasn't set as an environment variable or secret. `az containerapp logs show` tells you in seconds.
</details>

<details>
<summary>2. (Day 4) Your Azure app must reach a database. Where does the connection string live, and what must change in your code?</summary>

In a **Container Apps secret**, surfaced as the `DATABASE_URL` environment variable via
`secretref:`. **Nothing changes in your code.** `Settings` already reads the environment first, so
the identical image runs locally, in CI, and in Azure with only the environment differing.

That property — one artifact, many environments — is what "configuration by environment" buys you.
</details>

<details>
<summary>3. (Module 2) You wrote a scheduled workflow with <code>cron</code>. What's the difference between it and today's CD workflow?</summary>

The **trigger** and the intent. `pipeline.yml` runs on a **schedule** (the night shift) to do work
on data. `cd.yml` runs on an **event** — a push to `main` — to ship code (the delivery driver). Same
GitHub Actions machinery, same YAML, different `on:` block.

Both also carry `workflow_dispatch` so you can run them by hand while debugging, which you will.
</details>

---

## 📌 Day 8 on one screen

```
PIECES     Resource Group > [ ACR ] + [ Environment > Container App ]
           az group delete --name $RG --yes      # removes ALL of it

DEPLOY     az acr build --registry $ACR --image app:$SHA .     # builds IN THE CLOUD
           az containerapp update --name app --image $ACR.azurecr.io/app:$SHA
           NEW TAG EVERY TIME. :latest will not reliably redeploy.

COST       Container Apps: 180k vCPU-s + 360k GiB-s + 2M req free/month
                           min-replicas 0 => idle costs NOTHING (cold start is the trade)
           ACR Basic:      ~$5/month, NO free tier, bills while idle
           Free account:   $200 credit, 30 days

OIDC       permissions: id-token: write        <- mandatory
           azure/login@v3                      <- v1 is EOL; MS docs are stale
           federated-credential --id <OBJECT id, not client id>
           subject NEW repos: repo:owner@<ownerId>/repo@<repoId>:ref:refs/heads/main
           WRONG SUBJECT = SILENT FAILURE

SAFETY     cd.yml: needs: test    <- red tests can never deploy
           rollback = activate the previous revision
```

---

## ➡️ Next

Notebook **[16_cd_pipeline_practice.ipynb](16_cd_pipeline_practice.ipynb)** — build the federated
credential subject for your own repository, read the workflow YAML line by line, and rehearse the
failure modes before they cost you an afternoon.

Then **Days 9–10: the project.** Open
[project-insight-api/PROJECT_GUIDE.md](../../project-insight-api/PROJECT_GUIDE.md) and ship it.
