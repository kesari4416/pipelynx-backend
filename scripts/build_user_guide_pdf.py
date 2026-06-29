"""
Generate a polished PDF user guide for Pipelynx using ReportLab Platypus.
Run: python3 scripts/build_user_guide_pdf.py
Output: /app/docs/PIPELYNX_USER_GUIDE.pdf
"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, ListFlowable, ListItem, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas

OUTPUT_PATH = "/app/docs/PIPELYNX_USER_GUIDE.pdf"

# ---------- color palette (matches Pipelynx glassmorphism theme) ----------
INDIGO = colors.HexColor("#4F46E5")
PURPLE = colors.HexColor("#7C3AED")
SLATE_900 = colors.HexColor("#0F172A")
SLATE_700 = colors.HexColor("#334155")
SLATE_500 = colors.HexColor("#64748B")
SLATE_300 = colors.HexColor("#CBD5E1")
SLATE_100 = colors.HexColor("#F1F5F9")
SLATE_50 = colors.HexColor("#F8FAFC")
EMERALD = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
ROSE = colors.HexColor("#EF4444")
CODE_BG = colors.HexColor("#0F172A")
CODE_TEXT = colors.HexColor("#E2E8F0")


# ---------- styles ----------
ss = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
    fontSize=26, leading=32, textColor=SLATE_900, spaceBefore=18, spaceAfter=12,
)
H2 = ParagraphStyle(
    "H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
    fontSize=18, leading=24, textColor=INDIGO, spaceBefore=18, spaceAfter=8,
)
H3 = ParagraphStyle(
    "H3", parent=ss["Heading3"], fontName="Helvetica-Bold",
    fontSize=13, leading=17, textColor=SLATE_900, spaceBefore=12, spaceAfter=4,
)
BODY = ParagraphStyle(
    "Body", parent=ss["BodyText"], fontName="Helvetica",
    fontSize=10.5, leading=15.5, textColor=SLATE_700, spaceAfter=6, alignment=TA_LEFT,
)
SMALL = ParagraphStyle(
    "Small", parent=BODY, fontSize=9, textColor=SLATE_500, leading=12,
)
CODE = ParagraphStyle(
    "Code", parent=BODY, fontName="Courier", fontSize=9, leading=12,
    textColor=CODE_TEXT, backColor=CODE_BG,
    borderPadding=(8, 10, 8, 10), leftIndent=0, rightIndent=0, spaceAfter=10,
)
KICKER = ParagraphStyle(
    "Kicker", parent=BODY, fontSize=8, leading=10,
    textColor=INDIGO, spaceAfter=2,
)
CALLOUT_TITLE = ParagraphStyle(
    "CalloutTitle", parent=BODY, fontName="Helvetica-Bold",
    fontSize=10, leading=14, textColor=SLATE_900, spaceAfter=2,
)
CALLOUT_BODY = ParagraphStyle(
    "CalloutBody", parent=BODY, fontSize=9.5, leading=13, textColor=SLATE_700, spaceAfter=0,
)
COVER_TITLE = ParagraphStyle(
    "CoverTitle", parent=BODY, fontName="Helvetica-Bold",
    fontSize=44, leading=52, textColor=colors.white, alignment=TA_LEFT, spaceAfter=10,
)
COVER_SUB = ParagraphStyle(
    "CoverSub", parent=BODY, fontSize=14, leading=20, textColor=colors.HexColor("#C7D2FE"), spaceAfter=8,
)
COVER_META = ParagraphStyle(
    "CoverMeta", parent=BODY, fontSize=10, leading=14, textColor=colors.HexColor("#A5B4FC"),
)


def callout(title, body, accent=INDIGO, bg=colors.HexColor("#EEF2FF")):
    """Build a colored callout box."""
    inner = [
        Paragraph(f'<font color="{accent.hexval()}">●</font> &nbsp;<b>{title}</b>', CALLOUT_TITLE),
        Paragraph(body, CALLOUT_BODY),
    ]
    tbl = Table([[inner]], colWidths=[160 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return tbl


def code_block(text):
    """Render a code/command snippet with dark background."""
    safe = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    safe = safe.replace("\n", "<br/>")
    return Paragraph(safe, CODE)


def step(num, title, body=None, code=None):
    """Render a numbered step card."""
    parts = [Paragraph(f"<font color='{INDIGO.hexval()}'><b>STEP {num}</b></font>", KICKER),
             Paragraph(f"<b>{title}</b>", H3)]
    if body:
        parts.append(Paragraph(body, BODY))
    if code:
        parts.append(code_block(code))
    tbl = Table([[parts]], colWidths=[160 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_50),
        ("LINEBEFORE", (0, 0), (0, -1), 3, INDIGO),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([tbl, Spacer(1, 6)])


def bullet_list(items):
    return ListFlowable(
        [ListItem(Paragraph(i, BODY), leftIndent=10, bulletColor=INDIGO) for i in items],
        bulletType="bullet", start="circle", leftIndent=14,
    )


def hr():
    return HRFlowable(width="100%", thickness=0.6, color=SLATE_300, spaceBefore=6, spaceAfter=6)


# ---------- page chrome ----------
class PipelynxCanvas(canvas.Canvas):
    """Custom canvas: cover page gradient + footer page numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for idx, state in enumerate(self._saved_pages):
            self.__dict__.update(state)
            self._draw_chrome(idx + 1, total)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_num, total_pages):
        if page_num == 1:
            return  # Cover page draws its own background
        # Header bar
        self.setFillColor(SLATE_50)
        self.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
        self.setFillColor(SLATE_500)
        self.setFont("Helvetica-Bold", 8)
        self.drawString(15 * mm, A4[1] - 9 * mm, "PIPELYNX  ·  USER GUIDE")
        self.setFillColor(INDIGO)
        self.drawRightString(A4[0] - 15 * mm, A4[1] - 9 * mm, "pipelynx.io")
        # Footer
        self.setFillColor(SLATE_500)
        self.setFont("Helvetica", 8)
        self.drawString(15 * mm, 8 * mm, "© Sparkcurv Technologies · Nagercoil, India")
        self.drawRightString(A4[0] - 15 * mm, 8 * mm, f"Page {page_num} of {total_pages}")


