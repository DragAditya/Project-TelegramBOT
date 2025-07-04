# 🤖 Zultra Telegram Bot

A **production-ready**, **modular**, and **secure** Telegram bot built with Python 3.11+, featuring multi-AI provider support, comprehensive anti-spam protection, and cloud deployment capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://black.readthedocs.io)

## ✨ Key Features

### 🧠 **Multi-AI Provider Support**
- **OpenAI GPT** & **Google Gemini** integration
- **User-managed API keys** with encryption
- **Smart fallback** between providers
- **Usage tracking** and cost monitoring
- **Rate limiting** for AI requests

### 🛡️ **Advanced Security & Anti-Spam**
- **CAPTCHA verification** for new members
- **Smart spam detection** and filtering
- **Rate limiting** with configurable windows
- **Raid mode protection** for groups
- **Encrypted API key storage**
- **Role-based permissions**

### 📊 **Comprehensive Logging & Monitoring**
- **Structured logging** with Loguru
- **Request/response tracking**
- **Performance monitoring**
- **Error reporting** to admins
- **Health check endpoints**

### 🔧 **Modular Architecture**
- **Plug-and-play** command modules
- **Middleware system** for extensibility
- **Clean separation** of concerns
- **Easy to extend** and customize

### ☁️ **Cloud-Ready Deployment**
- **Render, Railway, Fly.io** compatible
- **Docker support** (optional)
- **Webhook & polling** modes
- **PostgreSQL & SQLite** support
- **Redis caching** (optional)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **PostgreSQL** (for production) or **SQLite** (for development)

### 1. Automated Setup
```bash
# Clone the repository
git clone <repository-url>
cd zultra

# Run the automated setup script
bash setup.sh
```

The setup script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Configure environment variables
- ✅ Set up database
- ✅ Run validation tests

### 2. Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Run the Bot
```bash
# Activate virtual environment
source venv/bin/activate

# Start the bot
python zultra/main.py
```

---

## 📁 Project Structure

```
zultra/
├── core/              # Core bot functionality
│   ├── config.py      # Configuration management
│   ├── bot.py         # Main bot class
│   └── errors.py      # Error handling
├── handlers/          # Command handlers
│   ├── core.py        # Core commands (/start, /help)
│   ├── fun.py         # Fun commands (/truth, /dare)
│   ├── ai.py          # AI commands (/ask, /translate)
│   ├── utility.py     # Utility commands (/ping, /calc)
│   ├── admin.py       # Admin commands (/ban, /kick)
│   └── ai_control.py  # AI management (/setai, /aiusage)
├── modules/           # Feature modules
│   ├── fun/           # Entertainment features
│   ├── moderation/    # Moderation tools
│   ├── ai/            # AI integrations
│   └── utilities/     # Utility functions
├── services/          # External services
│   ├── ai_orchestrator.py  # AI provider management
│   └── cache.py       # Caching service
├── middlewares/       # Request processing
│   ├── user.py        # User tracking
│   ├── rate_limit.py  # Rate limiting
│   ├── anti_spam.py   # Spam protection
│   ├── logging.py     # Request logging
│   └── permission.py  # Permission checks
├── db/                # Database layer
│   ├── models.py      # SQLAlchemy models
│   └── database.py    # Connection management
├── utils/             # Helper utilities
├── tests/             # Unit tests
├── deploy/            # Deployment files
│   ├── Dockerfile     # Docker configuration
│   └── docker-compose.yml
├── setup.sh           # Automated setup script
├── .env.example       # Environment template
└── README.md          # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BOT_TOKEN` | Telegram Bot Token | - | ✅ |
| `BOT_USERNAME` | Bot Username | - | ❌ |
| `DATABASE_URL` | Database connection URL | SQLite | ❌ |
| `REDIS_URL` | Redis connection URL | - | ❌ |
| `OWNER_IDS` | Comma-separated owner user IDs | - | ✅ |
| `ADMIN_IDS` | Comma-separated admin user IDs | - | ❌ |
| `OPENAI_API_KEY` | OpenAI API Key | - | ❌ |
| `GEMINI_API_KEY` | Google Gemini API Key | - | ❌ |
| `ENVIRONMENT` | Environment (development/production) | development | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |

### Database Configuration

**Development (SQLite):**
```env
DATABASE_URL=sqlite+aiosqlite:///./zultra_bot.db
```

**Production (PostgreSQL):**
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

---

## 🎮 Available Commands

### 📝 Core Commands
- `/start` - Welcome message and bot introduction
- `/help` - Display help and available commands
- `/settings` - Bot configuration panel
- `/about` - Bot information and statistics
- `/uptime` - Bot uptime and health status

### 🎪 Fun & Social Commands
- `/truth` - Truth or dare (truth)
- `/dare` - Truth or dare (dare)
- `/game` - Interactive games
- `/anime` - Random anime recommendations
- `/waifu` - Random waifu images
- `/afk` - Set AFK status
- `/roast` - Generate roasts
- `/8ball` - Magic 8-ball responses
- `/quote` - Inspirational quotes
- `/ship` - Ship compatibility
- `/leaderboard` - Group activity leaderboard

