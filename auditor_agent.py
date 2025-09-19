"""
Auditor Agent - Evaluates compliance controls and flags potential violations
Requests supporting evidence from Search Agent and argues findings
Now includes LangGraph thought process tracking
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
try:
    from search_agent import SearchAgent
except ImportError:
    from simple_search_agent import SimpleSearchAgent as SearchAgent

class AuditorAgent:
    def __init__(self, search_agent: SearchAgent):
        self.search_agent = search_agent
        self.findings = []
        self.current_audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.thought_process = []
        self.graph = self._create_langgraph()
        
    def _create_langgraph(self):
        """Create LangGraph for auditor agent thought process"""
        workflow = StateGraph(dict)
        
        workflow.add_node("gather_evidence", self._gather_evidence_node)
        workflow.add_node("analyze_control", self._analyze_control_node)
        workflow.add_node("evaluate_compliance", self._evaluate_compliance_node)
        workflow.add_node("determine_findings", self._determine_findings_node)
        
        workflow.set_entry_point("gather_evidence")
        workflow.add_edge("gather_evidence", "analyze_control")
        workflow.add_edge("analyze_control", "evaluate_compliance")
        workflow.add_edge("evaluate_compliance", "determine_findings")
        workflow.add_edge("determine_findings", END)
        
        return workflow.compile()
    
    def _gather_evidence_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gather evidence for the control being evaluated"""
        control_id = state.get('control_id', '')
        
        thought = f"Gathering evidence for control {control_id}"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'gather_evidence',
            'thought': thought,
            'control_id': control_id
        })
        
        # Get control details and evidence
        search_result = self.search_agent.query("", f"control:{control_id}")
        
        if not search_result.get('result', {}).get('control'):
            thought = f"Control {control_id} not found in knowledge base - marking as NOT_FOUND"
            self.thought_process.append({
                'timestamp': datetime.now().isoformat(),
                'agent': 'AuditorAgent',
                'node': 'gather_evidence',
                'thought': thought,
                'issue': 'control_not_found'
            })
            state['evidence_found'] = False
            state['error'] = f"Control {control_id} not found in knowledge base"
            return state
        
        control = search_result['result']['control']
        evidence = search_result['result']['evidence']
        
        thought = f"Found control: {control.get('Control Name', '')} with {len(evidence)} evidence items"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'gather_evidence',
            'thought': thought,
            'evidence_count': len(evidence)
        })
        
        state['control'] = control
        state['evidence'] = evidence
        state['evidence_found'] = True
        return state
    
    def _analyze_control_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the control requirements and categorize"""
        if not state.get('evidence_found'):
            return state
            
        control_id = state.get('control_id', '')
        control = state.get('control', {})
        
        # Determine control category
        if control_id == "5.1":
            category = "policy_control"
        elif control_id in ["5.15", "5.16", "5.17", "5.18"]:
            category = "access_control"
        elif control_id in ["5.24", "5.25", "5.26", "5.27", "5.28"]:
            category = "incident_control"
        elif control_id in ["5.9", "5.10", "5.11", "5.12", "5.13", "5.14"]:
            category = "asset_control"
        elif control_id in ["5.19", "5.20", "5.21", "5.22", "5.23"]:
            category = "supplier_control"
        else:
            category = "generic_control"
        
        thought = f"Categorized control {control_id} as {category} - will apply specific evaluation criteria"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'analyze_control',
            'thought': thought,
            'category': category
        })
        
        state['control_category'] = category
        return state
    
    def _evaluate_compliance_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate compliance based on control category and evidence"""
        if not state.get('evidence_found'):
            return state
            
        control_category = state.get('control_category', 'generic_control')
        evidence = state.get('evidence', [])
        
        thought = f"Evaluating compliance for {control_category} with {len(evidence)} evidence items"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'evaluate_compliance',
            'thought': thought
        })
        
        # Apply category-specific evaluation
        if control_category == "policy_control":
            compliance_score, findings = self._evaluate_policy_control(evidence)
        elif control_category == "access_control":
            compliance_score, findings = self._evaluate_access_control(evidence)
        elif control_category == "incident_control":
            compliance_score, findings = self._evaluate_incident_control(evidence)
        elif control_category == "asset_control":
            compliance_score, findings = self._evaluate_asset_control(evidence)
        elif control_category == "supplier_control":
            compliance_score, findings = self._evaluate_supplier_control(evidence)
        else:
            compliance_score, findings = self._evaluate_generic_control(evidence)
        
        thought = f"Compliance evaluation complete: score {compliance_score}/100, {len(findings)} findings"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'evaluate_compliance',
            'thought': thought,
            'compliance_score': compliance_score,
            'findings_count': len(findings)
        })
        
        state['compliance_score'] = compliance_score
        state['findings'] = findings
        return state
    
    def _determine_findings_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final status and compile results"""
        if not state.get('evidence_found'):
            state['final_result'] = {
                'control_id': state.get('control_id', ''),
                'status': 'NOT_FOUND',
                'findings': [state.get('error', 'Control not found')],
                'evidence_count': 0,
                'compliance_score': 0
            }
            return state
            
        control_id = state.get('control_id', '')
        control = state.get('control', {})
        evidence = state.get('evidence', [])
        compliance_score = state.get('compliance_score', 0)
        findings = state.get('findings', [])
        
        status = self._determine_status(compliance_score, findings)
        
        thought = f"Final determination for {control_id}: {status} (score: {compliance_score})"
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'AuditorAgent',
            'node': 'determine_findings',
            'thought': thought,
            'final_status': status
        })
        
        state['final_result'] = {
            'control_id': control_id,
            'control_name': control.get('Control Name', ''),
            'status': status,
            'compliance_score': compliance_score,
            'findings': findings,
            'evidence_count': len(evidence),
            'evidence_summary': self._summarize_evidence(evidence)
        }
        
        return state
    
    def evaluate_control(self, control_id: str) -> Dict[str, Any]:
        """Evaluate a specific ISO 27001 control for compliance with LangGraph tracking"""
        # Initialize state for LangGraph
        initial_state = {
            'control_id': control_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Execute the LangGraph workflow
        final_state = self.graph.invoke(initial_state)
        
        # Return the final result
        result = final_state.get('final_result', {})
        result['thought_process_id'] = len(self.thought_process)
        
        return result
    
    def _evaluate_policy_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Evaluate policy-related controls"""
        findings = []
        score = 0
        
        policy_evidence = [e for e in evidence if e['source'] == 'policy_evidence']
        
        if not policy_evidence:
            findings.append("CRITICAL: No policy evidence found")
            return 0, findings
        
        # Check for required policies
        policy_docs = policy_evidence[0]['record'] if policy_evidence else {}
        
        if policy_docs:
            score += 30  # Base score for having policies
            
            # Check approval dates
            approval_date = policy_docs.get('Approval Date', '')
            if approval_date:
                try:
                    approval_dt = datetime.strptime(approval_date, '%Y-%m-%d')
                    if approval_dt > datetime.now() - timedelta(days=365):
                        score += 20
                        findings.append("POSITIVE: Policy approved within last year")
                    else:
                        findings.append("MINOR: Policy approval older than 1 year")
                except:
                    findings.append("MINOR: Invalid approval date format")
            
            # Check acknowledgment count
            ack_count = policy_docs.get('Acknowledgment Count', 0)
            if isinstance(ack_count, str) and ack_count.isdigit():
                ack_count = int(ack_count)
            if ack_count > 500:
                score += 25
                findings.append("POSITIVE: High policy acknowledgment rate")
            elif ack_count > 100:
                score += 15
                findings.append("ACCEPTABLE: Moderate policy acknowledgment")
            else:
                findings.append("MAJOR: Low policy acknowledgment count")
            
            # Check review schedule
            next_review = policy_docs.get('Next Review', '')
            if next_review:
                score += 25
                findings.append("POSITIVE: Policy review schedule established")
            else:
                findings.append("MINOR: No clear review schedule")
        
        return min(score, 100), findings
    
    def _evaluate_access_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Evaluate access control related evidence"""
        findings = []
        score = 0
        
        access_evidence = [e for e in evidence if e['source'] == 'access_control_evidence']
        
        if not access_evidence:
            findings.append("CRITICAL: No access control evidence found")
            return 0, findings
        
        # Analyze user accounts
        user_records = [e['record'] for e in access_evidence]
        
        if user_records:
            score += 20  # Base score for having access records
            
            # Check MFA adoption
            mfa_enabled = sum(1 for user in user_records if user.get('MFA Enabled') == 'Yes')
            total_users = len([u for u in user_records if u.get('Account Status') == 'Active'])
            
            if total_users > 0:
                mfa_rate = mfa_enabled / total_users
                if mfa_rate >= 0.95:
                    score += 30
                    findings.append("POSITIVE: Excellent MFA adoption (>95%)")
                elif mfa_rate >= 0.80:
                    score += 20
                    findings.append("ACCEPTABLE: Good MFA adoption (>80%)")
                else:
                    findings.append("MAJOR: Poor MFA adoption rate")
            
            # Check for disabled accounts
            disabled_accounts = [u for u in user_records if u.get('Account Status') == 'Disabled']
            if disabled_accounts:
                score += 15
                findings.append("POSITIVE: Inactive accounts properly disabled")
            
            # Check recent access reviews
            recent_reviews = sum(1 for user in user_records 
                               if user.get('Last Access Review') and 
                               self._is_recent_date(user.get('Last Access Review')))
            
            if recent_reviews >= total_users * 0.9:
                score += 35
                findings.append("POSITIVE: Recent access reviews conducted")
            elif recent_reviews >= total_users * 0.5:
                score += 20
                findings.append("ACCEPTABLE: Partial access reviews completed")
            else:
                findings.append("MAJOR: Insufficient access reviews")
        
        return min(score, 100), findings
    
    def _evaluate_incident_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Evaluate incident management controls"""
        findings = []
        score = 0
        
        incident_evidence = [e for e in evidence if e['source'] == 'incident_management_evidence']
        
        if not incident_evidence:
            findings.append("MINOR: No recent incident evidence (could indicate good security)")
            return 70, findings  # Assume compliance if no incidents
        
        incidents = [e['record'] for e in incident_evidence]
        
        if incidents:
            score += 20  # Base score for incident tracking
            
            # Check incident response times
            closed_incidents = [inc for inc in incidents if inc.get('Status') == 'Closed']
            
            if closed_incidents:
                score += 25
                findings.append("POSITIVE: Incidents are being closed/resolved")
                
                # Check for lessons learned
                with_lessons = [inc for inc in closed_incidents if inc.get('Lessons Learned')]
                if len(with_lessons) >= len(closed_incidents) * 0.8:
                    score += 30
                    findings.append("POSITIVE: Lessons learned documented for most incidents")
                else:
                    findings.append("MINOR: Some incidents lack lessons learned")
            
            # Check incident severity handling
            critical_incidents = [inc for inc in incidents if inc.get('Severity') == 'Critical']
            if critical_incidents:
                findings.append(f"ATTENTION: {len(critical_incidents)} critical incidents identified")
                # Check if they're all closed
                open_critical = [inc for inc in critical_incidents if inc.get('Status') != 'Closed']
                if open_critical:
                    findings.append("MAJOR: Open critical incidents require attention")
                else:
                    score += 25
                    findings.append("POSITIVE: All critical incidents resolved")
        
        return min(score, 100), findings
    
    def _evaluate_asset_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Evaluate asset management controls"""
        findings = []
        score = 0
        
        asset_evidence = [e for e in evidence if 'asset' in e['source']]
        
        if not asset_evidence:
            findings.append("CRITICAL: No asset management evidence found")
            return 0, findings
        
        assets = []
        classifications = []
        
        for e in asset_evidence:
            if e['source'] == 'asset_management_evidence':
                assets.extend([e['record']] if isinstance(e['record'], dict) else [])
            elif e['source'] == 'asset_classification_evidence':
                classifications.extend([e['record']] if isinstance(e['record'], dict) else [])
        
        if assets:
            score += 30  # Base score for asset inventory
            
            # Check asset ownership
            owned_assets = [a for a in assets if a.get('Owner')]
            if len(owned_assets) >= len(assets) * 0.9:
                score += 25
                findings.append("POSITIVE: Most assets have assigned owners")
            else:
                findings.append("MAJOR: Many assets lack assigned owners")
            
            # Check asset status
            active_assets = [a for a in assets if a.get('Status') == 'Active']
            disposed_assets = [a for a in assets if a.get('Status') == 'Disposed']
            
            if disposed_assets:
                score += 15
                findings.append("POSITIVE: Proper asset disposal tracking")
            
            if classifications:
                score += 30
                findings.append("POSITIVE: Asset classification system in place")
                
                # Check classification completeness
                classified_assets = len(classifications)
                if classified_assets >= len(assets) * 0.8:
                    score += 20
                    findings.append("POSITIVE: Most assets properly classified")
                else:
                    findings.append("MINOR: Some assets lack classification")
        
        return min(score, 100), findings
    
    def _evaluate_supplier_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Evaluate supplier management controls"""
        findings = []
        score = 0
        
        supplier_evidence = [e for e in evidence if e['source'] == 'supplier_management_evidence']
        
        if not supplier_evidence:
            findings.append("MINOR: No supplier evidence (may not be applicable)")
            return 80, findings
        
        suppliers = [e['record'] for e in supplier_evidence]
        
        if suppliers:
            score += 25  # Base score for supplier tracking
            
            # Check risk assessments
            assessed_suppliers = [s for s in suppliers if s.get('Last Assessment')]
            if len(assessed_suppliers) >= len(suppliers) * 0.9:
                score += 30
                findings.append("POSITIVE: Regular supplier assessments conducted")
            else:
                findings.append("MAJOR: Missing supplier risk assessments")
            
            # Check SLA compliance
            compliant_suppliers = []
            for supplier in suppliers:
                sla_compliance = supplier.get('SLA Compliance', '0%')
                if isinstance(sla_compliance, str) and '%' in sla_compliance:
                    compliance_rate = float(sla_compliance.replace('%', ''))
                    if compliance_rate >= 95:
                        compliant_suppliers.append(supplier)
            
            if len(compliant_suppliers) >= len(suppliers) * 0.8:
                score += 30
                findings.append("POSITIVE: Good supplier SLA compliance")
            else:
                findings.append("MINOR: Some suppliers have SLA issues")
            
            # Check security requirements
            secure_suppliers = [s for s in suppliers if s.get('Security Requirements Met') == 'Yes']
            if len(secure_suppliers) >= len(suppliers) * 0.9:
                score += 15
                findings.append("POSITIVE: Suppliers meet security requirements")
            else:
                findings.append("MAJOR: Some suppliers don't meet security requirements")
        
        return min(score, 100), findings
    
    def _evaluate_generic_control(self, evidence: List[Dict]) -> Tuple[int, List[str]]:
        """Generic evaluation for other controls"""
        findings = []
        score = 50  # Default middle score
        
        if evidence:
            score += 30
            findings.append("POSITIVE: Supporting evidence available")
            
            # Check if evidence is recent
            recent_evidence = 0
            for e in evidence:
                record = e['record']
                for key, value in record.items():
                    if 'date' in key.lower() and self._is_recent_date(value):
                        recent_evidence += 1
                        break
            
            if recent_evidence > 0:
                score += 20
                findings.append("POSITIVE: Recent evidence available")
        else:
            findings.append("MAJOR: No supporting evidence found")
        
        return min(score, 100), findings
    
    def _is_recent_date(self, date_str: str, days: int = 180) -> bool:
        """Check if a date string represents a recent date"""
        if not date_str or not isinstance(date_str, str):
            return False
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj > datetime.now() - timedelta(days=days)
        except:
            return False
    
    def _determine_status(self, score: int, findings: List[str]) -> str:
        """Determine compliance status based on score and findings"""
        critical_findings = [f for f in findings if f.startswith("CRITICAL")]
        major_findings = [f for f in findings if f.startswith("MAJOR")]
        
        if critical_findings:
            return "NON_COMPLIANT"
        elif score >= 85 and not major_findings:
            return "COMPLIANT"
        elif score >= 70:
            return "PARTIALLY_COMPLIANT"
        else:
            return "NON_COMPLIANT"
    
    def _summarize_evidence(self, evidence: List[Dict]) -> str:
        """Create a summary of available evidence"""
        if not evidence:
            return "No evidence available"
        
        sources = {}
        for e in evidence:
            source = e['source']
            sources[source] = sources.get(source, 0) + 1
        
        summary_parts = []
        for source, count in sources.items():
            summary_parts.append(f"{source}: {count} records")
        
        return "; ".join(summary_parts)
    
    def audit_control_set(self, control_ids: List[str]) -> Dict[str, Any]:
        """Audit a set of controls and return comprehensive findings"""
        audit_results = {
            'audit_id': self.current_audit_id,
            'timestamp': datetime.now().isoformat(),
            'controls_evaluated': len(control_ids),
            'results': [],
            'summary': {
                'compliant': 0,
                'partially_compliant': 0,
                'non_compliant': 0,
                'not_found': 0
            }
        }
        
        for control_id in control_ids:
            result = self.evaluate_control(control_id)
            audit_results['results'].append(result)
            
            # Update summary
            status = result['status']
            if status == 'COMPLIANT':
                audit_results['summary']['compliant'] += 1
            elif status == 'PARTIALLY_COMPLIANT':
                audit_results['summary']['partially_compliant'] += 1
            elif status == 'NON_COMPLIANT':
                audit_results['summary']['non_compliant'] += 1
            else:
                audit_results['summary']['not_found'] += 1
        
        # Calculate overall compliance rate
        total_evaluated = len(control_ids) - audit_results['summary']['not_found']
        if total_evaluated > 0:
            compliance_rate = (audit_results['summary']['compliant'] + 
                             audit_results['summary']['partially_compliant'] * 0.5) / total_evaluated
            audit_results['summary']['overall_compliance_rate'] = round(compliance_rate * 100, 1)
        
        return audit_results
    
    def get_arguments_for_judge(self, control_id: str) -> Dict[str, Any]:
        """Prepare arguments for the Judge based on audit findings"""
        result = self.evaluate_control(control_id)
        
        arguments = {
            'agent': 'Auditor',
            'control_id': control_id,
            'position': result['status'],
            'evidence_analysis': result['findings'],
            'compliance_score': result['compliance_score'],
            'key_arguments': []
        }
        
        # Build key arguments based on findings
        if result['status'] == 'NON_COMPLIANT':
            arguments['key_arguments'].append("Evidence shows significant compliance gaps")
            arguments['key_arguments'].append("Control requirements are not adequately met")
        elif result['status'] == 'PARTIALLY_COMPLIANT':
            arguments['key_arguments'].append("Control partially implemented but gaps exist")
            arguments['key_arguments'].append("Additional measures needed for full compliance")
        else:
            arguments['key_arguments'].append("Evidence demonstrates adequate control implementation")
            arguments['key_arguments'].append("Control requirements are satisfactorily met")
        
        return arguments
    
    def get_thought_process(self) -> List[Dict[str, Any]]:
        """Return the complete thought process for this agent"""
        return self.thought_process
    
    def clear_thought_process(self):
        """Clear the thought process history"""
        self.thought_process = []

# Example usage
if __name__ == "__main__":
    search_agent = SearchAgent()
    auditor = AuditorAgent(search_agent)
    
    # Test single control evaluation
    result = auditor.evaluate_control("5.1")
    print(f"Control 5.1 Evaluation:")
    print(f"Status: {result['status']}")
    print(f"Score: {result['compliance_score']}")
    print("Findings:")
    for finding in result['findings']:
        print(f"  - {finding}")