def draw_cover_background(c, doc):
    """Indigo→purple gradient cover background drawn behind cover frame."""
    width, height = A4
    # Background gradient simulated with horizontal slices
    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        r = (0.31 * (1 - t)) + (0.49 * t)  # 4F46E5 → 7C3AED-ish
        g = (0.27 * (1 - t)) + (0.23 * t)
        b = (0.90 * (1 - t)) + (0.92 * t)
        c.setFillColorRGB(r, g, b)
        c.rect(0, height - (i + 1) * (height / steps), width, height / steps + 0.5, fill=1, stroke=0)
    # Decorative orbs
    c.setFillColorRGB(1, 1, 1, alpha=0.08)
    c.circle(width * 0.85, height * 0.78, 90, fill=1, stroke=0)
    c.circle(width * 0.15, height * 0.20, 110, fill=1, stroke=0)


# ---------- build content ----------
def build_cover():
    return [
        Spacer(1, 80 * mm),
        Paragraph("Pipelynx", COVER_TITLE),
        Paragraph("Enterprise CI/CD pipeline monitoring & analytics", COVER_SUB),
        Spacer(1, 4 * mm),
        Paragraph(
            "User Guide · How everything works and how to use it",
            ParagraphStyle("CoverTag", parent=COVER_SUB, fontSize=11, textColor=colors.white),
        ),
        Spacer(1, 70 * mm),
        Paragraph(
            f"Version 1.0 · {datetime.now().strftime('%B %Y')}<br/>"
            "Sparkcurv Technologies Pvt. Ltd.<br/>"
            "Nagercoil, Tamil Nadu",
            COVER_META,
        ),
    ]


