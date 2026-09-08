# Azure Setup Guide — an account you can trust with your card

**Time:** ~90 min (plus up to 48 h of waiting for one thing, explained below)
**When:** before **Module 3, Day 8** · **Cost if you follow this exactly:** €0 for 30 days, then ~€5/month *only if you choose to leave the deployment running*

This is the plumbing guide. The *concepts* — what a resource group is, what Container Apps does,
why OIDC exists — live in
**[Module 3, Day 8 theory](../module-03-fastapi-azure/lessons/day8-azure-and-cd/15_theory_azure_container_apps.md)**.
This page is the part where you type things into a website that has your credit card number, so it
starts with money and ends with deleting everything.

Metaphors carried over from that lesson, because they'll keep showing up here:

| Thing | Metaphor |
|---|---|
| Your API | A **restaurant** — a kitchen that takes orders and returns dishes |
| A container image | A **food truck** — the whole kitchen, packed, ready to be driven anywhere |
| A container registry (ACR) | The **depot** — where parked food trucks are stored |
| Azure Container Apps | The **festival ground** — rents you a pitch, turns the lights on when customers arrive |
| Your CD workflow | The **delivery driver** — drives the new truck to the festival every time you merge |
| OIDC federation | A **visitor badge** — issued on arrival, names the visitor, expires the same day |

---

## 🧠 Before you read — predict first

Answer these in your head. You'll check them as you go.

1. Azure gives new accounts **$200** of credit. How long do you think you have to spend it — and
   what happens to your card on the day it runs out?
2. Your demo API gets zero visitors for three weeks. Which of the pieces you deploy (registry,
   environment, app) do you think still costs money while nothing is happening?
3. GitHub Actions needs permission to deploy to your Azure account. If you *don't* store a password
   anywhere, what does GitHub actually send to Azure to prove who it is?

---

## 🧭 The route through this guide

- [ ] **Step 1** — Create the free account, understanding exactly what "free" means → §1
- [ ] **Step 2** — Set a budget alert **before you create a single resource** → §2
- [ ] **Step 3** — Install the Azure CLI, log in, register the providers → §3
- [ ] **Step 4** — Read the honest cost table so nothing surprises you → §4
- [ ] **Step 5** — Create the GitHub OIDC federated credential → §5
- [ ] **Step 6** — Store three secrets and three variables in your GitHub repo → §6
- [ ] **Step 7** — Know how to tear it all down → §8

Definition of done: `az account show` prints your subscription, a budget alert exists in the portal,
and your GitHub repo has three secrets plus three variables. Then go build the project in
[project-insight-api/PROJECT_GUIDE.md](../module-03-fastapi-azure/project-insight-api/PROJECT_GUIDE.md).

---

## 1. 💳 The account, and what "free" actually means

Most tutorials say "sign up for the free tier" and move on. That sentence hides three different
things, and one of them expires in a month.

### The three kinds of free

| What | How much | How long | Gotcha |
|---|---|---|---|
| **Signup credit** | **$200** | **30 days from signup** | Not 12 months. Blog posts written years ago say 12 months and are wrong |
| **12-month free services** | Monthly free amounts of *selected* services | 12 months | Container Registry is **not** on this list |
| **Always-free tiers** | Permanent monthly free grants on some services | Forever | Container Apps' free grant is one of these — see §4 |

> ⏳ **The number to remember is 30.** Your $200 credit is usable within **30 days**. Plan Module 3
> so that you deploy inside that window, and you will not spend a cent.

### The $1 on your card

During signup Azure places a **temporary authorization of about $1** on your card to verify it's
real. It is **reversed** — it is a hold, not a charge. Seeing it appear in your banking app is
normal and expected; seeing it disappear a few days later is also normal.

### "Spending protection" — the sentence that lets you sleep

A free account has **spending protection**: when the $200 credit is used up or the 30 days elapse,
Azure does **not** silently start charging your card. Paid resources are stopped/disabled and you
are asked to explicitly upgrade to pay-as-you-go. You have to *opt in* to being billed.

That is the single most important fact in this guide. It does not mean you should skip the budget
alert — spending protection is a backstop, not a monitoring tool, and the moment you *do* upgrade to
pay-as-you-go (which you may want to, to keep a portfolio demo live), it no longer applies.

### Doing it

1. Go to the Azure free account page and choose **Start free**.
2. Sign in with a Microsoft account (create one if you don't have one — use an email you'll keep).
3. Identity verification by phone, then card verification (the $1 hold above).
4. Agree to the terms. You land in the **Azure portal** with a subscription named something like
   *Azure subscription 1* or *Free Trial*.

> 🎯 **Remember this** — free means **$200 for 30 days**, plus some always-free grants, plus a
> promise that your card is not charged automatically. It does **not** mean everything is free.

### 🔁 Recall check

<details>
<summary>Your friend read a 2021 blog post saying the Azure free tier gives "$200 for 12 months". What two things has that sentence merged, and which number matters for this course?</summary>

It has merged the **$200 signup credit**, which is usable within **30 days**, with the separate
**12-month free amounts** of certain services. They are different offers with different clocks.

For this course, **30 days** is the number that matters — it's the window in which the one genuinely
non-free component (the container registry, §4) is covered by the credit.
</details>

---

## 2. 🔔 Set a budget alert now — before creating anything

Do this **before** the CLI, before the resource group, before anything. An alert on an empty
subscription costs nothing and takes five minutes. An alert set up after a surprise bill is a
post-mortem.

