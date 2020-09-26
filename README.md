# discomblebot

[![ci status](https://github.com/esabouraud/discomblebot/workflows/ci/badge.svg?branch=develop)](https://github.com/esabouraud/discomblebot/actions?query=workflow%3Aci+branch%3Adevelop)

A 2-in-1 mostly useless Mumble and Discord Bot written in Python 3.8.

A Mumble bot monitors users presence on a Mumble server and sends status messages to a Discord bot, which posts them in a channel, and vice versa.

It depends on:

- [pymumble](https://github.com/azlux/pymumble)
- [discord.py](https://github.com/Rapptz/discord.py)
- [protobuf](https://developers.google.com/protocol-buffers)
  
## Installation

### Prerequisites

[Download](https://github.com/protocolbuffers/protobuf) and install the protocol buffer compiler.

### General

```sh
git clone https://github.com/azlux/pymumble.git
pip install -U -r pymumble/requirements.txt
export PYTHONPATH=$(pwd)/pymumble
git clone https://github.com/esabouraud/discomblebot.git
cd discomblebot
pip install -U -r requirements.txt
protoc --python_out=. discomblebot/bot_msg.proto
```

### Windows

A 32-bit version of Python 3 is required. pymumble depends on opuslib which in turn depends on libopus-0.dll, which is only available as a 32-bit DLL.
Thus, some tinkering is necessary to make pymumble work on Windows.

```sh
git clone https://github.com/azlux/pymumble.git
git clone https://github.com/esabouraud/opuslib.git -b windows
git clone https://github.com/esabouraud/discomblebot.git
py -3-32 -m pip install -U -r pymumble/requirements.txt discomblebot/requirements.txt
set PYTHONPATH=%cd%\pymumble;%cd%\opuslib
set PATH=%PATH%;%cd%\discomblebot\libs
cd discomblebot
protoc --python_out=. discomblebot\bot_msg.proto
```

Download [libopus](https://archive.mozilla.org/pub/opus/win32/opusfile-v0.9-win32.zip) and unzip into discomblebot/libs.

## Usage

### Interactive

Copy conf/discomble.conf.sample into conf/discomble.conf and fill in the parameters.

```sh
python -m discomblebot -f conf/discomble.conf -i
```

Type `!status` + Enter to trigger status messages from bots
Type `!quit` + Enter or `Ctrl-C` to exit.

### Non-interactive

```sh
python -m discomblebot -f conf/discomble.conf
```

## Docker

### Build

```sh
git clone https://github.com/esabouraud/discomblebot.git
cd discomblebot
docker build -t discomblebot:latest .
```

### Run as daemon

Volume usage can be avoided by setting the content of the configuration file into the DISCOMBLE_CONF environment variable.

```sh
docker run -d -e DISCOMBLE_CONF=$(<conf/discomble.conf) discomblebot
```

## Todo

- Find out how to stop using globals in discord bot
