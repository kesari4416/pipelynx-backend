"""
Parser registry - central dispatch for all CI/CD event parsers.
Routes events to the appropriate parser based on source.
"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser
from app.services.event_parsers.github import GitHubEventParser
from app.services.event_parsers.gitlab import GitLabEventParser
from app.services.event_parsers.jenkins import JenkinsEventParser
from app.services.event_parsers.circleci import CircleCIEventParser
from app.services.event_parsers.argocd import ArgoCDEventParser
from app.services.event_parsers.aws import AWSEventParser
from app.services.event_parsers.bitbucket import BitbucketEventParser


# Registry: source name → parser instance
PARSER_REGISTRY: Dict[str, BaseEventParser] = {
    "github": GitHubEventParser(),
    "gitlab": GitLabEventParser(),
    "jenkins": JenkinsEventParser(),
    "circleci": CircleCIEventParser(),
    "argocd": ArgoCDEventParser(),
    "aws": AWSEventParser(),
    "bitbucket": BitbucketEventParser(),
}


def get_parser(source: str) -> Optional[BaseEventParser]:
    """Get parser by source name"""
    return PARSER_REGISTRY.get(source.lower())


def parse_event(source: str, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a CI/CD event using the appropriate parser.
    Returns normalized PipelineRun dict, or None if event cannot be parsed.
    """
    parser = get_parser(source)
    if not parser:
        return None
    if not parser.can_parse(event_type, payload):
        return None
    return parser.parse(event_type, payload)
