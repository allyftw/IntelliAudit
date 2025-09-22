# IntelliAudit AWS Lambda File Chunking Agent

This project refactors the original `chunking_agent.py` to run as an AWS Lambda function that reads files from S3 and outputs chunked data to DynamoDB. The solution provides intelligent document chunking with variable-sized chunks based on content characteristics.

## 🚀 Features

- **AWS Lambda Integration**: Serverless execution with automatic scaling
- **S3 File Processing**: Reads multiple file formats from S3 buckets
- **DynamoDB Storage**: Stores chunked content with metadata
- **Intelligent Chunking**: Variable-sized chunks based on content analysis
- **Multi-Format Support**: PDF, DOCX, CSV, XLSX, TXT, and more
- **Automatic Triggers**: Optional S3 event-driven processing
- **Cross-Platform Deployment**: Scripts for both Windows and Linux

## 📋 Prerequisites

### Required Software
- **Python 3.11** or later
- **AWS CLI** (configured with valid credentials)
- **pip** (Python package installer)

### AWS Account Requirements
- AWS account with appropriate permissions
- AWS CLI configured with credentials that have:
  - Lambda function creation/update permissions
  - S3 bucket access permissions
  - DynamoDB table creation/write permissions
  - CloudFormation stack deployment permissions
  - IAM role creation permissions

### AWS CLI Configuration
```bash
# Configure AWS CLI (if not already done)
aws configure
```

## 📁 Project Structure

```
IntelliAudit/
├── lambda_chunking_agent.py       # Main Lambda function code
├── requirements_lambda.txt        # Python dependencies for Lambda
├── cloudformation_template.yaml   # AWS infrastructure template
├── deploy_lambda.sh              # Linux/macOS deployment script
├── deploy_lambda.ps1             # Windows PowerShell deployment script
├── README_AWS_Lambda.md          # This documentation
├── test_lambda.py                # Test scripts
└── examples/                     # Example files and scripts
    ├── test_files/               # Sample files for testing
    ├── invoke_lambda.py          # Manual Lambda invocation
    └── query_dynamodb.py         # Query processed results
```

## 🛠 Quick Start

### Option 1: Automated Deployment (Recommended)

#### On Linux/macOS:
```bash
# Make script executable (Linux/macOS only)
chmod +x deploy_lambda.sh

# Run deployment script
./deploy_lambda.sh
```

#### On Windows:
```powershell
# Run PowerShell as Administrator (recommended)
# Navigate to project directory
cd C:\path\to\IntelliAudit

# Run deployment script
.\deploy_lambda.ps1
```

### Option 2: Manual Deployment

#### Step 1: Deploy Infrastructure
```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file cloudformation_template.yaml \
  --stack-name intelliaudit-chunking-stack \
  --parameter-overrides \
    S3BucketName=your-unique-bucket-name \
    DynamoDBTableName=chunked-content \
    EnableS3Triggers=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 2: Create Deployment Package
```bash
# Create temporary directory
mkdir lambda_package
cd lambda_package

# Copy Lambda function
cp ../lambda_chunking_agent.py .

# Install dependencies
pip install -r ../requirements_lambda.txt -t .

# Download NLTK data
python -c "
import nltk
import os
nltk_data_dir = './nltk_data'
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.download('punkt', download_dir=nltk_data_dir)
nltk.download('punkt_tab', download_dir=nltk_data_dir)
"

# Create ZIP package
zip -r ../lambda_deployment_package.zip . -x "*.pyc" "*__pycache__*"
cd ..
```

#### Step 3: Update Lambda Function
```bash
# Update function code
aws lambda update-function-code \
  --function-name intelliaudit-chunking-agent \
  --zip-file fileb://lambda_deployment_package.zip \
  --region us-east-1
```

## 📖 Usage

### Automatic Processing (S3 Triggers Enabled)

When S3 triggers are enabled, files uploaded to the S3 bucket will be processed automatically:

```bash
# Upload a file to trigger processing
aws s3 cp document.pdf s3://your-bucket-name/
```

### Manual Processing

#### Single File Processing
```bash
# Invoke Lambda function directly
aws lambda invoke \
  --function-name intelliaudit-chunking-agent \
  --payload '{"s3_key": "document.pdf", "bucket_name": "your-bucket-name"}' \
  response.json
```

#### Multiple Files Processing
```bash
# Process multiple files
aws lambda invoke \
  --function-name intelliaudit-chunking-agent \
  --payload '{"s3_keys": ["file1.pdf", "file2.txt"], "bucket_name": "your-bucket-name"}' \
  response.json
```

### Query Results from DynamoDB

```bash
# Get all chunks for a specific execution
aws dynamodb query \
  --table-name chunked-content \
  --index-name execution-id-index \
  --key-condition-expression "execution_id = :exec_id" \
  --expression-attribute-values '{":exec_id": {"S": "your-execution-id"}}'

# Get all chunks from a specific file
aws dynamodb query \
  --table-name chunked-content \
  --index-name file-path-index \
  --key-condition-expression "file_path = :file_path" \
  --expression-attribute-values '{":file_path": {"S": "document.pdf"}}'

