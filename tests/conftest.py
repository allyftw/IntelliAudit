"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_search_agent import SimpleSearchAgent
from auditor_agent import AuditorAgent
from defender_agent import DefenderAgent
from judge_agent import JudgeAgent


@pytest.fixture
def output_dir():
    """Path to test output directory"""
    return str(project_root / "Output")


@pytest.fixture
def search_agent(output_dir):
    """Create a search agent instance for testing"""
    return SimpleSearchAgent(output_dir)


@pytest.fixture
def auditor_agent(search_agent):
    """Create an auditor agent instance for testing"""
    return AuditorAgent(search_agent)


@pytest.fixture
def defender_agent(search_agent):
    """Create a defender agent instance for testing"""
    return DefenderAgent(search_agent)


@pytest.fixture
def judge_agent(search_agent, auditor_agent, defender_agent):
    """Create a judge agent instance for testing"""
    return JudgeAgent(search_agent, auditor_agent, defender_agent)


# Sample evidence fixtures
@pytest.fixture
def sample_policy_evidence():
    """Sample policy evidence with good compliance indicators - Control 5.1"""
    return [{
        'source': 'policy_evidence',
        'record': {
            'Document ID': 'POL-001',
            'Document Name': 'Information Security Policy',
            'Version': '2.1',
            'Approval Date': '2024-01-15',  # Recent (within 1 year)
            'Approved By': 'John Smith - CISO',
            'Review Date': '2024-07-15',
            'Next Review': '2025-01-15',
            'Distribution List': 'All Employees, Contractors, Third Parties',
            'Acknowledgment Count': 600,     # High (>500)
            'Control Reference': '5.1'
        }
    }]


@pytest.fixture
def sample_policy_evidence_fully_compliant():
    """Fully compliant policy evidence meeting all Control 5.1 requirements"""
    from datetime import datetime, timedelta
    return [{
        'source': 'policy_evidence',
        'record': {
            'Document ID': 'POL-001',
            'Document Name': 'Information Security Policy',
            'Version': '2.1',
            'Approval Date': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
            'Approved By': 'John Smith - CISO',
            'Review Date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'Next Review': (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'Distribution List': 'All Employees, Contractors, Third Parties, Board of Directors',
            'Acknowledgment Count': 847,
            'Control Reference': '5.1'
        }
    }]


@pytest.fixture
def sample_policy_evidence_poor():
    """Sample policy evidence with poor compliance indicators"""
    return [{
        'source': 'policy_evidence',
        'record': {
            'Document ID': 'POL-002',
            'Document Name': 'Old Policy',
            'Approval Date': '2020-01-15',  # Old (>1 year)
            'Acknowledgment Count': 50,     # Low (<100)
            'Next Review': '',              # Missing
            'Control Reference': '5.1'
        }
    }]


@pytest.fixture
def sample_access_control_evidence():
    """Sample access control evidence with good MFA adoption"""
    return [{
        'source': 'access_control_evidence',
        'record': {
            'User ID': 'USER-001',
            'Account Status': 'Active',
            'MFA Enabled': 'Yes',
            'Last Access Review': '2024-08-01',
            'Control Reference': '5.15'
        }
    }]


@pytest.fixture
def sample_asset_evidence():
    """Sample asset management evidence"""
    return [{
        'source': 'asset_management_evidence',
        'record': {
            'Asset ID': 'ASSET-001',
            'Owner': 'John Doe',
            'Status': 'Active',
            'Control Reference': '5.9'
        }
    }]


@pytest.fixture
def sample_business_continuity_evidence():
    """Sample business continuity evidence"""
    return [{
        'source': 'business_continuity_evidence',
        'record': {
            'BCP Tests': 2,
            'Last Test': '2024-06-15',
            'Results': 'Successful',
            'Control Reference': '5.29'
        }
    }]


@pytest.fixture
def empty_evidence():
    """Empty evidence list for testing missing evidence scenarios"""
    return []

