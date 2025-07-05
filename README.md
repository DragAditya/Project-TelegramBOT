# 🚀 Zultra Bot v2.0 - Advance Telegram Bot

A bulletproof, production-ready Telegram bot with zero errors, complete error handling, clean modular architecture, and enterprise-grade features. Built for 24/7 operation on platforms like Render, Vercel, Railway, and more.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)
![Tests](https://img.shields.io/badge/Tests-Passing-success.svg)

## ✨ Features

### 🔧 Core Features
- **Bulletproof Error Handling** - Comprehensive error recovery and logging
- **Modular Architecture** - Clean, maintainable, and extensible codebase
- **Production-Ready** - Zero errors, robust error handling, and monitoring
- **Multi-Database Support** - SQLite (dev) and PostgreSQL (production)
- **Redis Caching** - High-performance caching and session management
- **AI Integration** - OpenAI GPT and Google Gemini support
- **Rate Limiting** - Anti-spam and abuse protection
- **User Management** - Comprehensive user and group tracking
- **Health Monitoring** - Built-in health checks and status reporting

### 🎮 Bot Commands
- **Core Commands**: `/start`, `/help`, `/settings`, `/about`, `/uptime`, `/ping`
- **Fun Commands**: `/truth`, `/dare`, `/8ball`, `/quote`, `/roast`, `/ship`
- **Utility Commands**: `/id`, `/userinfo`, `/stats`, `/calc`, `/time`, `/invite`
- **AI Commands**: `/ask`, `/translate`, `/ocr`, `/imagegen`
- **Admin Commands**: `/ban`, `/kick`, `/mute`, `/warn` (permission-based)

### 🔒 Security Features
- **Encrypted API Keys** - Secure storage of sensitive data
- **Permission System** - Role-based access control
- **Anti-Spam Protection** - Intelligent spam detection
- **Rate Limiting** - Prevents abuse and overload
- **Input Validation** - Comprehensive data validation

## 🚀 Quick Start

### 1. One-Line Setup
```bash
curl -fsSL https://raw.githubusercontent.com/Project-TelegramBOT/main/install.sh | bash
```

### 2. Manual Setup
```bash
# Clone the repository
git clone https://github.com/your-repo/zultra-bot.git
cd zultra-bot

# Run setup script
python setup.py

# Configure your bot
cp .env.example .env
# Edit .env with your bot token and settings

# Start the bot
python main.py
```

## 📋 Requirements

- **Python**: 3.8 or higher
- **Memory**: 512MB RAM minimum (1GB recommended)
- **Storage**: 100MB minimum
- **Network**: Stable internet connection

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Bot Configuration (Required)
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username

# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./zultra_bot.db

# Optional Features
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# Admin Configuration
OWNER_IDS=123456789,987654321
ADMIN_IDS=111111111,222222222

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 🔧 Advanced Configuration

For production deployments, additional configuration options are available:

```env
# Performance Settings
MAX_WORKERS=4
CONNECTION_POOL_SIZE=10
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_WINDOW=60

# Security
SECRET_KEY=your-production-secret-key
ENCRYPTION_KEY=auto-generated-or-custom

# Webhook (for production)
BOT_WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
```

## 🚢 Deployment

### 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t zultra-bot .
docker run -d --env-file .env zultra-bot
```

### ☁️ Cloud Platforms

#### Render
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with `python main.py`

#### Railway
1. Connect repository to Railway
2. Configure environment variables
3. Auto-deploy on push

#### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel --env-file .env`

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-bot-name
heroku config:set BOT_TOKEN=your_token
git push heroku main
```

### 🖥️ VPS/Server Deployment

#### Using Systemd (Recommended)
```bash
# Setup script creates systemd service file
sudo cp zultra-bot.service /etc/systemd/system/
sudo systemctl enable zultra-bot
sudo systemctl start zultra-bot
sudo systemctl status zultra-bot
```

#### Using PM2
```bash
npm install -g pm2
pm2 start main.py --name zultra-bot --interpreter python3
pm2 startup
pm2 save
```

## 📊 Monitoring & Health Checks

### Built-in Health Endpoint
The bot includes a health check endpoint at `/health`:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
    "status": "healthy",
    "uptime": "2h 15m 30s",
    "version": "2.0.0",
    "database": "healthy",
    "redis": "healthy",
    "ai_services": "healthy"
}
```

### Logging
- **Development**: Console output with colors
- **Production**: File rotation with compression
- **Error Tracking**: Separate error logs with stack traces

### Metrics
- Request/response times
- Error rates and patterns
- User activity statistics
- AI usage tracking

## 🔧 API Reference

### Core Commands

#### `/start`
Initializes the bot for new users and displays welcome message.

#### `/help`
Shows comprehensive help with all available commands.

#### `/settings`
Interactive settings panel with inline keyboards.

### AI Commands

#### `/ask <question>`
Ask AI assistant using configured provider (OpenAI/Gemini).

#### `/translate <text>`
Translate text to different languages.

### Utility Commands

#### `/calc <expression>`
Safe mathematical calculator with expression evaluation.

#### `/time [timezone]`
Display current time in specified timezone.

## �️ Development

### Project Structure
```
zultra/
├── core/           # Core bot functionality
│   ├── bot.py      # Main bot class
│   ├── config.py   # Configuration management
│   └── errors.py   # Error handling
├── handlers/       # Command handlers
│   ├── core.py     # Core commands
│   ├── fun.py      # Fun commands
│   ├── utility.py  # Utility commands
│   └── ai.py       # AI commands
├── middlewares/    # Request processing
│   ├── logging.py  # Request logging
│   ├── user.py     # User tracking
│   └── rate_limit.py # Rate limiting
├── db/            # Database layer
│   ├── models.py   # SQLAlchemy models
│   └── database.py # Database management
└── services/      # External services
    └── ai.py      # AI orchestrator
```

### Adding New Commands

1. Create handler in appropriate module:
```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello!")
```

2. Register in `bot.py`:
```python
app.add_handler(CommandHandler("mycommand", self._wrap_handler(handler)))
```

### Adding Middleware

1. Create middleware class:
```python
class MyMiddleware(BaseMiddleware):
    async def _process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # Process update
        return True  # Continue processing
```

2. Register in bot initialization.

## 🧪 Testing

### Run Tests
```bash
# Basic functionality test
python -m pytest tests/

# Integration tests
python test_bot.py

# Health check
curl http://localhost:8000/health
```

### Test Bot Locally
```bash
# Development mode
ENVIRONMENT=development python main.py

# Test specific commands
python -c "from zultra.handlers.core import CoreHandlers; print('Import test passed')"
```

## 📝 Troubleshooting

### Common Issues

#### Bot Token Invalid
- Verify token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- Check with @BotFather on Telegram

#### Database Connection Failed
- SQLite: Check file permissions and disk space
- PostgreSQL: Verify connection string and credentials

#### AI Commands Not Working
- Check API keys in `.env` file
- Verify provider quotas and limits
- Check network connectivity

#### Memory Issues
- Increase server RAM (minimum 512MB)
- Enable swap if available
- Monitor with `htop` or `ps aux`

### Debug Mode
```bash
DEBUG=true LOG_LEVEL=DEBUG python main.py
```

### Logs Location
- **Development**: Console output
- **Production**: `logs/zultra_bot.log`
- **Errors**: `logs/errors.log`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-repo/zultra-bot.git
cd zultra-bot

# Install development dependencies
pip install -r requirements.txt

# Run in development mode
ENVIRONMENT=development python main.py
```

## � License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [SQLAlchemy](https://sqlalchemy.org/) - Database ORM
- [Loguru](https://github.com/Delgan/loguru) - Beautiful logging
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/zultra-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/zultra-bot/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/zultra-bot/wiki)

---

<div align="center">

**⭐ If you find this project helpful, please star it on GitHub! ⭐**

Made with ❤️ by the Zultra Team

</div>
