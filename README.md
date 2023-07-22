Fork of https://git.sr.ht/~bo41/matrix-channel-mirror-py

# Matrix-Telegram Channel Mirror

Matrix bot to mirror public Telegram channels.

Crawls Telegrams public view of channels (https://t.me/s/telegram) and sends them to a Matrix group.

Set the "Send messages" permission to something different than "Default" to achieve the read-only environment.

## Build

Get the dependencies from GitHub

```bash
pip install lxml matrix-nio cssselect
```

## Run

Use cron or similar to call it every few minutes (as [configured](#Configure) at `updateInterval`) to sync

```
0,15,30,45 * * * * /usr/bin/python3 /path/to/the/mirror/main.py
```

## Configure

See [config.sample.ini](/config.sample.ini) for Matrix config.

See [channels.sample.csv](/channels.sample.csv) for channel config. (`channel name in TG; room ID in Matrix`)
