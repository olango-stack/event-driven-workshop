#!/bin/bash
# MIT No Attribution - Copyright 2025 Amazon Web Services, Inc.

# Re:Invent 2025 CNS203 - E-Commerce Backend Deployment Script
# This script automatically installs required tools and deploys the CDK application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
AWS_PROFILE=""
DESTROY_MODE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDK_DIR="$SCRIPT_DIR/cdk-backend"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect OS and package manager
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/redhat-release ]] || [[ -f /etc/centos-release ]] || command -v yum >/dev/null 2>&1; then
        echo "rhel"
    elif [[ -f /etc/debian_version ]] || command -v apt-get >/dev/null 2>&1; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Function to add Homebrew to shell profile
add_brew_to_profile() {
    local brew_path="/opt/homebrew/bin/brew"
    local intel_brew_path="/usr/local/bin/brew"
    
    # Determine which brew path exists
    if [[ -f "$brew_path" ]]; then
        local brew_shellenv_cmd="$brew_path shellenv"
    elif [[ -f "$intel_brew_path" ]]; then
        local brew_shellenv_cmd="$intel_brew_path shellenv"
    else
        print_warning "Homebrew installation not found in expected locations"
        return 1
    fi
    
    # List of possible shell profile files
    local profile_files=(
        "$HOME/.zshrc"
        "$HOME/.bashrc" 
        "$HOME/.bash_profile"
        "$HOME/.profile"
    )
    
    local added_to_profile=false
    
    # Check each profile file and add brew setup if not already present
    for profile_file in "${profile_files[@]}"; do
        # Create the file if it doesn't exist and it's a primary shell config
        if [[ ! -f "$profile_file" ]] && [[ "$profile_file" == "$HOME/.zshrc" || "$profile_file" == "$HOME/.bashrc" ]]; then
            # Only create .zshrc if using zsh, .bashrc if using bash
            if [[ "$profile_file" == "$HOME/.zshrc" && "$SHELL" == *"zsh"* ]]; then
                touch "$profile_file"
            elif [[ "$profile_file" == "$HOME/.bashrc" && "$SHELL" == *"bash"* ]]; then
                touch "$profile_file"
            fi
        fi
        
        # If file exists, check if brew is already configured
        if [[ -f "$profile_file" ]]; then
            if ! grep -q "brew shellenv" "$profile_file" 2>/dev/null; then
                print_status "Adding Homebrew to $profile_file"
                echo "" >> "$profile_file"
                echo "# Added by deploy.sh - Homebrew setup" >> "$profile_file"
                echo "eval \"\$(/opt/homebrew/bin/brew shellenv)\" 2>/dev/null || eval \"\$(/usr/local/bin/brew shellenv)\" 2>/dev/null" >> "$profile_file"
                added_to_profile=true
            fi
        fi
    done
    
    if [[ "$added_to_profile" == true ]]; then
        print_success "Homebrew added to shell profile(s)"
        print_status "Please run 'source ~/.zshrc' or 'source ~/.bashrc' or restart your terminal"
        
        # Try to source the current shell's profile
        if [[ "$SHELL" == *"zsh"* && -f "$HOME/.zshrc" ]]; then
            source "$HOME/.zshrc" 2>/dev/null || true
        elif [[ "$SHELL" == *"bash"* && -f "$HOME/.bashrc" ]]; then
            source "$HOME/.bashrc" 2>/dev/null || true
        elif [[ -f "$HOME/.bash_profile" ]]; then
            source "$HOME/.bash_profile" 2>/dev/null || true
        fi
    fi
}

# Function to install packages based on OS
install_package() {
    local package=$1
    local os_type=$(detect_os)
    
    print_status "Installing $package..."
    
    case $os_type in
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                print_status "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
                add_brew_to_profile
                # Update PATH for current session
                export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
            fi
            brew install "$package" -q
            ;;
        "debian")
            sudo apt-get update -qq
            sudo apt-get install -y "$package"
            ;;
        "rhel")
            sudo yum install -y "$package"
            ;;
        *)
            print_error "Unsupported operating system. Please install $package manually."
            exit 1
            ;;
    esac
}

