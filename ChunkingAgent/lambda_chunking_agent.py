#!/usr/bin/env python3
"""
IntelliAudit AWS Lambda File Chunking AI Agent

This Lambda function reads files from an S3 bucket, intelligently chunks them based on 
content characteristics, and outputs structured data to a DynamoDB table.

Features:
- Variable-sized chunking based on content type and structure
- Support for multiple file formats (txt, pdf, docx, csv, xlsx)
- Intelligent content analysis for optimal chunk boundaries
- AWS S3 integration for file input
- AWS DynamoDB integration for output storage
- Lambda-optimized performance with error handling
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import pandas as pd
import numpy as np
from docx import Document
import PyPDF2
import chardet
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import io
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (reused across Lambda invocations)
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables for AWS resources
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'chunked-content')

# Download required NLTK data to /tmp (Lambda writable directory)
nltk.data.path.append('/tmp')

def download_nltk_data():
    """Download NLTK data if not already present."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', download_dir='/tmp')
    
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', download_dir='/tmp')

# Download NLTK data on module import
download_nltk_data()


class ContentAnalyzer:
    """Analyzes content characteristics to determine optimal chunking strategy."""
    
    def __init__(self):
        try:
            self.sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        except LookupError:
            download_nltk_data()
            self.sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    
    def analyze_content_type(self, text: str) -> Dict[str, Any]:
        """Analyze text content to determine its characteristics."""
        lines = text.split('\n')
        
        # Basic statistics
        total_chars = len(text)
        total_lines = len(lines)
        total_sentences = len(self.sentence_tokenizer.tokenize(text))
        avg_line_length = total_chars / max(total_lines, 1)
        
        # Content structure analysis
        has_headers = self._detect_headers(lines)
        has_bullet_points = self._detect_bullet_points(lines)
        has_numbered_lists = self._detect_numbered_lists(lines)
        paragraph_count = self._count_paragraphs(text)
        
        # Determine content type
        content_type = self._classify_content_type(
            has_headers, has_bullet_points, has_numbered_lists, 
            avg_line_length, paragraph_count, total_lines
        )
        
        return {
            'content_type': content_type,
            'total_chars': total_chars,
            'total_lines': total_lines,
            'total_sentences': total_sentences,
            'avg_line_length': avg_line_length,
            'paragraph_count': paragraph_count,
            'has_headers': has_headers,
            'has_bullet_points': has_bullet_points,
            'has_numbered_lists': has_numbered_lists
        }
    
    def _detect_headers(self, lines: List[str]) -> bool:
        """Detect if text contains headers (short lines followed by longer content)."""
        header_pattern = re.compile(r'^[A-Z][^.!?]*$')
        header_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 50 and header_pattern.match(line):
                # Check if followed by content
                if i + 1 < len(lines) and len(lines[i + 1].strip()) > len(line):
                    header_count += 1
        
        return header_count > 0
    
    def _detect_bullet_points(self, lines: List[str]) -> bool:
        """Detect bullet points or list items."""
        bullet_pattern = re.compile(r'^\s*[•\-\*\+]\s+')
        return any(bullet_pattern.match(line) for line in lines)
    
    def _detect_numbered_lists(self, lines: List[str]) -> bool:
        """Detect numbered lists."""
        numbered_pattern = re.compile(r'^\s*\d+[\.\)]\s+')
        return any(numbered_pattern.match(line) for line in lines)
    
    def _count_paragraphs(self, text: str) -> int:
        """Count paragraphs in text."""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        return len([p for p in paragraphs if p.strip()])
    
    def _classify_content_type(self, has_headers: bool, has_bullet_points: bool, 
                              has_numbered_lists: bool, avg_line_length: float,
                              paragraph_count: int, total_lines: int) -> str:
        """Classify content type based on structural features."""
        if avg_line_length < 30 and (has_bullet_points or has_numbered_lists):
            return 'list_document'
        elif has_headers and paragraph_count > 3:
            return 'structured_document'
        elif avg_line_length > 80 and paragraph_count > 5:
            return 'narrative_document'
        elif ',' in str(avg_line_length) and avg_line_length < 50:
            return 'tabular_data'
        else:
            return 'general_text'


