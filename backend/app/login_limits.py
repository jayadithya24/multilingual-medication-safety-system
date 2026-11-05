"""Shared account-and-client attempt windows; no attacker-triggered global lockout.

Distributed attacks still require deployment monitoring and MFA. A global hard
lock would allow strangers to deny a known user access from every network.
"""
import hashlib
import time
import logging
from datetime import datetime, timezone
from pymongo import ReturnDocument
from fastapi import HTTPException
from backend.app.database import db

attempts = db['login_attempts']
attempts.create_index('expires_at', expireAfterSeconds=0)


def reserve(username, client_ip='unknown'):
    window = int(time.time()) // 900
    account_hash = hashlib.sha256(username.strip().lower().encode()).hexdigest()
    global_key = 'monitor:' + account_hash + ':' + str(window)
    global_row = attempts.find_one_and_update({'_id': global_key}, {'$inc': {'count': 1}, '$setOnInsert': {
        'expires_at': datetime.fromtimestamp((window + 1) * 900, timezone.utc)}},
        upsert=True, return_document=ReturnDocument.AFTER)
    if global_row['count'] == 32:
        attempts.update_one({'_id': global_key}, {'$set': {'monitor_required': True}})
        logging.getLogger(__name__).warning('distributed_login_threshold account_hash=%s window=%s', account_hash, window)
    key = hashlib.sha256((username.strip().lower() + '\0' + client_ip).encode()).hexdigest() + ':' + str(window)
    row = attempts.find_one_and_update({'_id': key}, {'$inc': {'count': 1}, '$setOnInsert': {
        'expires_at': datetime.fromtimestamp((window + 1) * 900, timezone.utc)}}, upsert=True, return_document=ReturnDocument.AFTER)
    if row['count'] > 8:
        raise HTTPException(429, 'Too many sign-in attempts. Please retry later.',
                            headers={'Retry-After': str(max(1, (window + 1) * 900 - int(time.time())))})
    return key


def succeeded(key):
    attempts.delete_one({'_id': key})
