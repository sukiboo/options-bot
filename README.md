# Options Bot ⏱️🦙💸

A simple bot for automated options trading on ~~[IBKR](https://www.interactivebrokers.com/en/trading/ib-api.php)~~ [Alpaca](https://alpaca.markets/).

## What it does

The bot monitors a single ticker and executes a wheel-style options strategy:
- **If you hold shares**: sells covered calls at a strike price above current price
- **If you have cash**: sells cash-secured puts at a strike price below current price

Using the example settings (`AAPL` with 5% OTM margins):
- If `AAPL` is at `$200` and you own `1,000` shares → sells `10` calls at `$210` strike price
- If `AAPL` is at `$200` and you have `$200,000` in cash → sells `10` puts at `$190` strike price
- Options expiration is always set to be the closest Friday

The bot runs on a cron schedule, checks positions hourly, and sends Telegram notifications.

## Setup

### 1. Create `.env` from template

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Alpaca API credentials (from https://alpaca.markets)
ALPACA_API_KEY=...
ALPACA_API_SECRET=...

# Telegram bot for notifications (from @BotFather)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Deployment settings
SERVER_USER=YOUR_USERNAME_HERE
SERVER_HOST=YOUR_HOSTNAME_HERE
SERVER_PATH=YOUR_PATH_HERE  # bot deployed to `SERVER_PATH/bot_name`
REPO_URL=https://github.com/your-username/options-bot.git
```

### 2. Create `settings.yaml` from template

```bash
cp settings.example.yaml settings.yaml
```

Edit `settings.yaml`:

```yaml
bot_name: options-bot                     # Docker image name and deploy path
paper_trading: true                       # true for paper, false for live trading

ticker: AAPL                              # stock to trade options on
call_option_margin: 0.05                  # 5% above current price for calls
put_option_margin: 0.05                   # 5% below current price for puts

timezone: America/New_York                # schedule timezone
trade_options_schedule: "59 9 * * 0-4"    # 09:59 AM weekdays
check_value_schedule: "0 10-16 * * 0-4"   # hourly 10:00-16:00 weekdays
```

## Deployment

Deploy to server with:
```bash
./deploy.sh
```

This will:
1. Pull latest code to `~/SERVER_PATH/bot_name` on the server
2. Copy `.env` and `settings.yaml` to the server
3. Build and run the Docker container

## Docker commands

```bash
# View logs
docker logs -f options-bot

# Stop/start
docker stop options-bot
docker start options-bot

# Rebuild manually
docker build -t options-bot:latest .
docker run -d --name options-bot \
  --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  options-bot:latest
```

## Local development

```bash
# Run directly
python app.py

# Run pre-commit checks
pre-commit run --all-files
```