class IntelligentChunker:
    """Intelligent chunker that creates variable-sized chunks based on content characteristics."""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
    
    def chunk_content(self, text: str, file_path: str) -> List[str]:
        """Create chunks based on content analysis."""
        content_analysis = self.analyzer.analyze_content_type(text)
        content_type = content_analysis['content_type']
        
        if content_type == 'structured_document':
            return self._chunk_by_sections(text)
        elif content_type == 'narrative_document':
            return self._chunk_by_paragraphs(text)
        elif content_type == 'list_document':
            return self._chunk_by_list_items(text)
        elif content_type == 'tabular_data':
            return self._chunk_by_rows(text)
        else:
            return self._chunk_by_sentences(text)
    
    def _chunk_by_sections(self, text: str) -> List[str]:
        """Chunk structured documents by sections/headers."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            # Check if line is likely a header
            if (len(line.strip()) < 50 and 
                line.strip() and 
                not line.startswith(' ') and 
                not line.startswith('\t')):
                
                # Save previous chunk if it exists
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk narrative documents by paragraphs, combining small ones."""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        current_chunk = []
        current_length = 0
        target_length = 500  # Target chunk size in characters
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if current_length + len(paragraph) > target_length and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_by_list_items(self, text: str) -> List[str]:
        """Chunk list documents by grouping related list items."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            if re.match(r'^\s*[•\-\*\+\d+[\.\)]]\s+', line) and current_chunk:
                # Start new chunk on list items, but group related ones
                if len('\n'.join(current_chunk)) > 300:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
            else:
                current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_rows(self, text: str) -> List[str]:
        """Chunk tabular data by grouping rows."""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        chunk_size = 20  # Number of rows per chunk
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            if (i + 1) % chunk_size == 0:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk general text by sentences with target size."""
        sentences = self.analyzer.sentence_tokenizer.tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        target_length = 400  # Target chunk size in characters
        
        for sentence in sentences:
            if current_length + len(sentence) > target_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


