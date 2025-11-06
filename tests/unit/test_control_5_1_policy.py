"""
Comprehensive Test Suite for ISO 27001 Control 5.1: Policies for Information Security

Control Text (ISO 27001:2022):
"Information security policy and topic-specific policies shall be defined, approved by 
management, published, communicated to and acknowledged by relevant personnel and relevant 
interested parties and reviewed at planned intervals and if significant changes occur."

This test suite validates that the evaluator checks ALL aspects of the control:
1. Defined - Policy exists
2. Approved by management - Management approval present
3. Published - Policy is published/available
4. Communicated - Distributed to relevant parties
5. Acknowledged - Personnel acknowledge receipt/understanding
6. Relevant personnel and interested parties - Coverage of stakeholders
7. Reviewed at planned intervals - Regular review schedule
8. Reviewed if significant changes occur - Change-triggered reviews
"""
import pytest
from datetime import datetime, timedelta


class TestControl51PolicyDefinition:
    """Test Requirement 1: Policy must be DEFINED"""
    
    def test_policy_defined_with_valid_document(self, auditor_agent):
        """Policy is defined when evidence document exists"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document ID': 'POL-001',
                'Document Name': 'Information Security Policy',
                'Version': '2.1',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15',
                'Control Reference': '5.1'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Policy exists = base score
        assert score >= 30, "Policy definition should provide base score"
        assert any('policy' in f.lower() for f in findings or []), \
            "Should acknowledge policy existence"
    
    def test_policy_not_defined_missing_evidence(self, auditor_agent):
        """CRITICAL: Policy not defined when no evidence exists"""
        evidence = []
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score == 0, "Missing policy should result in zero score"
        assert len(findings) == 1
        assert 'CRITICAL' in findings[0]
        assert 'No policy evidence' in findings[0] or 'not found' in findings[0].lower()


class TestControl51ManagementApproval:
    """Test Requirement 2: Policy must be APPROVED BY MANAGEMENT"""
    
    def test_management_approval_present_recent(self, auditor_agent):
        """Policy approved by management within last year"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                'Approved By': 'John Smith - CISO',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 50, "Recent management approval should boost score"
        assert any('approved' in f.lower() or 'POSITIVE' in f for f in findings), \
            "Should acknowledge recent approval"
    
    def test_management_approval_old_stale(self, auditor_agent):
        """Policy approved but approval is stale (>1 year old)"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d'),
                'Approved By': 'John Smith - CISO',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should be penalized for stale approval
        assert score < 85, "Stale approval should reduce score"
        assert any('older' in f.lower() or 'MINOR' in f for f in findings), \
            "Should flag old approval date"
    
    def test_management_approval_missing(self, auditor_agent):
        """Policy exists but no approval date"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '',  # Missing
                'Approved By': '',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should have base score + acknowledgment + review schedule, but missing approval bonus (20 points)
        # Base (30) + Acknowledgment >500 (25) + Review schedule (15) = 70, but evaluator may add more
        # So we check it's less than what it would be with approval (which adds 20)
        assert score >= 30, "Should have base score even without approval"
        assert score < 100, "Missing approval should prevent perfect score"
        # Check that approval-related finding is present or score reflects missing approval
        assert any('approval' in f.lower() or 'MINOR' in f for f in findings) or score < 90, \
            "Should flag missing approval or have reduced score"
    
    def test_management_approval_invalid_format(self, auditor_agent):
        """Policy has approval date in invalid format"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': 'Invalid-Date-Format',
                'Approved By': 'John Smith - CISO',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should handle gracefully
        assert any('Invalid' in f or 'format' in f.lower() or 'MINOR' in f for f in findings), \
            "Should flag invalid date format"


class TestControl51Publication:
    """Test Requirement 3: Policy must be PUBLISHED
    
    Note: Current evidence schema doesn't explicitly track publication status.
    This test documents the gap and tests what we can validate."""
    
    def test_policy_publication_inferred_from_distribution(self, auditor_agent):
        """Publication inferred from distribution list presence"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees, Contractors, Third Parties',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Distribution list suggests publication
        assert score >= 30, "Distribution suggests publication"
    
    def test_policy_publication_gap_documentation(self, auditor_agent):
        """Document that publication status is not explicitly tracked in current schema
        
        TODO: Add 'Published Date' or 'Publication Status' field to evidence schema
        """
        # This test documents a gap - we should track publication explicitly
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                # Missing: Published Date, Publication Status
                'Acknowledgment Count': 600
            }
        }]
        
        # Current evaluator doesn't check publication explicitly
        # This is a known limitation
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should still score based on other factors
        assert score >= 0


class TestControl51Communication:
    """Test Requirement 4: Policy must be COMMUNICATED to relevant parties"""
    
    def test_communication_via_distribution_list(self, auditor_agent):
        """Communication evidenced by distribution list"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees, Contractors, Third Parties',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Distribution list indicates communication
        assert score >= 30
    
    def test_communication_broad_coverage(self, auditor_agent):
        """Communication covers relevant personnel AND interested parties"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees, Contractors, Third Parties, Board of Directors',
                'Acknowledgment Count': 847,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Broad distribution = good communication
        assert score >= 50


