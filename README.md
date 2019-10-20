# discomblebot

A 2-in-1 mostly useless Mumble and Discord Bot written in Python 3.8.

A Mumble bot monitors users presence on a Mumble server and sends status messages to a Discord bot, which posts them in a channel, and vice versa.

It depends on:
  - [pymumble](https://github.com/azlux/pymumble)
  - [discord.py](https://github.com/Rapptz/discord.py)
  
## Installation

### General
```
git clone https://github.com/azlux/pymumble.git
pip install -U -r pymumble/requirements.txt
export PYTHONPATH=$(pwd)/pymumble
git clone https://github.com/esabouraud/discomblebot.git
cd discomblebot
pip install -U -r requirements.txt
```

### Windows
A 32-bit version of Python 3 is required. pymumble depends on opuslib which in turn depends on libopus-0.dll.
Thus, some tinkering is necessary to make pymumble work on Windows.
```
git clone https://github.com/azlux/pymumble.git
git clone https://github.com/esabouraud/opuslib.git -b windows
git clone https://github.com/esabouraud/discomblebot.git
py -3-32 -m pip install -U -r pymumble/requirements.txt discomblebot/requirements.txt
set PYTHONPATH=%cd%\pymumble;%cd%\opuslib
set PATH=%PATH%;%cd%\discomblebot\libs
cd discomblebot
```
Download [libopus](https://archive.mozilla.org/pub/opus/win32/opusfile-v0.9-win32.zip) and unzip into discomblebot/libs.

### Docker
```
git clone https://github.com/esabouraud/discomblebot.git
cd discomblebot
docker build -t discomblebot:latest .
```

## Usage

### Interactive
Copy conf/discomble.conf.sample into conf/discomble.conf and fill in the parameters.
```
python -m discomblebot -f conf/discomble.conf -i
```
Type `!status` + Enter to trigger status messages from bots
Type `!quit` + Enter or `Ctrl-C` to exit.

### Daemon with docker
No volume needed.
```
docker run -d -e DISCOMBLE_CONF=$(<conf/discomble.conf) discomblebot
```

## Todo
- Use protobuf for bot2bot communication, instead of current ad-hoc message format
- Respond to commands in the same channel they were sent in
- Find out how to stop using globals in discord bot
