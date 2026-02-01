"""
Pytest configuration and fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_good_email():
    """Sample high-quality email for testing."""
    return {
        "subject": "Quick thought on your marketing automation stack",
        "body": """Hi Marcus,

Noticed your agency just won the B2B SaaS campaign award—congrats! Running campaigns at that scale usually means your team is drowning in manual reporting and client updates.

We've helped agencies like Directive and WebMechanix cut 15 hours/week of busywork by automating their client reporting with AI. No dashboards to build—just Slack pings when metrics move.

Worth a 15-minute call to see if it fits your workflow?

Best,
Sarah"""
    }


@pytest.fixture
def sample_poor_email():
    """Sample low-quality email for testing."""
    return {
        "subject": "REVOLUTIONARY AI SOLUTION FOR YOUR BUSINESS!!!",
        "body": """Hi there,

I hope this email finds you well! I'm reaching out because I think our revolutionary AI platform could be a game-changer for your business.

We offer cutting-edge solutions that leverage artificial intelligence to streamline operations. Our platform has helped countless companies achieve massive growth.

I'd love to schedule a call to tell you more about what we can do. Are you free for an hour-long demo next week? You can also visit our website or call me directly!

Looking forward to hearing from you soon!

Best regards,
Sales Team"""
    }


@pytest.fixture
def prospect_description():
    """Sample prospect description for testing."""
    return "CEO of a 50-person marketing agency struggling with manual client reporting and looking to scale operations"
