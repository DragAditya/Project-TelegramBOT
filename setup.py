#!/usr/bin/env python3
"""
Production-ready setup script for Zultra Telegram Bot.
Handles installation, configuration, and deployment preparation.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Colors for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_colored(text: str, color: str = WHITE, bold: bool = False) -> None:
    """Print colored text to terminal."""
    if bold:
        print(f"{BOLD}{color}{text}{RESET}")
    else:
        print(f"{color}{text}{RESET}")


def print_header(text: str) -> None:
    """Print a header with styling."""
    print_colored("=" * 60, CYAN)
    print_colored(f"  {text}", CYAN, bold=True)
    print_colored("=" * 60, CYAN)
    print()


def print_success(text: str) -> None:
    """Print success message."""
    print_colored(f"✅ {text}", GREEN)


def print_error(text: str) -> None:
    """Print error message."""
    print_colored(f"❌ {text}", RED)


def print_warning(text: str) -> None:
    """Print warning message."""
    print_colored(f"⚠️ {text}", YELLOW)


def print_info(text: str) -> None:
    """Print info message."""
    print_colored(f"ℹ️ {text}", BLUE)


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Found: {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def install_requirements() -> bool:
    """Install required Python packages."""
    print_info("Installing required packages...")
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print_success("Packages installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        return False


def create_env_file() -> bool:
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_warning(".env file already exists")
        return True
    
    if not env_example.exists():
        print_error(".env.example file not found")
        return False
    
    shutil.copy(env_example, env_file)
    print_success(".env file created from template")
    print_info("Please edit .env file with your bot token and configuration")
    return True


def setup_directories() -> bool:
    """Create necessary directories."""
    directories = ["logs", "backups", "data", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_success(f"Created directory: {directory}")
    
    return True


def validate_environment() -> Dict[str, Any]:
    """Validate environment configuration."""
    issues = []
    
    # Check .env file
    if not Path(".env").exists():
        issues.append("Missing .env file")
    
    # Check required environment variables
    required_vars = ["BOT_TOKEN", "DATABASE_URL"]
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing environment variable: {var}")
    
    # Check bot token format
    bot_token = os.getenv("BOT_TOKEN", "")
    if bot_token and not (bot_token.count(':') == 1 and len(bot_token.split(':')[1]) == 35):
        issues.append("Invalid bot token format")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def create_systemd_service() -> bool:
    """Create systemd service file for production deployment."""
    service_content = """[Unit]
Description=Zultra Telegram Bot
After=network.target

[Service]
Type=simple
User=zultra
WorkingDirectory=/opt/zultra-bot
ExecStart=/opt/zultra-bot/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PATH=/opt/zultra-bot/venv/bin

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("zultra-bot.service", "w") as f:
            f.write(service_content)
        
        print_success("Systemd service file created: zultra-bot.service")
        print_info("To install: sudo cp zultra-bot.service /etc/systemd/system/")
        print_info("To enable: sudo systemctl enable zultra-bot")
        print_info("To start: sudo systemctl start zultra-bot")
        return True
        
    except Exception as e:
        print_error(f"Failed to create systemd service: {e}")
        return False


def create_docker_files() -> bool:
    """Create Docker deployment files."""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bot
USER bot

# Expose port
EXPOSE 8000

# Run the bot
CMD ["python", "main.py"]
"""
    
    docker_compose_content = """version: '3.8'

services:
  zultra-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zultra_bot
      - POSTGRES_USER=zultra
      - POSTGRES_PASSWORD=your_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
"""
    
    try:
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        with open("docker-compose.yml", "w") as f:
            f.write(docker_compose_content)
        
        print_success("Docker files created: Dockerfile, docker-compose.yml")
        return True
        
    except Exception as e:
        print_error(f"Failed to create Docker files: {e}")
        return False


def run_tests() -> bool:
    """Run basic tests to verify setup."""
    print_info("Running basic tests...")
    
    try:
        # Test imports
        import zultra
        from zultra.core.config import initialize_config
        
        # Test configuration
        if not initialize_config():
            print_error("Configuration initialization failed")
            return False
        
        print_success("Basic tests passed")
        return True
        
    except Exception as e:
        print_error(f"Tests failed: {e}")
        return False


def main():
    """Main setup function."""
    print_header("🚀 ZULTRA BOT v2.0 - PRODUCTION SETUP")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        sys.exit(1)
    
    # Setup directories
    if not setup_directories():
        sys.exit(1)
    
    # Create deployment files
    print_header("📦 CREATING DEPLOYMENT FILES")
    create_systemd_service()
    create_docker_files()
    
    # Validate environment
    print_header("🔍 VALIDATING ENVIRONMENT")
    validation = validate_environment()
    
    if validation["valid"]:
        print_success("Environment validation passed")
    else:
        print_warning("Environment validation issues found:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    # Run tests
    print_header("🧪 RUNNING TESTS")
    if run_tests():
        print_success("All tests passed")
    else:
        print_warning("Some tests failed - check configuration")
    
    # Final instructions
    print_header("✅ SETUP COMPLETE")
    print_info("Next steps:")
    print("1. Edit .env file with your bot token and configuration")
    print("2. Run: python main.py")
    print("3. For production, use Docker or systemd service")
    print()
    print_colored("🎉 Zultra Bot is ready to deploy!", GREEN, bold=True)


if __name__ == "__main__":
    main()