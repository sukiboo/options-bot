# Options Bot

A simple bot for an automated options trading on IBKR.

### Docker Commands
- Remove container
```
docker rm -f options-bot
```
- Rebuild image
```
docker build -t options-bot:latest .
```
- Run container
```
docker run --rm --env-file .env -v "$(pwd)/logs:/app/logs" options-bot:latest
```
- Check logs
```
docker logs -f options-bot
```