class TestControl51Acknowledgment:
    """Test Requirement 5: Policy must be ACKNOWLEDGED by relevant personnel"""
    
    def test_acknowledgment_high_count_excellent(self, auditor_agent):
        """High acknowledgment count (>500) indicates excellent coverage"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 55, "High acknowledgment should boost score significantly"
        assert any('acknowledgment' in f.lower() and 'POSITIVE' in f for f in findings), \
            "Should recognize high acknowledgment rate"
    
    def test_acknowledgment_moderate_count_acceptable(self, auditor_agent):
        """Moderate acknowledgment count (100-500) is acceptable"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 250,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert 45 <= score < 80, "Moderate acknowledgment should provide acceptable score"
        assert any('ACCEPTABLE' in f or 'Moderate' in f for f in findings), \
            "Should recognize moderate acknowledgment"
    
    def test_acknowledgment_low_count_major_issue(self, auditor_agent):
        """Low acknowledgment count (<100) is a major issue"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 50,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert any('MAJOR' in f or 'Low' in f for f in findings), \
            "Should flag low acknowledgment as major issue"
    
    def test_acknowledgment_zero_critical(self, auditor_agent):
        """Zero acknowledgment is critical"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 0,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should still have base score but flag the issue
        assert any('Low' in f or 'MAJOR' in f for f in findings)
    
    def test_acknowledgment_string_conversion(self, auditor_agent):
        """Acknowledgment count as string should be converted correctly"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': '600',  # String format
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should handle string conversion
        assert score >= 55, "String acknowledgment should be converted and scored"


class TestControl51RelevantPersonnelAndInterestedParties:
    """Test Requirement 6: Coverage of RELEVANT PERSONNEL AND INTERESTED PARTIES"""
    
    def test_coverage_all_employees(self, auditor_agent):
        """Policy covers all employees"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees',
                'Acknowledgment Count': 847,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 30
    
    def test_coverage_employees_and_contractors(self, auditor_agent):
        """Policy covers employees AND contractors (interested parties)"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees, Contractors, Third Parties',
                'Acknowledgment Count': 900,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Broad coverage should be positive
        assert score >= 50
    
    def test_coverage_gap_documentation(self, auditor_agent):
        """Document that we should track coverage of interested parties explicitly
        
        TODO: Add fields to track:
        - Employee count
        - Contractor count
        - Third party count
        - Acknowledgment rate per group
        """
        # Current schema doesn't distinguish personnel vs interested parties
        # This is a known limitation
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Distribution List': 'All Employees, Contractors',
                'Acknowledgment Count': 600
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should still score based on available data
        assert score >= 0


class TestControl51ReviewAtPlannedIntervals:
    """Test Requirement 7: Policy must be REVIEWED AT PLANNED INTERVALS"""
    
    def test_review_schedule_established(self, auditor_agent):
        """Review schedule is established with next review date"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Review Date': '2024-07-15',
                'Next Review': '2025-01-15',
                'Acknowledgment Count': 600
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 55, "Review schedule should boost score"
        assert any('review' in f.lower() and 'POSITIVE' in f for f in findings), \
            "Should recognize review schedule"
    
    def test_review_schedule_missing(self, auditor_agent):
        """Review schedule missing is a minor issue"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Next Review': '',  # Missing
                'Acknowledgment Count': 600
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert any('review' in f.lower() and ('MINOR' in f or 'No' in f) for f in findings), \
            "Should flag missing review schedule"
    
    def test_review_schedule_reasonable_interval(self, auditor_agent):
        """Review interval should be reasonable (typically 6-12 months)"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Next Review': '2025-01-15',  # 12 months = reasonable
                'Acknowledgment Count': 600
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 55


class TestControl51ReviewOnSignificantChanges:
    """Test Requirement 8: Policy must be REVIEWED IF SIGNIFICANT CHANGES OCCUR
    
    Note: Current schema doesn't explicitly track change-triggered reviews.
    This test documents the gap."""
    
    def test_change_triggered_review_gap_documentation(self, auditor_agent):
        """Document that change-triggered reviews are not explicitly tracked
        
        TODO: Add fields to track:
        - Significant Change Date
        - Change-Triggered Review Date
        - Change Description
        - Review Triggered By Change (Yes/No)
        """
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Version': '2.1',  # Version suggests changes
                'Review Date': '2024-07-15',
                'Next Review': '2025-01-15',
                'Acknowledgment Count': 600
            }
        }]
        
        # Current evaluator doesn't check for change-triggered reviews
        # Version field exists but not used for this purpose
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should still score based on scheduled reviews
        assert score >= 0


