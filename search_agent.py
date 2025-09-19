"""
Search Agent - Unbiased retrieval agent for ISO 27001 audit evidence
Semantically searches and extracts relevant information from structured knowledge base
Now includes LangGraph thought process tracking
"""

import pandas as pd
import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import json

class SearchAgent:
    def __init__(self, output_dir: str = "Output"):
        self.output_dir = output_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = {}
        self.embeddings = {}
        self.thought_process = []
        self.load_knowledge_base()
        self.graph = self._create_langgraph()
    
    def load_knowledge_base(self):
        """Load all CSV files from the Output directory into the knowledge base"""
        try:
            # Load ISO 27001 controls
            controls_file = os.path.join(self.output_dir, "ISO27001_Controls.csv")
            if os.path.exists(controls_file):
                self.knowledge_base['controls'] = pd.read_csv(controls_file)
                print(f"Loaded controls: {len(self.knowledge_base['controls'])} records")
            
            # Load evidence files
            evidence_files = [
                "ISO27001_Policy_Evidence.csv",
                "ISO27001_Access_Control_Evidence.csv", 
                "ISO27001_Incident_Management_Evidence.csv",
                "ISO27001_Asset_Management_Evidence.csv",
                "ISO27001_Asset_Classification_Evidence.csv",
                "ISO27001_Supplier_Management_Evidence.csv",
                "ISO27001_Training_Records.csv",
                "ISO27001_Risk_Assessment_Evidence.csv",
                "ISO27001_Compliance_Review_Evidence.csv",
                "ISO27001_Business_Continuity_Evidence.csv",
                "ISO27001_Monitoring_Logs.csv"
            ]
            
            for file in evidence_files:
                file_path = os.path.join(self.output_dir, file)
                if os.path.exists(file_path):
                    key = file.replace("ISO27001_", "").replace(".csv", "").lower()
                    self.knowledge_base[key] = pd.read_csv(file_path)
                    print(f"Loaded {key}: {len(self.knowledge_base[key])} records")
            
            # Create embeddings for semantic search
            self.create_embeddings()
            
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def create_embeddings(self):
        """Create embeddings for semantic search"""
        for key, df in self.knowledge_base.items():
            if key == 'controls':
                # Combine control description and name for embedding using new column names
                texts = df.apply(lambda row: f"{row.get('Control Name', '')} {row.get('Control Description', '')}", axis=1).tolist()
            else:
                # Combine all text columns for other evidence
                text_columns = df.select_dtypes(include=['object']).columns
                texts = df[text_columns].apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()
            
            if texts:
                self.embeddings[key] = self.model.encode(texts)
                print(f"Created embeddings for {key}: {len(texts)} items")
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across all knowledge base"""
        query_embedding = self.model.encode([query])
        results = []
        
        for key, embeddings in self.embeddings.items():
            if len(embeddings) == 0:
                continue
                
            similarities = cosine_similarity(query_embedding, embeddings)[0]
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    record = self.knowledge_base[key].iloc[idx].to_dict()
                    results.append({
                        'source': key,
                        'similarity': float(similarities[idx]),
                        'record': record
                    })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def search_by_control(self, control_id: str) -> Dict[str, Any]:
        """Search for specific control and related evidence"""
        # Find the control using the new Control/Sub Control format
        if 'controls' in self.knowledge_base:
            control_df = self.knowledge_base['controls']
            
            # Parse control_id (e.g., "5.1" -> Control=5, Sub Control=1)
            try:
                if '.' in control_id:
                    control_num, sub_control_num = control_id.split('.')
                    control_num = int(control_num)
                    sub_control_num = int(sub_control_num)
                    
                    # Find matching control
                    control = control_df[
                        (control_df['Control'] == control_num) & 
                        (control_df['Sub Control'] == sub_control_num)
                    ]
                else:
                    # Fallback for old format
                    control = control_df[control_df.get('Control ID', '') == control_id]
                
                if not control.empty:
                    control_info = control.iloc[0].to_dict()
                    # Add formatted control_id for consistency
                    control_info['Control ID'] = f"{control_info.get('Control', '')}.{control_info.get('Sub Control', '')}"
                    
                    # Find related evidence by searching for control reference
                    related_evidence = []
                    for key, df in self.knowledge_base.items():
                        if key != 'controls' and 'Control Reference' in df.columns:
                            matches = df[df['Control Reference'] == control_id]
                            if not matches.empty:
                                related_evidence.extend([
                                    {'source': key, 'record': row.to_dict()} 
                                    for _, row in matches.iterrows()
                                ])
                    
                    return {
                        'control': control_info,
                        'evidence': related_evidence
                    }
            except (ValueError, IndexError) as e:
                print(f"Error parsing control_id {control_id}: {e}")
        
        return {'control': None, 'evidence': []}
    
    def search_evidence_by_type(self, evidence_type: str) -> List[Dict[str, Any]]:
        """Search for evidence by type (e.g., 'policy', 'incident', 'access')"""
        if evidence_type in self.knowledge_base:
            df = self.knowledge_base[evidence_type]
            return [row.to_dict() for _, row in df.iterrows()]
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        stats = {
            'total_controls': len(self.knowledge_base.get('controls', [])),
            'evidence_sources': len([k for k in self.knowledge_base.keys() if k != 'controls']),
            'total_evidence_records': sum(len(df) for k, df in self.knowledge_base.items() if k != 'controls')
        }
        
        # Count evidence by type
        evidence_counts = {}
        for key, df in self.knowledge_base.items():
            if key != 'controls':
                evidence_counts[key] = len(df)
        
        stats['evidence_by_type'] = evidence_counts
        return stats
    
    def _create_langgraph(self):
        """Create LangGraph for search agent thought process"""
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("select_strategy", self._select_strategy_node)
        workflow.add_node("execute_search", self._execute_search_node)
        workflow.add_node("evaluate_results", self._evaluate_results_node)
        
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "select_strategy")
        workflow.add_edge("select_strategy", "execute_search")
        workflow.add_edge("execute_search", "evaluate_results")
        workflow.add_edge("evaluate_results", END)
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the incoming query to understand intent"""
        query = state.get('query', '')
        search_type = state.get('search_type', 'semantic')
        
        thought = f"Analyzing query: '{query}' with search type: '{search_type}'"
        analysis = {
            'intent': self._determine_intent(query, search_type),
            'complexity': 'simple' if len(query.split()) < 5 else 'complex',
            'domain_specific': any(term in query.lower() for term in ['policy', 'access', 'incident', 'asset', 'supplier'])
        }
        
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'SearchAgent',
            'node': 'analyze_query',
            'thought': thought,
            'analysis': analysis
        })
        
        state['analysis'] = analysis
        return state
    
    def _select_strategy_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Select the appropriate search strategy"""
        analysis = state.get('analysis', {})
        search_type = state.get('search_type', 'semantic')
        
        if search_type.startswith('control:'):
            strategy = 'control_lookup'
        elif search_type.startswith('evidence:'):
            strategy = 'evidence_type_filter'
        elif analysis.get('domain_specific'):
            strategy = 'semantic_with_domain_boost'
        else:
            strategy = 'semantic_general'
        
        thought = f"Selected search strategy: {strategy} based on analysis: {analysis}"
        
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'SearchAgent', 
            'node': 'select_strategy',
            'thought': thought,
            'strategy': strategy
        })
        
        state['strategy'] = strategy
        return state
    
    def _execute_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search using selected strategy"""
        strategy = state.get('strategy', 'semantic_general')
        query = state.get('query', '')
        search_type = state.get('search_type', 'semantic')
        
        thought = f"Executing search with strategy: {strategy}"
        
        if strategy == 'control_lookup':
            control_id = search_type.replace("control:", "")
            results = self.search_by_control(control_id)
            search_results = {
                'type': 'control_search',
                'control_id': control_id,
                'result': results
            }
        elif strategy == 'evidence_type_filter':
            evidence_type = search_type.replace("evidence:", "")
            results = self.search_evidence_by_type(evidence_type)
            search_results = {
                'type': 'evidence_search',
                'evidence_type': evidence_type,
                'results': results,
                'total_found': len(results)
            }
        else:
            results = self.semantic_search(query, top_k=10 if strategy == 'semantic_with_domain_boost' else 5)
            search_results = {
                'type': 'semantic_search',
                'results': results,
                'total_found': len(results)
            }
        
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'SearchAgent',
            'node': 'execute_search', 
            'thought': thought,
            'results_count': search_results.get('total_found', len(search_results.get('results', [])))
        })
        
        state['search_results'] = search_results
        return state
    
    def _evaluate_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality and relevance of search results"""
        search_results = state.get('search_results', {})
        query = state.get('query', '')
        
        if search_results.get('type') == 'semantic_search':
            results = search_results.get('results', [])
            if results:
                avg_similarity = sum(r.get('similarity', 0) for r in results) / len(results)
                quality = 'high' if avg_similarity > 0.7 else 'medium' if avg_similarity > 0.4 else 'low'
            else:
                quality = 'none'
        else:
            # For control/evidence searches, quality based on whether results found
            quality = 'high' if search_results.get('total_found', 0) > 0 else 'none'
        
        thought = f"Search quality assessment: {quality}. Found {search_results.get('total_found', 0)} results for query: '{query}'"
        
        self.thought_process.append({
            'timestamp': datetime.now().isoformat(),
            'agent': 'SearchAgent',
            'node': 'evaluate_results',
            'thought': thought,
            'quality': quality,
            'final_results': search_results
        })
        
        state['final_results'] = search_results
        state['quality'] = quality
        return state
    
    def _determine_intent(self, query: str, search_type: str) -> str:
        """Determine the intent of the search query"""
        if search_type.startswith('control:'):
            return 'control_lookup'
        elif search_type.startswith('evidence:'):
            return 'evidence_retrieval'
        elif any(word in query.lower() for word in ['compliance', 'audit', 'assessment']):
            return 'compliance_verification'
        elif any(word in query.lower() for word in ['evidence', 'proof', 'documentation']):
            return 'evidence_gathering'
        else:
            return 'general_search'
    
    def query(self, query: str, search_type: str = "semantic") -> Dict[str, Any]:
        """Main query interface for other agents with LangGraph thought tracking"""
        # Initialize state for LangGraph
        initial_state = {
            'query': query,
            'search_type': search_type,
            'timestamp': datetime.now().isoformat()
        }
        
        # Execute the LangGraph workflow
        final_state = self.graph.invoke(initial_state)
        
        # Return the results with additional metadata
        results = final_state.get('final_results', {})
        results['query'] = query
        results['thought_process_id'] = len(self.thought_process)
        
        return results
    
    def get_thought_process(self) -> List[Dict[str, Any]]:
        """Return the complete thought process for this agent"""
        return self.thought_process
    
    def clear_thought_process(self):
        """Clear the thought process history"""
        self.thought_process = []

# Example usage
if __name__ == "__main__":
    agent = SearchAgent()
    
    # Test semantic search
    result = agent.query("access control policies and user management")
    print("Semantic Search Results:")
    for item in result['results'][:3]:
        print(f"- {item['source']}: {item['similarity']:.3f}")
        print(f"  {item['record']}")
        print()
    
    # Test control search
    result = agent.query("", "control:5.1")
    print("Control 5.1 Search:")
    print(f"Control: {result['result']['control']}")
    print(f"Evidence count: {len(result['result']['evidence'])}")


