#!/bin/bash

# Zultra Telegram Bot - Automated Setup Script
# This script automates the local development setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.11+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists, skipping creation"
    else
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Create .env file
create_env_file() {
    print_status "Setting up environment configuration..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Skipping .env creation"
            return
        fi
    fi
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from template"
        
        # Prompt for essential configuration
        echo
        print_status "Please configure the following essential settings:"
        echo
        
        # Bot Token
        read -p "Enter your Telegram Bot Token: " BOT_TOKEN
        if [ ! -z "$BOT_TOKEN" ]; then
            sed -i "s/your_telegram_bot_token_here/$BOT_TOKEN/" .env
        fi
        
        # Bot Username
        read -p "Enter your Bot Username (optional): " BOT_USERNAME
        if [ ! -z "$BOT_USERNAME" ]; then
            sed -i "s/your_bot_username/$BOT_USERNAME/" .env
        fi
        
        # Owner IDs
        read -p "Enter Owner User IDs (comma-separated): " OWNER_IDS
        if [ ! -z "$OWNER_IDS" ]; then
            sed -i "s/123456789,987654321/$OWNER_IDS/" .env
        fi
        
        # Database choice
        echo
        print_status "Database Configuration:"
        echo "1) SQLite (recommended for development)"
        echo "2) PostgreSQL (for production)"
        read -p "Choose database type (1/2): " -n 1 -r DB_CHOICE
        echo
        
        if [[ $DB_CHOICE == "2" ]]; then
            read -p "Enter PostgreSQL connection URL: " DB_URL
            if [ ! -z "$DB_URL" ]; then
                sed -i "s|postgresql://username:password@localhost:5432/zultra_bot|$DB_URL|" .env
                sed -i "s|# For SQLite.*||" .env
            fi
        else
            # Use SQLite (default)
            sed -i "s|DATABASE_URL=postgresql://username:password@localhost:5432/zultra_bot|DATABASE_URL=sqlite+aiosqlite:///./zultra_bot.db|" .env
        fi
        
        # Generate encryption key
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        sed -i "s/your_32_byte_base64_encryption_key_here/$ENCRYPTION_KEY/" .env
        
        print_success "Environment configuration completed"
    else
        print_error ".env.example not found"
        exit 1
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Create logs directory
    mkdir -p logs
    
    # For SQLite, create the database file
    if grep -q "sqlite" .env; then
        print_status "Using SQLite database"
        touch zultra_bot.db
        print_success "SQLite database file created"
    fi
    
    print_success "Database setup completed"
}

# Run tests
run_tests() {
    print_status "Running basic validation tests..."
    
    # Test import
    $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    from zultra.core.config import get_settings
    settings = get_settings()
    print('✓ Configuration loaded successfully')
    
    if settings.bot_token and settings.bot_token != 'your_telegram_bot_token_here':
        print('✓ Bot token configured')
    else:
        print('⚠ Bot token not configured')
    
    print('✓ Basic validation passed')
except Exception as e:
    print(f'✗ Validation failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Validation tests passed"
    else
        print_error "Validation tests failed"
        exit 1
    fi
}

# Print usage instructions
print_usage() {
    echo
    print_success "🎉 Setup completed successfully!"
    echo
    print_status "Next steps:"
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Configure any additional settings in .env file"
    echo "3. Run the bot: python zultra/main.py"
    echo
    print_status "Useful commands:"
    echo "• Run bot: python zultra/main.py"
    echo "• Run tests: python -m pytest tests/"
    echo "• Format code: black zultra/"
    echo "• Lint code: flake8 zultra/"
    echo
    print_status "For production deployment:"
    echo "• Set ENVIRONMENT=production in .env"
    echo "• Configure PostgreSQL database"
    echo "• Set up webhook URL for cloud deployment"
    echo
}

# Main setup function
main() {
    echo "=============================================="
    echo "    Zultra Telegram Bot Setup Script"
    echo "=============================================="
    echo
    
    check_python
    create_venv
    install_dependencies
    create_env_file
    setup_database
    run_tests
    print_usage
}

# Run main function
main "$@"