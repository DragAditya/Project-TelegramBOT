#!/usr/bin/env python3
"""
Test script for Zultra Telegram Bot.
This script tests the bot configuration and basic functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from zultra.core.config import get_settings, setup_logging
    from zultra.core.bot import ZultraBot
    from zultra.db.database import init_db, close_db
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you've installed the dependencies with: pip install -r requirements.txt")
    sys.exit(1)


async def test_configuration():
    """Test bot configuration."""
    print("🔧 Testing configuration...")
    
    try:
        settings = get_settings()
        print(f"✅ Configuration loaded")
        print(f"   - Environment: {settings.environment}")
        print(f"   - Debug mode: {settings.debug}")
        print(f"   - Database: {settings.database_url.split('://')[0]}://...")
        
        if settings.bot_token and settings.bot_token != "your_telegram_bot_token_here":
            print("✅ Bot token configured")
        else:
            print("⚠️  Bot token not configured")
            
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_database():
    """Test database connection."""
    print("\n🗄️ Testing database...")
    
    try:
        await init_db()
        print("✅ Database initialized successfully")
        await close_db()
        print("✅ Database connection closed")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_bot_initialization():
    """Test bot initialization."""
    print("\n🤖 Testing bot initialization...")
    
    try:
        bot = ZultraBot()
        print("✅ Bot instance created")
        
        # Test health check
        # health = await bot.health_check()
        # print(f"✅ Health check: {health['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Bot initialization test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Zultra Bot Test Suite")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    
    tests = [
        test_configuration,
        test_database,
        test_bot_initialization,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   - Passed: {passed}/{total}")
    print(f"   - Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Your bot is ready to run.")
        print("\n📝 Next steps:")
        print("   1. Configure your bot token in .env file")
        print("   2. Run the bot: python zultra/main.py")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please check the configuration.")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)