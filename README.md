# Options Bot

A simple bot for an automated options trading on IBKR.


### Deployment Commands
The bot can be delpoyed on the server with `deploy.sh` script:
```
./deploy.sh
```
This will copy local `.env` file to the server, pull the latest repo, rebuild and run the docker container.


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
