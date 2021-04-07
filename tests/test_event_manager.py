from time import time

import pytest

from httpx import AsyncClient

from fastapi_slackeventsapi import SlackEventManager


@pytest.fixture
def slack_event_manager():
    yield SlackEventManager(singing_secret='some', endpoint='/slack/events/')


@pytest.mark.asyncio
async def test_invalid_request_signature(slack_event_manager):
    signature = 'bad signature'
    timestamp = int(time())
    data = pytest.reaction_event_fixture
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
        assert response.status_code == 403, 'Invalid error code'


@pytest.mark.asyncio
async def test_invalid_request_timestamp(slack_event_manager):
    signature = 'bad signature'
    timestamp = int(time() + 1000)
    data = pytest.reaction_event_fixture
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
        assert response.status_code == 403, 'Invalid error code'


@pytest.mark.asyncio
async def test_challenge_request(slack_event_manager):
    timestamp = int(time())
    data = pytest.url_challenge_fixture
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
        assert response.status_code == 200, 'Invalid response code'
        assert response.text.strip('"') == "valid_challenge_token", 'Challenge token not match'
