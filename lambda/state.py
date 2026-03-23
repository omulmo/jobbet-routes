"""State persistence — single JSON document in S3."""

import json
import os
import boto3
from models import AppState, state_to_dict, dict_to_state

_s3 = None
_bucket = None
_key = "state.json"
_default_state_path = os.path.join(os.path.dirname(__file__), "default_state.json")


def _get_s3():
    global _s3, _bucket
    if _s3 is None:
        _s3 = boto3.client("s3")
        _bucket = os.environ["STATE_BUCKET"]
    return _s3


def _load_default() -> AppState:
    with open(_default_state_path) as f:
        return dict_to_state(json.load(f))


def load_state() -> AppState:
    try:
        resp = _get_s3().get_object(Bucket=_bucket, Key=_key)
        data = json.loads(resp["Body"].read())
        return dict_to_state(data)
    except _get_s3().exceptions.NoSuchKey:
        return _load_default()


def save_state(state: AppState) -> None:
    _get_s3().put_object(
        Bucket=_bucket,
        Key=_key,
        Body=json.dumps(state_to_dict(state), ensure_ascii=False),
        ContentType="application/json",
    )
