import json
import hashlib
import hmac
import pytest


def create_signature(secret, timestamp, data):
    req = str.encode('v0:' + str(timestamp) + ':') + str.encode(data)
    request_signature = 'v0=' + hmac.new(
        str.encode(secret),
        req, hashlib.sha256
    ).hexdigest()
    return request_signature


def load_event_fixture(event, as_string=True):
    event_data = {
        'reaction_added': {
            "token": "vFO9LARnLI7GflLR8tGqHgdy",
            "team_id": "T0JFD6M53",
            "api_app_id": "A28SCUES3",
            "event": {
                "type": "reaction_added",
                "user": "U27FFLNF4",
                "item": {
                    "type": "message",
                    "channel": "D2AQCJCQ2",
                    "ts": "1477958101.000004"
                },
                "reaction": "grinning",
                "item_user": "U299ATJ2X",
                "event_ts": "1477958240.864741"
            },
            "type": "event_callback",
            "authed_users": [
                "U299ATJ2X"
            ]
        },
        'url_challenge': {
            "token": "Jhj5dZrVaK7ZwHHjRyZWjbDl",
            "challenge": "valid_challenge_token",
            "type": "url_verification"
        }
    }
    if not as_string:
        return event_data[event]
    else:
        return json.dumps(event_data[event])


def event_with_bad_token():
    event_data = load_event_fixture('reaction_added', as_string=False)
    event_data['token'] = "bad_token"
    return json.dumps(event_data)


def pytest_configure():
    pytest.reaction_event_fixture = load_event_fixture('reaction_added')
    pytest.url_challenge_fixture = load_event_fixture('url_challenge')
    pytest.bad_token_fixture = event_with_bad_token()
    pytest.create_signature = create_signature
