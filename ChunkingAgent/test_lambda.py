#!/usr/bin/env python3
"""
Test script for IntelliAudit Lambda Function

This script provides various ways to test the Lambda function:
1. Direct Lambda invocation
2. S3 upload simulation
3. DynamoDB query for results
4. Performance testing
"""

import boto3
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
import argparse


class LambdaTester:
    """Test harness for the IntelliAudit Lambda function."""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
    def test_single_file(self, function_name: str, s3_key: str, bucket_name: str, 
                        table_name: str = 'chunked-content') -> Dict[str, Any]:
        """Test processing a single file."""
        print(f"🧪 Testing single file: {s3_key}")
        
        payload = {
            "s3_key": s3_key,
            "bucket_name": bucket_name,
            "table_name": table_name
        }
        
        start_time = time.time()
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(payload),
                LogType='Tail'
            )
            
            execution_time = time.time() - start_time
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            # Decode logs
            logs = ""
            if 'LogResult' in response:
                import base64
                logs = base64.b64decode(response['LogResult']).decode('utf-8')
            
            print(f"✅ Execution completed in {execution_time:.2f} seconds")
            print(f"📊 Status Code: {response['StatusCode']}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"🎯 Chunks created: {body.get('total_chunks', 0)}")
                print(f"📝 Execution ID: {body.get('execution_id', 'N/A')}")
            else:
                print(f"❌ Error: {result.get('body', 'Unknown error')}")
            
            return {
                'success': response['StatusCode'] == 200,
                'execution_time': execution_time,
                'result': result,
                'logs': logs
            }
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return {
                'success': False,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
    
    def test_multiple_files(self, function_name: str, s3_keys: List[str], 
                          bucket_name: str, table_name: str = 'chunked-content') -> Dict[str, Any]:
        """Test processing multiple files."""
        print(f"🧪 Testing multiple files: {s3_keys}")
        
        payload = {
            "s3_keys": s3_keys,
            "bucket_name": bucket_name,
            "table_name": table_name
        }
        
        start_time = time.time()
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(payload)
            )
            
            execution_time = time.time() - start_time
            result = json.loads(response['Payload'].read())
            
            print(f"✅ Execution completed in {execution_time:.2f} seconds")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"📁 Files processed: {body.get('successful_files', 0)}/{body.get('total_files_processed', 0)}")
                print(f"🎯 Total chunks: {body.get('total_chunks_created', 0)}")
            
            return {
                'success': response['StatusCode'] == 200,
                'execution_time': execution_time,
                'result': result
            }
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def upload_test_file(self, bucket_name: str, local_file_path: str, s3_key: str = None) -> str:
        """Upload a test file to S3."""
        if s3_key is None:
            s3_key = f"test-files/{uuid.uuid4().hex}_{local_file_path.split('/')[-1]}"
        
        print(f"📤 Uploading {local_file_path} to s3://{bucket_name}/{s3_key}")
        
        try:
            self.s3_client.upload_file(local_file_path, bucket_name, s3_key)
            print(f"✅ Upload successful")
            return s3_key
        except Exception as e:
            print(f"❌ Upload failed: {str(e)}")
            raise
    
    def query_chunks(self, table_name: str, execution_id: str = None, 
                    file_path: str = None, limit: int = 10) -> List[Dict]:
        """Query chunks from DynamoDB."""
        table = self.dynamodb.Table(table_name)
        
        try:
            if execution_id:
                print(f"🔍 Querying chunks for execution: {execution_id}")
                response = table.query(
                    IndexName='execution-id-index',
                    KeyConditionExpression='execution_id = :exec_id',
                    ExpressionAttributeValues={':exec_id': execution_id},
                    Limit=limit
                )
            elif file_path:
                print(f"🔍 Querying chunks for file: {file_path}")
                response = table.query(
                    IndexName='file-path-index',
                    KeyConditionExpression='file_path = :file_path',
                    ExpressionAttributeValues={':file_path': file_path},
                    Limit=limit
                )
            else:
                print(f"🔍 Scanning recent chunks (limit: {limit})")
                response = table.scan(Limit=limit)
            
            items = response.get('Items', [])
            print(f"📊 Found {len(items)} chunks")
            
            return items
            
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            return []
    
    def create_test_data(self, bucket_name: str) -> List[str]:
        """Create sample test files and upload to S3."""
        print("📝 Creating test data...")
        
        test_files = []
        
        # Create a simple text file
        text_content = """
        # Test Document
        
        This is a test document for the IntelliAudit chunking system.
        
        ## Section 1: Introduction
        This section contains introductory text that should be chunked appropriately.
        The chunking algorithm will analyze this content and determine optimal boundaries.
        
        ## Section 2: Content Analysis
        - The system supports multiple file formats
        - It performs intelligent content analysis
        - Variable-sized chunks are created based on content type
        
        ### Subsection 2.1: Features
        1. PDF processing
        2. DOCX processing  
        3. CSV processing
        4. Excel file processing
        
        ## Conclusion
        This test document provides various content types to validate the chunking logic.
        """
        
        # Upload text content as a file
        try:
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(text_content)
                temp_file = f.name
            
            s3_key = self.upload_test_file(bucket_name, temp_file, 'test-data/sample_document.txt')
            test_files.append(s3_key)
            
            # Cleanup temp file
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"⚠️ Could not create test text file: {e}")
        
        # Create CSV test data
        csv_content = """Name,Age,City,Country
John Doe,30,New York,USA
Jane Smith,25,London,UK
Bob Johnson,35,Toronto,Canada
Alice Brown,28,Sydney,Australia
Charlie Wilson,32,Berlin,Germany"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(csv_content)
                temp_file = f.name
            
            s3_key = self.upload_test_file(bucket_name, temp_file, 'test-data/sample_data.csv')
            test_files.append(s3_key)
            
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"⚠️ Could not create test CSV file: {e}")
        
        return test_files
    
    def run_performance_test(self, function_name: str, bucket_name: str, 
                           s3_keys: List[str], iterations: int = 5) -> Dict[str, Any]:
        """Run performance tests."""
        print(f"🚀 Running performance test ({iterations} iterations)")
        
        results = []
        total_chunks = 0
        
        for i in range(iterations):
            print(f"📊 Iteration {i + 1}/{iterations}")
            
            # Test single file
            if s3_keys:
                result = self.test_single_file(function_name, s3_keys[0], bucket_name)
                results.append(result)
                
                if result['success'] and 'result' in result:
                    try:
                        body = json.loads(result['result']['body'])
                        total_chunks += body.get('total_chunks', 0)
                    except:
                        pass
        
        # Calculate statistics
        execution_times = [r['execution_time'] for r in results if 'execution_time' in r]
        success_rate = sum(1 for r in results if r['success']) / len(results)
        
        stats = {
            'iterations': iterations,
            'success_rate': success_rate,
            'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'total_chunks_created': total_chunks
        }
        
        print(f"📈 Performance Results:")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
        print(f"   Avg Execution Time: {stats['avg_execution_time']:.2f}s")
        print(f"   Min/Max Time: {stats['min_execution_time']:.2f}s / {stats['max_execution_time']:.2f}s")
        print(f"   Total Chunks: {stats['total_chunks_created']}")
        
        return stats


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test IntelliAudit Lambda Function')
    parser.add_argument('--function-name', default='intelliaudit-chunking-agent',
                       help='Lambda function name')
    parser.add_argument('--bucket-name', required=True,
                       help='S3 bucket name')
    parser.add_argument('--table-name', default='chunked-content',
                       help='DynamoDB table name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--test-file', 
                       help='Local file to upload and test')
    parser.add_argument('--s3-key',
                       help='Existing S3 key to test')
    parser.add_argument('--create-test-data', action='store_true',
                       help='Create and upload test data')
    parser.add_argument('--performance-test', action='store_true',
                       help='Run performance tests')
    parser.add_argument('--query-execution-id',
                       help='Query chunks by execution ID')
    parser.add_argument('--query-file-path',
                       help='Query chunks by file path')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = LambdaTester(region=args.region)
    
    print("🔧 IntelliAudit Lambda Function Tester")
    print(f"📍 Region: {args.region}")
    print(f"⚡ Function: {args.function_name}")
    print(f"🪣 Bucket: {args.bucket_name}")
    print(f"🗄️ Table: {args.table_name}")
    print("-" * 50)
    
    try:
        # Create test data if requested
        if args.create_test_data:
            test_files = tester.create_test_data(args.bucket_name)
            print(f"✅ Created {len(test_files)} test files")
            
            if test_files and not args.s3_key:
                args.s3_key = test_files[0]  # Use first test file
        
        # Upload and test local file
        if args.test_file:
            s3_key = tester.upload_test_file(args.bucket_name, args.test_file)
            result = tester.test_single_file(args.function_name, s3_key, args.bucket_name, args.table_name)
            
            if result['success'] and 'result' in result:
                try:
                    body = json.loads(result['result']['body'])
                    execution_id = body.get('execution_id')
                    if execution_id:
                        print("\n🔍 Querying created chunks...")
                        chunks = tester.query_chunks(args.table_name, execution_id=execution_id)
                        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                            print(f"   Chunk {i+1}: {chunk.get('chunk_content', '')[:100]}...")
                except:
                    pass
        
        # Test existing S3 file
        elif args.s3_key:
            result = tester.test_single_file(args.function_name, args.s3_key, args.bucket_name, args.table_name)
        
        # Query operations
        if args.query_execution_id:
            chunks = tester.query_chunks(args.table_name, execution_id=args.query_execution_id)
            for i, chunk in enumerate(chunks):
                print(f"Chunk {chunk.get('chunk_number', i+1)}: {chunk.get('chunk_content', '')[:200]}...")
        
        if args.query_file_path:
            chunks = tester.query_chunks(args.table_name, file_path=args.query_file_path)
            for i, chunk in enumerate(chunks):
                print(f"Chunk {chunk.get('chunk_number', i+1)}: {chunk.get('chunk_content', '')[:200]}...")
        
        # Performance testing
        if args.performance_test and args.s3_key:
            stats = tester.run_performance_test(
                args.function_name, 
                args.bucket_name, 
                [args.s3_key], 
                iterations=5
            )
        
        print("\n✅ Testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