# Scan all items (use carefully with large datasets)
aws dynamodb scan --table-name chunked-content
```

## 🔧 Configuration

### Environment Variables

The Lambda function uses these environment variables (automatically set by CloudFormation):

- `S3_BUCKET_NAME`: Source S3 bucket name
- `DYNAMODB_TABLE_NAME`: Target DynamoDB table name

### Lambda Function Settings

- **Runtime**: Python 3.11
- **Memory**: 1024 MB (1 GB)
- **Timeout**: 900 seconds (15 minutes)
- **Concurrent Executions**: Limited to 10 (configurable)

### DynamoDB Schema

The DynamoDB table stores chunks with the following structure:

```json
{
  "id": "execution-id_chunk-number",
  "execution_id": "uuid",
  "file_path": "path/to/file.pdf",
  "file_name": "file.pdf",
  "total_chunks": 25,
  "chunk_number": 1,
  "chunk_content": "The actual text content...",
  "chunk_size": 450,
  "created_at": "2024-01-01T12:00:00.000Z",
  "source_bucket": "my-bucket",
  "content_type": "narrative_document"
}
```

## 🔍 Monitoring and Logging

### CloudWatch Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/intelliaudit-chunking-agent --follow

# View logs with filter
aws logs filter-log-events \
  --log-group-name /aws/lambda/intelliaudit-chunking-agent \
  --filter-pattern "ERROR"
```

### CloudWatch Alarms

The CloudFormation template creates alarms for:
- Lambda function errors (threshold: 5 errors in 10 minutes)
- Lambda function duration (threshold: 10 minutes average)

### Dead Letter Queue

Failed Lambda executions are sent to an SQS Dead Letter Queue for analysis:

```bash
# Check dead letter queue messages
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/account/intelliaudit-chunking-agent-dlq
```

## 🧪 Testing

### Test Files

Upload test files to your S3 bucket:

```bash
# Upload sample files
aws s3 cp test_document.pdf s3://your-bucket-name/
aws s3 cp test_document.docx s3://your-bucket-name/
aws s3 cp test_data.csv s3://your-bucket-name/
```

### Manual Testing Script

Use the provided test script:

```python
# test_lambda.py
import boto3
import json

def test_lambda_function():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test payload
    payload = {
        "s3_key": "test_document.pdf",
        "bucket_name": "your-bucket-name"
    }
    
    # Invoke function
    response = lambda_client.invoke(
        FunctionName='intelliaudit-chunking-agent',
        Payload=json.dumps(payload)
    )
    
    # Print results
    result = json.loads(response['Payload'].read())
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_lambda_function()
```

## 🛡 Security Best Practices

### IAM Permissions

The Lambda function uses least-privilege IAM permissions:
- S3: Read-only access to specified bucket
- DynamoDB: Write access to specified table only
- CloudWatch: Log writing permissions

### Network Security

- Lambda function runs in AWS managed VPC by default
- S3 bucket has public access blocked
- DynamoDB table uses AWS managed encryption

### Data Protection

- All data is encrypted in transit and at rest
- S3 bucket versioning is enabled
- DynamoDB point-in-time recovery is enabled

## 🚨 Troubleshooting

### Common Issues

#### 1. Lambda Function Timeout
```
Error: Task timed out after 900.00 seconds
```
**Solution**: Increase memory allocation or split large files into smaller chunks.

#### 2. Package Size Too Large
```
Error: Unzipped size must be smaller than 262144000 bytes
```
**Solution**: Use Lambda Layers for large dependencies or optimize package size.

#### 3. NLTK Data Not Found
```
Error: [nltk_data] Error loading punkt
```
**Solution**: Ensure NLTK data is downloaded to `/tmp` directory in Lambda.

#### 4. S3 Access Denied
```
Error: An error occurred (AccessDenied) when calling the GetObject operation
```
**Solution**: Check IAM permissions and bucket policy.

#### 5. DynamoDB Write Errors
```
Error: ValidationException: One or more parameter values were invalid
```
**Solution**: Check data types (use Decimal for numbers in DynamoDB).

### Debug Commands

```bash
# Check Lambda function configuration
aws lambda get-function --function-name intelliaudit-chunking-agent

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name intelliaudit-chunking-stack

# Check S3 bucket notification configuration
aws s3api get-bucket-notification-configuration --bucket your-bucket-name

# Check DynamoDB table status
aws dynamodb describe-table --table-name chunked-content
```

## 📊 Performance Optimization

### Lambda Optimization
- Use provisioned concurrency for consistent performance
- Optimize package size by removing unnecessary dependencies
- Use Lambda Layers for shared dependencies

### S3 Optimization
- Use S3 Transfer Acceleration for faster uploads
- Enable S3 Intelligent Tiering for cost optimization
- Use appropriate S3 storage classes based on access patterns

### DynamoDB Optimization
- Use composite keys for efficient querying
- Consider DynamoDB Accelerator (DAX) for read-heavy workloads
- Monitor and adjust read/write capacity based on usage

## 💰 Cost Estimation

### Lambda Costs
- Request charges: $0.20 per 1M requests
- Duration charges: $0.0000166667 per GB-second
- Free tier: 1M requests and 400,000 GB-seconds per month

### S3 Costs
- Storage: ~$0.023 per GB per month (Standard)
- Requests: ~$0.0004 per 1,000 PUT requests

### DynamoDB Costs
- On-demand pricing: $1.25 per million write requests
- Storage: $0.25 per GB per month

**Example**: Processing 1,000 documents (1MB each) monthly:
- Lambda: ~$2-5
- S3: ~$1-2
- DynamoDB: ~$3-6
- **Total**: ~$6-13 per month

## 📝 License

This project is part of the IntelliAudit system. Please refer to the main project license.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for error details
3. Check AWS service limits and quotas
4. Create an issue in the project repository

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
- Monitor CloudWatch metrics and alarms
- Review and rotate AWS credentials regularly
- Update Lambda runtime and dependencies
- Clean up old DynamoDB data if needed
- Review and optimize costs monthly

### Version Updates
To update the Lambda function:
1. Modify `lambda_chunking_agent.py`
2. Update `requirements_lambda.txt` if needed
3. Run deployment script again
4. Test with sample files

---

**Note**: This documentation assumes basic familiarity with AWS services. For detailed AWS service documentation, refer to the official AWS documentation.
