"""
Search Agent - Unbiased retrieval agent for ISO 27001 audit evidence
Semantically searches and extracts relevant information from structured knowledge base
"""

import pandas as pd
import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

class SearchAgent:
    def __init__(self, output_dir: str = "Output"):
        self.output_dir = output_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = {}
        self.embeddings = {}
        self.load_knowledge_base()
    
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
                # Combine control description and name for embedding
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
        # Find the control
        if 'controls' in self.knowledge_base:
            control_df = self.knowledge_base['controls']
            control = control_df[control_df['Control ID'] == control_id]
            if not control.empty:
                control_info = control.iloc[0].to_dict()
                
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
    
    def query(self, query: str, search_type: str = "semantic") -> Dict[str, Any]:
        """Main query interface for other agents"""
        if search_type == "semantic":
            results = self.semantic_search(query)
            return {
                'query': query,
                'type': 'semantic_search',
                'results': results,
                'total_found': len(results)
            }
        elif search_type.startswith("control:"):
            control_id = search_type.replace("control:", "")
            result = self.search_by_control(control_id)
            return {
                'query': query,
                'type': 'control_search',
                'control_id': control_id,
                'result': result
            }
        elif search_type.startswith("evidence:"):
            evidence_type = search_type.replace("evidence:", "")
            results = self.search_evidence_by_type(evidence_type)
            return {
                'query': query,
                'type': 'evidence_search',
                'evidence_type': evidence_type,
                'results': results,
                'total_found': len(results)
            }
        else:
            return {
                'query': query,
                'type': 'unknown',
                'error': f"Unknown search type: {search_type}"
            }

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