def section_overview():
    return [
        PageBreak(),
        Paragraph("1. What is Pipelynx?", H1),
        Paragraph(
            "Pipelynx is a single-pane-of-glass platform that watches every CI/CD pipeline in your engineering "
            "organization, normalizes the events, and turns them into actionable signal — DORA metrics, failure "
            "patterns, real-time live dashboards, and multi-channel alerts.",
            BODY,
        ),
        Paragraph(
            "Instead of jumping between GitHub Actions, Jenkins, GitLab CI, CircleCI, ArgoCD, AWS CodePipeline "
            "and Bitbucket tabs, every build, deploy and push lands in one place — searchable, comparable, "
            "AI-analyzed, and alertable.",
            BODY,
        ),
        Spacer(1, 6),
        callout(
            "What you get out of the box",
            "Real-time live view of every running build · Per-platform stats · DORA metrics "
            "(Deployment Frequency, Lead Time, MTTR, Change Failure Rate) · AI failure analysis · "
            "Slack + Email alerts · Multi-tenant org & RBAC · Plan-based quotas.",
        ),
        Spacer(1, 10),
        Paragraph("Supported platforms", H3),
        bullet_list([
            "<b>GitHub Actions</b> — workflow runs, jobs, check runs, pushes (webhook + pull)",
            "<b>Jenkins</b> — Freestyle, Pipeline, Multibranch (Notification plugin webhook + JSON API pull)",
            "<b>GitLab CI</b> — pipelines, jobs, pushes (gitlab.com or self-hosted)",
            "<b>CircleCI</b> — workflow + job webhooks",
            "<b>ArgoCD</b> — sync notifications for GitOps deploys",
            "<b>AWS CodePipeline</b> — via SNS / EventBridge",
            "<b>Bitbucket Pipelines</b> — push + build status webhooks",
        ]),
    ]


def section_architecture():
    return [
        Paragraph("2. How it works (under the hood)", H1),
        Paragraph(
            "Pipelynx has three layers that work together — an ingestion layer that accepts events, a normalization "
            "layer that maps them to a unified schema, and an analytics layer that produces metrics, alerts and AI insights.",
            BODY,
        ),
        Spacer(1, 6),
        Paragraph("The data flow", H3),
        bullet_list([
            "<b>Ingest</b> — CI/CD systems either push events to <font face='Courier'>/api/v1/webhooks/{platform}</font>, "
            "or Pipelynx pulls them every 60s via the platform's REST API.",
            "<b>Parse</b> — A platform-specific parser converts the raw payload into a normalized "
            "<font face='Courier'>PipelineRun</font> document (status, branch, commit, duration, author, error message).",
            "<b>Persist</b> — Stored in MongoDB (primary) and optionally streamed to a TimescaleDB hypertable for "
            "long-term time-series analytics.",
            "<b>React</b> — Alert rules fire, AI insights are generated on demand, the Live page updates within 5 seconds.",
        ]),
        Spacer(1, 6),
        callout(
            "Why two ingestion modes?",
            "<b>Webhooks</b> are real-time and zero-cost — recommended whenever your CI/CD system can reach Pipelynx. "
            "<b>Pull mode</b> covers the cases webhooks can't — Jenkins behind a corporate firewall, GitLab projects "
            "you only have read access to, audit-only setups. Pipelynx polls every 60 seconds.",
            accent=AMBER,
            bg=colors.HexColor("#FEF3C7"),
        ),
        Spacer(1, 6),
        Paragraph("Multi-tenant design", H3),
        Paragraph(
            "Every record (integration, pipeline, run, alert, AI usage) is scoped to an <b>Organization</b>. "
            "When you register, an org is created automatically and you become its admin. You can invite teammates "
            "with role-based access (admin / member / viewer).",
            BODY,
        ),
    ]