# Function to install Node.js and npm
install_nodejs() {
    local os_type=$(detect_os)
    
    print_status "Installing Node.js and npm..."
    
    case $os_type in
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                print_status "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
                add_brew_to_profile
                # Update PATH for current session
                export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
            fi
            brew install node -q
            ;;
        "debian")
            sudo apt-get update -qq
            sudo apt-get install -y curl
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        "rhel")
            sudo yum install -y curl
            curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
            sudo yum install -y nodejs npm
            ;;
        *)
            print_error "Unsupported operating system. Please install Node.js manually."
            exit 1
            ;;
    esac
}

# Function to install Python 3
install_python() {
    local os_type=$(detect_os)
    
    print_status "Installing Python 3..."
    
    case $os_type in
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                print_status "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
                add_brew_to_profile
                # Update PATH for current session
                export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
            fi
            brew install python3 -q
            ;;
        "debian")
            sudo apt-get update -qq
            sudo apt-get install -y python3 python3-pip python3-venv
            ;;
        "rhel")
            sudo yum install -y python3 python3-pip
            ;;
        *)
            print_error "Unsupported operating system. Please install Python 3 manually."
            exit 1
            ;;
    esac
}

# Function to check and install AWS CLI
check_install_aws_cli() {
    if ! command -v aws >/dev/null 2>&1; then
        print_status "AWS CLI not found. Installing..."
        local os_type=$(detect_os)
        
        case $os_type in
            "macos")
                curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
                sudo installer -pkg AWSCLIV2.pkg -target /
                rm AWSCLIV2.pkg
                ;;
            "debian"|"rhel")
                curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                if ! command -v unzip >/dev/null 2>&1; then
                    if [[ $os_type == "debian" ]]; then
                        sudo apt-get install -y unzip
                    else
                        sudo yum install -y unzip
                    fi
                fi
                unzip -q awscliv2.zip
                sudo ./aws/install
                rm -rf awscliv2.zip aws/
                ;;
        esac
        print_success "AWS CLI installed successfully"
    else
        print_success "AWS CLI is already installed"
    fi
}

# Function to ensure Homebrew is installed on macOS
ensure_homebrew() {
    # Special handling for AWS CloudShell
    if [[ -n "$AWS_CLOUDSHELL" ]] || [[ "$USER" == "cloudshell-user" ]] || [[ -f "/etc/cloudshell-version" ]]; then
        print_status "AWS CloudShell detected - Homebrew not needed in CloudShell environment"
        return 0
    fi
    
    if [[ "$(detect_os)" == "macos" ]]; then
        if ! command -v brew >/dev/null 2>&1; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
            add_brew_to_profile
            # Update PATH for current session
            export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
            print_success "Homebrew installed successfully"
        else
            print_success "Homebrew is already installed"
        fi
    fi
}







# Function to check and install Node.js
check_install_nodejs() {
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        print_status "Node.js/npm not found. Installing..."
        install_nodejs
        print_success "Node.js and npm installed successfully"
    else
        print_success "Node.js and npm are already installed"
    fi
}

# Function to check and install Python
check_install_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        print_status "Python 3 not found. Installing..."
        install_python
        print_success "Python 3 installed successfully"
    else
        print_success "Python 3 is already installed"
    fi
}