### Why the portal and not the CLI

You'd expect this course to reach for `az`. Here we don't, deliberately:

- The `az consumption budget` command group is **in Preview**, and Microsoft's own documentation
  points you at the **Cost Management REST API** instead of the CLI for budgets.
- Preview commands change shape between CLI versions. A portal click-path that works today is a
  better instruction to hand a beginner than a preview command that may rename a flag next month.

So: portal. This is one of the few places in the whole course where clicking is the right answer,
and knowing *why* you're clicking is the actual lesson.

### The click path

```
portal.azure.com
  → search "Cost Management + Billing"
    → Billing scopes / Subscriptions  →  select your subscription
      → Budgets (left-hand menu, under "Cost Management")
        → + Add
```

### The fields

| Field | Put this | Why |
|---|---|---|
| **Scope** | Your subscription | Everything you create in this course lives under it |
| **Name** | `budget-learning` | Any name; you'll rarely look at it again |
| **Reset period** | Monthly | Resets on the 1st, matching how Azure's free grants reset |
| **Creation date / start** | The **1st of a month** | ⚠️ Azure requires the budget start date to be the first of a month. You cannot start it "today" mid-month |
| **Expiration date** | ~1 year out | An expired budget stops alerting silently |
| **Amount** | **€10** (or $10) | Your whole course budget is €10–20. Make the alarm ring long before you reach it |
| **Alert condition 1** | **Actual** cost ≥ **50 %** | "I have really spent €5." The honest number |
| **Alert condition 2** | **Forecasted** cost ≥ **100 %** | "At this rate you *will* hit €10." Warns you before the money is gone |
| **Alert recipients** | Your email address | The whole point. An alert nobody receives is a log entry |

Set **both** an actual-cost threshold and a **forecasted**-cost threshold. Actual tells you what
already happened; forecasted is the one that catches a runaway resource on day two of a month
instead of day twenty-eight.

### Two caveats that will confuse you if nobody warns you

- ⚠️ **A brand-new subscription can take up to 48 hours before Cost Management data appears.** If
  Budgets or Cost Analysis look broken, empty, or refuse to save on your first day — that's usually
  this, not you. Come back tomorrow.
- ⚠️ **The start date must be the 1st of a month.** If today is the 14th, set the start to the 1st of
  this month (allowed) or the 1st of next month; you cannot pick today.

> 🎯 **Remember this** — budget alerts are **portal-first** because the `az consumption budget` CLI
> is Preview and Microsoft recommends the REST API instead. Set **actual 50 %** *and*
> **forecasted 100 %**, both emailed to you.

### 🔁 Recall check

<details>
<summary>You set a €10 budget with a single alert at "actual ≥ 100 %". What failure mode have you left open?</summary>

You only find out **after** you've spent the entire €10 — the alert is a receipt, not a warning.
A **forecasted** threshold fires when Azure's projection for the month crosses the line, which can
be days or weeks earlier, while you can still delete the thing that's costing money.

Also worth noting: a budget alert **does not stop spending**. It emails you. Only deleting resources
(§8) stops spending.
</details>

---

## 3. 🛠️ The Azure CLI: install, log in, register

`az` is the command-line client for Azure. Everything the portal can do, it can do — and unlike
clicking, a command can be pasted into a README and re-run in ten minutes (§8).

### Install — Windows first

```powershell
# Windows (PowerShell) — recommended
winget install -e --id Microsoft.AzureCLI
```

| Token | Meaning |
|---|---|
| `winget` | Windows' built-in package manager (ships with Windows 11) |
| `install` | The subcommand that downloads and installs |
| `-e` | `--exact`: match the package ID exactly, don't fuzzy-search and install something similar |
| `--id Microsoft.AzureCLI` | The exact package identifier in the winget catalogue |

If `winget` isn't available, download the **MSI installer** from Microsoft's Azure CLI install page
and double-click it. Either way: **close and reopen your terminal afterwards**, or `az` won't be on
your `PATH` yet — the most common "I installed it and it says command not found" cause.

