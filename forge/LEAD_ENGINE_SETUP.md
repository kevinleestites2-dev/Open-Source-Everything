# PropPilot AI — Lead Follow-Up Engine Setup
### Adapted from Sabrina.dev "Smart Lead Follow-Up for Service Businesses"

## What This Does
When a buyer signs up on the PropPilot AI landing page:

1. **EmailOctopus** captures their email → adds to "Audience" list (already live)
2. **Lead Follow-Up Engine** detects new contact
3. **OpenAI GPT-4o** generates a personalized follow-up email
4. **SMTP/Gmail** sends the email to the buyer within seconds
5. **Forgemaster Alert** fires to your email — name, email, AI draft preview
6. **logs/leads.json** logs the full lead record permanently

---

## Status

| Component           | Status                  |
|---------------------|-------------------------|
| Landing page form   | ✅ Built (prop_clone/)  |
| EmailOctopus API    | ✅ Wired & tested       |
| Lead Follow-Up Engine | ✅ Built               |
| OpenAI email gen    | ⚠️  Needs OPENAI_API_KEY |
| SMTP email sending  | ⚠️  Needs SMTP creds    |
| Netlify deployment  | ⏳ Next step            |
| Webhook URL in page | ⏳ After server deploy  |

---

## Quick Activation (3 steps)

### Step 1 — Set environment variables

Create `.env` in workspace root:

```bash
# EmailOctopus (already set in code)
EO_API_KEY=eo_c31f4c1b1d65c2a63fca72914998816255aa47619e76a130444898786e5050f4
EO_LIST_ID=2f14af34-2a2f-11f1-bfee-4dc30cc37367

# OpenAI (get from platform.openai.com)
OPENAI_API_KEY=sk-...

# Gmail SMTP (use an App Password — NOT your real password)
# Gmail → Account → Security → 2FA → App Passwords → generate one
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=xxxx-xxxx-xxxx-xxxx   # 16-char App Password

FROM_EMAIL=deals@proppilot.ai
FROM_NAME=PropPilot AI

# Forgemaster alert email
FORGEMASTER_EMAIL=your@gmail.com
```

### Step 2 — Run the engine

```bash
# One-time poll (check for new leads now)
python3 lead_followup_engine.py --poll

# Webhook server (real-time, runs 24/7)
python3 lead_followup_engine.py --server --port 5555

# Check status
python3 lead_followup_engine.py --status
```

### Step 3 — Wire webhook URL into landing page

Once the webhook server has a public URL (via ngrok or Cloudflare Tunnel):

In `prop_clone/index.html`, add this line before `handleLeadSubmit`:
```javascript
window.PROPPILOT_WEBHOOK = 'https://your-tunnel-url.trycloudflare.com';
```

Or if deployed to a server, the webhook runs at `http://your-server:5555/lead`.

---

## Deployment Options

### Option A: Netlify (Landing Page) + Cloudflare Tunnel (Engine)
- Deploy `prop_clone/index.html` to Netlify (free)
- Run `lead_followup_engine.py --server` in Termux/phone
- Use existing Cloudflare tunnel for webhook URL

### Option B: Full Server Deployment
- VPS or Render.com free tier
- Run everything server-side
- Most reliable for 24/7 follow-ups

### Option C: Poll-Based (No Server Needed)
- Set up a cron to run `--poll` every 5 minutes
- EmailOctopus already stores new leads
- No webhook URL needed in the page
- Slight delay (up to 5 min) vs real-time

---

## File Structure

```
logs/
  leads.json              ← All leads logged here
  forgemaster_alerts.json ← Forgemaster notifications
  email_queue.json        ← Emails pending (when no SMTP)
  leadbot.log             ← Engine activity log
```

---

## Sabrina.dev Template Mapping

| Sabrina Template Step   | PropPilot Equivalent              |
|-------------------------|-----------------------------------|
| Webflow form trigger    | EmailOctopus webhook / poll       |
| Google Sheets log       | logs/leads.json                   |
| OpenAI email draft      | lead_followup_engine.py → OpenAI  |
| HTML email send         | SMTP / Gmail App Password         |
| Slack notify            | Forgemaster email alert           |

---

## Test It

```bash
# Dry run with manual lead entry
python3 lead_followup_engine.py --manual

# Full status
python3 lead_followup_engine.py --status
```
