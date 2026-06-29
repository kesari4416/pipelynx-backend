"""
Per-platform setup guides for connecting CI/CD systems to Pipelynx.

Each guide returns:
  - mode: "webhook" or "pull"
  - title, summary
  - steps: ordered list of { title, body, code?, code_lang?, link? }
"""
from typing import Dict, Any, List, Optional
from app.core.config import settings


def _backend_base_url(override: Optional[str] = None) -> str:
    """Return the public backend URL (used to build webhook endpoints shown to users)."""
    import os
    if override:
        return override.rstrip("/")
    return (os.environ.get("PUBLIC_BACKEND_URL") or "<your-pipelynx-domain>").rstrip("/")


def _webhook_url(platform: str, base_url: Optional[str] = None) -> str:
    return f"{_backend_base_url(base_url)}/api/v1/webhooks/{platform}"


def _github_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    secret = (integration.get("config") or {}).get("webhook_secret") or "your-webhook-secret"
    return {
        "mode": "webhook",
        "title": "Connect GitHub Actions",
        "summary": "Stream every workflow run, job and push from any GitHub repo or organization into Pipelynx.",
        "steps": [
            {
                "title": "1. Open the repository's webhook settings",
                "body": "Go to your repo on GitHub and navigate to: Settings → Webhooks → Add webhook. For organization-wide monitoring use Org Settings → Webhooks.",
                "link": "https://docs.github.com/webhooks",
            },
            {
                "title": "2. Paste the Pipelynx Payload URL",
                "body": "Use the URL below as the webhook target. Content type must be application/json.",
                "code": _webhook_url("github", base_url),
                "code_lang": "text",
            },
            {
                "title": "3. (Optional) Add a secret",
                "body": "Add this secret to GitHub and Pipelynx will verify the signature on each delivery.",
                "code": secret,
                "code_lang": "text",
            },
            {
                "title": "4. Choose events to send",
                "body": "Select 'Let me select individual events' and enable: Workflow runs, Workflow jobs, Check runs, Pushes. Click 'Add webhook'.",
            },
            {
                "title": "5. Trigger a workflow",
                "body": "Push any commit or run a workflow manually. Within seconds you'll see the run appear on the Runs page.",
            },
        ],
    }


def _gitlab_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "mode": "webhook",
        "title": "Connect GitLab CI",
        "summary": "Receive every GitLab pipeline, job and push event in Pipelynx — works for gitlab.com and self-hosted.",
        "steps": [
            {
                "title": "1. Open the project Webhooks page",
                "body": "In your GitLab project, go to: Settings → Webhooks → Add new webhook.",
                "link": "https://docs.gitlab.com/ee/user/project/integrations/webhooks.html",
            },
            {
                "title": "2. Use the Pipelynx URL",
                "body": "Paste this URL as the webhook target:",
                "code": _webhook_url("gitlab", base_url),
                "code_lang": "text",
            },
            {
                "title": "3. Select trigger events",
                "body": "Enable these checkboxes: ✓ Push events ✓ Pipeline events ✓ Job events. Leave SSL verification enabled.",
            },
            {
                "title": "4. Save & test",
                "body": "Click 'Add webhook', then 'Test → Pipeline events'. Pipelynx should receive a 200 OK and the test run appears in the Live Pipelines view.",
            },
            {
                "title": "5. For groups / self-hosted",
                "body": "Repeat for additional projects, or add a Group-level webhook (Settings → Webhooks at the group root) to cover every project under that group.",
            },
        ],
    }


def _jenkins_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    webhook = _webhook_url("jenkins", base_url)
    return {
        "mode": "webhook",
        "title": "Connect Jenkins",
        "summary": "Stream every Jenkins build into Pipelynx using the official Notification plugin (works for Freestyle, Pipeline and Multibranch jobs).",
        "steps": [
            {
                "title": "1. Install the Notification plugin",
                "body": "On your Jenkins controller go to: Manage Jenkins → Plugins → Available → search 'Notification'. Install and restart.",
                "link": "https://plugins.jenkins.io/notification/",
            },
            {
                "title": "2. Add a Job Notification endpoint",
                "body": "Open your job → Configure → 'Job Notifications' section → Add Endpoint. Set Format = JSON, Protocol = HTTP, Event = 'All Events'.",
            },
            {
                "title": "3. Use this URL",
                "body": "Paste this as the endpoint URL:",
                "code": webhook,
                "code_lang": "text",
            },
            {
                "title": "4. Or use a Pipeline post-build step",
                "body": "If you prefer code-based config, add this to your Jenkinsfile post block:",
                "code": (
                    "post {\n"
                    "  always {\n"
                    "    httpRequest httpMode: 'POST',\n"
                    "      contentType: 'APPLICATION_JSON',\n"
                    f"      url: '{webhook}',\n"
                    "      requestBody: \"\"\"{\n"
                    "        \"name\": \"${env.JOB_NAME}\",\n"
                    "        \"build\": {\n"
                    "          \"number\": ${env.BUILD_NUMBER},\n"
                    "          \"phase\": \"COMPLETED\",\n"
                    "          \"status\": \"${currentBuild.currentResult}\",\n"
                    "          \"full_url\": \"${env.BUILD_URL}\",\n"
                    "          \"duration\": ${currentBuild.duration ?: 0},\n"
                    "          \"timestamp\": ${currentBuild.startTimeInMillis},\n"
                    "          \"scm\": { \"branch\": \"${env.BRANCH_NAME ?: 'main'}\", \"commit\": \"${env.GIT_COMMIT ?: ''}\" }\n"
                    "        }\n"
                    "      }\"\"\"\n"
                    "  }\n"
                    "}"
                ),
                "code_lang": "groovy",
            },
            {
                "title": "5. Trigger a build",
                "body": "Run the job. Within seconds the build will show up on the Pipelynx Runs page with status, duration and branch information.",
            },
        ],
    }