def section_account():
    return [
        PageBreak(),
        Paragraph("3. Getting started", H1),
        Paragraph(
            "Pipelynx ships with a one-click signup. You don't need to install anything — just open the app in "
            "your browser and create an account.",
            BODY,
        ),
        step(
            1,
            "Create your account",
            "Visit your Pipelynx URL and click <b>Get started</b>. Enter your full name, work email, password, and "
            "an organization name. You'll be the admin of this org with the <b>Free plan</b> by default.",
        ),
        step(
            2,
            "Sign in",
            "From now on, sign in at <font face='Courier'>/auth/login</font> with your email + password. Sessions "
            "last 7 days. The pre-seeded super-admin (for self-hosted deploys) is:",
            code="admin@sparkcurv.com   /   Aiden@1996",
        ),
        step(
            3,
            "Land on the Overview dashboard",
            "After login you'll see DORA metrics, an activity summary, and a 30-day timeline of pipeline runs. "
            "If you haven't connected any platforms yet, the dashboard will guide you to the Integrations page.",
        ),
    ]


def section_integrations():
    return [
        PageBreak(),
        Paragraph("4. Connecting your CI/CD platforms", H1),
        Paragraph(
            "From the <b>Integrations</b> page (left-nav · Integrations) you can add as many CI/CD platforms as your "
            "plan allows. Each connection has two modes:",
            BODY,
        ),
        bullet_list([
            "<b>Webhook mode</b> (default & recommended) — your CI/CD system pushes events to Pipelynx in real time.",
            "<b>Pull mode</b> — Pipelynx polls the CI/CD system's REST API every 60 seconds. Available for GitHub, "
            "GitLab and Jenkins.",
        ]),
        Spacer(1, 8),

        Paragraph("4.1 GitHub Actions", H2),
        Paragraph(
            "GitHub is the most common starting point. Webhook mode covers every workflow run, job, check run and "
            "push event from the repo or organization you connect.",
            BODY,
        ),
        step(
            1,
            "Add the integration",
            "Open <b>Integrations → Add Integration</b>, pick <b>GitHub Actions</b>, give it a name, and click "
            "<b>Connect</b>. A Setup Guide modal opens automatically.",
        ),
        step(
            2,
            "Copy the webhook URL",
            "The modal shows your unique webhook URL. Paste it into GitHub at "
            "<b>Settings → Webhooks → Add webhook</b>. For org-wide monitoring, use the org's Settings → Webhooks page.",
            code="https://your-pipelynx-domain/api/v1/webhooks/github",
        ),
        step(
            3,
            "Choose events",
            "Set <b>Content type</b> to <font face='Courier'>application/json</font>. Choose 'Let me select individual "
            "events' and tick: Workflow runs · Workflow jobs · Check runs · Pushes. Save.",
        ),
        step(
            4,
            "Trigger a workflow",
            "Push a commit or run a workflow manually. Within seconds the run appears on the Pipelynx <b>Live</b> page "
            "and is counted in your DORA metrics.",
        ),
        callout(
            "Pull mode for GitHub",
            "Choose <b>Pull mode</b> in the Add modal. Paste a Personal Access Token (PAT) with "
            "<font face='Courier'>repo</font> + <font face='Courier'>actions:read</font> scopes and list the repos as "
            "<font face='Courier'>owner/repo</font>, comma-separated. Pipelynx will poll every 60s.",
        ),

        PageBreak(),
        Paragraph("4.2 Jenkins", H2),
        Paragraph(
            "Jenkins integrations work in two ways: the official Notification plugin (push) or polling the Jenkins JSON "
            "API with a username + API token (pull, ideal when Jenkins is behind a VPN / firewall).",
            BODY,
        ),
        step(
            1,
            "Install the Notification plugin",
            "On your Jenkins controller go to <b>Manage Jenkins → Plugins → Available</b>, search for "
            "<b>Notification</b>, install, restart.",
        ),
        step(
            2,
            "Add the endpoint on every job",
            "<b>Configure → Job Notifications → Add endpoint.</b> Set Format=JSON, Protocol=HTTP, Event=All Events, "
            "and paste the URL:",
            code="https://your-pipelynx-domain/api/v1/webhooks/jenkins",
        ),
        step(
            3,
            "Or use a Jenkinsfile post block",
            "If you prefer code-as-config, add this to every Jenkinsfile:",
            code=(
                "post {\n"
                "  always {\n"
                "    httpRequest httpMode: 'POST',\n"
                "      contentType: 'APPLICATION_JSON',\n"
                "      url: 'https://your-pipelynx-domain/api/v1/webhooks/jenkins',\n"
                "      requestBody: \"\"\"{\n"
                "        \"name\": \"${env.JOB_NAME}\",\n"
                "        \"build\": {\n"
                "          \"number\": ${env.BUILD_NUMBER},\n"
                "          \"phase\": \"COMPLETED\",\n"
                "          \"status\": \"${currentBuild.currentResult}\",\n"
                "          \"full_url\": \"${env.BUILD_URL}\",\n"
                "          \"duration\": ${currentBuild.duration ?: 0},\n"
                "          \"timestamp\": ${currentBuild.startTimeInMillis}\n"
                "        }\n"
                "      }\"\"\"\n"
                "  }\n"
                "}"
            ),
        ),
        callout(
            "Pull mode for Jenkins (firewalled installs)",
            "In Add Integration, pick <b>Pull mode</b>. Provide your Jenkins base URL "
            "(<font face='Courier'>https://jenkins.example.com</font>), the username, the API token "
            "(<b>Profile → Configure → Add new token</b>), and a comma-separated list of jobs you want monitored "
            "(folder paths like <font face='Courier'>mobile/build-ios</font> are supported).",
            accent=AMBER, bg=colors.HexColor("#FEF3C7"),
        ),

        PageBreak(),
        Paragraph("4.3 GitLab CI", H2),
        Paragraph(
            "GitLab integrations cover Pipeline events, Job events and Push events — for both gitlab.com and "
            "self-hosted GitLab installations.",
            BODY,
        ),
        step(
            1,
            "Add the integration",
            "Integrations → Add Integration → <b>GitLab CI</b>. Webhook URL is shown in the Setup Guide modal.",
            code="https://your-pipelynx-domain/api/v1/webhooks/gitlab",
        ),
        step(
            2,
            "Configure the webhook in GitLab",
            "In your project: <b>Settings → Webhooks → Add new webhook</b>. Paste the Pipelynx URL. Enable: "
            "✓ Push events ✓ Pipeline events ✓ Job events. Keep SSL verification on.",
        ),
        step(
            3,
            "Test the webhook",
            "Click <b>Test → Pipeline events</b>. You should receive 200 OK. A test run will appear in your Pipelynx "
            "Live page.",
        ),
        step(
            4,
            "Cover multiple projects with one group webhook",
            "If you have many projects under one GitLab group, add the webhook at the <b>group level</b> instead — "
            "Pipelynx will receive events from every project under that group automatically.",
        ),
        callout(
            "Pull mode for GitLab",
            "Provide the base URL (<font face='Courier'>https://gitlab.com</font> or your self-hosted address), a "
            "Personal Access Token with <b>read_api</b> scope, and a comma-separated list of project IDs or "
            "<font face='Courier'>namespace/project</font> paths.",
        ),

        Paragraph("4.4 Other platforms", H2),
        Paragraph(
            "CircleCI, ArgoCD, AWS CodePipeline and Bitbucket Pipelines all support webhook mode via the same "
            "Setup Guide modal. Click <b>Setup Guide</b> on any integration card to see step-by-step instructions "
            "for that platform — including the exact webhook URL, required scopes, and a copy-paste config block.",
            BODY,
        ),
    ]