class S3FileReader:
    """Handles reading various file formats from S3."""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = s3_client
    
    def get_object_content(self, key: str) -> bytes:
        """Get file content from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error retrieving S3 object {key}: {e}")
            raise
    
    def detect_encoding(self, content: bytes) -> str:
        """Detect file encoding."""
        result = chardet.detect(content)
        return result['encoding'] or 'utf-8'
    
    def read_text_file(self, key: str) -> str:
        """Read plain text files from S3."""
        content = self.get_object_content(key)
        encoding = self.detect_encoding(content)
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            return content.decode('utf-8', errors='ignore')
    
    def read_pdf_file(self, key: str) -> str:
        """Read PDF files from S3."""
        content = self.get_object_content(key)
        text = ""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"Error reading PDF {key}: {e}")
            return ""
        return text
    
    def read_docx_file(self, key: str) -> str:
        """Read DOCX files from S3."""
        try:
            content = self.get_object_content(key)
            docx_file = io.BytesIO(content)
            doc = Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.warning(f"Error reading DOCX {key}: {e}")
            return ""
    
    def read_csv_file(self, key: str) -> str:
        """Read CSV files from S3."""
        try:
            content = self.get_object_content(key)
            csv_file = io.StringIO(content.decode('utf-8'))
            df = pd.read_csv(csv_file)
            return df.to_string()
        except Exception as e:
            logger.warning(f"Error reading CSV {key}: {e}")
            return ""
    
    def read_excel_file(self, key: str) -> str:
        """Read Excel files from S3."""
        try:
            content = self.get_object_content(key)
            excel_file = io.BytesIO(content)
            df = pd.read_excel(excel_file)
            return df.to_string()
        except Exception as e:
            logger.warning(f"Error reading Excel {key}: {e}")
            return ""
    
    def read_file(self, key: str) -> str:
        """Read any supported file format from S3."""
        file_ext = Path(key).suffix.lower()
        
        if file_ext == '.pdf':
            return self.read_pdf_file(key)
        elif file_ext == '.docx':
            return self.read_docx_file(key)
        elif file_ext == '.csv':
            return self.read_csv_file(key)
        elif file_ext in ['.xlsx', '.xls']:
            return self.read_excel_file(key)
        else:
            return self.read_text_file(key)


class DynamoDBWriter:
    """Handles writing chunk data to DynamoDB."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dynamodb = dynamodb
        try:
            self.table = self.dynamodb.Table(table_name)
        except Exception as e:
            logger.error(f"Error accessing DynamoDB table {table_name}: {e}")
            raise
    
    def write_chunk(self, chunk_data: Dict[str, Any]) -> bool:
        """Write a single chunk to DynamoDB."""
        try:
            # Convert all numeric values to Decimal for DynamoDB compatibility
            item = {}
            for key, value in chunk_data.items():
                if isinstance(value, (int, float)):
                    item[key] = Decimal(str(value))
                else:
                    item[key] = value
            
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error writing to DynamoDB: {e}")
            return False
    
    def batch_write_chunks(self, chunks_data: List[Dict[str, Any]]) -> int:
        """Batch write multiple chunks to DynamoDB."""
        successful_writes = 0
        
        # DynamoDB batch_write_item has a limit of 25 items
        batch_size = 25
        
        for i in range(0, len(chunks_data), batch_size):
            batch = chunks_data[i:i + batch_size]
            
            try:
                # Prepare batch write request
                with self.table.batch_writer() as batch_writer:
                    for chunk_data in batch:
                        try:
                            # Convert numeric values to Decimal
                            item = {}
                            for key, value in chunk_data.items():
                                if isinstance(value, (int, float)):
                                    item[key] = Decimal(str(value))
                                else:
                                    item[key] = value
                            
                            batch_writer.put_item(Item=item)
                            successful_writes += 1
                        except Exception as e:
                            logger.error(f"Error in batch write for chunk: {e}")
            except Exception as e:
                logger.error(f"Error in batch write operation: {e}")
        
        return successful_writes