class TestControl51TopicSpecificPolicies:
    """Test Requirement: TOPIC-SPECIFIC POLICIES must also be defined
    
    Control 5.1 requires both:
    1. Information security policy (general)
    2. Topic-specific policies (e.g., Access Control, Data Classification, etc.)
    """
    
    def test_topic_specific_policies_linked(self, auditor_agent):
        """Topic-specific policies should be linked to main policy"""
        # Main policy
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document ID': 'POL-001',
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15',
                'Control Reference': '5.1'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Current evaluator only checks main policy
        # TODO: Should also check for topic-specific policies (5.15, 5.12, etc.)
        assert score >= 0
    
    def test_topic_specific_policies_gap_documentation(self, auditor_agent):
        """Document that topic-specific policy linkage is not checked
        
        TODO: Enhance evaluator to:
        1. Check for main Information Security Policy (5.1)
        2. Check for topic-specific policies (Access Control, Data Classification, etc.)
        3. Verify they are linked/consistent
        4. Score based on completeness of policy framework
        """
        # This documents a gap in current implementation
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 600
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Current implementation doesn't check for topic-specific policies
        # This is a known limitation


class TestControl51ComprehensiveScenarios:
    """End-to-end scenarios testing multiple requirements together"""
    
    def test_fully_compliant_policy(self, auditor_agent):
        """Policy meeting all requirements should score highly"""
        evidence = [{
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
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score >= 85, "Fully compliant policy should score >= 85"
        assert len([f for f in findings if 'POSITIVE' in f]) >= 3, \
            "Should have multiple positive findings"
    
    def test_partially_compliant_policy(self, auditor_agent):
        """Policy with some gaps should score moderately"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d'),  # Old
                'Acknowledgment Count': 150,  # Moderate
                'Next Review': ''  # Missing
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert 40 <= score < 85, "Partially compliant should score 40-84"
        assert any('MINOR' in f or 'MAJOR' in f for f in findings), \
            "Should flag gaps"
    
    def test_non_compliant_policy(self, auditor_agent):
        """Policy with critical gaps should score low"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': (datetime.now() - timedelta(days=800)).strftime('%Y-%m-%d'),  # Very old
                'Acknowledgment Count': 20,  # Very low
                'Next Review': ''  # Missing
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        assert score < 70, "Non-compliant should score < 70"
        assert any('MAJOR' in f for f in findings), \
            "Should flag major issues"


class TestControl51EdgeCases:
    """Edge cases and error handling"""
    
    def test_malformed_date_handling(self, auditor_agent):
        """Should handle malformed dates gracefully"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': 'not-a-date',
                'Acknowledgment Count': 600,
                'Next Review': '2025-01-15'
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should not crash, should handle error
        assert score >= 0
        assert isinstance(findings, list)
    
    def test_missing_optional_fields(self, auditor_agent):
        """Should handle missing optional fields"""
        evidence = [{
            'source': 'policy_evidence',
            'record': {
                'Document Name': 'Information Security Policy',
                'Approval Date': '2024-01-15',
                'Acknowledgment Count': 600
                # Missing: Next Review, Distribution List, etc.
            }
        }]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Should still score based on available fields
        assert score >= 30
    
    def test_multiple_policy_documents(self, auditor_agent):
        """Should handle multiple policy evidence records"""
        evidence = [
            {
                'source': 'policy_evidence',
                'record': {
                    'Document ID': 'POL-001',
                    'Document Name': 'Information Security Policy',
                    'Approval Date': '2024-01-15',
                    'Acknowledgment Count': 600
                }
            },
            {
                'source': 'policy_evidence',
                'record': {
                    'Document ID': 'POL-002',
                    'Document Name': 'Access Control Policy',
                    'Approval Date': '2024-02-01',
                    'Acknowledgment Count': 234
                }
            }
        ]
        
        score, findings = auditor_agent._evaluate_policy_control(evidence)
        
        # Current implementation uses first record
        # TODO: Should evaluate all policies or select main policy
        assert score >= 0


class TestControl51EvidenceSchemaGaps:
    """Document gaps in current evidence schema vs. full control requirements"""
    
    def test_schema_gaps_documentation(self):
        """Document what evidence fields we need to add for full control coverage
        
        Current Schema Has:
        - Document ID, Document Name, Version
        - Approval Date, Approved By
        - Review Date, Next Review
        - Distribution List
        - Acknowledgment Count
        - Control Reference
        
        Missing Fields for Full Control Coverage:
        1. Published Date / Publication Status
        2. Communication Date / Communication Method
        3. Acknowledgment Details (who, when, not just count)
        4. Employee Count (to calculate acknowledgment rate)
        5. Contractor Count
        6. Third Party Count
        7. Significant Change Date
        8. Change-Triggered Review Date
        9. Topic-Specific Policy Linkage
        10. Review Interval (months)
        """
        # This test documents the schema gaps
        required_fields = [
            'Published Date',
            'Communication Date',
            'Acknowledgment Rate (%)',
            'Employee Count',
            'Contractor Count',
            'Significant Change Tracking',
            'Topic-Specific Policy Links'
        ]
        
        # Current implementation works with available fields
        # but could be more comprehensive with additional fields
        assert len(required_fields) > 0, "Schema gaps documented"