def section_using():
    return [
        PageBreak(),
        Paragraph("5. Using Pipelynx day-to-day", H1),

        Paragraph("5.1 The Overview dashboard", H2),
        Paragraph(
            "The Overview is where most people land each morning. It shows the four DORA metrics across the time "
            "window you pick (7d / 30d / 90d), plus an activity summary (total runs, success rate, failures, "
            "average duration) and a daily run-volume chart.",
            BODY,
        ),
        bullet_list([
            "<b>Deployment Frequency</b> — successful runs per day (deploys/day).",
            "<b>Lead Time</b> — median minutes from commit-push to successful build.",
            "<b>Change Failure Rate</b> — % of runs that failed in the window.",
            "<b>MTTR (Mean Time to Recovery)</b> — average minutes between a failure and the next success on the same repo.",
        ]),

        Paragraph("5.2 The Live page", H2),
        Paragraph(
            "<b>Live</b> (the second item in the nav) is a real-time monitor of every running and queued build "
            "across every connected platform. It auto-refreshes every 5 seconds.",
            BODY,
        ),
        bullet_list([
            "<b>Stat tiles</b> at the top show in-flight, running, queued and active-source counts.",
            "<b>By-platform breakdown</b> displays per-source running / queued / failure counts at a glance.",
            "<b>In-flight cards</b> show each running build with branch, repo, author, elapsed time and a shimmering progress bar.",
            "<b>Most recent</b> timeline below shows the last 20 completed runs — click any row to jump to the run details page.",
            "<b>Filter pills</b> (All / GitHub / Jenkins / GitLab) narrow the view.",
            "<b>Pause / Resume</b> freezes the auto-refresh when you're investigating a specific build.",
        ]),

        Paragraph("5.3 Runs and run details", H2),
        Paragraph(
            "The <b>Runs</b> page is a sortable, filterable table of every pipeline run ever ingested. You can "
            "filter by source, status, or pipeline; click any row to open the run details page with branch, commit, "
            "author, full timeline, error message and the AI-generated log summary (Phase 4+).",
            BODY,
        ),

        Paragraph("5.4 AI Insights", H2),
        Paragraph(
            "Pipelynx ships with an AI Insights panel that uses OpenAI (via the Emergent Universal LLM Key) to:",
            BODY,
        ),
        bullet_list([
            "<b>Analyze a single failure</b> — open any failed run and click <b>Analyze with AI</b>. You'll get a "
            "summary of why the build failed and suggested fixes.",
            "<b>Detect failure patterns</b> across the last N days (Business plan and above).",
            "<b>Weekly digest</b> — a one-paragraph summary of the most important pipeline activity (Business+).",
            "<b>Anomaly detection</b> — surface duration spikes and unusual failure clusters (Business+).",
        ]),
        callout(
            "AI usage quotas",
            "Free plan: 0 AI analyses/day. Basic: 10/day. Business & Enterprise: unlimited. Quotas are enforced "
            "server-side; if you exceed your daily quota you'll see the Upgrade modal pointing to the right plan.",
        ),

        PageBreak(),
        Paragraph("5.5 Alerts & Notifications", H2),
        Paragraph(
            "Alerts let Pipelynx notify you when a pipeline matches a condition you care about. Each rule has:",
            BODY,
        ),
        bullet_list([
            "<b>Trigger conditions</b> — match by status, source, branch, repository, or duration threshold.",
            "<b>Channels</b> — Email, Slack, or generic webhook (e.g. PagerDuty, Opsgenie).",
            "<b>Channel config</b> — recipient email list, Slack incoming-webhook URL, or webhook target.",
        ]),
        step(
            1,
            "Create an alert rule",
            "<b>Alerts → New Rule</b>. Pick the conditions (e.g. status = failure, source = github, branch = main). "
            "Choose a channel. Paste recipients or webhook URL.",
        ),
        step(
            2,
            "Test the channel",
            "Before saving, click <b>Send test</b>. Pipelynx will send a fake failure alert through the channel so "
            "you can verify it lands.",
        ),
        step(
            3,
            "Save and forget",
            "Now whenever a pipeline run matches the rule, Pipelynx will dispatch the notification "
            "and log it under <b>Alerts → History</b>.",
        ),

        Paragraph("Email delivery", H3),
        Paragraph(
            "Email notifications go out through SMTP. The platform comes configured with Gmail SMTP "
            "(<font face='Courier'>smtp.gmail.com:587</font>, STARTTLS, App Password). For production you can switch "
            "to SendGrid / SES / Resend by updating the <font face='Courier'>SMTP_*</font> environment variables in "
            "<font face='Courier'>backend/.env</font>:",
            BODY,
        ),
        code_block(
            "SMTP_HOST=smtp.gmail.com\n"
            "SMTP_PORT=587\n"
            "SMTP_USER=alerts@your-company.com\n"
            "SMTP_PASSWORD=•••••••••••\n"
            "SMTP_FROM_EMAIL=alerts@your-company.com\n"
            "SMTP_FROM_NAME=Your Company Alerts\n"
            "SMTP_USE_TLS=true"
        ),
        Paragraph(
            "Each email includes the run name, status, repo + branch, source, duration, error message, and a "
            "direct link back to the run in the CI/CD system.",
            BODY,
        ),
    ]


