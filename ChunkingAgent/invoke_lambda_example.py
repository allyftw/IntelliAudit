#!/usr/bin/env python3
"""
Example script for manually invoking the IntelliAudit Lambda function

This script demonstrates various ways to invoke the Lambda function:
1. Single file processing
2. Multiple file processing  
3. Processing with custom parameters
4. Asynchronous invocation
"""

import boto3
import json
import time
from typing import Dict, Any, List, Optional


class LambdaInvoker:
    """Helper class for invoking the IntelliAudit Lambda function."""
    
    def __init__(self, function_name: str, region: str = 'us-east-1'):
        self.function_name = function_name
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
    
    def invoke_single_file(self, s3_key: str, bucket_name: str, 
                          table_name: Optional[str] = None, 
                          synchronous: bool = True) -> Dict[str, Any]:
        """
        Invoke Lambda function to process a single file.
        
        Args:
            s3_key: S3 object key (file path in bucket)
            bucket_name: S3 bucket name
            table_name: DynamoDB table name (optional)
            synchronous: Whether to wait for response (True) or invoke async (False)
        
        Returns:
            Dictionary containing the response
        """
        payload = {
            "s3_key": s3_key,
            "bucket_name": bucket_name
        }
        
        if table_name:
            payload["table_name"] = table_name
        
        print(f"🚀 Invoking Lambda function: {self.function_name}")
        print(f"📁 Processing file: s3://{bucket_name}/{s3_key}")
        
        invocation_type = 'RequestResponse' if synchronous else 'Event'
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            if synchronous:
                # Parse response for synchronous invocation
                result = json.loads(response['Payload'].read())
                
                print(f"✅ Lambda invocation completed")
                print(f"📊 Status Code: {response['StatusCode']}")
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    print(f"🎯 Execution ID: {body.get('execution_id', 'N/A')}")
                    print(f"📝 Total chunks: {body.get('total_chunks', 0)}")
                    print(f"✍️ Successful writes: {body.get('successful_writes', 0)}")
                else:
                    print(f"❌ Error: {result.get('body', 'Unknown error')}")
                
                return result
            else:
                # For asynchronous invocation
                print(f"🚀 Async invocation triggered")
                print(f"📊 Status Code: {response['StatusCode']}")
                return {
                    'statusCode': response['StatusCode'],
                    'async': True,
                    'message': 'Asynchronous invocation completed'
                }
                
        except Exception as e:
            print(f"❌ Lambda invocation failed: {str(e)}")
            return {
                'statusCode': 500,
                'error': str(e)
            }
    
    def invoke_multiple_files(self, s3_keys: List[str], bucket_name: str,
                            table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke Lambda function to process multiple files.
        
        Args:
            s3_keys: List of S3 object keys
            bucket_name: S3 bucket name
            table_name: DynamoDB table name (optional)
        
        Returns:
            Dictionary containing the response
        """
        payload = {
            "s3_keys": s3_keys,
            "bucket_name": bucket_name
        }
        
        if table_name:
            payload["table_name"] = table_name
        
        print(f"🚀 Invoking Lambda function: {self.function_name}")
        print(f"📁 Processing {len(s3_keys)} files from s3://{bucket_name}/")
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            print(f"✅ Lambda invocation completed")
            print(f"📊 Status Code: {response['StatusCode']}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"🎯 Execution ID: {body.get('execution_id', 'N/A')}")
                print(f"📁 Files processed: {body.get('successful_files', 0)}/{body.get('total_files_processed', 0)}")
                print(f"📝 Total chunks: {body.get('total_chunks_created', 0)}")
            else:
                print(f"❌ Error: {result.get('body', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Lambda invocation failed: {str(e)}")
            return {
                'statusCode': 500,
                'error': str(e)
            }
    
    def get_function_info(self) -> Dict[str, Any]:
        """Get information about the Lambda function."""
        try:
            response = self.lambda_client.get_function(FunctionName=self.function_name)
            
            config = response['Configuration']
            print(f"📋 Function Information:")
            print(f"   Name: {config['FunctionName']}")
            print(f"   Runtime: {config['Runtime']}")
            print(f"   Memory: {config['MemorySize']} MB")
            print(f"   Timeout: {config['Timeout']} seconds")
            print(f"   Last Modified: {config['LastModified']}")
            
            # Environment variables
            env_vars = config.get('Environment', {}).get('Variables', {})
            if env_vars:
                print(f"   Environment Variables:")
                for key, value in env_vars.items():
                    print(f"     {key}: {value}")
            
            return response
            
        except Exception as e:
            print(f"❌ Could not get function info: {str(e)}")
            return {}


def example_single_file():
    """Example: Process a single file."""
    print("=" * 60)
    print("Example 1: Processing a Single File")
    print("=" * 60)
    
    # Configuration
    function_name = "intelliaudit-chunking-agent"
    bucket_name = "your-bucket-name"  # Replace with your bucket
    s3_key = "documents/sample.pdf"   # Replace with your file
    
    # Create invoker
    invoker = LambdaInvoker(function_name)
    
    # Get function info
    invoker.get_function_info()
    print()
    
    # Invoke function
    result = invoker.invoke_single_file(s3_key, bucket_name)
    
    # Print detailed results
    print("\n📋 Detailed Results:")
    print(json.dumps(result, indent=2, default=str))


def example_multiple_files():
    """Example: Process multiple files."""
    print("=" * 60)
    print("Example 2: Processing Multiple Files")
    print("=" * 60)
    
    # Configuration
    function_name = "intelliaudit-chunking-agent"
    bucket_name = "your-bucket-name"  # Replace with your bucket
    s3_keys = [                       # Replace with your files
        "documents/file1.pdf",
        "documents/file2.txt",
        "documents/file3.docx"
    ]
    
    # Create invoker
    invoker = LambdaInvoker(function_name)
    
    # Invoke function
    result = invoker.invoke_multiple_files(s3_keys, bucket_name)
    
    # Print detailed results
    print("\n📋 Detailed Results:")
    print(json.dumps(result, indent=2, default=str))


def example_async_processing():
    """Example: Asynchronous processing."""
    print("=" * 60)
    print("Example 3: Asynchronous Processing")
    print("=" * 60)
    
    # Configuration
    function_name = "intelliaudit-chunking-agent"
    bucket_name = "your-bucket-name"  # Replace with your bucket
    s3_key = "documents/large_file.pdf"  # Replace with your file
    
    # Create invoker
    invoker = LambdaInvoker(function_name)
    
    # Invoke function asynchronously
    result = invoker.invoke_single_file(s3_key, bucket_name, synchronous=False)
    
    print("\n📋 Async Invocation Result:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n💡 Tip: Check CloudWatch logs to see the async execution:")
    print(f"aws logs tail /aws/lambda/{function_name} --follow")


def example_batch_processing():
    """Example: Process all files in an S3 prefix."""
    print("=" * 60)
    print("Example 4: Batch Processing with S3 Listing")
    print("=" * 60)
    
    # Configuration
    function_name = "intelliaudit-chunking-agent"
    bucket_name = "your-bucket-name"  # Replace with your bucket
    prefix = "documents/"             # Replace with your prefix
    
    # List files in S3 bucket
    s3_client = boto3.client('s3')
    
    try:
        print(f"📁 Listing files in s3://{bucket_name}/{prefix}")
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        # Filter for supported file types
        supported_extensions = {'.pdf', '.txt', '.docx', '.csv', '.xlsx', '.xls', '.md', '.json'}
        s3_keys = []
        
        for obj in response.get('Contents', []):
            key = obj['Key']
            if any(key.lower().endswith(ext) for ext in supported_extensions):
                s3_keys.append(key)
                print(f"   📄 {key}")
        
        if not s3_keys:
            print("⚠️ No supported files found")
            return
        
        print(f"\n🚀 Processing {len(s3_keys)} files...")
        
        # Create invoker and process files
        invoker = LambdaInvoker(function_name)
        
        # Process in batches to avoid Lambda payload limits
        batch_size = 10
        for i in range(0, len(s3_keys), batch_size):
            batch = s3_keys[i:i + batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1} ({len(batch)} files)")
            
            result = invoker.invoke_multiple_files(batch, bucket_name)
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"✅ Batch completed: {body.get('successful_files', 0)} files processed")
            else:
                print(f"❌ Batch failed: {result.get('body', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Batch processing failed: {str(e)}")


def example_with_monitoring():
    """Example: Process file with monitoring."""
    print("=" * 60)
    print("Example 5: Processing with Monitoring")
    print("=" * 60)
    
    # Configuration
    function_name = "intelliaudit-chunking-agent"
    bucket_name = "your-bucket-name"  # Replace with your bucket
    s3_key = "documents/sample.pdf"   # Replace with your file
    
    # Create invoker
    invoker = LambdaInvoker(function_name)
    
    # Monitor execution
    print("🔍 Starting monitored execution...")
    start_time = time.time()
    
    result = invoker.invoke_single_file(s3_key, bucket_name)
    
    execution_time = time.time() - start_time
    print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
    
    # Check for success and get execution ID
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        execution_id = body.get('execution_id')
        
        if execution_id:
            print(f"\n🔍 Querying results for execution: {execution_id}")
            
            # Query DynamoDB for results
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('chunked-content')  # Replace with your table name
            
            try:
                response = table.query(
                    IndexName='execution-id-index',
                    KeyConditionExpression='execution_id = :exec_id',
                    ExpressionAttributeValues={':exec_id': execution_id}
                )
                
                chunks = response.get('Items', [])
                print(f"📊 Found {len(chunks)} chunks in DynamoDB")
                
                # Show sample chunks
                for i, chunk in enumerate(chunks[:3]):
                    print(f"\n📝 Chunk {chunk.get('chunk_number', i+1)}:")
                    print(f"   Size: {chunk.get('chunk_size', 0)} characters")
                    print(f"   Content: {chunk.get('chunk_content', '')[:100]}...")
                
                if len(chunks) > 3:
                    print(f"\n... and {len(chunks) - 3} more chunks")
                
            except Exception as e:
                print(f"⚠️ Could not query DynamoDB: {str(e)}")


if __name__ == "__main__":
    """Run all examples."""
    
    print("🔧 IntelliAudit Lambda Function Examples")
    print("📍 Make sure to update the configuration variables in each example!")
    print()
    
    # Note: Comment out examples you don't want to run
    # and update the configuration variables above
    
    try:
        # example_single_file()
        # example_multiple_files() 
        # example_async_processing()
        # example_batch_processing()
        # example_with_monitoring()
        
        print("💡 Uncomment the examples you want to run and update the configuration!")
        print("💡 Make sure to replace 'your-bucket-name' and file paths with real values!")
        
    except Exception as e:
        print(f"❌ Example execution failed: {str(e)}")
        print("💡 Make sure your AWS credentials are configured and the Lambda function exists!")
