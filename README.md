# Options Bot

A simple bot for automated options trading on ~~IBKR~~ Alpaca.


### Deployment Commands
The bot can be delpoyed on the server with `deploy.sh` script:
```
./deploy.sh
```
This will copy local `.env` file to the server, pull the latest repo, rebuild and run the docker container.


### Server Setup
If docker/git is not installed:
```
sudo apt-get update
sudo apt-get install -y docker.io git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```


### Docker Commands
- Stop and remove container
```
docker stop options-bot
docker rm options-bot
```
- Rebuild image
```
docker build -t options-bot:latest .
```
- Run container (continuous with auto-restart)
```
docker run -d --name options-bot \
  --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  options-bot:latest
```
- Check container status
```
docker ps
```
- Check logs
```
docker logs -f options-bot
```
- Stop container
```
docker stop options-bot
```
- Start container
```
docker start options-bot
```