def section_billing():
    return [
        PageBreak(),
        Paragraph("6. Billing & Plans", H1),
        Paragraph(
            "Pipelynx is offered in four tiers — Free, Basic, Business, Enterprise. Plan limits are enforced "
            "server-side: when you exceed a quota, the API returns <b>HTTP 402 Payment Required</b> and the UI "
            "opens an Upgrade modal pointing to the right plan.",
            BODY,
        ),
        Spacer(1, 4),
        Table(
            [
                ["Feature", "Free", "Basic", "Business", "Enterprise"],
                ["Integrations", "1", "3", "10", "Unlimited"],
                ["Users", "1", "5", "20", "Unlimited"],
                ["Runs / month", "1,000", "20,000", "100,000", "Unlimited"],
                ["Retention", "7 days", "30 days", "90 days", "365 days"],
                ["AI analyses / day", "0", "10", "Unlimited", "Unlimited"],
                ["Alert channels", "Email", "Email + Slack", "+ Webhook + PagerDuty", "+ Custom"],
                ["Anomaly / patterns", "—", "—", "✓", "✓"],
                ["Weekly digest", "—", "—", "✓", "✓"],
            ],
            colWidths=[55 * mm, 25 * mm, 25 * mm, 30 * mm, 30 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_50, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, SLATE_300),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 12),
        Paragraph(
            "To upgrade, open <b>Pricing</b> from the public site (or the link in the Upgrade modal). When real "
            "payment processing is enabled, you'll be routed to Stripe / Razorpay; meanwhile the system records "
            "your billing intent and operations team will reach out to provision the plan manually.",
            BODY,
        ),
    ]