```bash
# macOS
brew update && brew install azure-cli

# Linux (Debian/Ubuntu)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

| Token | Meaning |
|---|---|
| `curl -sL <url>` | Download the install script. `-s` silent (no progress bar), `-L` follow redirects (`aka.ms` links are redirects) |
| `\| sudo bash` | Pipe the downloaded script straight into a root shell |

⚠️ `curl … \| sudo bash` runs code from the internet as root. It's Microsoft's documented install
method and the URL is a Microsoft domain, but the habit is worth naming: only ever do this with a
URL you trust, and if you want to be careful, download it first and read it.

Verify:

```bash
az version
```

Prints a small JSON blob with `azure-cli`, `azure-cli-core`, and any installed extensions. If you
get JSON, you're installed.

Keeping it current:

```bash
az upgrade
```

Upgrades the CLI **and** its installed extensions in place. Run it if a command's flags don't match
this guide — the Azure CLI moves quickly, and a stale CLI produces confusing "unrecognized
arguments" errors.

### Log in

```bash
az login
```

This opens your **browser**, you sign in with the Microsoft account from §1, and the CLI stores a
token locally. Back in the terminal you get a JSON list of the subscriptions you can reach.

If no browser opens (a remote machine, WSL without a browser bridge, an SSH session):

```bash
az login --use-device-code
```

| Token | Meaning |
|---|---|
| `--use-device-code` | Prints a short code and a URL instead of launching a browser. You open that URL on *any* device — your phone is fine — type the code, and the terminal completes the login |

### Pick the subscription

If your account can see more than one subscription, every later command needs to know which one:

```bash
az account set --subscription "Azure subscription 1"
az account show --output table
```

| Token | Meaning |
|---|---|
| `az account` | "Account" here means **subscription**, confusingly. It's a historical name |
| `set --subscription "<name>"` | Makes that subscription the default for every subsequent `az` command. Accepts the name *or* the GUID |
| `show --output table` | Prints the current subscription as a human-readable table instead of JSON |

The two IDs you'll need in §6 come from here:

```bash
az account show --query tenantId --output tsv     # AZURE_TENANT_ID
az account show --query id       --output tsv     # AZURE_SUBSCRIPTION_ID
```

| Token | Meaning |
|---|---|
| `--query <JMESPath>` | Extracts one field from the JSON response. `az` speaks **JMESPath**, a JSON query language |
| `--output tsv` (`-o tsv`) | Tab-separated output: **just the bare value**, no quotes, no braces. Exactly what you want to copy into a secret or capture into a shell variable |

### Add the Container Apps extension

```bash
az extension add --name containerapp --upgrade
```

| Token | Meaning |
|---|---|
| `az extension add` | Installs an add-on command group. The `az` core ships with a subset of Azure; the rest lives in extensions |
| `--name containerapp` | The extension providing the whole `az containerapp …` command group |
| `--upgrade` | If it's already installed, upgrade it to the current version instead of failing or keeping a stale one |

**Why bother if `az` offers to install it automatically?** Because it does that *silently, mid-command,
once*, and afterwards you keep whatever version got cached that day. Running this explicitly means
(a) the install happens now rather than in the middle of your first deploy, and (b) `--upgrade`
guarantees you're on the current version, which matters because `containerapp` gains flags often.

> 📌 Since **May 2024**, Azure CLI extensions **no longer enable preview features by default**. If a
> future command tells you a capability is preview-only, the opt-in flag is `--allow-preview true`.
> You should not need it anywhere in this course — if you find yourself reaching for it, re-read the
> error first.

### Register the resource providers

```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

| Token | Meaning |
|---|---|
| `az provider register` | Turns on a whole *family* of Azure services for your subscription. Subscriptions start with most families switched off |
| `--namespace Microsoft.App` | The Container Apps family — the festival ground itself |
| `--namespace Microsoft.OperationalInsights` | Log Analytics — the Container Apps **environment** writes its logs here, so it must be on too |

Registration is asynchronous and takes a couple of minutes. Check it:

```bash
az provider show --namespace Microsoft.App --query registrationState --output tsv
# Registering  -> wait
# Registered   -> good
```

Skipping this produces the error *"The subscription is not registered to use namespace
'Microsoft.App'"*, which appears at deploy time and reads like a permissions problem. It isn't — see
the troubleshooting table.

> 🎯 **Remember this** — `az login` → `az account set` → `az extension add --name containerapp
> --upgrade` → register **`Microsoft.App`** *and* **`Microsoft.OperationalInsights`**. The second
> provider is the one everybody forgets.

### 🔁 Recall check

<details>
<summary>What does <code>-o tsv</code> give you that plain <code>az account show</code> doesn't, and why does it matter for this guide specifically?</summary>

Plain output is JSON — braces, quotes, field names. `--query id -o tsv` prints **only the value**,
with no quotes and no formatting.

It matters because in §5 you capture these values into shell variables with `$( … )`. If the output
carried quotes or JSON braces, the variable would contain them too and the resulting command would
fail in a way that's genuinely hard to see. `--query X -o tsv` is the idiom for "give me one bare
value I can pipe or assign".
</details>

---

## 4. 💸 The honest cost table

Read this section slowly. It's the reason the guide exists.

### Container Apps: genuinely free at your scale

Per **subscription**, per **calendar month**, Microsoft gives you free:

| Resource | Free every month |
|---|---|
| vCPU time | **180,000 vCPU-seconds** |
| Memory time | **360,000 GiB-seconds** |
| HTTP requests | **2,000,000** |

Your demo API runs at 0.25 vCPU / 0.5 GiB. Even running continuously, a single small replica is a
fraction of that grant — and you won't be running continuously, because of the next line.

Microsoft's billing documentation states it verbatim:

> "When a revision is scaled to zero replicas, no resource consumption charges are incurred."

So with `--min-replicas 0`, **an idle demo app costs nothing for compute.** That answers prediction
question 2 for the app itself.

**The trade-off is a cold start.** With zero replicas running, the first request after an idle
period waits a few seconds while a container boots. For a portfolio demo that's a good trade — but
put a line in your README so a recruiter clicking your link doesn't think the app is broken.

