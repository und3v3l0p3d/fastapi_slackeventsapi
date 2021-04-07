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
