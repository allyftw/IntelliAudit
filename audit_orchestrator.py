"""
Audit Orchestrator - Main script to coordinate the multi-agent audit system
Orchestrates interactions between Search, Auditor, Defender, and Judge agents
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

from search_agent import SearchAgent
from auditor_agent import AuditorAgent
from defender_agent import DefenderAgent
from judge_agent import JudgeAgent

class AuditOrchestrator:
    def __init__(self, output_dir: str = "Output", report_dir: str = "Report"):
        self.output_dir = output_dir
        self.report_dir = report_dir
        
        # Initialize agents
        print("Initializing audit agents...")
        self.search_agent = SearchAgent(output_dir)
        self.auditor_agent = AuditorAgent(self.search_agent)
        self.defender_agent = DefenderAgent(self.search_agent)
        self.judge_agent = JudgeAgent(self.search_agent, self.auditor_agent, self.defender_agent)
        
        print("Multi-agent audit system initialized successfully!")
    
    def run_full_audit(self, control_ids: List[str] = None) -> Dict[str, Any]:
        """Run a full audit with all agents for specified controls"""
        
        if control_ids is None:
            # Default set of key ISO 27001 controls
            control_ids = [
                "5.1",   # Information security policies
                "5.15",  # Access control
                "5.16",  # Identity management
                "5.18",  # Access rights
                "5.24",  # Information security incident management planning
                "5.25",  # Assessment and decision on information security events
                "5.9",   # Inventory of information and other associated assets
                "5.12",  # Classification of information
                "5.19",  # Information security in supplier relationships
                "5.35",  # Independent review of information security
            ]
        
        print(f"\n=== Starting Multi-Agent ISO 27001 Audit ===")
        print(f"Controls to evaluate: {', '.join(control_ids)}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Generate comprehensive audit report using Judge agent
        print("\n--- Judge Agent generating comprehensive audit report ---")
        audit_report = self.judge_agent.generate_comprehensive_audit_report(control_ids)
        
        # Save the audit report
        report_file = self._save_audit_report(audit_report)
        print(f"\nAudit report saved to: {report_file}")
        
        # Print executive summary
        self._print_executive_summary(audit_report)
        
        return audit_report
    
    def run_single_control_audit(self, control_id: str, detailed: bool = True) -> Dict[str, Any]:
        """Run detailed audit for a single control with agent interactions"""
        
        print(f"\n=== Single Control Audit: {control_id} ===")
        
        # Step 1: Auditor evaluation
        print(f"\n--- Auditor Agent evaluating control {control_id} ---")
        auditor_findings = self.auditor_agent.evaluate_control(control_id)
        auditor_arguments = self.auditor_agent.get_arguments_for_judge(control_id)
        
        if detailed:
            print(f"Auditor Position: {auditor_arguments['position']}")
            print(f"Compliance Score: {auditor_findings['compliance_score']}")
            print(f"Evidence Count: {auditor_findings['evidence_count']}")
            print("Key Findings:")
            for finding in auditor_findings['findings'][:3]:
                print(f"  - {finding}")
        
        # Step 2: Defender response
        print(f"\n--- Defender Agent responding to audit findings ---")
        defender_arguments = self.defender_agent.get_arguments_for_judge(control_id, auditor_findings)
        
        if detailed:
            print(f"Defender Position: {defender_arguments['position']}")
            print(f"Additional Evidence: {defender_arguments['additional_evidence_count']} items")
            print("Counter Arguments:")
            for arg in defender_arguments['counter_arguments'][:3]:
                print(f"  - {arg}")
        
        # Step 3: Judge decision
        print(f"\n--- Judge Agent making final determination ---")
        judgment = self.judge_agent.evaluate_control_dispute(control_id)
        
        print(f"Final Determination: {judgment['final_determination']}")
        print(f"Confidence Level: {judgment['confidence_level']}")
        print(f"Follow-up Required: {judgment['follow_up_required']}")
        print("Rationale:")
        for rationale in judgment['rationale']:
            print(f"  - {rationale}")
        
        return {
            'control_id': control_id,
            'auditor_findings': auditor_findings,
            'auditor_arguments': auditor_arguments,
            'defender_arguments': defender_arguments,
            'final_judgment': judgment
        }
    
    def demonstrate_agent_interactions(self, control_id: str = "5.1") -> None:
        """Demonstrate how the agents interact for a specific control"""
        
        print(f"\n=== Agent Interaction Demonstration: Control {control_id} ===")
        
        # Show search agent capabilities
        print(f"\n1. Search Agent - Retrieving evidence for control {control_id}")
        search_result = self.search_agent.query("", f"control:{control_id}")
        print(f"   Found control: {search_result['result']['control'] is not None}")
        print(f"   Evidence items: {len(search_result['result']['evidence'])}")
        
        # Show semantic search
        semantic_result = self.search_agent.query("policy management and approval", "semantic")
        print(f"   Semantic search results: {len(semantic_result['results'])}")
        
        # Run the detailed single control audit
        self.run_single_control_audit(control_id, detailed=True)
    
    def _save_audit_report(self, audit_report: Dict[str, Any]) -> str:
        """Save the audit report to the Report directory"""
        
        # Ensure report directory exists
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Generate filename
        report_id = audit_report['report_metadata']['report_id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON
        json_filename = f"{report_id}_{timestamp}.json"
        json_path = os.path.join(self.report_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)
        
        # Save as human-readable report
        readable_filename = f"ISO27001_Audit_Report_{timestamp}.txt"
        readable_path = os.path.join(self.report_dir, readable_filename)
        
        self._generate_readable_report(audit_report, readable_path)
        
        return readable_path
    
    def _generate_readable_report(self, audit_report: Dict[str, Any], file_path: str) -> None:
        """Generate a human-readable audit report"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ISO 27001 MULTI-AGENT AUDIT REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Report metadata
            metadata = audit_report['report_metadata']
            f.write(f"Report ID: {metadata['report_id']}\n")
            f.write(f"Generation Date: {metadata['generation_date']}\n")
            f.write(f"Audit Scope: {metadata['audit_scope']}\n")
            f.write(f"Assessment Methodology: {metadata['assessment_methodology']}\n\n")
            
            # Executive summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            summary = audit_report['executive_summary']
            f.write(f"Total Controls Assessed: {summary['total_controls_assessed']}\n")
            f.write(f"Overall Compliance Rate: {summary['overall_compliance_rate']}%\n")
            f.write(f"Overall Risk Level: {summary['overall_risk_level']}\n\n")
            
            breakdown = summary['compliance_breakdown']
            f.write("Compliance Breakdown:\n")
            f.write(f"  - Compliant: {breakdown['compliant']}\n")
            f.write(f"  - Partially Compliant: {breakdown['partially_compliant']}\n")
            f.write(f"  - Non-Compliant: {breakdown['non_compliant']}\n")
            f.write(f"  - Insufficient Evidence: {breakdown['insufficient_evidence']}\n\n")
            
            # Key strengths and concerns
            if summary.get('key_strengths'):
                f.write("Key Strengths:\n")
                for strength in summary['key_strengths']:
                    f.write(f"  + {strength}\n")
                f.write("\n")
            
            if summary.get('key_concerns'):
                f.write("Key Concerns:\n")
                for concern in summary['key_concerns']:
                    f.write(f"  ! {concern}\n")
                f.write("\n")
            
            # Overall assessment
            f.write("OVERALL ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            overall = audit_report['overall_assessment']
            f.write(f"ISMS Maturity Level: {overall['overall_isms_maturity']}\n")
            
            cert_readiness = overall['certification_readiness']
            f.write(f"Certification Readiness: {cert_readiness['readiness_level']}\n")
            f.write(f"Estimated Timeline: {cert_readiness['estimated_timeline']}\n\n")
            
            # Detailed findings
            f.write("DETAILED FINDINGS BY CONTROL\n")
            f.write("-" * 40 + "\n\n")
            
            for finding in audit_report['detailed_findings']:
                f.write(f"Control {finding['control_id']}\n")
                f.write(f"Final Determination: {finding['final_determination']}\n")
                f.write(f"Confidence Level: {finding['confidence_level']}\n")
                f.write(f"Follow-up Required: {finding['follow_up_required']}\n")
                
                f.write("Rationale:\n")
                for rationale in finding['rationale']:
                    f.write(f"  - {rationale}\n")
                
                if finding.get('recommendations'):
                    f.write("Recommendations:\n")
                    for rec in finding['recommendations']:
                        f.write(f"  * {rec}\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
            
            # Recommendations
            f.write("CONSOLIDATED RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            recommendations = audit_report['recommendations']
            if recommendations.get('immediate_actions'):
                f.write("IMMEDIATE ACTIONS (0-30 days):\n")
                for action in recommendations['immediate_actions']:
                    f.write(f"  1. {action}\n")
                f.write("\n")
            
            if recommendations.get('short_term_actions'):
                f.write("SHORT-TERM ACTIONS (1-6 months):\n")
                for action in recommendations['short_term_actions']:
                    f.write(f"  2. {action}\n")
                f.write("\n")
            
            if recommendations.get('long_term_actions'):
                f.write("LONG-TERM ACTIONS (6+ months):\n")
                for action in recommendations['long_term_actions']:
                    f.write(f"  3. {action}\n")
                f.write("\n")
            
            # Follow-up schedule
            if audit_report.get('follow_up_schedule'):
                f.write("FOLLOW-UP SCHEDULE\n")
                f.write("-" * 40 + "\n")
                for item in audit_report['follow_up_schedule']:
                    f.write(f"Control {item['control_id']}: {item['follow_up_date']} ({item['priority']} priority)\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("End of Report\n")
            f.write("=" * 80 + "\n")
    
    def _print_executive_summary(self, audit_report: Dict[str, Any]) -> None:
        """Print executive summary to console"""
        
        print("\n" + "=" * 60)
        print("EXECUTIVE SUMMARY")
        print("=" * 60)
        
        summary = audit_report['executive_summary']
        print(f"Overall Compliance Rate: {summary['overall_compliance_rate']}%")
        print(f"Overall Risk Level: {summary['overall_risk_level']}")
        
        breakdown = summary['compliance_breakdown']
        print(f"\nCompliance Breakdown:")
        print(f"  ✓ Compliant: {breakdown['compliant']}")
        print(f"  ⚠ Partially Compliant: {breakdown['partially_compliant']}")
        print(f"  ✗ Non-Compliant: {breakdown['non_compliant']}")
        print(f"  ? Insufficient Evidence: {breakdown['insufficient_evidence']}")
        
        cert_readiness = audit_report['overall_assessment']['certification_readiness']
        print(f"\nCertification Readiness: {cert_readiness['readiness_level']}")
        print(f"Estimated Timeline: {cert_readiness['estimated_timeline']}")
        
        print("=" * 60)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get statistics about the audit system"""
        search_stats = self.search_agent.get_statistics()
        
        return {
            'knowledge_base_stats': search_stats,
            'agents_initialized': {
                'search_agent': True,
                'auditor_agent': True,
                'defender_agent': True,
                'judge_agent': True
            },
            'system_ready': True
        }

def main():
    """Main function to run the audit system"""
    
    print("ISO 27001 Multi-Agent Audit System")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = AuditOrchestrator()
    except Exception as e:
        print(f"Error initializing orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    try:
        # Show system statistics
        stats = orchestrator.get_system_statistics()
        print(f"\nKnowledge Base Loaded:")
        print(f"  - Controls: {stats['knowledge_base_stats']['total_controls']}")
        print(f"  - Evidence Records: {stats['knowledge_base_stats']['total_evidence_records']}")
        print(f"  - Evidence Sources: {stats['knowledge_base_stats']['evidence_sources']}")
        
        # Demonstrate agent interactions
        print("\n" + "=" * 50)
        orchestrator.demonstrate_agent_interactions("5.1")
        
        # Run full audit
        print("\n" + "=" * 50)
        audit_report = orchestrator.run_full_audit()
        
        print(f"\n✓ Multi-agent audit completed successfully!")
        print(f"✓ Report generated in Report directory")
        
        return audit_report
        
    except Exception as e:
        print(f"Error during audit execution: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