⚠️ **`--min-replicas 1` is not free.** Idle *rates* (the cheaper per-second price for a replica that
isn't actively serving) only apply **above zero replicas** — they're a discount on running, not on
not-running. Keeping one replica warm to avoid cold starts means paying for it. Don't do it for a
demo.

### 🚨 The container registry is the one thing that is not free

**Azure Container Registry has no free tier.** There are exactly three SKUs:

| SKU | Price | For |
|---|---|---|
| **Basic** | **$0.1666 per day ≈ $5/month** | This course |
| Standard | More | More storage, more throughput |
| Premium | More again | Geo-replication, private links, enterprise features |

Roughly **€5/month** — and say *roughly* out loud, because Azure publishes a **separate euro price
list** that is not a live currency conversion of the dollar one. Treat every euro figure in this
course as approximate.

The registry **bills whether or not your app is running**. It's the depot: you pay rent on the
parking space even while the truck is asleep. This is the single recurring cost in the entire
curriculum, and the reason §2 comes before everything else.

### So what should you actually do?

Two honest options. There is no third option where it's free forever.

| Option | Cost | Trade-off |
|---|---|---|
| **Leave it live** during a job hunt | ~€5/month | A recruiter can click your link at 23:00 on a Sunday. Covered by the $200 credit for the first 30 days |
| **Tear it down** (§8), redeploy on request | €0 | ~10 minutes to redeploy from your repo when someone asks |

The second option is not a consolation prize. *"The whole environment is scripted — I can rebuild my
production stack from the repository in ten minutes"* is a **stronger** interview answer than "it's
still running". Say it in exactly those words and you've turned a cost decision into evidence of
infrastructure-as-code discipline.

### ⚠️ Verify the bill in week one — don't trust a predicted €0

Go to **Cost Management + Billing → Cost analysis** a few days after your first deploy and look at
the actual meters, broken down by resource.

Here's the honest reason: Container Apps has a meter named **"Environment Management Hour"**, and
whether (or when) it applies to a plain **Consumption** environment like yours is genuinely unclear
from the public documentation. It may be €0 for you. It may not. Rather than have this guide guess,
**look at your own Cost Analysis blade in week one** and see what your subscription is actually
metering. Reading your own bill is a professional skill; assuming a tutorial's cost estimate is not.

> 🎯 **Remember this** — Container Apps at demo scale with `--min-replicas 0`: **free, truly zero when
> idle** (cold start is the price). ACR Basic: **~€5/month, no free tier, bills while you sleep.**
> Check Cost Analysis in week one instead of trusting any prediction, including this one.

### 🔁 Recall check

<details>
<summary>You deployed on 1 March and went on holiday. Nobody touches the API for three weeks. On 22 March, what has it cost you?</summary>

**The container app: nothing.** Scaled to zero replicas, no resource consumption charges are
incurred, and the free monthly grant would have absorbed the traffic anyway.

**The registry: about three weeks of ACR Basic** — 21 × $0.1666 ≈ **$3.50**, roughly €3.50. It bills
continuously regardless of app activity.

If you were still inside the 30-day $200 credit window, that came out of the credit and your card
saw nothing.
</details>

---

## 5. 🎫 GitHub OIDC federated credentials, step by step

This is the section where learners fail **silently**. Slow down here.

### Why not just store a password?

The old pattern — `az ad sp create-for-rbac --sdk-auth`, paste the resulting JSON into a GitHub
secret called `AZURE_CREDENTIALS` — has real problems:

- It's a **long-lived credential**: valid until someone remembers to rotate it, which is never.
- If it leaks (a log line, a fork, a screen share), the attacker holds it until you notice.
- The `--sdk-auth` flag is **deprecated** — it's now `--json-auth` — and Microsoft's own docs
  discourage the whole pattern in favour of federation.

**OIDC** (OpenID Connect) removes the stored secret entirely. Instead of a copied key, GitHub gets a
**visitor badge**: at the start of each workflow run, GitHub mints a short-lived signed token that
says *"this is repository X, branch `main`, run 4271"*. Microsoft Entra ID (Azure's identity service,
formerly Azure AD) checks that description against a **federated credential** you registered ahead of
time, and if it matches, hands back an Azure token valid for minutes.

Nothing secret is stored in GitHub. The three values you *do* store (§6) are identifiers, useless
without a token from the exact repository and branch you named.

### The commands

Set your names first (bash / Git Bash / WSL):

```bash
RG=rg-insight-api
SUB_ID=$(az account show --query id -o tsv)
```

PowerShell equivalent, since this course is Windows-first:

```powershell
$RG     = "rg-insight-api"
$SUB_ID = az account show --query id -o tsv
```

Then, four steps:

```bash
# 1. Register an application (the identity GitHub will impersonate)
APP_ID=$(az ad app create --display-name "gh-actions-insight-api" --query appId -o tsv)
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)

# 2. Create the service principal (the app's usable presence in YOUR tenant)
az ad sp create --id "$APP_ID"
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# 3. Grant it permission — on ONE resource group, not the subscription
az role assignment create \
  --assignee-object-id "$SP_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope /subscriptions/$SUB_ID/resourceGroups/$RG

# 4. Register the trust relationship with GitHub
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters credential.json
```

Every token, explained:

| Token | What it does | Why it's there |
|---|---|---|
| `az ad app create` | Creates an **application registration** in Entra ID | The abstract identity — "an app called gh-actions-insight-api exists" |
| `--display-name "gh-actions-insight-api"` | Human-readable name | So you can find and delete it later. Not an identifier — names aren't unique |
| `--query appId -o tsv` | Extract the **client ID** | This is the value that becomes `AZURE_CLIENT_ID` in GitHub |
| `az ad app show --id "$APP_ID" --query id` | Extract the **object ID** | A *different* GUID for the same app. Step 4 needs this one. See the red flag below |
| `az ad sp create --id "$APP_ID"` | Creates the **service principal** | The app registration is the blueprint; the service principal is the instance in your tenant that can actually be assigned permissions |
| `az ad sp show --id "$APP_ID" --query id` | The service principal's own object ID | Yet a third GUID. This is what role assignments point at |
| `az role assignment create` | Grants an Azure RBAC role | Without it the identity can authenticate but do nothing |
| `--assignee-object-id "$SP_OBJECT_ID"` | *Who* gets the role | Using the object ID directly avoids a lookup that can fail on a just-created principal |
| `--assignee-principal-type ServicePrincipal` | Tells Azure the assignee is a service principal, not a user or group | Skipping it can cause a "principal not found" error due to replication lag |
| `--role Contributor` | *What* they may do: create/update/delete resources | Enough to build images and roll out revisions. Not `Owner` — Contributor cannot hand out further permissions |
| `--scope /subscriptions/<SUB_ID>/resourceGroups/<RG>` | *Where* the role applies | **The resource group.** See the second red flag below |
| `az ad app federated-credential create` | Registers "I trust GitHub tokens matching this description" | The actual federation |
| `--id "$APP_OBJECT_ID"` | Which app registration to attach the trust to | **Object ID, not client ID.** See below |
| `--parameters credential.json` | The trust description, as a JSON file | Can be inline JSON, but quoting JSON inline in PowerShell is misery. Use a file |

### 🚩 Red flag 1: `--id` in step 4 wants the **object** ID

`az ad app create` returns **two** GUIDs and they look identical in shape:

| Field | Also called | Where it goes |
|---|---|---|
| `appId` | **client ID** | The GitHub secret `AZURE_CLIENT_ID` |
| `id` | **object ID** | `az ad app federated-credential create --id …` |

Passing the client ID to `federated-credential create` is **the single most common failure** in every
walkthrough of this process. The script above sidesteps it by capturing both into separate,
explicitly named variables. If you type the commands by hand instead, check twice.

### 🚩 Red flag 2: `--scope` is the resource **group**

```
/subscriptions/<SUB_ID>/resourceGroups/rg-insight-api     ✅ one project
/subscriptions/<SUB_ID>                                    ❌ everything you own
```

Least privilege: a leaked or misused identity should be able to damage one project, not your whole
account. Every tutorial that scopes to the subscription is teaching you a bad habit for the sake of
one less variable.

### 🚨 Red flag 3: the 15 July 2026 immutable-subject change

`credential.json` contains a **`subject`** that must match the token GitHub sends **exactly,
character for character**.

Until recently the subject looked like this:

```
repo:my-org/my-repo:ref:refs/heads/main
```

**On 15 July 2026, GitHub switched to immutable subject claims.** Names can be renamed; numeric IDs
cannot. So GitHub now embeds the numeric **owner ID** and **repository ID**:

```
repo:my-org@123456/my-repo@456789:ref:refs/heads/main
```

| Your repository | Subject format |
|---|---|
| Created **before** 15 Jul 2026 | `repo:owner/repo:ref:refs/heads/main` (unless opted in) |
| Created **after** 15 Jul 2026 | `repo:owner@<ownerId>/repo@<repoId>:ref:refs/heads/main` |
| **Renamed or transferred** after that date | **Switches to immutable automatically** — silently breaking a pipeline that worked yesterday |

**Your project repository will be brand new, so you need the immutable format.** And note the third
row: renaming a working repo months from now will break CD with no warning and no code change. When
that happens, come back here.

### Finding your owner ID and repository ID

Both are public — no authentication needed. GitHub's REST API returns them for any public repo.

**Windows (PowerShell):**

```powershell
$r = Invoke-RestMethod https://api.github.com/repos/OWNER/REPO
"repo:$($r.owner.login)@$($r.owner.id)/$($r.name)@$($r.id):ref:refs/heads/main"
```

**macOS / Linux / Git Bash, with `jq`:**

```bash
curl -s https://api.github.com/repos/OWNER/REPO \
  | jq -r '"repo:\(.owner.login)@\(.owner.id)/\(.name)@\(.id):ref:refs/heads/main"'
```

**Anywhere Python is installed (no `jq` needed):**

```bash
curl -s https://api.github.com/repos/OWNER/REPO | python -c "import sys, json; d = json.load(sys.stdin); print('repo:%s@%s/%s@%s:ref:refs/heads/main' % (d['owner']['login'], d['owner']['id'], d['name'], d['id']))"
```

| Token | Meaning |
|---|---|
| `https://api.github.com/repos/OWNER/REPO` | GitHub's public repository endpoint. Returns a large JSON object |
| `.id` | The **repository** ID — the number after `repo@` |
| `.owner.id` | The **owner** (user or organisation) ID — the number after `owner@` |
| `.owner.login` / `.name` | The human-readable owner and repo names, which stay in the subject alongside the IDs |
| `curl -s` | Silent: no progress meter polluting the piped JSON |
| `jq -r` | Raw output: print the built string without surrounding quotes |

Each one-liner prints a complete, ready-to-paste `subject` string. Copy it verbatim.

> 📎 GitHub also exposes an endpoint describing how the `sub` claim is customised for a repository —
> `GET /repos/{owner}/{repo}/actions/oidc/customization/sub`, most easily called with
> `gh api /repos/OWNER/REPO/actions/oidc/customization/sub` (it needs admin auth, so `gh auth login`
> first). Be aware it reports the **customisation setting**, not a fully rendered subject string, so
> the API-derived construction above is the practical route. If they ever disagree, the token wins.

### Why a wrong subject is so dangerous

Microsoft's documentation warns, verbatim:

> "If you accidentally add the incorrect external workload information in the *subject* setting the
> federated identity credential is created successfully without error. The error does not become
> apparent until the token exchange fails."

Read that twice. **A wrong subject produces no error at creation time.** Everything looks like it
worked. You find out days later from a failing workflow, with an error message
(`AADSTS70021`) that does not mention the word "subject". If your deploy job can't log in, suspect
this **first**.

### Rules for `subject` and friends

| Rule | Consequence |
|---|---|
| **Wildcards are not supported** in `subject` | You cannot write `refs/heads/*`. Each branch needs its own credential |
| **Max 20 federated credentials** per app registration | Plenty, but not unlimited |
| **`issuer` + `subject` must be unique** per app | You can't register the same pair twice |
| **`audiences` must be `["api://AzureADTokenExchange"]`** | This exact string. It's what `azure/login` requests |
| A **branch** and an **environment** are different subjects | Deploying from `main` *and* from a GitHub Environment called `production` = **two** credentials |

### `credential.json`

```json
{
  "name": "gh-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:my-org@123456/my-repo@456789:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}
```

| Field | Meaning |
|---|---|
| `name` | A label for this credential inside the app registration. Yours to choose |
| `issuer` | **Who signs the token.** This exact URL is GitHub Actions' OIDC issuer — do not change it |
| `subject` | **What the token must say.** Paste the string your one-liner printed |
| `audiences` | **Who the token is for.** Always `["api://AzureADTokenExchange"]` for Azure |

Save it next to where you're running `az`, substitute your own subject, then run step 4.

Verify it landed:

```bash
az ad app federated-credential list --id "$APP_OBJECT_ID" --output table
```

This shows the subject that is actually registered — which is exactly the string to compare,
character by character, against your one-liner's output when something fails.

> 🎯 **Remember this** — OIDC is a **visitor badge, not a copied key**. `--id` takes the **object**
> ID. `--scope` is the **resource group**. A **wrong `subject` fails silently**, and a new repo needs
> the `owner@<ownerId>/repo@<repoId>` format.

### 🔁 Recall check

<details>
<summary>Your CD workflow fails at the Azure login step with <code>AADSTS70021: No matching federated identity record found</code>. Everything was created without errors. What are the first three things you check, in order?</summary>

1. **The `subject` string**, against what GitHub actually sends. Almost always it's the immutable
   format: you registered `repo:me/my-repo:ref:refs/heads/main` but your new repo emits
   `repo:me@123456/my-repo@456789:ref:refs/heads/main`. Run the one-liner, run
   `az ad app federated-credential list`, diff the two strings.
2. **Which branch/event fired.** A subject registered for `refs/heads/main` does not match a pull
   request (`pull_request` events emit a different subject entirely), and wildcards aren't supported.
3. **Whether `--id` got the object ID.** If you passed the client ID, the credential may have landed
   on the wrong object — or the command failed earlier than you noticed.

And if the error is *no useful message at all* rather than AADSTS70021, check
`permissions: id-token: write` in the workflow instead — see the troubleshooting table.
</details>

---

## 6. 🔐 Storing the values in GitHub

Six values go into your repository. Three as **secrets**, three as **variables**. The distinction is
the lesson here.

```
Your repository on github.com
  → Settings
    → Secrets and variables  →  Actions
      → tab "Secrets"    →  New repository secret
      → tab "Variables"  →  New repository variable
```

### Secrets vs variables

| | Secret | Variable |
|---|---|---|
| Referenced as | `${{ secrets.NAME }}` | `${{ vars.NAME }}` |
| Visible after saving? | **No** — write-only, you can only replace it | **Yes** — readable in Settings any time |
| Masked in logs? | **Yes**, GitHub redacts it as `***` | No, it prints normally |
| Use for | Anything that grants access | Non-sensitive config |

Why do the Azure identifiers go in **Secrets** if OIDC means they're not passwords? Two reasons:
it's what `azure/login`'s documented examples do, and while a client ID isn't a credential, there's
no upside to broadcasting your tenant and subscription GUIDs to anyone reading your public repo.
Habit-wise: **identifiers of your account → secrets; names of your resources → variables.**

### The three secrets

| Secret name | Value | Where it comes from |
|---|---|---|
| `AZURE_CLIENT_ID` | The app registration's **`appId`** | `echo $APP_ID` from §5 — the **client** ID, not the object ID |
| `AZURE_TENANT_ID` | Your Entra tenant GUID | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | Your subscription GUID | `az account show --query id -o tsv` |

```bash
az account show --query tenantId --output tsv     # -> AZURE_TENANT_ID
az account show --query id       --output tsv     # -> AZURE_SUBSCRIPTION_ID
echo "$APP_ID"                                    # -> AZURE_CLIENT_ID
```

⚠️ `AZURE_CLIENT_ID` is `appId`. The **object** ID from §5 goes nowhere near GitHub — it was only
ever an argument to `federated-credential create`.

### The three variables

| Variable name | Example value | What it is |
|---|---|---|
| `ACR_NAME` | `insightapi12345` | Your registry's short name — **not** the full `.azurecr.io` hostname |
| `AZURE_RESOURCE_GROUP` | `rg-insight-api` | The resource group holding everything |
| `CONTAINER_APP_NAME` | `insight-api` | The container app itself |

These are names of things in your own subscription. They're not sensitive, and keeping them
*visible* is actively useful: when a workflow fails, you can read the value in Settings instead of
guessing what a masked `***` contained.

They're exactly the names used by the project's
[`cd.yml`](../module-03-fastapi-azure/project-insight-api/.github/workflows/cd.yml) — spelling
matters, `${{ vars.TYPO }}` silently evaluates to an empty string.

### One more thing: use `azure/login@v3`

```yaml
- uses: azure/login@v3
  with:
    client-id:       ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id:       ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

`v3` is the current major version. **`v1` is end-of-life**; `v2` receives security fixes only.

⚠️ **Microsoft's own Container Apps + GitHub Actions documentation page still shows
`azure/login@v1` with an `AZURE_CREDENTIALS` JSON blob.** That page is stale. Copying it gives you
an end-of-life action *and* the long-lived-secret pattern you just spent §5 avoiding. Don't.

And in the workflow file itself, at the top:

```yaml
permissions:
  id-token: write        # MANDATORY — lets the runner mint an OIDC token
  contents: read         # for actions/checkout
```

Without `id-token: write`, GitHub never issues the badge, and `azure/login` fails in a way that
looks like an Azure problem but isn't.

> 🎯 **Remember this** — three **secrets** (client/tenant/subscription IDs), three **variables**
> (ACR / resource group / app names), `azure/login@v3`, and `permissions: id-token: write` or none
> of it works.

### 🔁 Recall check

<details>
<summary>Why is <code>ACR_NAME</code> a variable and not a secret — and what practical debugging advantage does that give you?</summary>

Because a registry name isn't a credential; it grants nobody anything without an authenticated
identity. Registries are also discoverable by name, so hiding it buys nothing.

The practical advantage: when a build step fails with something like
`***.azurecr.io: not found`, a masked secret has erased the one piece of information you needed.
As a variable it prints normally in the log, and you can also read it back in Settings to check for
a typo. **Mask credentials; don't mask configuration.**
</details>

---

## 7. 🧯 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AADSTS70021: No matching federated identity record found for presented assertion subject` | The `subject` you registered ≠ the `sub` GitHub sends. **Most likely the immutable format**: your new repo emits `repo:owner@<ownerId>/repo@<repoId>:…` and you registered the old name-based form | Rebuild the subject with the API one-liner in §5, compare against `az ad app federated-credential list --id "$APP_OBJECT_ID" -o table`, delete and recreate the credential. Remember: wildcards don't work, and a different branch or a `pull_request` event is a different subject |
| `azure/login` fails with **no useful error** — empty or generic message, no AADSTS code | Missing `permissions: id-token: write` in the workflow. GitHub never minted a token, so there was nothing to exchange | Add the `permissions:` block at the top of the workflow (or to the job). See §6 |
| `The subscription is not registered to use namespace 'Microsoft.App'` | Resource provider not registered on this subscription. Reads like a permissions error; isn't | `az provider register --namespace Microsoft.App` and `--namespace Microsoft.OperationalInsights`, then wait for `az provider show --namespace Microsoft.App --query registrationState -o tsv` to say `Registered` |
| ACR name rejected at creation | Registry names must be **5–50 characters, alphanumeric only** (no hyphens, no underscores), **lowercase**, and **globally unique across all of Azure** — `insight-api` fails twice over | Use something like `insightapi` plus digits, e.g. `ACR=insightapi$RANDOM`. If creation says the name is taken, someone else on Azure has it — pick another |
| Container app deploys but is **unhealthy** / never serves traffic | Three usual causes: (1) uvicorn bound to `127.0.0.1` instead of `0.0.0.0`, so nothing outside the container can reach it; (2) `--target-port` doesn't match the port in the Dockerfile's `CMD`; (3) the app crashed at startup — most often `Settings` failing because `DATABASE_URL` wasn't set | Read the logs, don't guess: `az containerapp logs show --name <app> --resource-group <rg> --follow`. Then bind `--host 0.0.0.0`, align `--target-port`, or set the secret + env var |
| New image pushed, but the **old code still serves** | The tag was reused (`:latest`). Nothing about the requested image changed as far as Azure can tell, so no new revision is created | Tag with the commit SHA: `az acr build --image insight-api:$GITHUB_SHA .` then `az containerapp update --image <acr>.azurecr.io/insight-api:$GITHUB_SHA`. The project's `cd.yml` already does this |
| Container Apps **secret name rejected** | Azure Container Apps secret names are capped at **20 characters** (this is the Azure-side secret, not the GitHub one) | Shorten it — `db-url`, not `database-connection-string-primary` |
| `az` says "unrecognized arguments" on a command copied from this guide | Stale CLI or stale `containerapp` extension | `az upgrade` and `az extension add --name containerapp --upgrade` |
| **Unexpected bill** | Almost certainly the **ACR Basic registry** (~$0.1666/day), which bills whether or not the app runs. Possibly the Environment Management Hour meter — check §4 | Open Cost Management → Cost analysis, group by resource, and read the actual meters. If you're done with the deployment, delete the resource group (§8) |
| Budgets / Cost analysis look empty or broken on a new subscription | Cost Management data can take **up to 48 hours** to appear on a brand-new subscription | Wait a day and retry. Not your mistake |

---

## 8. 🧹 Tearing it all down

The habit that keeps this course inside its budget.

```bash
az group delete --name rg-insight-api --yes --no-wait
```

| Token | Meaning |
|---|---|
| `az group delete` | Deletes a resource group **and everything inside it** — registry, environment, app, log workspace, all of it |
| `--name rg-insight-api` | Which group. This is why you create **one resource group per project**: teardown is one command and cannot miss anything |
| `--yes` | Skip the interactive "are you sure?" prompt. Required for scripts; be deliberate when typing it by hand |
| `--no-wait` | Return to your prompt immediately instead of blocking for the several minutes deletion takes. It continues in the background |

Confirm it's gone:

```bash
az group list --output table          # your group should no longer be listed
```

### What teardown does *not* remove

The Entra ID app registration and its federated credential from §5 live in your **directory**, not
in a resource group, so `az group delete` leaves them alone. They cost nothing. That's convenient:
redeploying later means recreating the resource group, not redoing the OIDC dance. The one thing you
*will* need to redo is the role assignment, because it was scoped to the resource group you just
deleted:

```bash
az role assignment create \
  --assignee-object-id "$SP_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope /subscriptions/$SUB_ID/resourceGroups/$RG
```

If you want the identity gone too: `az ad app delete --id "$APP_OBJECT_ID"`.

### Teardown is not losing your work

Your repository still contains the Dockerfile, the workflow, and every `az` command. Deleting the
deployment deletes a *result*, not the *recipe*. Redeploying takes about ten minutes, most of it
waiting.

> 💬 **"I can rebuild my entire production environment from a repository in ten minutes"** is a
> stronger interview answer than "it's still running." One describes a URL; the other describes a
> practice. Put the deploy commands in your project README so the claim is verifiable.

### Verify the bill actually went to zero

A few days after deleting, open **Cost Management + Billing → Cost analysis** and confirm the daily
cost has flattened to zero. Confirming that a bill actually stopped — rather than assuming it did —
is part of the skill, and it's the same muscle as checking that a test actually ran rather than
silently skipping.

> 🎯 **Remember this** — one resource group per project makes teardown a single command. Scripted
> infrastructure makes teardown a non-event. **Then go and check the bill.**

---

## 📌 Azure setup on one screen

```
MONEY      $200 credit, 30 DAYS (not 12 months) + always-free grants
           $1 card hold = temporary, reversed
           Spending protection = card NOT charged automatically when credit ends
           BUDGET ALERT FIRST, in the PORTAL:
             Cost Management + Billing > Subscriptions > Budgets > + Add
             actual >= 50%  AND  forecasted >= 100%, emailed to you
             start date must be the 1st of a month; new subs need up to 48h
             (az consumption budget is PREVIEW; MS recommends the REST API)

CLI        winget install -e --id Microsoft.AzureCLI      # then reopen the terminal
           az login            (or: az login --use-device-code)
           az account set --subscription "<name>"
           az extension add --name containerapp --upgrade
           az provider register --namespace Microsoft.App
           az provider register --namespace Microsoft.OperationalInsights
           (since May 2024 extensions don't enable preview by default: --allow-preview true)

COST       Container Apps free/month: 180,000 vCPU-s | 360,000 GiB-s | 2,000,000 requests
                   --min-replicas 0  =>  idle costs NOTHING (cold start is the trade)
                   --min-replicas 1  =>  NOT free; idle rates apply only above zero
           ACR:    NO free tier. Basic $0.1666/day ~= $5/mo (~EUR 5, approx.)
                   bills whether or not the app runs. THE one recurring cost.
           CHECK Cost Analysis in week 1 — do not trust a predicted EUR 0

OIDC       APP_ID        = az ad app create ... --query appId -o tsv   -> AZURE_CLIENT_ID
           APP_OBJECT_ID = az ad app show --id $APP_ID --query id -o tsv -> --id below
           az ad sp create --id $APP_ID
           role assignment --scope .../resourceGroups/<RG>   <- GROUP, not subscription
           az ad app federated-credential create --id <OBJECT ID> --parameters credential.json
           subject (new repos): repo:owner@<ownerId>/repo@<repoId>:ref:refs/heads/main
           audiences: ["api://AzureADTokenExchange"]   no wildcards   max 20 creds
           >>> A WRONG SUBJECT IS CREATED WITHOUT ERROR AND FAILS LATER <<<

GITHUB     Settings > Secrets and variables > Actions
           secrets:   AZURE_CLIENT_ID  AZURE_TENANT_ID  AZURE_SUBSCRIPTION_ID
           variables: ACR_NAME  AZURE_RESOURCE_GROUP  CONTAINER_APP_NAME
           azure/login@v3      (v1 EOL, v2 security-only; MS's own docs are stale)
           permissions: id-token: write     <- without it, login fails

TEARDOWN   az group delete --name <RG> --yes --no-wait
           app registration survives (it's in Entra, not the group) — re-add the role assignment
           verify Cost Analysis is flat a few days later
```

---

## ➡️ Where to go next

- **Concepts:** [Module 3, Day 8 — Parking the Truck](../module-03-fastapi-azure/lessons/day8-azure-and-cd/15_theory_azure_container_apps.md)
- **Build it:** [project-insight-api/PROJECT_GUIDE.md](../module-03-fastapi-azure/project-insight-api/PROJECT_GUIDE.md)
- **The image you'll be deploying:** [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- **Branches, secrets and the repo itself:** [GIT_GITHUB_GUIDE.md](GIT_GITHUB_GUIDE.md)

One last time, because it's the sentence that costs money if you skip it: **set the budget alert
before you create anything, and delete the resource group when you're done.**