# Function to check and upgrade CDK CLI
check_upgrade_cdk() {
    print_status "Checking AWS CDK CLI version..."
    
    # Check if CDK is installed
    if ! command -v cdk >/dev/null 2>&1; then
        print_status "AWS CDK CLI not found. Installing..."
        install_cdk_cli
        return
    fi
    
    # Get current version
    local current_version=$(cdk --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
    print_status "Current CDK version: $current_version"
    
    # Try to get latest version from npm
    local latest_version=$(npm view aws-cdk version 2>/dev/null || echo "")
    
    if [[ -n "$latest_version" ]]; then
        print_status "Latest CDK version: $latest_version"
        
        # Compare versions (simple string comparison should work for most cases)
        if [[ "$current_version" != "$latest_version" ]]; then
            print_status "Upgrading AWS CDK CLI from $current_version to $latest_version..."
            install_cdk_cli
        else
            print_success "AWS CDK CLI is already up to date ($current_version)"
        fi
    else
        print_warning "Could not check latest CDK version. Attempting upgrade anyway..."
        install_cdk_cli
    fi
}

# Function to install/upgrade CDK CLI with multiple fallback strategies
install_cdk_cli() {
    local install_success=false
    
    # Strategy 1: Try global install without sudo
    if npm install -g aws-cdk@latest >/dev/null 2>&1; then
        print_success "AWS CDK CLI installed/upgraded successfully (global)"
        install_success=true
    # Strategy 2: Try global install with sudo (for some Linux environments)
    elif sudo npm install -g aws-cdk@latest >/dev/null 2>&1; then
        print_success "AWS CDK CLI installed/upgraded successfully (global with sudo)"
        install_success=true
    # Strategy 3: Try local installation as fallback
    elif npm install aws-cdk@latest >/dev/null 2>&1; then
        export PATH="$PWD/node_modules/.bin:$PATH"
        print_success "AWS CDK CLI installed locally (fallback)"
        install_success=true
    # Strategy 4: Check if we're in CloudShell and CDK is already available
    elif [[ -n "$AWS_CLOUDSHELL" ]] || [[ "$USER" == "cloudshell-user" ]] || [[ -f "/etc/cloudshell-version" ]]; then
        if command -v cdk >/dev/null 2>&1; then
            print_warning "CDK upgrade failed in CloudShell environment (permission denied)"
            print_status "Using existing CDK version: $(cdk --version 2>/dev/null | head -1)"
            print_status "This is normal in restricted environments like AWS CloudShell"
            install_success=true
        fi
    fi
    
    if [[ "$install_success" != true ]]; then
        print_error "Failed to install/upgrade AWS CDK CLI with all strategies"
        print_error "Please install CDK manually: npm install -g aws-cdk@latest"
        exit 1
    fi
}

# Function to check and install CDK CLI (legacy - now calls the new function)
check_install_cdk() {
    check_upgrade_cdk
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    cd "$CDK_DIR"
    
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    
    print_status "Installing Python dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    pip install -r requirements-dev.txt -q
    
    # Setup Lambda layer dependencies
    setup_lambda_layer_dependencies
    
    print_success "Python environment setup complete"
}

# Function to setup Lambda layer dependencies
setup_lambda_layer_dependencies() {
    print_status "Setting up Lambda layer dependencies..."
    
    local layer_dir="lambda/layers/third_party"
    local python_dir="$layer_dir/python"
    
    # Create python directory if it doesn't exist
    if [[ ! -d "$python_dir" ]]; then
        mkdir -p "$python_dir"
    fi
    
    # Install layer dependencies
    if [[ -f "$layer_dir/requirements.txt" ]]; then
        print_status "Installing layer dependencies..."
        pip install -r "$layer_dir/requirements.txt" -t "$python_dir/" -q
        print_success "Layer dependencies installed"
    else
        print_warning "No requirements.txt found for Lambda layer"
    fi
}

# Function to cleanup Lambda layer dependencies
cleanup_lambda_layer_dependencies() {
    print_status "Cleaning up Lambda layer dependencies..."
    
    local layer_dir="$CDK_DIR/lambda/layers/third_party/python"
    
    if [[ -d "$layer_dir" ]]; then
        rm -rf "$layer_dir"
        print_success "Lambda layer dependencies cleaned up"
    fi
}

# Function to get current AWS region
get_aws_region() {
    local aws_cmd="aws"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    local region=$($aws_cmd configure get region 2>/dev/null)
    
    # If no region configured, try to get from environment or default
    if [[ -z "$region" ]]; then
        region="${AWS_DEFAULT_REGION:-us-east-1}"
    fi
    
    echo "$region"
}

# Function to check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    local aws_cmd="aws"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    if ! $aws_cmd sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid"
        print_error "Please run 'aws configure' or set up your AWS credentials"
        exit 1
    fi
    
    local region=$(get_aws_region)
    local account_id=$($aws_cmd sts get-caller-identity --region "$region" --query Account --output text)
    
    print_success "AWS credentials valid - Account: $account_id, Region: $region"
}

