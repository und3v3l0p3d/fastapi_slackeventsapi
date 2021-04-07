from time import time
import json

import pytest
from httpx import AsyncClient

from fastapi_slackeventsapi import SlackEventManager


@pytest.fixture
def slack_event_manager():
    sem = SlackEventManager(singing_secret='some', endpoint='/slack/events/')
    yield sem


@pytest.mark.asyncio
async def test_event_dispatch(slack_event_manager):
    async def handler(data):
        assert json.dumps(data) == pytest.reaction_event_fixture, 'Wrong body'

    slack_event_manager.on_event('reaction_added', handler)

    timestamp = int(time())
    data = pytest.reaction_event_fixture
    signature = pytest.create_signature(slack_event_manager.singing_secret, timestamp, data)
    async with AsyncClient(app=slack_event_manager.app, base_url='http://test') as client:
        response = await client.post(
            '/',
            content=data,
            headers={
                'Content-Type': 'application/json',
                'X-Slack-Request-Timestamp': str(timestamp),
                'X-Slack-Signature': signature
            }
        )
        assert response.status_code == 200, 'Not valid response code'


@pytest.mark.asyncio
async def test_event_dispatch_exception(slack_event_manager):
    async def handler(data):
        raise Exception

    exception_handled = []

    async def exception_handler(exception):
        exception_handled.append(exception)

    slack_event_manager.on_event('reaction_added', handler)
    slack_event_manager.add_exception('reaction_added', exception_handler)
    slack_event_manager.add_exception(Exception, exception_handler)

    timestamp = int(time())
    data = pytest.reaction_event_fixture
    signature = pytest.create_signature(slack_event_manager.singing_secret, timestamp, data)
    async with AsyncClient(app=slack_event_manager.app, base_url='http://test') as client:
        response = await client.post(
            '/',
            content=data,
            headers={
                'Content-Type': 'application/json',
                'X-Slack-Request-Timestamp': str(timestamp),
                'X-Slack-Signature': signature
            }
        )
        assert response.status_code == 200, 'Not valid response code'
        assert len(exception_handled) == 2, 'Not all exception handled'