def _bitbucket_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "mode": "webhook",
        "title": "Connect Bitbucket Pipelines",
        "summary": "Receive Bitbucket Pipelines build status events directly in Pipelynx.",
        "steps": [
            {
                "title": "1. Open repository webhooks",
                "body": "In your Bitbucket repo: Repository settings → Webhooks → Add webhook.",
            },
            {
                "title": "2. Use the Pipelynx URL",
                "code": _webhook_url("bitbucket", base_url),
                "code_lang": "text",
                "body": "Paste this as the webhook URL.",
            },
            {
                "title": "3. Select triggers",
                "body": "Enable 'Repository push' and 'Build status created/updated'. Save.",
            },
        ],
    }


def _circleci_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "mode": "webhook",
        "title": "Connect CircleCI",
        "summary": "Stream CircleCI workflow + job events into Pipelynx.",
        "steps": [
            {
                "title": "1. Project Settings → Webhooks",
                "body": "Open your CircleCI project → Project Settings → Webhooks → 'Add Webhook'.",
                "link": "https://circleci.com/docs/webhooks/",
            },
            {
                "title": "2. Use the Pipelynx URL",
                "code": _webhook_url("circleci", base_url),
                "code_lang": "text",
                "body": "Paste this URL as the webhook target.",
            },
            {
                "title": "3. Enable events",
                "body": "Enable both 'Workflow Completed' and 'Job Completed' events. Save.",
            },
        ],
    }


def _argocd_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "mode": "webhook",
        "title": "Connect ArgoCD",
        "summary": "Receive ArgoCD sync events to track GitOps deploys alongside CI runs.",
        "steps": [
            {
                "title": "1. Configure ArgoCD Notifications",
                "body": "Add a webhook trigger in your argocd-notifications-cm ConfigMap targeting Pipelynx.",
                "link": "https://argo-cd.readthedocs.io/en/stable/operator-manual/notifications/services/webhook/",
            },
            {
                "title": "2. Use this webhook URL",
                "code": _webhook_url("argocd", base_url),
                "code_lang": "text",
                "body": "Set this as the webhook 'url' in your notifications ConfigMap.",
            },
        ],
    }


def _aws_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "mode": "webhook",
        "title": "Connect AWS CodePipeline",
        "summary": "Stream AWS CodePipeline events into Pipelynx via CloudWatch / SNS → HTTPS.",
        "steps": [
            {
                "title": "1. Create an SNS topic",
                "body": "In AWS Console → SNS → Create topic (Standard).",
            },
            {
                "title": "2. Subscribe Pipelynx",
                "body": "Add an HTTPS subscription with this endpoint:",
                "code": _webhook_url("aws", base_url),
                "code_lang": "text",
            },
            {
                "title": "3. Hook up CodePipeline → EventBridge → SNS",
                "body": "Create an EventBridge rule for source aws.codepipeline (pipeline + stage + action events) and target the SNS topic.",
                "link": "https://docs.aws.amazon.com/codepipeline/latest/userguide/detect-state-changes-cloudwatch-events.html",
            },
        ],
    }


_GUIDES = {
    "github": _github_guide,
    "gitlab": _gitlab_guide,
    "jenkins": _jenkins_guide,
    "bitbucket": _bitbucket_guide,
    "circleci": _circleci_guide,
    "argocd": _argocd_guide,
    "aws": _aws_guide,
}


def build_setup_guide(integration: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    """Return a structured setup guide for the given integration."""
    builder = _GUIDES.get(integration.get("type", "").lower())
    if not builder:
        return {
            "mode": "webhook",
            "title": "Webhook setup",
            "summary": "Send platform events to this URL.",
            "steps": [
                {
                    "title": "Webhook URL",
                    "code": _webhook_url(integration.get("type", "unknown"), base_url),
                    "code_lang": "text",
                    "body": "Post your CI/CD events to this URL.",
                },
            ],
        }
    return builder(integration, base_url)


def all_platform_guides(base_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """List the setup guides for every supported platform (for the marketing/setup pages)."""
    return [
        {"type": key, **builder({"type": key, "config": {}}, base_url)}
        for key, builder in _GUIDES.items()
    ]