def section_troubleshooting():
    return [
        PageBreak(),
        Paragraph("7. Troubleshooting & FAQ", H1),

        Paragraph("\"I added a webhook but nothing shows up.\"", H3),
        bullet_list([
            "Check the integration is listed under <b>Integrations → Connected</b> with status Active.",
            "In your CI/CD system, open the webhook's <b>Recent Deliveries</b> log. Pipelynx should respond with HTTP 200.",
            "If you see 401/403, the integration was likely deleted in Pipelynx — re-add it.",
            "Trigger an event manually (push a commit, run a workflow) — Pipelynx parses the event and shows it on Live within ~5 seconds.",
        ]),

        Paragraph("\"Pull-mode integration isn't pulling.\"", H3),
        bullet_list([
            "Hit the <b>Sync now</b> button on the integration card — you'll get an immediate result toast.",
            "Open the Setup Guide to check the API token scopes (GitHub: repo + actions:read; GitLab: read_api; Jenkins: admin or job/read).",
            "Verify the base URL for self-hosted Jenkins / GitLab matches what the CI/CD system actually serves on (no trailing slash needed).",
        ]),

        Paragraph("\"Emails aren't arriving.\"", H3),
        bullet_list([
            "Go to <b>Alerts → New Rule → Send test</b> with your address — you'll get a result toast immediately.",
            "Check your spam folder. Gmail can quarantine the first message from a new sender.",
            "If you replaced the SMTP creds, restart the backend (<font face='Courier'>sudo supervisorctl restart backend</font>) so the new env vars are picked up.",
        ]),

        Paragraph("\"Live page shows no runs.\"", H3),
        bullet_list([
            "It only shows <b>running</b> and <b>queued</b> runs in the top half. If everything's idle, that's expected — the bottom 'Most recent' section will still show your last 20 runs.",
            "Use the source filter pills to narrow by platform.",
            "Pause auto-refresh if you want to inspect a specific build without losing the state.",
        ]),

        Paragraph("Where to get help", H3),
        Paragraph(
            "Email <b>support@sparkcurv.com</b> · Docs portal at <b>pipelynx.io/docs</b> (coming soon) · "
            "For deployment / self-hosted questions consult <font face='Courier'>INSTALLATION.md</font> in the repo.",
            BODY,
        ),
    ]


