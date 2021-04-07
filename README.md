# Slack Events API adapter for Python with FastAPI  

SlackEventManager is a Python-based solution to recieve and parse events from Slack's Events API

This is simple add to fastapi server SLack Events API  

## Installation
```bash
pip install fastapi-slackeventsapi
```

## Work Setup 
* [App Setup](https://github.com/slackapi/python-slack-events-api/blob/main/README.rst#--app-setup)
* [Development Workflow](https://github.com/slackapi/python-slack-events-api/blob/main/README.rst#--development-workflow)  

## Usage  

Create simple FastAPI app and add SlackEventManager event handler

```python
import os

import uvicorn
from fastapi import FastAPI
from fastapi_slackeventsapi import SlackEventManager

signing_secret = os.environ.get('SLACK_BOT_SIGNING_SECRET')

app = FastAPI()

slack_event_manger = SlackEventManager(singing_secret=signing_secret,
                                       endpoint='/slack/events/',
                                       app=app)


@slack_event_manger.on('reaction_added')
async def reaction_added(event_data):
    emoji = event_data['event']['reaction']
    print(emoji)


uvicorn.run(app, host='0.0.0.0')

```

