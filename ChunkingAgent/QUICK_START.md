# IntelliAudit AWS Lambda - Quick Start Guide

This guide will get you up and running with the AWS Lambda version of IntelliAudit in under 10 minutes.

## 📋 Prerequisites Checklist

- [ ] AWS account with appropriate permissions
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Python 3.11+ installed
- [ ] pip package manager

## 🚀 Quick Deployment

### Option 1: Windows (PowerShell)
```powershell
# 1. Open PowerShell as Administrator
# 2. Navigate to project directory
cd C:\path\to\IntelliAudit

# 3. Run deployment script
.\deploy_lambda.ps1

# 4. Follow the prompts:
#    - Enter unique S3 bucket name
#    - Enter DynamoDB table name (or use default)
#    - Choose whether to enable S3 triggers
```

### Option 2: Linux/macOS (Bash)
```bash
# 1. Open terminal
# 2. Navigate to project directory
cd /path/to/IntelliAudit

# 3. Make script executable and run
chmod +x deploy_lambda.sh
./deploy_lambda.sh

# 4. Follow the prompts:
#    - Enter unique S3 bucket name
#    - Enter DynamoDB table name (or use default)
#    - Choose whether to enable S3 triggers
```

## 🧪 Quick Test

After deployment, test your Lambda function:

### Upload and Process a File
```bash
# Replace 'your-bucket-name' with your actual bucket
echo "This is a test document for IntelliAudit chunking." > test.txt
aws s3 cp test.txt s3://your-bucket-name/

# If S3 triggers are enabled, processing starts automatically
# If not, invoke manually:
aws lambda invoke \
  --function-name intelliaudit-chunking-agent \
  --payload '{"s3_key": "test.txt"}' \
  response.json
```

### Check Results
```bash
# Query the chunks from DynamoDB
aws dynamodb scan --table-name chunked-content --max-items 5

# Or use our query tool
python query_dynamodb_example.py --recent-hours 1 --show-content
```

## 📊 What's Created

The deployment creates:

### AWS Resources
- **Lambda Function**: `intelliaudit-chunking-agent`
- **S3 Bucket**: Your specified bucket name
- **DynamoDB Table**: `chunked-content` (or your specified name)
- **IAM Role**: With minimal required permissions
- **CloudWatch Logs**: For monitoring and debugging

### Local Files
- `lambda_chunking_agent.py` - Main Lambda function
- `requirements_lambda.txt` - Python dependencies
- `cloudformation_template.yaml` - Infrastructure template
- `deploy_lambda.sh` / `deploy_lambda.ps1` - Deployment scripts
- `README_AWS_Lambda.md` - Comprehensive documentation
- Test and example scripts

## 🔍 Monitoring

### View Lambda Logs
```bash
# Follow live logs
aws logs tail /aws/lambda/intelliaudit-chunking-agent --follow

# View recent logs
aws logs tail /aws/lambda/intelliaudit-chunking-agent --since 1h
```

### Check Function Status
```bash
# Get function information
aws lambda get-function --function-name intelliaudit-chunking-agent

# List recent invocations
aws logs filter-log-events \
  --log-group-name /aws/lambda/intelliaudit-chunking-agent \
  --start-time $(date -d '1 hour ago' +%s)000
```

## 🛠 Common Use Cases

### 1. Automatic Processing (S3 Triggers Enabled)
```bash
# Just upload files - they'll be processed automatically
aws s3 cp document.pdf s3://your-bucket-name/
aws s3 cp presentation.pptx s3://your-bucket-name/reports/
```

### 2. Manual Processing
```bash
# Process specific file
aws lambda invoke \
  --function-name intelliaudit-chunking-agent \
  --payload '{"s3_key": "documents/report.pdf"}' \
  response.json

# Process multiple files
aws lambda invoke \
  --function-name intelliaudit-chunking-agent \
  --payload '{"s3_keys": ["file1.pdf", "file2.docx"]}' \
  response.json
```

### 3. Query and Analysis
```bash
# Find chunks from specific file
python query_dynamodb_example.py --file-path "report.pdf" --show-content

# Search for specific content
python query_dynamodb_example.py --search "security policy" --show-content

# Get statistics for recent chunks
python query_dynamodb_example.py --recent-hours 24 --stats-only
```

## 📁 Supported File Types

- **Text Files**: .txt, .md
- **PDF Documents**: .pdf
- **Word Documents**: .docx
- **Spreadsheets**: .csv, .xlsx, .xls
- **JSON Files**: .json

## 💡 Tips

1. **Bucket Naming**: Use a globally unique name (e.g., `company-intelliaudit-2024`)
2. **File Organization**: Use prefixes like `documents/`, `reports/` for better organization
3. **Monitoring**: Set up CloudWatch alarms for errors and duration
4. **Cost Control**: Monitor S3 storage and DynamoDB usage regularly

## 🚨 Troubleshooting

### Common Issues

#### "Access Denied" Error
```bash
# Check your AWS credentials
aws sts get-caller-identity

# Verify IAM permissions
aws iam get-user
```

#### "Function Not Found"
```bash
# Check if function exists
aws lambda list-functions --query 'Functions[?FunctionName==`intelliaudit-chunking-agent`]'

# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name intelliaudit-chunking-stack
```

#### "Package Too Large"
- The deployment scripts optimize package size automatically
- If still too large, consider using Lambda Layers for dependencies

### Get Help
1. Check CloudWatch logs for detailed error messages
2. Review the comprehensive documentation in `README_AWS_Lambda.md`
3. Use the test scripts to isolate issues

## 🔄 Updates

To update the Lambda function:
```bash
# Modify lambda_chunking_agent.py as needed
# Run deployment script again
./deploy_lambda.sh  # or deploy_lambda.ps1 on Windows
```

## 📞 Next Steps

1. **Scale Up**: Process larger document sets
2. **Integrate**: Connect with your existing document management systems
3. **Analyze**: Use the chunked data for AI/ML applications
4. **Monitor**: Set up alerts and dashboards
5. **Optimize**: Tune chunk sizes and processing parameters

---

**🎉 Congratulations!** You now have a serverless document chunking system running on AWS. 

For detailed documentation, see `README_AWS_Lambda.md`
