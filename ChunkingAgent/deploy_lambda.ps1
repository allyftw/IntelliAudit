# IntelliAudit Lambda Deployment Script for Windows PowerShell
# This script creates a deployment package and deploys the Lambda function with all AWS infrastructure

param(
    [string]$FunctionName = "intelliaudit-chunking-agent",
    [string]$StackName = "intelliaudit-chunking-stack",
    [string]$Region = $env:AWS_DEFAULT_REGION,
    [string]$PythonVersion = "3.11",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Configuration
if ([string]::IsNullOrEmpty($Region)) {
    $Region = "us-east-1"
}
$DeploymentPackage = "lambda_deployment_package.zip"

# Help text
if ($Help) {
    Write-Host @"
IntelliAudit Lambda Deployment Script

USAGE:
    .\deploy_lambda.ps1 [OPTIONS]

OPTIONS:
    -FunctionName <name>    Lambda function name (default: intelliaudit-chunking-agent)
    -StackName <name>       CloudFormation stack name (default: intelliaudit-chunking-stack)
    -Region <region>        AWS region (default: us-east-1 or AWS_DEFAULT_REGION)
    -PythonVersion <ver>    Python version (default: 3.11)
    -Help                   Show this help message

EXAMPLES:
    .\deploy_lambda.ps1
    .\deploy_lambda.ps1 -Region us-west-2 -FunctionName my-chunking-agent

PREREQUISITES:
    - Python 3.11 or later
    - AWS CLI configured with valid credentials
    - Required files: lambda_chunking_agent.py, requirements_lambda.txt, cloudformation_template.yaml
"@
    exit 0
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Status {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" -Color Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" -Color Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" -Color Red
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "[STEP] $Message" -Color Cyan
}

function Test-CommandExists {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Cleanup {
    if ($TempDir -and (Test-Path $TempDir)) {
        Write-Status "Cleaning up temporary directory..."
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $DeploymentPackage) {
        Write-Status "Cleaning up deployment package..."
        Remove-Item $DeploymentPackage -Force -ErrorAction SilentlyContinue
    }
}

# Set up cleanup on exit
try {
    Write-Status "Starting IntelliAudit Lambda deployment..."

    # Check if required tools are installed
    Write-Step "Checking required tools..."

    if (-not (Test-CommandExists "python")) {
        Write-Error "Python is required but not found in PATH"
        Write-Warning "Please install Python 3.11 or later from https://python.org"
        exit 1
    }

    if (-not (Test-CommandExists "pip")) {
        Write-Error "pip is required but not found in PATH"
        Write-Warning "Please ensure pip is installed with Python"
        exit 1
    }

    if (-not (Test-CommandExists "aws")) {
        Write-Error "AWS CLI is required but not found in PATH"
        Write-Warning "Please install AWS CLI from https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    }

    # Check AWS credentials
    Write-Step "Checking AWS credentials..."
    try {
        $null = aws sts get-caller-identity
    }
    catch {
        Write-Error "AWS credentials not configured or invalid"
        Write-Warning "Please run 'aws configure' to set up your credentials"
        exit 1
    }

    # Get AWS account info
    $AwsAccountId = aws sts get-caller-identity --query Account --output text
    Write-Status "Using AWS Account: $AwsAccountId"
    Write-Status "Using AWS Region: $Region"

    # Check if required files exist
    Write-Step "Checking required files..."
    $RequiredFiles = @("lambda_chunking_agent.py", "requirements_lambda.txt", "cloudformation_template.yaml")
    
    foreach ($File in $RequiredFiles) {
        if (-not (Test-Path $File)) {
            Write-Error "$File not found in current directory"
            exit 1
        }
    }

    # Get parameters from user
    do {
        $S3BucketName = Read-Host "Enter S3 bucket name (must be globally unique)"
    } while ([string]::IsNullOrWhiteSpace($S3BucketName))

    $DynamoDBTableName = Read-Host "Enter DynamoDB table name [chunked-content]"
    if ([string]::IsNullOrWhiteSpace($DynamoDBTableName)) {
        $DynamoDBTableName = "chunked-content"
    }

    $EnableTriggersInput = Read-Host "Enable S3 automatic triggers? [y/N]"
    $EnableS3Triggers = if ($EnableTriggersInput -match '^[Yy]') { "true" } else { "false" }

    # Create temporary directory for package
    Write-Step "Creating deployment package..."
    $TempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_ -Force; New-Item -ItemType Directory -Path $_ }
    $OriginalLocation = Get-Location
    Set-Location $TempDir

    # Copy Lambda function
    Copy-Item "$OriginalLocation\lambda_chunking_agent.py" .

    # Install dependencies
    Write-Status "Installing Python dependencies..."
    $pipOutput = pip install -r "$OriginalLocation\requirements_lambda.txt" -t . --quiet 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Some pip dependencies may have failed to install"
    }

    # Download NLTK data
    Write-Status "Downloading NLTK data..."
    python -c @"
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
"@

    # Remove unnecessary files to reduce package size
    Write-Status "Optimizing package size..."
    Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Name "*.dist-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Directory -Name "tests" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # Create ZIP package
    Write-Status "Creating ZIP package..."
    $zipPath = Join-Path $OriginalLocation $DeploymentPackage

    # Remove existing zip if it exists
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    # Create ZIP using .NET
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $zipPath)

    # Return to original directory
    Set-Location $OriginalLocation

    # Get package size
    $PackageSize = [math]::Round((Get-Item $DeploymentPackage).Length / 1MB, 2)
    Write-Status "Deployment package created: $DeploymentPackage ($PackageSize MB)"

    # Deploy infrastructure using CloudFormation
    Write-Step "Deploying AWS infrastructure..."
    $deployArgs = @(
        "cloudformation", "deploy",
        "--template-file", "cloudformation_template.yaml",
        "--stack-name", $StackName,
        "--parameter-overrides",
        "LambdaFunctionName=$FunctionName",
        "S3BucketName=$S3BucketName",
        "DynamoDBTableName=$DynamoDBTableName",
        "EnableS3Triggers=$EnableS3Triggers",
        "--capabilities", "CAPABILITY_IAM", "CAPABILITY_NAMED_IAM",
        "--region", $Region
    )

    & aws @deployArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Infrastructure deployment failed"
        exit 1
    }

    Write-Status "Infrastructure deployed successfully!"

    # Update Lambda function code
    Write-Step "Updating Lambda function code..."
    aws lambda update-function-code --function-name $FunctionName --zip-file "fileb://$DeploymentPackage" --region $Region | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Lambda function code update failed"
        exit 1
    }

    Write-Status "Lambda function code updated successfully!"

    # Wait for function to be ready
    Write-Status "Waiting for function to be ready..."
    aws lambda wait function-updated --function-name $FunctionName --region $Region

    # Get stack outputs
    Write-Step "Retrieving deployment information..."
    $StackOutputsJson = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query 'Stacks[0].Outputs' --output json
    
    # Display success message and useful information
    Write-Status "🚀 Deployment completed successfully!"
    Write-Host ""
    Write-Host "=== Deployment Summary ===" -ForegroundColor Cyan
    Write-Host "Stack Name: $StackName"
    Write-Host "Function Name: $FunctionName"
    Write-Host "S3 Bucket: $S3BucketName"
    Write-Host "DynamoDB Table: $DynamoDBTableName"
    Write-Host "Region: $Region"
    Write-Host "S3 Triggers Enabled: $EnableS3Triggers"
    Write-Host ""

    Write-Host "=== Next Steps ===" -ForegroundColor Cyan
    Write-Host "1. Upload test files to S3:"
    Write-Host "   aws s3 cp your-file.pdf s3://$S3BucketName/"
    Write-Host ""
    Write-Host "2. Test the Lambda function manually:"
    Write-Host "   aws lambda invoke --function-name $FunctionName \"
    Write-Host "     --payload '{`"s3_key`": `"your-file.pdf`"}' \"
    Write-Host "     --region $Region response.json"
    Write-Host ""
    Write-Host "3. Query processed chunks from DynamoDB:"
    Write-Host "   aws dynamodb scan --table-name $DynamoDBTableName \"
    Write-Host "     --region $Region"
    Write-Host ""
    Write-Host "4. Monitor function logs:"
    Write-Host "   aws logs tail /aws/lambda/$FunctionName --follow \"
    Write-Host "     --region $Region"
    Write-Host ""

    if ($EnableS3Triggers -eq "true") {
        Write-Status "✅ S3 triggers are enabled - files uploaded to the bucket will be processed automatically"
    } else {
        Write-Warning "⚠️ S3 triggers are disabled - you'll need to invoke the Lambda function manually"
    }

    Write-Status "Deployment complete! 🎉"

} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
} finally {
    Cleanup
}