### 🤖 AI Commands
- `/ask <question>` - Ask AI a question
- `/translate <text>` - Translate text
- `/ocr` - Extract text from images
- `/imagegen <prompt>` - Generate images with AI

### 🔧 Utility Commands
- `/id` - Get user/chat IDs
- `/userinfo` - User information
- `/stats` - Bot statistics
- `/ping` - Check bot latency
- `/invite` - Generate invite link
- `/shorten <url>` - Shorten URLs
- `/weather <city>` - Weather information
- `/calc <expression>` - Calculator
- `/convert` - Unit conversion
- `/time <timezone>` - Current time
- `/whois <username>` - User lookup
- `/paste` - Create text pastes

### 👮 Admin Commands
- `/ban <user>` - Ban user from group
- `/kick <user>` - Kick user from group
- `/mute <user>` - Mute user
- `/warn <user>` - Warn user
- `/purge <count>` - Delete messages
- `/del` - Delete replied message
- `/lock <type>` - Lock chat features
- `/unlock <type>` - Unlock chat features
- `/approve <user>` - Approve user
- `/captcha` - Toggle captcha mode
- `/raidmode` - Toggle raid protection
- `/logs` - View bot logs
- `/backups` - Manage backups
- `/restore` - Restore from backup

### 🎛️ AI Control Commands
- `/setai <provider> <key>` - Set AI provider API key
- `/aiusage` - View AI usage statistics

---

## 🤖 AI Provider Management

### Adding API Keys
Users can add their own API keys for AI providers:

```
/setai openai sk-your-openai-key-here
/setai gemini your-gemini-key-here
```

### Usage Tracking
Monitor your AI usage:
```
/aiusage
```

Shows:
- Tokens used per provider
- Cost estimation
- Daily/monthly limits
- Request history

### Smart Fallback
The bot automatically switches between providers if:
- Primary provider fails
- Rate limits exceeded
- API key issues

---

## 🛡️ Security Features

### Anti-Spam Protection
- **Message rate limiting** (configurable per user)
- **Spam pattern detection** (links, mentions, repetition)
- **Automatic muting/banning** for violations
- **Whitelist system** for trusted users

### CAPTCHA System
- **Mathematical captchas** for new members
- **Image-based challenges** (optional)
- **Automatic removal** for failed attempts
- **Configurable difficulty** levels

### Raid Mode Protection
- **Emergency lockdown** for group attacks
- **Auto-ban new members** during raids
- **Temporary restrictions** on messages
- **Admin-only communication** mode

### Data Encryption
- **API keys encrypted** with Fernet
- **Secure key storage** in database
- **No plaintext secrets** in logs
- **Automatic key rotation** (optional)

---

## 📊 Monitoring & Logging

### Health Checks
Access health status at:
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "uptime": "2d 14h 32m",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "ai_services": "healthy"
  }
}
```

### Logging Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

### Log Formats
```
2024-01-01 12:00:00 | INFO | core.bot:initialize:45 | Bot initialized successfully
2024-01-01 12:00:01 | INFO | middleware.logging:process:67 | Incoming command from user 123456
```

---

## 🚀 Deployment

### Local Development
```bash
# Run with polling
python zultra/main.py

# Run with specific environment
ENVIRONMENT=development python zultra/main.py
```

### Cloud Deployment

#### Render
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with:
   ```bash
   # Build command
   pip install -r requirements.txt
   
   # Start command
   python zultra/main.py
   ```

#### Railway
1. Connect repository to Railway
2. Set environment variables
3. Railway will auto-deploy on git push

#### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly deploy
```

#### Docker (Optional)
```bash
# Build image
docker build -t zultra-bot .

# Run container
docker run -d --env-file .env zultra-bot
```

### Environment-Specific Settings

**Development:**
```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./zultra_bot.db
LOG_LEVEL=DEBUG
```

**Production:**
```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
LOG_LEVEL=INFO
BOT_WEBHOOK_URL=https://your-app.render.com/webhook
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=zultra

# Specific test file
python -m pytest tests/test_core.py
```

### Code Quality
```bash
# Format code
black zultra/

# Lint code
flake8 zultra/

# Type checking
mypy zultra/
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Add** tests for new features
5. **Ensure** code quality with black/flake8
6. **Submit** a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests before committing
python -m pytest
```

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **python-telegram-bot** - Excellent Telegram Bot API wrapper
- **SQLAlchemy** - Powerful ORM for database operations
- **Loguru** - Beautiful and powerful logging
- **Pydantic** - Data validation with type hints
- **FastAPI** - For webhook endpoints (optional)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/zultra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/zultra/discussions)
- **Email**: support@yourproject.com

---

## 🔮 Roadmap

- [ ] **Web Dashboard** for bot management
- [ ] **Plugin System** for community extensions
- [ ] **Multi-language Support** with i18n
- [ ] **Voice Message Processing** with AI
- [ ] **Advanced Analytics** and metrics
- [ ] **Backup Encryption** and cloud storage
- [ ] **GraphQL API** for external integrations
- [ ] **Machine Learning** spam detection

---

**Made with ❤️ by the Zultra Team**