# Function to bootstrap CDK
bootstrap_cdk() {
    print_status "Checking CDK bootstrap status..."
    
    cd "$CDK_DIR"
    source .venv/bin/activate
    
    local region=$(get_aws_region)
    local aws_cmd="aws"
    local cdk_cmd="cdk"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
        cdk_cmd="cdk --profile $AWS_PROFILE"
    fi
    
    # Get account ID
    local account_id=$($aws_cmd sts get-caller-identity --query Account --output text --region "$region")
    
    # Check if CDK is bootstrapped by looking for the SSM parameter
    local bootstrap_version=$($aws_cmd ssm get-parameter \
        --name "/cdk-bootstrap/hnb659fds/version" \
        --region "$region" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [[ "$bootstrap_version" == "NOT_FOUND" ]]; then
        print_status "CDK bootstrap required. Bootstrapping CDK in region: $region for account: $account_id"
        
        # Bootstrap CDK
        if $cdk_cmd bootstrap "aws://$account_id/$region"; then
            print_success "CDK bootstrap completed successfully"
        else
            print_error "CDK bootstrap failed"
            print_error "Please ensure you have the necessary IAM permissions for CDK bootstrapping"
            print_error "Required permissions include: CloudFormation, S3, IAM, SSM"
            exit 1
        fi
    else
        print_success "CDK is already bootstrapped (version: $bootstrap_version)"
    fi
}

# Function to empty and delete S3 buckets
cleanup_s3_buckets() {
    print_status "Cleaning up S3 buckets..."
    
    local aws_cmd="aws"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    local region=$(get_aws_region)
    
    # Get stack name
    local stack_name="CNS203CdkBackendStack"
    
    # Get S3 buckets from the stack
    local buckets=$($aws_cmd cloudformation describe-stack-resources \
        --stack-name "$stack_name" \
        --region "$region" \
        --query "StackResources[?ResourceType==\`AWS::S3::Bucket\`].PhysicalResourceId" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$buckets" ]]; then
        for bucket in $buckets; do
            if [[ "$bucket" != "None" ]] && [[ -n "$bucket" ]]; then
                print_status "Emptying S3 bucket: $bucket"
                
                # Check if bucket exists
                if $aws_cmd s3api head-bucket --bucket "$bucket" --region "$region" 2>/dev/null; then
                    # Remove all objects
                    $aws_cmd s3 rm s3://$bucket --recursive --region "$region" 2>/dev/null || true
                    
                    # Delete all versions and delete markers
                    $aws_cmd s3api list-object-versions --bucket $bucket --region "$region" --query 'Versions[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | while read key version; do
                        if [[ -n "$key" ]] && [[ -n "$version" ]] && [[ "$key" != "None" ]] && [[ "$version" != "None" ]]; then
                            $aws_cmd s3api delete-object --bucket $bucket --key "$key" --version-id "$version" --region "$region" 2>/dev/null || true
                        fi
                    done
                    
                    $aws_cmd s3api list-object-versions --bucket $bucket --region "$region" --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | while read key version; do
                        if [[ -n "$key" ]] && [[ -n "$version" ]] && [[ "$key" != "None" ]] && [[ "$version" != "None" ]]; then
                            $aws_cmd s3api delete-object --bucket $bucket --key "$key" --version-id "$version" --region "$region" 2>/dev/null || true
                        fi
                    done
                    
                    print_success "S3 bucket $bucket emptied"
                else
                    print_warning "S3 bucket $bucket does not exist or is not accessible"
                fi
            fi
        done
    else
        print_status "No S3 buckets found in stack or stack does not exist"
    fi
}

# Function to build and deploy React frontend
build_deploy_frontend() {
    print_status "Building and deploying React frontend..."
    
    local frontend_dir="$SCRIPT_DIR/react-frontend"
    
    # Check if React app exists
    if [[ ! -f "$frontend_dir/package.json" ]]; then
        print_error "React frontend not found at $frontend_dir"
        return 1
    fi
    
    cd "$frontend_dir"
    
    # Install dependencies if node_modules doesn't exist or if package-lock.json is newer
    if [[ ! -d "node_modules" ]] || [[ "package-lock.json" -nt "node_modules" ]]; then
        print_status "Installing React dependencies..."
        
        # Clear npm cache to avoid potential issues
        npm cache clean --force 2>/dev/null || true
        
        # Install with specific flags for CloudShell compatibility
        if npm install --no-audit --no-fund --legacy-peer-deps; then
            print_success "React dependencies installed successfully"
        else
            print_error "Failed to install React dependencies"
            print_status "Attempting to install with alternative method..."
            
            # Try alternative installation method
            if npm ci --no-audit --no-fund --legacy-peer-deps 2>/dev/null || npm install --no-audit --no-fund --force; then
                print_success "React dependencies installed with alternative method"
            else
                print_error "All npm install methods failed"
                print_error "This may be due to network issues or package conflicts in CloudShell"
                print_status "Attempting to continue with existing node_modules if available..."
                
                if [[ ! -d "node_modules" ]]; then
                    print_error "No node_modules directory found. Cannot proceed with frontend build."
                    return 1
                fi
            fi
        fi
    fi
    
    # Get API URL from CloudFormation stack
    local aws_cmd="aws"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    local region=$(get_aws_region)
    
    local api_url=$($aws_cmd cloudformation describe-stacks \
        --stack-name CNS203CdkBackendStack \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`CNS203ApiUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]] && [[ "$api_url" != "None" ]]; then
        print_status "Setting API URL: $api_url"
        export REACT_APP_API_URL="$api_url"
        
        # Create .env file for the build
        echo "REACT_APP_API_URL=$api_url" > .env
    else
        print_warning "Could not retrieve API URL from stack. Frontend will use placeholder URL."
    fi
    
    # Build the React app
    print_status "Building React application..."
    
    # Set NODE_OPTIONS to handle potential memory issues in CloudShell
    export NODE_OPTIONS="--max-old-space-size=4096"
    
    if npm run build; then
        print_success "React build completed successfully"
    else
        print_error "React build failed"
        print_status "Checking if build directory exists from previous successful build..."
        
        if [[ -d "build" ]]; then
            print_warning "Using existing build directory from previous build"
        else
            print_error "No build directory found. Cannot deploy frontend."
            return 1
        fi
    fi
    
    if [[ ! -d "build" ]]; then
        print_error "React build failed - build directory not found"
        return 1
    fi
    
    # Get S3 bucket name from CloudFormation stack
    local bucket_name=$($aws_cmd cloudformation describe-stacks \
        --stack-name CNS203CdkBackendStack \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`CNS203FrontendBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$bucket_name" ]] || [[ "$bucket_name" == "None" ]]; then
        print_error "Could not retrieve S3 bucket name from stack"
        return 1
    fi
    
    print_status "Syncing to S3 bucket: $bucket_name"
    
    # Sync build files to S3 with delete option
    if $aws_cmd s3 sync build/ s3://$bucket_name/ --delete --region "$region"; then
        print_success "Files synced to S3 successfully"
    else
        print_error "Failed to sync files to S3"
        return 1
    fi
    
    # Set proper content types for common file types
    $aws_cmd s3 cp s3://$bucket_name/ s3://$bucket_name/ --recursive \
        --exclude "*" --include "*.html" --content-type "text/html" \
        --metadata-directive REPLACE --region "$region" 2>/dev/null || true
    
    $aws_cmd s3 cp s3://$bucket_name/ s3://$bucket_name/ --recursive \
        --exclude "*" --include "*.css" --content-type "text/css" \
        --metadata-directive REPLACE --region "$region" 2>/dev/null || true
    
    $aws_cmd s3 cp s3://$bucket_name/ s3://$bucket_name/ --recursive \
        --exclude "*" --include "*.js" --content-type "application/javascript" \
        --metadata-directive REPLACE --region "$region" 2>/dev/null || true
    
    # Get CloudFront distribution ID and invalidate cache
    local distribution_id=$($aws_cmd cloudformation describe-stacks \
        --stack-name CNS203CdkBackendStack \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`CNS203CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$distribution_id" ]] && [[ "$distribution_id" != "None" ]]; then
        print_status "Invalidating CloudFront cache: $distribution_id"
        local invalidation_id=$($aws_cmd cloudfront create-invalidation \
            --distribution-id "$distribution_id" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text)
        print_status "CloudFront invalidation created: $invalidation_id"
    fi
    
    # Get frontend URL
    local frontend_url=$($aws_cmd cloudformation describe-stacks \
        --stack-name CNS203CdkBackendStack \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`CNS203FrontendUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$frontend_url" ]] && [[ "$frontend_url" != "None" ]]; then
        print_success "Frontend deployed successfully!"
        print_success "Frontend URL: $frontend_url"
    fi
    
    # Clean up .env file and reset NODE_OPTIONS
    rm -f .env
    unset NODE_OPTIONS
    
    cd "$SCRIPT_DIR"
}

# Function to build React frontend only (CDK will handle deployment)
build_react_frontend() {
    print_status "Building React frontend..."
    
    local frontend_dir="$SCRIPT_DIR/react-frontend"
    
    # Check if React app exists
    if [[ ! -f "$frontend_dir/package.json" ]]; then
        print_error "React frontend not found at $frontend_dir"
        return 1
    fi
    
    cd "$frontend_dir"
    
    # Install dependencies if node_modules doesn't exist or if package-lock.json is newer
    if [[ ! -d "node_modules" ]] || [[ "package-lock.json" -nt "node_modules" ]]; then
        print_status "Installing React dependencies..."
        
        # Clear npm cache to avoid potential issues
        npm cache clean --force 2>/dev/null || true
        
        # Install with specific flags for CloudShell compatibility
        if npm install --no-audit --no-fund --legacy-peer-deps; then
            print_success "React dependencies installed successfully"
        else
            print_error "Failed to install React dependencies"
            print_status "Attempting to install with alternative method..."
            
            # Try alternative installation method
            if npm ci --no-audit --no-fund --legacy-peer-deps 2>/dev/null || npm install --no-audit --no-fund --force; then
                print_success "React dependencies installed with alternative method"
            else
                print_error "All npm install methods failed"
                print_error "This may be due to network issues or package conflicts in CloudShell"
                print_status "Attempting to continue with existing node_modules if available..."
                
                if [[ ! -d "node_modules" ]]; then
                    print_error "No node_modules directory found. Cannot proceed with frontend build."
                    return 1
                fi
            fi
        fi
    fi
    
    # Build the React app
    print_status "Building React application..."
    
    # Set NODE_OPTIONS to handle potential memory issues in CloudShell
    export NODE_OPTIONS="--max-old-space-size=4096"
    
    if npm run build; then
        print_success "React build completed successfully"
    else
        print_error "React build failed"
        print_status "Checking if build directory exists from previous successful build..."
        
        if [[ -d "build" ]]; then
            print_warning "Using existing build directory from previous build"
        else
            print_error "No build directory found. Cannot deploy frontend."
            return 1
        fi
    fi
    
    if [[ ! -d "build" ]]; then
        print_error "React build failed - build directory not found"
        return 1
    fi
    
    print_success "React frontend build completed!"
    
    # Clean up and reset NODE_OPTIONS
    unset NODE_OPTIONS
    
    cd "$SCRIPT_DIR"
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying CDK stack..."
    
    cd "$CDK_DIR"
    source .venv/bin/activate
    
    local region=$(get_aws_region)
    local cdk_cmd="cdk deploy"
    if [[ -n "$AWS_PROFILE" ]]; then
        cdk_cmd="cdk deploy --profile $AWS_PROFILE"
    fi
    
    print_status "Deploying CDK stack to region: $region"
    
    # Deploy with automatic approval
    $cdk_cmd --require-approval never
    
    print_success "Stack deployed successfully!"
    
    # Get API Gateway URL
    local aws_cmd="aws"
    if [[ -n "$AWS_PROFILE" ]]; then
        aws_cmd="aws --profile $AWS_PROFILE"
    fi
    
    local region=$(get_aws_region)
    
    local api_url=$($aws_cmd cloudformation describe-stacks \
        --stack-name CNS203CdkBackendStack \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`CNS203ApiUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]] && [[ "$api_url" != "None" ]]; then
        print_success "API Gateway URL: $api_url"
    fi
    
    # Cleanup Lambda layer dependencies after successful deployment
    cleanup_lambda_layer_dependencies
}

# Function to destroy the stack
destroy_stack() {
    print_status "Destroying CDK stack..."
    
    # First cleanup S3 buckets
    cleanup_s3_buckets
    
    cd "$CDK_DIR"
    source .venv/bin/activate
    
    local region=$(get_aws_region)
    local cdk_cmd="cdk destroy"
    if [[ -n "$AWS_PROFILE" ]]; then
        cdk_cmd="cdk destroy --profile $AWS_PROFILE"
    fi
    
    print_status "Destroying CDK stack in region: $region"
    
    # Destroy with automatic approval
    $cdk_cmd --force
    
    print_success "Stack destroyed successfully!"
    
    # Cleanup Lambda layer dependencies after destroy
    cleanup_lambda_layer_dependencies
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --profile PROFILE    Use specific AWS profile"
    echo "  --delete, --destroy  Delete/destroy the stack and all resources"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Deploy with default AWS profile"
    echo "  $0 --profile dev            # Deploy with 'dev' AWS profile"
    echo "  $0 --destroy                # Destroy the stack"
    echo "  $0 --destroy --profile dev  # Destroy stack using 'dev' profile"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --delete|--destroy)
            DESTROY_MODE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting Re:Invent 2025 CNS203 E-Commerce Backend Deployment"
    print_status "========================================================="
    
    if [[ "$DESTROY_MODE" == true ]]; then
        print_warning "DESTROY MODE: This will delete all resources!"
        sleep 3
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "$CDK_DIR/app.py" ]]; then
        print_error "CDK application not found. Please run this script from the project root."
        exit 1
    fi
    
    # Install required tools
    print_status "Checking and installing required tools..."
    check_install_python
    check_install_nodejs
    
    # CDK version check and upgrade (early and prominent)
    print_status "=== AWS CDK CLI Version Check ==="
    check_upgrade_cdk
    print_status "=== CDK Check Complete ==="
    
    check_install_aws_cli
    ensure_homebrew
    
    # Setup Python environment
    setup_python_env
    
    # Check AWS credentials
    check_aws_credentials
    
    if [[ "$DESTROY_MODE" == true ]]; then
        destroy_stack
    else
        # Build React frontend first (CDK deployment will handle S3 sync)
        build_react_frontend
        
        # Bootstrap CDK if needed
        bootstrap_cdk
        
        # Deploy the stack
        deploy_stack
    fi
    
    print_success "Operation completed successfully!"
}

# Run main function
main "$@"