class LambdaChunkingAgent:
    """AWS Lambda compatible AI agent for intelligent file chunking."""
    
    def __init__(self, bucket_name: str, table_name: str):
        self.bucket_name = bucket_name
        self.table_name = table_name
        self.chunker = IntelligentChunker()
        self.file_reader = S3FileReader(bucket_name)
        self.db_writer = DynamoDBWriter(table_name)
    
    def process_s3_file(self, s3_key: str, execution_id: str = None) -> Dict[str, Any]:
        """Process a single file from S3 and write chunks to DynamoDB."""
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        logger.info(f"Processing S3 file: {s3_key}")
        
        try:
            # Read file content from S3
            content = self.file_reader.read_file(s3_key)
            
            if not content.strip():
                logger.warning(f"File {s3_key} is empty or unreadable")
                return {
                    'statusCode': 400,
                    'message': f'File {s3_key} is empty or unreadable',
                    'chunks_created': 0
                }
            
            # Create chunks
            chunks = self.chunker.chunk_content(content, s3_key)
            total_chunks = len(chunks)
            
            # Prepare chunk data for DynamoDB
            chunks_data = []
            timestamp = datetime.utcnow().isoformat()
            
            for chunk_index, chunk in enumerate(chunks, 1):
                chunk_data = {
                    'id': f"{execution_id}_{chunk_index}",  # Primary key
                    'execution_id': execution_id,
                    'file_path': s3_key,
                    'file_name': Path(s3_key).name,
                    'total_chunks': total_chunks,
                    'chunk_number': chunk_index,
                    'chunk_content': chunk.strip(),
                    'chunk_size': len(chunk.strip()),
                    'created_at': timestamp,
                    'source_bucket': self.bucket_name,
                    'content_type': self.chunker.analyzer.analyze_content_type(content)['content_type']
                }
                chunks_data.append(chunk_data)
            
            # Write chunks to DynamoDB
            successful_writes = self.db_writer.batch_write_chunks(chunks_data)
            
            logger.info(f"Successfully wrote {successful_writes}/{total_chunks} chunks for {s3_key}")
            
            return {
                'statusCode': 200,
                'message': f'Successfully processed {s3_key}',
                'execution_id': execution_id,
                'file_path': s3_key,
                'file_name': Path(s3_key).name,
                'total_chunks': total_chunks,
                'successful_writes': successful_writes,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing file {s3_key}: {e}")
            return {
                'statusCode': 500,
                'message': f'Error processing file {s3_key}: {str(e)}',
                'execution_id': execution_id,
                'chunks_created': 0
            }
    
    def process_multiple_files(self, s3_keys: List[str]) -> Dict[str, Any]:
        """Process multiple files from S3."""
        execution_id = str(uuid.uuid4())
        results = []
        total_chunks = 0
        successful_files = 0
        
        for s3_key in s3_keys:
            result = self.process_s3_file(s3_key, execution_id)
            results.append(result)
            
            if result['statusCode'] == 200:
                successful_files += 1
                total_chunks += result.get('total_chunks', 0)
        
        return {
            'statusCode': 200,
            'message': f'Processed {successful_files}/{len(s3_keys)} files successfully',
            'execution_id': execution_id,
            'total_files_processed': len(s3_keys),
            'successful_files': successful_files,
            'total_chunks_created': total_chunks,
            'individual_results': results
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Expected event structure:
    {
        "s3_key": "path/to/file.pdf",  # For single file processing
        "s3_keys": ["file1.pdf", "file2.txt"],  # For multiple file processing
        "bucket_name": "my-bucket",  # Optional, uses env var if not provided
        "table_name": "my-table"  # Optional, uses env var if not provided
    }
    
    Or S3 event structure for automatic processing:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "bucket-name"},
                    "object": {"key": "file-key"}
                }
            }
        ]
    }
    """
    
    try:
        # Handle S3 event triggers
        if 'Records' in event and event['Records']:
            s3_record = event['Records'][0]['s3']
            bucket_name = s3_record['bucket']['name']
            s3_key = s3_record['object']['key']
            table_name = DYNAMODB_TABLE_NAME
            
            logger.info(f"Processing S3 event for {s3_key} in bucket {bucket_name}")
            
        else:
            # Handle direct invocation
            bucket_name = event.get('bucket_name', BUCKET_NAME)
            table_name = event.get('table_name', DYNAMODB_TABLE_NAME)
            s3_key = event.get('s3_key')
        
        if not bucket_name:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'S3 bucket name not provided in event or environment variables'
                })
            }
        
        if not table_name:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'DynamoDB table name not provided in event or environment variables'
                })
            }
        
        # Initialize the chunking agent
        agent = LambdaChunkingAgent(bucket_name, table_name)
        
        # Process single file or multiple files
        if s3_key:
            # Single file processing
            result = agent.process_s3_file(s3_key)
        elif 's3_keys' in event:
            # Multiple file processing
            s3_keys = event['s3_keys']
            result = agent.process_multiple_files(s3_keys)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Either s3_key or s3_keys must be provided in the event'
                })
            }
        
        return {
            'statusCode': result['statusCode'],
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Lambda execution error: {str(e)}'
            })
        }


# For testing locally
if __name__ == "__main__":
    # Example test event
    test_event = {
        "s3_key": "sample_document.pdf",
        "bucket_name": "my-test-bucket",
        "table_name": "chunked-content-test"
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
