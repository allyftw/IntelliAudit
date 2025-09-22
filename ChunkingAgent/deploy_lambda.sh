#!/bin/bash

# IntelliAudit Lambda Deployment Script for Linux/macOS
# This script creates a deployment package and deploys the Lambda function with all AWS infrastructure

set -e

# Configuration
FUNCTION_NAME="intelliaudit-chunking-agent"
STACK_NAME="intelliaudit-chunking-stack"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
PYTHON_VERSION="3.11"
DEPLOYMENT_PACKAGE="lambda_deployment_package.zip"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        print_status "Cleaning up temporary directory..."
        rm -rf "$TEMP_DIR"
    fi
    if [ -f "$DEPLOYMENT_PACKAGE" ]; then
        print_status "Cleaning up deployment package..."
        rm -f "$DEPLOYMENT_PACKAGE"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

print_status "Starting IntelliAudit Lambda deployment..."

# Check if required tools are installed
print_step "Checking required tools..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists pip; then
    print_error "pip is required but not installed"
    exit 1
fi

if ! command_exists aws; then
    print_error "AWS CLI is required but not installed"
    print_warning "Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command_exists zip; then
    print_error "zip command is required but not installed"
    exit 1
fi

# Check AWS credentials
print_step "Checking AWS credentials..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    print_error "AWS credentials not configured or invalid"
    print_warning "Please run 'aws configure' to set up your credentials"
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "Using AWS Account: $AWS_ACCOUNT_ID"
print_status "Using AWS Region: $REGION"

# Check if required files exist
print_step "Checking required files..."
if [ ! -f "lambda_chunking_agent.py" ]; then
    print_error "lambda_chunking_agent.py not found"
    exit 1
fi

if [ ! -f "requirements_lambda.txt" ]; then
    print_error "requirements_lambda.txt not found"
    exit 1
fi

if [ ! -f "cloudformation_template.yaml" ]; then
    print_error "cloudformation_template.yaml not found"
    exit 1
fi

# Get parameters from user
read -p "Enter S3 bucket name (must be globally unique): " S3_BUCKET_NAME
if [ -z "$S3_BUCKET_NAME" ]; then
    print_error "S3 bucket name is required"
    exit 1
fi

read -p "Enter DynamoDB table name [chunked-content]: " DYNAMODB_TABLE_NAME
DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME:-chunked-content}

read -p "Enable S3 automatic triggers? [y/N]: " ENABLE_TRIGGERS
if [[ $ENABLE_TRIGGERS =~ ^[Yy]$ ]]; then
    ENABLE_S3_TRIGGERS="true"
else
    ENABLE_S3_TRIGGERS="false"
fi

# Create temporary directory for package
print_step "Creating deployment package..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Copy Lambda function
cp "$OLDPWD/lambda_chunking_agent.py" .

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r "$OLDPWD/requirements_lambda.txt" -t . --quiet

# Download NLTK data
print_status "Downloading NLTK data..."
python3 -c "
import nltk
import os
nltk_data_dir = './nltk_data'
os.makedirs(nltk_data_dir, exist_ok=True)
try:
    nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
    nltk.download('punkt_tab', download_dir=nltk_data_dir, quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'Warning: Could not download NLTK data: {e}')
"

# Remove unnecessary files to reduce package size
print_status "Optimizing package size..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# Create ZIP package
print_status "Creating ZIP package..."
zip -r "$DEPLOYMENT_PACKAGE" . -x "*.git*" "*.DS_Store*" > /dev/null

# Move package back to original directory
mv "$DEPLOYMENT_PACKAGE" "$OLDPWD/"
cd "$OLDPWD"

# Get package size
PACKAGE_SIZE=$(du -h "$DEPLOYMENT_PACKAGE" | cut -f1)
print_status "Deployment package created: $DEPLOYMENT_PACKAGE ($PACKAGE_SIZE)"

# Deploy infrastructure using CloudFormation
print_step "Deploying AWS infrastructure..."
aws cloudformation deploy \
    --template-file cloudformation_template.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        LambdaFunctionName="$FUNCTION_NAME" \
        S3BucketName="$S3_BUCKET_NAME" \
        DynamoDBTableName="$DYNAMODB_TABLE_NAME" \
        EnableS3Triggers="$ENABLE_S3_TRIGGERS" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$REGION"

if [ $? -eq 0 ]; then
    print_status "Infrastructure deployed successfully!"
else
    print_error "Infrastructure deployment failed"
    exit 1
fi

# Update Lambda function code
print_step "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$DEPLOYMENT_PACKAGE" \
    --region "$REGION" > /dev/null

if [ $? -eq 0 ]; then
    print_status "Lambda function code updated successfully!"
else
    print_error "Lambda function code update failed"
    exit 1
fi

# Wait for function to be ready
print_status "Waiting for function to be ready..."
aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION"

# Get stack outputs
print_step "Retrieving deployment information..."
STACK_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json)

# Display success message and useful information
print_status "🚀 Deployment completed successfully!"
echo
echo "=== Deployment Summary ==="
echo "Stack Name: $STACK_NAME"
echo "Function Name: $FUNCTION_NAME"
echo "S3 Bucket: $S3_BUCKET_NAME"
echo "DynamoDB Table: $DYNAMODB_TABLE_NAME"
echo "Region: $REGION"
echo "S3 Triggers Enabled: $ENABLE_S3_TRIGGERS"
echo

echo "=== Next Steps ==="
echo "1. Upload test files to S3:"
echo "   aws s3 cp your-file.pdf s3://$S3_BUCKET_NAME/"
echo
echo "2. Test the Lambda function manually:"
echo "   aws lambda invoke --function-name $FUNCTION_NAME \\"
echo "     --payload '{\"s3_key\": \"your-file.pdf\"}' \\"
echo "     --region $REGION response.json"
echo
echo "3. Query processed chunks from DynamoDB:"
echo "   aws dynamodb scan --table-name $DYNAMODB_TABLE_NAME \\"
echo "     --region $REGION"
echo
echo "4. Monitor function logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow \\"
echo "     --region $REGION"
echo

if [ "$ENABLE_S3_TRIGGERS" == "true" ]; then
    print_status "✅ S3 triggers are enabled - files uploaded to the bucket will be processed automatically"
else
    print_warning "⚠️  S3 triggers are disabled - you'll need to invoke the Lambda function manually"
fi

print_status "Deployment complete! 🎉"
