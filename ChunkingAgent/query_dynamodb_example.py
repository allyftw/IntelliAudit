#!/usr/bin/env python3
"""
Example script for querying processed chunks from DynamoDB

This script demonstrates various ways to query and analyze the chunked data:
1. Query by execution ID
2. Query by file path
3. Search by content
4. Generate reports and statistics
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import argparse
from collections import Counter
import re


class DynamoDBQuerier:
    """Helper class for querying chunked content from DynamoDB."""
    
    def __init__(self, table_name: str, region: str = 'us-east-1'):
        self.table_name = table_name
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def query_by_execution_id(self, execution_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query chunks by execution ID."""
        print(f"🔍 Querying chunks for execution: {execution_id}")
        
        try:
            response = self.table.query(
                IndexName='execution-id-index',
                KeyConditionExpression='execution_id = :exec_id',
                ExpressionAttributeValues={':exec_id': execution_id},
                Limit=limit,
                ScanIndexForward=True  # Sort by range key (created_at)
            )
            
            items = response.get('Items', [])
            print(f"📊 Found {len(items)} chunks")
            
            return items
            
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            return []
    
    def query_by_file_path(self, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query chunks by file path."""
        print(f"🔍 Querying chunks for file: {file_path}")
        
        try:
            response = self.table.query(
                IndexName='file-path-index',
                KeyConditionExpression='file_path = :file_path',
                ExpressionAttributeValues={':file_path': file_path},
                Limit=limit,
                ScanIndexForward=True
            )
            
            items = response.get('Items', [])
            print(f"📊 Found {len(items)} chunks")
            
            return items
            
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            return []
    
    def scan_recent_chunks(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Scan for chunks created in the last N hours."""
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        print(f"🔍 Scanning for chunks created after: {cutoff_time}")
        
        try:
            response = self.table.scan(
                FilterExpression='created_at > :cutoff',
                ExpressionAttributeValues={':cutoff': cutoff_time},
                Limit=limit
            )
            
            items = response.get('Items', [])
            print(f"📊 Found {len(items)} recent chunks")
            
            return items
            
        except Exception as e:
            print(f"❌ Scan failed: {str(e)}")
            return []
    
    def search_content(self, search_term: str, case_sensitive: bool = False, 
                      limit: int = 50) -> List[Dict[str, Any]]:
        """Search for chunks containing specific text."""
        print(f"🔍 Searching for content: '{search_term}'")
        
        try:
            # Use scan with filter expression for content search
            if case_sensitive:
                filter_expr = 'contains(chunk_content, :search_term)'
            else:
                # For case-insensitive search, we'll need to scan and filter manually
                # Note: DynamoDB doesn't support case-insensitive contains
                filter_expr = 'contains(chunk_content, :search_term)'
            
            response = self.table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues={':search_term': search_term},
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # If not case sensitive, do additional filtering
            if not case_sensitive:
                search_lower = search_term.lower()
                items = [
                    item for item in items 
                    if search_lower in item.get('chunk_content', '').lower()
                ]
            
            print(f"📊 Found {len(items)} chunks containing '{search_term}'")
            
            return items
            
        except Exception as e:
            print(f"❌ Search failed: {str(e)}")
            return []
    
    def get_chunk_statistics(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics for a list of chunks."""
        if not items:
            return {}
        
        # Basic statistics
        total_chunks = len(items)
        total_characters = sum(int(item.get('chunk_size', 0)) for item in items)
        
        # Content type distribution
        content_types = [item.get('content_type', 'unknown') for item in items]
        content_type_counts = Counter(content_types)
        
        # File distribution
        files = [item.get('file_name', 'unknown') for item in items]
        file_counts = Counter(files)
        
        # Chunk size statistics
        chunk_sizes = [int(item.get('chunk_size', 0)) for item in items]
        
        stats = {
            'total_chunks': total_chunks,
            'total_characters': total_characters,
            'average_chunk_size': total_characters / total_chunks if total_chunks > 0 else 0,
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
            'content_type_distribution': dict(content_type_counts),
            'file_distribution': dict(file_counts),
            'unique_files': len(file_counts),
            'unique_executions': len(set(item.get('execution_id', '') for item in items))
        }
        
        return stats
    
    def print_statistics(self, stats: Dict[str, Any]):
        """Print formatted statistics."""
        print("\n📊 Chunk Statistics:")
        print("-" * 40)
        print(f"Total Chunks: {stats.get('total_chunks', 0):,}")
        print(f"Total Characters: {stats.get('total_characters', 0):,}")
        print(f"Average Chunk Size: {stats.get('average_chunk_size', 0):.1f} characters")
        print(f"Min/Max Chunk Size: {stats.get('min_chunk_size', 0)} / {stats.get('max_chunk_size', 0)}")
        print(f"Unique Files: {stats.get('unique_files', 0)}")
        print(f"Unique Executions: {stats.get('unique_executions', 0)}")
        
        # Content type distribution
        print(f"\n📋 Content Type Distribution:")
        for content_type, count in stats.get('content_type_distribution', {}).items():
            percentage = (count / stats.get('total_chunks', 1)) * 100
            print(f"  {content_type}: {count} ({percentage:.1f}%)")
        
        # File distribution (top 10)
        print(f"\n📁 File Distribution (Top 10):")
        file_dist = stats.get('file_distribution', {})
        sorted_files = sorted(file_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for filename, count in sorted_files:
            print(f"  {filename}: {count} chunks")
    
    def print_chunks(self, items: List[Dict[str, Any]], show_content: bool = True, 
                    max_content_length: int = 200):
        """Print formatted chunk information."""
        if not items:
            print("📭 No chunks found")
            return
        
        print(f"\n📋 Chunk Details ({len(items)} items):")
        print("-" * 80)
        
        for i, item in enumerate(items, 1):
            print(f"\n🔸 Chunk {i}:")
            print(f"   ID: {item.get('id', 'N/A')}")
            print(f"   File: {item.get('file_name', 'N/A')}")
            print(f"   Chunk #: {item.get('chunk_number', 'N/A')} / {item.get('total_chunks', 'N/A')}")
            print(f"   Size: {item.get('chunk_size', 0)} characters")
            print(f"   Type: {item.get('content_type', 'N/A')}")
            print(f"   Created: {item.get('created_at', 'N/A')}")
            
            if show_content and 'chunk_content' in item:
                content = item['chunk_content']
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "..."
                print(f"   Content: {content}")
    
    def export_to_json(self, items: List[Dict[str, Any]], filename: str):
        """Export chunks to JSON file."""
        try:
            # Convert Decimal types for JSON serialization
            export_items = []
            for item in items:
                export_item = {}
                for key, value in item.items():
                    if hasattr(value, '__float__'):  # Decimal type
                        export_item[key] = float(value)
                    else:
                        export_item[key] = value
                export_items.append(export_item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_items, f, indent=2, default=str, ensure_ascii=False)
            
            print(f"📁 Exported {len(items)} chunks to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
    
    def get_all_executions(self, limit: int = 50) -> List[Dict[str, str]]:
        """Get list of recent executions."""
        try:
            response = self.table.scan(
                ProjectionExpression='execution_id, created_at, file_name',
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # Group by execution_id
            executions = {}
            for item in items:
                exec_id = item.get('execution_id')
                if exec_id and exec_id not in executions:
                    executions[exec_id] = {
                        'execution_id': exec_id,
                        'created_at': item.get('created_at', ''),
                        'sample_file': item.get('file_name', '')
                    }
            
            return list(executions.values())
            
        except Exception as e:
            print(f"❌ Failed to get executions: {str(e)}")
            return []


def main():
    """Main query function with command-line interface."""
    parser = argparse.ArgumentParser(description='Query IntelliAudit DynamoDB chunks')
    parser.add_argument('--table-name', default='chunked-content',
                       help='DynamoDB table name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--execution-id',
                       help='Query by execution ID')
    parser.add_argument('--file-path',
                       help='Query by file path')
    parser.add_argument('--search',
                       help='Search for text in chunk content')
    parser.add_argument('--recent-hours', type=int, default=24,
                       help='Show chunks from last N hours')
    parser.add_argument('--limit', type=int, default=100,
                       help='Maximum number of items to return')
    parser.add_argument('--show-content', action='store_true',
                       help='Show chunk content in output')
    parser.add_argument('--export', 
                       help='Export results to JSON file')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show only statistics')
    parser.add_argument('--list-executions', action='store_true',
                       help='List recent executions')
    
    args = parser.parse_args()
    
    # Initialize querier
    querier = DynamoDBQuerier(args.table_name, args.region)
    
    print("🔧 IntelliAudit DynamoDB Query Tool")
    print(f"🗄️ Table: {args.table_name}")
    print(f"📍 Region: {args.region}")
    print("-" * 50)
    
    try:
        items = []
        
        # Execute query based on parameters
        if args.list_executions:
            executions = querier.get_all_executions(args.limit)
            if executions:
                print(f"\n📋 Recent Executions ({len(executions)}):")
                for exec_info in executions:
                    print(f"  🔸 {exec_info['execution_id']}")
                    print(f"     Created: {exec_info['created_at']}")
                    print(f"     Sample File: {exec_info['sample_file']}")
                    print()
            else:
                print("📭 No executions found")
            return
            
        elif args.execution_id:
            items = querier.query_by_execution_id(args.execution_id, args.limit)
        elif args.file_path:
            items = querier.query_by_file_path(args.file_path, args.limit)
        elif args.search:
            items = querier.search_content(args.search, limit=args.limit)
        else:
            items = querier.scan_recent_chunks(args.recent_hours, args.limit)
        
        if not items:
            print("📭 No chunks found matching the criteria")
            return
        
        # Generate and show statistics
        stats = querier.get_chunk_statistics(items)
        querier.print_statistics(stats)
        
        # Show detailed results unless stats-only
        if not args.stats_only:
            querier.print_chunks(items, args.show_content)
        
        # Export if requested
        if args.export:
            querier.export_to_json(items, args.export)
        
        print(f"\n✅ Query completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Query failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
