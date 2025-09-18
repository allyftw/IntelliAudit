"""
Judge Agent - Makes final determinations based on Auditor and Defender arguments
Decides when interactions have reached conclusion and generates structured reports
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
try:
    from search_agent import SearchAgent
except ImportError:
    from simple_search_agent import SimpleSearchAgent as SearchAgent
from auditor_agent import AuditorAgent
from defender_agent import DefenderAgent

class JudgeAgent:
    def __init__(self, search_agent: SearchAgent, auditor_agent: AuditorAgent, defender_agent: DefenderAgent):
        self.search_agent = search_agent
        self.auditor_agent = auditor_agent
        self.defender_agent = defender_agent
        self.judgments = []
        self.current_session_id = f"JUDGE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def evaluate_control_dispute(self, control_id: str) -> Dict[str, Any]:
        """Evaluate arguments from both Auditor and Defender for a control"""
        
        # Get auditor's findings
        auditor_findings = self.auditor_agent.evaluate_control(control_id)
        auditor_arguments = self.auditor_agent.get_arguments_for_judge(control_id)
        
        # Get defender's response
        defender_arguments = self.defender_agent.get_arguments_for_judge(control_id, auditor_findings)
        
        # Make judgment
        judgment = self._make_judgment(control_id, auditor_arguments, defender_arguments, auditor_findings)
        
        # Record the judgment
        self.judgments.append(judgment)
        
        return judgment
    
    def _make_judgment(self, control_id: str, auditor_args: Dict, defender_args: Dict, auditor_findings: Dict) -> Dict[str, Any]:
        """Make a final judgment based on arguments from both sides"""
        
        judgment = {
            'session_id': self.current_session_id,
            'control_id': control_id,
            'timestamp': datetime.now().isoformat(),
            'auditor_position': auditor_args['position'],
            'defender_position': defender_args['position'],
            'evidence_reviewed': self._summarize_evidence(auditor_findings, defender_args),
            'key_considerations': [],
            'final_determination': '',
            'confidence_level': '',
            'rationale': [],
            'recommendations': [],
            'follow_up_required': False
        }
        
        # Analyze the strength of arguments
        auditor_score = self._score_arguments(auditor_args, 'auditor')
        defender_score = self._score_arguments(defender_args, 'defender')
        evidence_quality = self._assess_evidence_quality(auditor_findings)
        
        # Consider key factors
        judgment['key_considerations'] = self._identify_key_considerations(
            control_id, auditor_args, defender_args, auditor_findings
        )
        
        # Make final determination
        final_status, confidence, rationale = self._determine_final_status(
            control_id, auditor_score, defender_score, evidence_quality, 
            auditor_findings, auditor_args, defender_args
        )
        
        judgment['final_determination'] = final_status
        judgment['confidence_level'] = confidence
        judgment['rationale'] = rationale
        judgment['recommendations'] = self._generate_recommendations(
            final_status, control_id, auditor_findings, defender_args
        )
        
        # Determine if follow-up is needed
        judgment['follow_up_required'] = self._requires_follow_up(
            final_status, confidence, auditor_findings, defender_args
        )
        
        return judgment
    
    def _score_arguments(self, arguments: Dict, agent_type: str) -> int:
        """Score the strength of arguments (0-100)"""
        score = 50  # Base score
        
        if agent_type == 'auditor':
            # Score auditor arguments
            compliance_score = arguments.get('compliance_score', 50)
            score = compliance_score
            
            # Adjust based on evidence analysis
            evidence_analysis = arguments.get('evidence_analysis', [])
            critical_issues = [f for f in evidence_analysis if 'CRITICAL' in f]
            major_issues = [f for f in evidence_analysis if 'MAJOR' in f]
            positive_findings = [f for f in evidence_analysis if 'POSITIVE' in f]
            
            score -= len(critical_issues) * 20
            score -= len(major_issues) * 10
            score += len(positive_findings) * 5
            
        else:  # defender
            # Score defender arguments
            counter_args = len(arguments.get('counter_arguments', []))
            mitigating_factors = len(arguments.get('mitigating_factors', []))
            additional_evidence = arguments.get('additional_evidence_count', 0)
            
            score += counter_args * 8
            score += mitigating_factors * 6
            score += min(additional_evidence * 3, 15)  # Cap at 15 points
        
        return max(0, min(100, score))
    
    def _assess_evidence_quality(self, auditor_findings: Dict) -> str:
        """Assess the quality and completeness of evidence"""
        evidence_count = auditor_findings.get('evidence_count', 0)
        
        if evidence_count == 0:
            return 'INSUFFICIENT'
        elif evidence_count < 3:
            return 'LIMITED'
        elif evidence_count < 10:
            return 'ADEQUATE'
        else:
            return 'COMPREHENSIVE'
    
    def _identify_key_considerations(self, control_id: str, auditor_args: Dict, 
                                   defender_args: Dict, auditor_findings: Dict) -> List[str]:
        """Identify key considerations for the judgment"""
        considerations = []
        
        # Evidence quality consideration
        evidence_count = auditor_findings.get('evidence_count', 0)
        if evidence_count == 0:
            considerations.append("No direct evidence available for evaluation")
        elif evidence_count < 3:
            considerations.append("Limited evidence may not represent full control implementation")
        
        # Compliance score consideration
        compliance_score = auditor_findings.get('compliance_score', 0)
        if compliance_score >= 85:
            considerations.append("High compliance score indicates strong control implementation")
        elif compliance_score <= 40:
            considerations.append("Low compliance score raises significant concerns")
        
        # Defender's additional evidence
        additional_evidence = defender_args.get('additional_evidence_count', 0)
        if additional_evidence > 5:
            considerations.append("Defender provided substantial additional supporting evidence")
        
        # Control criticality (based on control family)
        if control_id.startswith('5.1'):
            considerations.append("Policy controls are foundational to ISMS effectiveness")
        elif control_id.startswith('5.15') or control_id.startswith('5.16'):
            considerations.append("Access controls are critical for data protection")
        elif control_id.startswith('5.24') or control_id.startswith('5.25'):
            considerations.append("Incident response capabilities are essential for security resilience")
        
        # Conflicting arguments
        auditor_pos = auditor_args.get('position', '')
        defender_pos = defender_args.get('position', '')
        if 'NON_COMPLIANT' in auditor_pos and 'COMPLIANT' in defender_pos:
            considerations.append("Significant disagreement between auditor and defender positions")
        
        return considerations
    
    def _determine_final_status(self, control_id: str, auditor_score: int, defender_score: int,
                              evidence_quality: str, auditor_findings: Dict, 
                              auditor_args: Dict, defender_args: Dict) -> Tuple[str, str, List[str]]:
        """Determine final compliance status with confidence and rationale"""
        
        rationale = []
        
        # Weight the scores based on evidence quality
        evidence_weight = {
            'INSUFFICIENT': 0.3,
            'LIMITED': 0.5,
            'ADEQUATE': 0.8,
            'COMPREHENSIVE': 1.0
        }
        
        weighted_auditor_score = auditor_score * evidence_weight[evidence_quality]
        adjusted_score = (weighted_auditor_score + defender_score * 0.3) / 1.3
        
        # Determine status based on adjusted score and specific factors
        compliance_score = auditor_findings.get('compliance_score', 0)
        auditor_status = auditor_findings.get('status', '')
        
        # Critical issues override everything
        critical_findings = [f for f in auditor_findings.get('findings', []) if 'CRITICAL' in f]
        if critical_findings and evidence_quality != 'INSUFFICIENT':
            rationale.append("Critical compliance gaps identified that cannot be mitigated")
            return 'NON_COMPLIANT', 'HIGH', rationale
        
        # Evidence quality considerations
        if evidence_quality == 'INSUFFICIENT':
            rationale.append("Insufficient evidence prevents definitive compliance determination")
            return 'INSUFFICIENT_EVIDENCE', 'HIGH', rationale
        
        # Score-based determination with defender arguments consideration
        if adjusted_score >= 85:
            if defender_score > 70:
                rationale.append("Strong evidence of compliance with effective defender arguments")
                return 'COMPLIANT', 'HIGH', rationale
            else:
                rationale.append("Evidence supports compliance despite some concerns")
                return 'COMPLIANT', 'MEDIUM', rationale
        elif adjusted_score >= 70:
            if defender_score > 75:
                rationale.append("Defender arguments effectively address auditor concerns")
                return 'COMPLIANT', 'MEDIUM', rationale
            else:
                rationale.append("Partial compliance with some gaps requiring attention")
                return 'PARTIALLY_COMPLIANT', 'MEDIUM', rationale
        elif adjusted_score >= 50:
            if defender_score > 80:
                rationale.append("Strong defender arguments suggest compliance despite auditor concerns")
                return 'PARTIALLY_COMPLIANT', 'LOW', rationale
            else:
                rationale.append("Significant compliance gaps identified")
                return 'PARTIALLY_COMPLIANT', 'HIGH', rationale
        else:
            rationale.append("Evidence indicates substantial non-compliance")
            return 'NON_COMPLIANT', 'HIGH', rationale
    
    def _generate_recommendations(self, final_status: str, control_id: str, 
                                auditor_findings: Dict, defender_args: Dict) -> List[str]:
        """Generate recommendations based on the judgment"""
        recommendations = []
        
        if final_status == 'NON_COMPLIANT':
            recommendations.append("Immediate remediation required to achieve compliance")
            recommendations.append("Develop and implement detailed action plan with timelines")
            recommendations.append("Conduct follow-up assessment within 90 days")
        
        elif final_status == 'PARTIALLY_COMPLIANT':
            recommendations.append("Address identified gaps to achieve full compliance")
            recommendations.append("Implement monitoring to track improvement progress")
            recommendations.append("Schedule re-assessment within 6 months")
        
        elif final_status == 'COMPLIANT':
            recommendations.append("Maintain current control implementation")
            recommendations.append("Continue regular monitoring and review cycles")
        
        elif final_status == 'INSUFFICIENT_EVIDENCE':
            recommendations.append("Gather additional evidence to support compliance evaluation")
            recommendations.append("Implement documentation procedures for future assessments")
            recommendations.append("Re-assess once adequate evidence is available")
        
        # Control-specific recommendations
        if control_id.startswith('5.1'):  # Policies
            recommendations.append("Ensure policy acknowledgment tracking covers all personnel")
        elif control_id.startswith('5.15'):  # Access control
            recommendations.append("Consider implementing automated access review processes")
        elif control_id.startswith('5.24'):  # Incident management
            recommendations.append("Enhance incident response training and tabletop exercises")
        
        return recommendations
    
    def _requires_follow_up(self, final_status: str, confidence: str, 
                          auditor_findings: Dict, defender_args: Dict) -> bool:
        """Determine if follow-up assessment is required"""
        
        if final_status in ['NON_COMPLIANT', 'INSUFFICIENT_EVIDENCE']:
            return True
        
        if final_status == 'PARTIALLY_COMPLIANT':
            return True
        
        if confidence == 'LOW':
            return True
        
        # Check for major issues even in compliant status
        major_findings = [f for f in auditor_findings.get('findings', []) if 'MAJOR' in f]
        if major_findings and final_status == 'COMPLIANT':
            return True
        
        return False
    
    def _summarize_evidence(self, auditor_findings: Dict, defender_args: Dict) -> Dict[str, Any]:
        """Summarize evidence reviewed"""
        return {
            'auditor_evidence_count': auditor_findings.get('evidence_count', 0),
            'auditor_evidence_sources': auditor_findings.get('evidence_summary', ''),
            'defender_additional_evidence': defender_args.get('additional_evidence_count', 0),
            'total_evidence_items': auditor_findings.get('evidence_count', 0) + defender_args.get('additional_evidence_count', 0)
        }
    
    def generate_comprehensive_audit_report(self, control_ids: List[str]) -> Dict[str, Any]:
        """Generate a comprehensive audit report for multiple controls"""
        
        report = {
            'report_metadata': {
                'report_id': f"ISO27001-AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                'generation_date': datetime.now().isoformat(),
                'audit_scope': f"ISO 27001 Controls: {', '.join(control_ids)}",
                'total_controls_evaluated': len(control_ids),
                'assessment_methodology': 'Multi-Agent Audit System (Auditor, Defender, Judge)'
            },
            'executive_summary': {},
            'detailed_findings': [],
            'overall_assessment': {},
            'recommendations': {
                'immediate_actions': [],
                'short_term_actions': [],
                'long_term_actions': []
            },
            'follow_up_schedule': []
        }
        
        # Evaluate each control
        all_judgments = []
        for control_id in control_ids:
            judgment = self.evaluate_control_dispute(control_id)
            all_judgments.append(judgment)
            report['detailed_findings'].append(judgment)
        
        # Generate executive summary
        report['executive_summary'] = self._generate_executive_summary(all_judgments)
        
        # Generate overall assessment
        report['overall_assessment'] = self._generate_overall_assessment(all_judgments)
        
        # Consolidate recommendations
        report['recommendations'] = self._consolidate_recommendations(all_judgments)
        
        # Create follow-up schedule
        report['follow_up_schedule'] = self._create_follow_up_schedule(all_judgments)
        
        return report
    
    def _generate_executive_summary(self, judgments: List[Dict]) -> Dict[str, Any]:
        """Generate executive summary from all judgments"""
        
        total_controls = len(judgments)
        compliant = len([j for j in judgments if j['final_determination'] == 'COMPLIANT'])
        partially_compliant = len([j for j in judgments if j['final_determination'] == 'PARTIALLY_COMPLIANT'])
        non_compliant = len([j for j in judgments if j['final_determination'] == 'NON_COMPLIANT'])
        insufficient_evidence = len([j for j in judgments if j['final_determination'] == 'INSUFFICIENT_EVIDENCE'])
        
        compliance_rate = (compliant + partially_compliant * 0.5) / total_controls * 100 if total_controls > 0 else 0
        
        risk_level = 'LOW' if compliance_rate >= 85 else 'MEDIUM' if compliance_rate >= 70 else 'HIGH'
        
        return {
            'total_controls_assessed': total_controls,
            'compliance_breakdown': {
                'compliant': compliant,
                'partially_compliant': partially_compliant,
                'non_compliant': non_compliant,
                'insufficient_evidence': insufficient_evidence
            },
            'overall_compliance_rate': round(compliance_rate, 1),
            'overall_risk_level': risk_level,
            'key_strengths': self._identify_key_strengths(judgments),
            'key_concerns': self._identify_key_concerns(judgments),
            'priority_actions_required': non_compliant + insufficient_evidence > 0
        }
    
    def _generate_overall_assessment(self, judgments: List[Dict]) -> Dict[str, Any]:
        """Generate overall assessment"""
        
        high_confidence = len([j for j in judgments if j['confidence_level'] == 'HIGH'])
        medium_confidence = len([j for j in judgments if j['confidence_level'] == 'MEDIUM'])
        low_confidence = len([j for j in judgments if j['confidence_level'] == 'LOW'])
        
        follow_up_required = len([j for j in judgments if j['follow_up_required']])
        
        return {
            'assessment_confidence': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'follow_up_required_count': follow_up_required,
            'overall_isms_maturity': self._assess_isms_maturity(judgments),
            'certification_readiness': self._assess_certification_readiness(judgments)
        }
    
    def _identify_key_strengths(self, judgments: List[Dict]) -> List[str]:
        """Identify key organizational strengths"""
        strengths = []
        
        compliant_controls = [j for j in judgments if j['final_determination'] == 'COMPLIANT']
        if len(compliant_controls) >= len(judgments) * 0.7:
            strengths.append("Strong overall compliance posture")
        
        high_confidence_judgments = [j for j in judgments if j['confidence_level'] == 'HIGH']
        if len(high_confidence_judgments) >= len(judgments) * 0.6:
            strengths.append("Well-documented and evidenced control implementations")
        
        # Check for specific control families
        policy_controls = [j for j in judgments if j['control_id'].startswith('5.1')]
        if policy_controls and all(j['final_determination'] == 'COMPLIANT' for j in policy_controls):
            strengths.append("Strong policy foundation established")
        
        return strengths
    
    def _identify_key_concerns(self, judgments: List[Dict]) -> List[str]:
        """Identify key areas of concern"""
        concerns = []
        
        non_compliant = [j for j in judgments if j['final_determination'] == 'NON_COMPLIANT']
        if non_compliant:
            concerns.append(f"{len(non_compliant)} controls identified as non-compliant")
        
        insufficient_evidence = [j for j in judgments if j['final_determination'] == 'INSUFFICIENT_EVIDENCE']
        if insufficient_evidence:
            concerns.append(f"{len(insufficient_evidence)} controls lack sufficient evidence")
        
        low_confidence = [j for j in judgments if j['confidence_level'] == 'LOW']
        if len(low_confidence) > len(judgments) * 0.3:
            concerns.append("Significant assessment uncertainty due to evidence limitations")
        
        return concerns
    
    def _consolidate_recommendations(self, judgments: List[Dict]) -> Dict[str, List[str]]:
        """Consolidate recommendations across all judgments"""
        immediate = []
        short_term = []
        long_term = []
        
        for judgment in judgments:
            recommendations = judgment.get('recommendations', [])
            status = judgment['final_determination']
            
            if status == 'NON_COMPLIANT':
                immediate.extend(recommendations)
            elif status == 'PARTIALLY_COMPLIANT':
                short_term.extend(recommendations)
            else:
                long_term.extend(recommendations)
        
        # Remove duplicates while preserving order
        return {
            'immediate_actions': list(dict.fromkeys(immediate)),
            'short_term_actions': list(dict.fromkeys(short_term)),
            'long_term_actions': list(dict.fromkeys(long_term))
        }
    
    def _create_follow_up_schedule(self, judgments: List[Dict]) -> List[Dict[str, Any]]:
        """Create follow-up schedule for controls requiring reassessment"""
        schedule = []
        
        for judgment in judgments:
            if judgment['follow_up_required']:
                control_id = judgment['control_id']
                status = judgment['final_determination']
                
                if status == 'NON_COMPLIANT':
                    days = 90
                elif status == 'PARTIALLY_COMPLIANT':
                    days = 180
                else:
                    days = 365
                
                follow_up_date = datetime.now().replace(day=1) + timedelta(days=days)
                
                schedule.append({
                    'control_id': control_id,
                    'current_status': status,
                    'follow_up_date': follow_up_date.strftime('%Y-%m-%d'),
                    'priority': 'HIGH' if status == 'NON_COMPLIANT' else 'MEDIUM'
                })
        
        return sorted(schedule, key=lambda x: x['follow_up_date'])
    
    def _assess_isms_maturity(self, judgments: List[Dict]) -> str:
        """Assess overall ISMS maturity level"""
        compliant_rate = len([j for j in judgments if j['final_determination'] == 'COMPLIANT']) / len(judgments)
        
        if compliant_rate >= 0.9:
            return 'OPTIMIZED'
        elif compliant_rate >= 0.8:
            return 'MANAGED'
        elif compliant_rate >= 0.6:
            return 'DEFINED'
        elif compliant_rate >= 0.4:
            return 'DEVELOPING'
        else:
            return 'INITIAL'
    
    def _assess_certification_readiness(self, judgments: List[Dict]) -> Dict[str, Any]:
        """Assess readiness for ISO 27001 certification"""
        non_compliant = len([j for j in judgments if j['final_determination'] == 'NON_COMPLIANT'])
        insufficient_evidence = len([j for j in judgments if j['final_determination'] == 'INSUFFICIENT_EVIDENCE'])
        
        blocking_issues = non_compliant + insufficient_evidence
        
        if blocking_issues == 0:
            readiness = 'READY'
            timeline = '0-3 months'
        elif blocking_issues <= 2:
            readiness = 'NEARLY_READY'
            timeline = '3-6 months'
        elif blocking_issues <= 5:
            readiness = 'SIGNIFICANT_WORK_REQUIRED'
            timeline = '6-12 months'
        else:
            readiness = 'EXTENSIVE_WORK_REQUIRED'
            timeline = '12+ months'
        
        return {
            'readiness_level': readiness,
            'estimated_timeline': timeline,
            'blocking_issues_count': blocking_issues,
            'key_blockers': [j['control_id'] for j in judgments if j['final_determination'] in ['NON_COMPLIANT', 'INSUFFICIENT_EVIDENCE']]
        }

# Example usage
if __name__ == "__main__":
    # Initialize agents
    search_agent = SearchAgent()
    auditor = AuditorAgent(search_agent)
    defender = DefenderAgent(search_agent)
    judge = JudgeAgent(search_agent, auditor, defender)
    
    # Test single control judgment
    judgment = judge.evaluate_control_dispute("5.1")
    print(f"Control 5.1 Final Determination: {judgment['final_determination']}")
    print(f"Confidence: {judgment['confidence_level']}")
    print(f"Rationale: {judgment['rationale']}")