def section_appendix():
    return [
        PageBreak(),
        Paragraph("Appendix A — REST API at a glance", H1),
        Paragraph("Everything you see in the UI is backed by a REST API. The most useful endpoints:", BODY),
        Table(
            [
                ["Method · Path", "What it does"],
                ["POST /api/v1/auth/register", "Create a new account + organization"],
                ["POST /api/v1/auth/login", "Get a JWT access token (7-day expiry)"],
                ["GET  /api/v1/auth/me", "Current user"],
                ["GET  /api/v1/pipelines/integrations", "List your CI/CD integrations"],
                ["POST /api/v1/pipelines/integrations", "Add an integration (webhook or pull mode)"],
                ["GET  /api/v1/pipelines/integrations/{id}/setup-guide", "Per-platform setup steps"],
                ["POST /api/v1/pipelines/integrations/{id}/sync", "Trigger a pull-mode sync now"],
                ["DELETE /api/v1/pipelines/integrations/{id}", "Remove an integration"],
                ["POST /api/v1/webhooks/{platform}", "Ingest a CI/CD event (no auth)"],
                ["GET  /api/v1/runs/", "List runs with filters"],
                ["GET  /api/v1/runs/live", "Live: in-flight + recent + per-source aggregation"],
                ["GET  /api/v1/runs/{id}", "Run detail"],
                ["GET  /api/v1/metrics/dora", "DORA metrics for a time window"],
                ["GET  /api/v1/metrics/summary", "Run counts + success rate"],
                ["POST /api/v1/ai/runs/{id}/analyze", "AI failure analysis for one run"],
                ["GET  /api/v1/ai/patterns", "AI failure patterns (Business+)"],
                ["GET  /api/v1/alerts/rules", "List alert rules"],
                ["POST /api/v1/alerts/rules", "Create a new alert rule"],
                ["POST /api/v1/alerts/test", "Send a test notification through any channel"],
                ["GET  /api/v1/billing/limits", "Current plan + live quota usage"],
            ],
            colWidths=[85 * mm, 75 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Courier"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SLATE_50, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, SLATE_300),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 14),
        callout(
            "API authentication",
            "Every request (except <font face='Courier'>/auth/*</font> and <font face='Courier'>/webhooks/*</font>) "
            "needs a Bearer token: <font face='Courier'>Authorization: Bearer &lt;your-jwt&gt;</font>. Tokens are "
            "obtained via <font face='Courier'>POST /auth/login</font>.",
        ),
    ]


# ---------- main ----------
def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="Pipelynx — User Guide",
        author="Sparkcurv Technologies",
    )

    # Hack: paint cover background on first page via onFirstPage
    def on_first_page(canv, _doc):
        draw_cover_background(canv, _doc)

    story = []
    story += build_cover()
    story += section_overview()
    story += section_architecture()
    story += section_account()
    story += section_integrations()
    story += section_using()
    story += section_billing()
    story += section_troubleshooting()
    story += section_appendix()

    doc.build(story, onFirstPage=on_first_page, canvasmaker=PipelynxCanvas)
    size = os.path.getsize(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH} ({size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
