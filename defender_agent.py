"""
Defender Agent - Responds to audit findings and defends the organization
Seeks additional evidence and provides alternative explanations
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
try:
    from search_agent import SearchAgent
except ImportError:
    from simple_search_agent import SimpleSearchAgent as SearchAgent

class DefenderAgent:
    def __init__(self, search_agent: SearchAgent):
        self.search_agent = search_agent
        self.defense_strategies = {}
        
    def defend_control(self, control_id: str, auditor_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Defend against auditor findings for a specific control"""
        
        # Get additional evidence through targeted searches
        additional_evidence = self._gather_additional_evidence(control_id, auditor_findings)
        
        # Analyze auditor's findings and prepare counter-arguments
        defense = {
            'agent': 'Defender',
            'control_id': control_id,
            'auditor_status': auditor_findings.get('status'),
            'defense_position': self._determine_defense_position(auditor_findings),
            'counter_arguments': [],
            'additional_evidence': additional_evidence,
            'mitigating_factors': [],
            'alternative_explanations': []
        }
        
        # Build specific defenses based on control type and findings
        if control_id == "5.1":  # Information security policies
            defense = self._defend_policy_control(defense, auditor_findings, additional_evidence)
        elif control_id in ["5.15", "5.16", "5.17", "5.18"]:  # Access control
            defense = self._defend_access_control(defense, auditor_findings, additional_evidence)
        elif control_id in ["5.24", "5.25", "5.26", "5.27", "5.28"]:  # Incident management
            defense = self._defend_incident_control(defense, auditor_findings, additional_evidence)
        elif control_id in ["5.9", "5.10", "5.11", "5.12", "5.13", "5.14"]:  # Asset management
            defense = self._defend_asset_control(defense, auditor_findings, additional_evidence)
        elif control_id in ["5.19", "5.20", "5.21", "5.22", "5.23"]:  # Supplier management
            defense = self._defend_supplier_control(defense, auditor_findings, additional_evidence)
        else:
            defense = self._defend_generic_control(defense, auditor_findings, additional_evidence)
        
        return defense
    
    def _gather_additional_evidence(self, control_id: str, auditor_findings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather additional evidence that might support the defense"""
        additional_evidence = []
        
        # Search for related evidence using semantic search
        control_result = self.search_agent.query("", f"control:{control_id}")
        if control_result['result']['control']:
            control_name = control_result['result']['control'].get('Control Name', '')
            
            # Semantic search for related concepts
            related_searches = [
                f"{control_name} implementation",
                f"{control_name} procedures",
                f"{control_name} documentation",
                "compliance evidence",
                "security measures",
                "risk mitigation"
            ]
            
            for search_term in related_searches:
                semantic_results = self.search_agent.query(search_term, "semantic")
                for result in semantic_results.get('results', [])[:2]:  # Limit to top 2 per search
                    if result['similarity'] > 0.3:  # Higher threshold for additional evidence
                        additional_evidence.append(result)
        
        # Look for training and compliance evidence
        training_evidence = self.search_agent.query("", "evidence:training_records")
        compliance_evidence = self.search_agent.query("", "evidence:compliance_review_evidence")
        monitoring_evidence = self.search_agent.query("", "evidence:monitoring_logs")
        
        additional_evidence.extend(training_evidence.get('results', [])[:3])
        additional_evidence.extend(compliance_evidence.get('results', [])[:3])
        additional_evidence.extend(monitoring_evidence.get('results', [])[:3])
        
        return additional_evidence
    
    def _determine_defense_position(self, auditor_findings: Dict[str, Any]) -> str:
        """Determine the overall defense position"""
        auditor_status = auditor_findings.get('status')
        compliance_score = auditor_findings.get('compliance_score', 0)
        
        if auditor_status == 'COMPLIANT':
            return 'AGREE_COMPLIANT'
        elif auditor_status == 'PARTIALLY_COMPLIANT':
            if compliance_score >= 75:
                return 'ARGUE_FULLY_COMPLIANT'
            else:
                return 'ACCEPT_WITH_MITIGATION'
        elif auditor_status == 'NON_COMPLIANT':
            if compliance_score >= 60:
                return 'ARGUE_PARTIALLY_COMPLIANT'
            else:
                return 'ACCEPT_WITH_STRONG_MITIGATION'
        else:
            return 'CHALLENGE_ASSESSMENT'
    
    def _defend_policy_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Defend policy-related controls"""
        findings = auditor_findings.get('findings', [])
        
        # Look for positive indicators in additional evidence
        training_records = [e for e in additional_evidence if 'training' in e.get('source', '')]
        
        if training_records:
            defense['counter_arguments'].append(
                "Training records demonstrate active policy communication and awareness"
            )
            defense['mitigating_factors'].append(
                f"Found {len(training_records)} training records showing policy implementation"
            )
        
        # Address specific auditor concerns
        for finding in findings:
            if "acknowledgment" in finding.lower():
                defense['counter_arguments'].append(
                    "Acknowledgment counts may not reflect total training completion rates"
                )
                defense['alternative_explanations'].append(
                    "Some users may have acknowledged policies through alternative training methods"
                )
            elif "approval" in finding.lower() and "older" in finding.lower():
                defense['counter_arguments'].append(
                    "Policy age does not necessarily indicate non-compliance if content remains current"
                )
                defense['mitigating_factors'].append(
                    "Policies may have been reviewed and confirmed current without version updates"
                )
        
        # Look for compliance review evidence
        compliance_reviews = [e for e in additional_evidence if 'compliance' in e.get('source', '')]
        if compliance_reviews:
            defense['counter_arguments'].append(
                "Regular compliance reviews demonstrate ongoing policy effectiveness monitoring"
            )
        
        return defense
    
    def _defend_access_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Defend access control measures"""
        findings = auditor_findings.get('findings', [])
        
        # Look for monitoring evidence
        monitoring_logs = [e for e in additional_evidence if 'monitoring' in e.get('source', '')]
        
        if monitoring_logs:
            defense['counter_arguments'].append(
                "Continuous monitoring logs demonstrate active access control oversight"
            )
            defense['mitigating_factors'].append(
                "Real-time monitoring provides additional security beyond static access reviews"
            )
        
        # Address MFA concerns
        mfa_concerns = [f for f in findings if "mfa" in f.lower()]
        if mfa_concerns:
            defense['counter_arguments'].append(
                "MFA implementation may be phased based on risk assessment and user roles"
            )
            defense['alternative_explanations'].append(
                "Some accounts may use alternative strong authentication methods"
            )
        
        # Address access review concerns
        review_concerns = [f for f in findings if "review" in f.lower()]
        if review_concerns:
            defense['counter_arguments'].append(
                "Access reviews may be conducted through multiple mechanisms not captured in single dataset"
            )
            defense['mitigating_factors'].append(
                "Automated access controls and role-based permissions provide continuous review"
            )
        
        return defense
    
    def _defend_incident_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Defend incident management controls"""
        findings = auditor_findings.get('findings', [])
        
        # If few incidents, this is actually positive
        incident_count = auditor_findings.get('evidence_count', 0)
        if incident_count < 5:
            defense['counter_arguments'].append(
                "Low incident count demonstrates effective preventive controls"
            )
            defense['mitigating_factors'].append(
                "Fewer incidents indicate strong security posture and effective prevention"
            )
        
        # Address critical incident concerns
        critical_concerns = [f for f in findings if "critical" in f.lower()]
        if critical_concerns:
            defense['counter_arguments'].append(
                "Proper identification and escalation of critical incidents shows mature process"
            )
            defense['alternative_explanations'].append(
                "Critical incidents may be part of proactive threat hunting exercises"
            )
        
        # Look for business continuity evidence
        bcp_evidence = [e for e in additional_evidence if 'continuity' in e.get('source', '')]
        if bcp_evidence:
            defense['counter_arguments'].append(
                "Business continuity plans provide additional incident response capabilities"
            )
        
        return defense
    
    def _defend_asset_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Defend asset management controls"""
        findings = auditor_findings.get('findings', [])
        
        # Address ownership concerns
        ownership_concerns = [f for f in findings if "owner" in f.lower()]
        if ownership_concerns:
            defense['counter_arguments'].append(
                "Asset ownership may be implied through departmental assignment and management structure"
            )
            defense['alternative_explanations'].append(
                "Some assets may have collective ownership through team-based management"
            )
        
        # Address classification concerns
        classification_concerns = [f for f in findings if "classification" in f.lower()]
        if classification_concerns:
            defense['counter_arguments'].append(
                "Not all assets require explicit classification if they fall under standard protection levels"
            )
            defense['mitigating_factors'].append(
                "Default security controls may provide adequate protection for unclassified assets"
            )
        
        # Look for monitoring evidence showing asset oversight
        monitoring_logs = [e for e in additional_evidence if 'monitoring' in e.get('source', '')]
        if monitoring_logs:
            defense['counter_arguments'].append(
                "Continuous monitoring demonstrates active asset oversight and protection"
            )
        
        return defense
    
    def _defend_supplier_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Defend supplier management controls"""
        findings = auditor_findings.get('findings', [])
        
        # Address assessment concerns
        assessment_concerns = [f for f in findings if "assessment" in f.lower()]
        if assessment_concerns:
            defense['counter_arguments'].append(
                "Supplier assessments may include informal reviews and continuous monitoring"
            )
            defense['alternative_explanations'].append(
                "Low-risk suppliers may require less frequent formal assessments"
            )
        
        # Address SLA concerns
        sla_concerns = [f for f in findings if "sla" in f.lower()]
        if sla_concerns:
            defense['counter_arguments'].append(
                "SLA variations may be within acceptable ranges and contractually negotiated"
            )
            defense['mitigating_factors'].append(
                "Service quality may be maintained through alternative performance metrics"
            )
        
        # Look for risk assessment evidence
        risk_evidence = [e for e in additional_evidence if 'risk' in e.get('source', '')]
        if risk_evidence:
            defense['counter_arguments'].append(
                "Comprehensive risk assessments guide supplier management decisions"
            )
        
        return defense
    
    def _defend_generic_control(self, defense: Dict, auditor_findings: Dict, additional_evidence: List) -> Dict:
        """Generic defense for other controls"""
        findings = auditor_findings.get('findings', [])
        
        if additional_evidence:
            defense['counter_arguments'].append(
                "Additional evidence sources provide broader compliance context"
            )
            defense['mitigating_factors'].append(
                f"Found {len(additional_evidence)} additional evidence items supporting compliance"
            )
        
        # Generic defense arguments
        defense['counter_arguments'].append(
            "Control implementation may use alternative methods not captured in single evidence source"
        )
        defense['alternative_explanations'].append(
            "Compliance may be achieved through compensating controls and risk mitigation"
        )
        
        return defense
    
    def get_arguments_for_judge(self, control_id: str, auditor_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare defense arguments for the Judge"""
        defense = self.defend_control(control_id, auditor_findings)
        
        arguments = {
            'agent': 'Defender',
            'control_id': control_id,
            'position': defense['defense_position'],
            'counter_arguments': defense['counter_arguments'],
            'mitigating_factors': defense['mitigating_factors'],
            'alternative_explanations': defense['alternative_explanations'],
            'additional_evidence_count': len(defense['additional_evidence']),
            'key_defenses': []
        }
        
        # Summarize key defense points
        if defense['counter_arguments']:
            arguments['key_defenses'].append("Evidence supports alternative compliance interpretation")
        if defense['mitigating_factors']:
            arguments['key_defenses'].append("Mitigating factors reduce compliance risks")
        if defense['additional_evidence']:
            arguments['key_defenses'].append("Additional evidence strengthens compliance case")
        if defense['alternative_explanations']:
            arguments['key_defenses'].append("Alternative implementation methods achieve control objectives")
        
        return arguments
    
    def challenge_methodology(self, auditor_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Challenge auditor methodology or evidence interpretation"""
        challenges = {
            'methodological_concerns': [],
            'evidence_interpretation_issues': [],
            'scope_limitations': [],
            'alternative_metrics': []
        }
        
        # Check for potential methodology issues
        evidence_count = auditor_findings.get('evidence_count', 0)
        if evidence_count < 3:
            challenges['scope_limitations'].append(
                "Limited evidence sample may not represent full control implementation"
            )
        
        compliance_score = auditor_findings.get('compliance_score', 0)
        findings = auditor_findings.get('findings', [])
        
        # Check for scoring consistency
        negative_findings = [f for f in findings if any(word in f.lower() for word in ['major', 'critical', 'poor'])]
        if len(negative_findings) > 2 and compliance_score > 50:
            challenges['methodological_concerns'].append(
                "Scoring methodology may not adequately weight positive evidence"
            )
        
        # Challenge binary interpretations
        if auditor_findings.get('status') == 'NON_COMPLIANT' and compliance_score > 40:
            challenges['evidence_interpretation_issues'].append(
                "Compliance determination may be overly binary and not reflect partial implementation"
            )
        
        # Suggest alternative metrics
        challenges['alternative_metrics'].extend([
            "Risk-based assessment may be more appropriate than checklist compliance",
            "Trend analysis over point-in-time assessment provides better compliance picture",
            "Compensating controls should be considered in overall compliance evaluation"
        ])
        
        return challenges

# Example usage
if __name__ == "__main__":
    from auditor_agent import AuditorAgent
    
    search_agent = SearchAgent()
    auditor = AuditorAgent(search_agent)
    defender = DefenderAgent(search_agent)
    
    # Test defense
    auditor_findings = auditor.evaluate_control("5.1")
    defense = defender.defend_control("5.1", auditor_findings)
    
    print("Auditor Findings:")
    print(f"Status: {auditor_findings['status']}")
    print(f"Score: {auditor_findings['compliance_score']}")
    
    print("\nDefender Response:")
    print(f"Position: {defense['defense_position']}")
    print("Counter-arguments:")
    for arg in defense['counter_arguments']:
        print(f"  - {arg}")
