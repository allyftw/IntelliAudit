# IntelliAudit AWS Lambda Chunking Agent

This directory contains the AWS Lambda version of the IntelliAudit chunking agent, refactored from the original `chunking_agent.py` to work with AWS cloud services.

## 📁 Directory Contents

### Core Files
- `lambda_chunking_agent.py` - Main Lambda function code
- `requirements_lambda.txt` - Python dependencies optimized for Lambda
- `cloudformation_template.yaml` - AWS infrastructure template

### Deployment Scripts
- `deploy_lambda.sh` - Linux/macOS deployment script
- `deploy_lambda.ps1` - Windows PowerShell deployment script

### Documentation
- `README_AWS_Lambda.md` - Comprehensive documentation
- `QUICK_START.md` - Quick getting started guide

### Testing & Examples
- `test_lambda.py` - Test harness with various testing scenarios
- `invoke_lambda_example.py` - Manual Lambda invocation examples
- `query_dynamodb_example.py` - DynamoDB query and analysis tools

## 🚀 Quick Start

**Windows:**
```powershell
cd ChunkingAgent
.\deploy_lambda.ps1
```

**Linux/macOS:**
```bash
cd ChunkingAgent
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

## 📖 Key Features

- **S3 Integration**: Reads files from S3 buckets
- **DynamoDB Storage**: Stores chunked content with metadata
- **Intelligent Chunking**: Preserves original variable-sized chunking logic
- **Cross-Platform**: Deployment scripts for Windows and Linux
- **Production Ready**: Includes monitoring, error handling, and security
- **Comprehensive Testing**: Full test suite and examples

## 🔗 Relationship to Original

This Lambda version maintains the same intelligent chunking algorithms from the original `chunking_agent.py` but adapts them for:
- Serverless execution
- Cloud storage (S3 instead of local files)
- NoSQL database (DynamoDB instead of CSV)
- AWS best practices for security and monitoring

For detailed documentation, see `README_AWS_Lambda.md` or `QUICK_START.md`.
