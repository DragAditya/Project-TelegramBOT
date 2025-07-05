#!/usr/bin/env python3
"""
Comprehensive test script for Zultra Telegram Bot.
Verifies all core functionality and configuration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color constants for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_test(name: str, status: str, details: str = ""):
    """Print test result with color coding."""
    color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
    print(f"{color}[{status}]{RESET} {name}")
    if details:
        print(f"      {details}")


def print_section(title: str):
    """Print test section header."""
    print(f"\n{BLUE}{BOLD}=== {title} ==={RESET}")


async def test_imports():
    """Test core module imports."""
    print_section("Testing Imports")
    
    try:
        import zultra
        print_test("Core module import", "PASS")
    except ImportError as e:
        print_test("Core module import", "FAIL", str(e))
        return False
    
    try:
        from zultra.core.config import initialize_config, get_settings
        print_test("Configuration import", "PASS")
    except ImportError as e:
        print_test("Configuration import", "FAIL", str(e))
        return False
    
    try:
        from zultra.core.bot import ZultraBot
        print_test("Bot class import", "PASS")
    except ImportError as e:
        print_test("Bot class import", "FAIL", str(e))
        return False
    
    try:
        from zultra.db.database import init_db
        print_test("Database import", "PASS")
    except ImportError as e:
        print_test("Database import", "FAIL", str(e))
        return False
    
    try:
        from zultra.handlers.core import CoreHandlers
        print_test("Handlers import", "PASS")
    except ImportError as e:
        print_test("Handlers import", "FAIL", str(e))
        return False
    
    return True


async def test_configuration():
    """Test configuration system."""
    print_section("Testing Configuration")
    
    try:
        from zultra.core.config import initialize_config, get_settings
        
        # Test configuration initialization
        if initialize_config():
            print_test("Configuration initialization", "PASS")
        else:
            print_test("Configuration initialization", "FAIL", "Failed to initialize")
            return False
        
        # Test settings access
        settings = get_settings()
        print_test("Settings access", "PASS")
        
        # Test required settings
        if hasattr(settings, 'bot_token'):
            print_test("Bot token setting", "PASS")
        else:
            print_test("Bot token setting", "FAIL", "No bot_token attribute")
        
        # Test environment detection
        if hasattr(settings, 'is_production'):
            is_prod = settings.is_production
            env_type = "Production" if is_prod else "Development"
            print_test("Environment detection", "PASS", f"Running in {env_type} mode")
        else:
            print_test("Environment detection", "FAIL")
        
        return True
        
    except Exception as e:
        print_test("Configuration test", "FAIL", str(e))
        return False


async def test_database():
    """Test database functionality."""
    print_section("Testing Database")
    
    try:
        from zultra.db.database import db_manager
        
        # Test database initialization
        success = await db_manager.initialize()
        if success:
            print_test("Database initialization", "PASS")
        else:
            print_test("Database initialization", "FAIL", "Failed to initialize")
            return False
        
        # Test health check
        health = await db_manager.health_check()
        if health.get('status') == 'healthy':
            print_test("Database health check", "PASS")
        else:
            print_test("Database health check", "WARN", f"Status: {health.get('status')}")
        
        # Test basic query
        try:
            result = await db_manager.execute_query("SELECT 1 as test")
            if result:
                print_test("Database query", "PASS")
            else:
                print_test("Database query", "FAIL", "No result returned")
        except Exception as e:
            print_test("Database query", "FAIL", str(e))
        
        return True
        
    except Exception as e:
        print_test("Database test", "FAIL", str(e))
        return False


async def test_bot_initialization():
    """Test bot initialization."""
    print_section("Testing Bot Initialization")
    
    try:
        from zultra.core.bot import ZultraBot
        
        # Create bot instance
        bot = ZultraBot()
        print_test("Bot instance creation", "PASS")
        
        # Test initialization
        success = await bot.initialize()
        if success:
            print_test("Bot initialization", "PASS")
        else:
            print_test("Bot initialization", "FAIL", "Initialization returned False")
            return False
        
        # Test health status
        health = bot.get_health_status()
        if health:
            print_test("Bot health status", "PASS", f"Status available")
        else:
            print_test("Bot health status", "FAIL", "No health status")
        
        # Cleanup
        await bot.shutdown()
        print_test("Bot shutdown", "PASS")
        
        return True
        
    except Exception as e:
        print_test("Bot initialization test", "FAIL", str(e))
        return False


async def test_handlers():
    """Test command handlers."""
    print_section("Testing Handlers")
    
    try:
        from zultra.handlers.core import CoreHandlers
        from zultra.handlers.fun import FunHandlers
        from zultra.handlers.utility import UtilityHandlers
        
        # Test handler initialization
        core_handlers = CoreHandlers()
        print_test("Core handlers initialization", "PASS")
        
        fun_handlers = FunHandlers()
        print_test("Fun handlers initialization", "PASS")
        
        utility_handlers = UtilityHandlers()
        print_test("Utility handlers initialization", "PASS")
        
        # Test handler methods exist
        required_core_methods = ['start_command', 'help_command', 'ping_command']
        for method in required_core_methods:
            if hasattr(core_handlers, method):
                print_test(f"Core handler method: {method}", "PASS")
            else:
                print_test(f"Core handler method: {method}", "FAIL")
        
        return True
        
    except Exception as e:
        print_test("Handlers test", "FAIL", str(e))
        return False


async def test_middlewares():
    """Test middleware system."""
    print_section("Testing Middlewares")
    
    try:
        from zultra.middlewares import (
            LoggingMiddleware, UserMiddleware, RateLimitMiddleware,
            AntiSpamMiddleware, PermissionMiddleware
        )
        
        # Test middleware initialization
        middlewares = [
            LoggingMiddleware(),
            UserMiddleware(),
            RateLimitMiddleware(),
            AntiSpamMiddleware(),
            PermissionMiddleware()
        ]
        
        for middleware in middlewares:
            print_test(f"Middleware: {middleware.name}", "PASS")
        
        return True
        
    except Exception as e:
        print_test("Middlewares test", "FAIL", str(e))
        return False


async def test_environment_variables():
    """Test environment variable configuration."""
    print_section("Testing Environment Variables")
    
    # Check for .env file
    if Path(".env").exists():
        print_test(".env file exists", "PASS")
    else:
        print_test(".env file exists", "WARN", "Consider creating .env file")
    
    # Check critical environment variables
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token and bot_token != "your_telegram_bot_token_here":
        print_test("BOT_TOKEN configured", "PASS")
    else:
        print_test("BOT_TOKEN configured", "FAIL", "Please set BOT_TOKEN in .env")
    
    # Check database URL
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print_test("DATABASE_URL configured", "PASS", f"Using: {db_url.split('://')[0]}://...")
    else:
        print_test("DATABASE_URL configured", "WARN", "Using default SQLite")
    
    # Check owner IDs
    owner_ids = os.getenv("OWNER_IDS")
    if owner_ids and owner_ids != "123456789,987654321":
        print_test("OWNER_IDS configured", "PASS")
    else:
        print_test("OWNER_IDS configured", "WARN", "Consider setting your Telegram user ID")
    
    return True


async def test_file_structure():
    """Test project file structure."""
    print_section("Testing File Structure")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        ".env.example",
        "zultra/__init__.py",
        "zultra/core/bot.py",
        "zultra/core/config.py",
        "zultra/db/models.py",
        "zultra/handlers/core.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_test(f"File: {file_path}", "PASS")
        else:
            print_test(f"File: {file_path}", "FAIL", "Missing required file")
    
    return True


async def run_all_tests():
    """Run all tests and provide summary."""
    print(f"{BOLD}{BLUE}🧪 ZULTRA BOT COMPREHENSIVE TEST SUITE{RESET}\n")
    
    tests = [
        test_file_structure,
        test_environment_variables,
        test_imports,
        test_configuration,
        test_database,
        test_handlers,
        test_middlewares,
        test_bot_initialization
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print_test(f"Test {test.__name__}", "FAIL", str(e))
            results.append(False)
    
    # Print summary
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✅ All tests passed! ({passed}/{total}){RESET}")
        print(f"{GREEN}🎉 Your bot is ready for deployment!{RESET}")
    elif passed > total * 0.8:
        print(f"{YELLOW}⚠️  Most tests passed ({passed}/{total}){RESET}")
        print(f"{YELLOW}📝 Check warnings above and configure missing settings{RESET}")
    else:
        print(f"{RED}❌ Some tests failed ({passed}/{total}){RESET}")
        print(f"{RED}🔧 Please fix the issues above before deploying{RESET}")
    
    return passed == total


if __name__ == "__main__":
    try:
        # Run tests
        success = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️ Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}❌ Test suite failed: {e}{RESET}")
        sys.exit(1)