#!/usr/bin/env python3
"""OMC browser corpus audit, in the live owner's existing resource ledger.

Only operator-published PUBLIC_SHIPPABLE UTF-8 documents are assigned. Browser
timings are untrusted observations, never CPU credits. No executable task input.
The owner verifies every result and retains at most two distinct-principal audits per
document revision; an empty queue idles instead of manufacturing compute work.
"""
import argparse
import hashlib
import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import re
import sys
import time
import uuid

POLICY = 'hoh-omc-browser/1'
LIMITS = {'workers': 1, 'inputBytes': 65536, 'taskTimeoutMs': 5000,
          'minimumIntervalMs': 10000, 'leaseMs': 45000, 'gpu': False}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path, limit):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit, 'Invalid owner file')
    raw = path.read_bytes()
    require(len(raw) <= limit, 'Owner file grew')
    return json.loads(raw)


def audit(text):
    raw = text.encode('utf-8')
    return {'sha256': sha(raw), 'bytes': len(raw), 'characters': len(text),
            'lines': text.count('\n') + 1}


class BrowserContribution:
    def __init__(self, broker, corpus, clock=time.time):
        self.broker, self.clock = broker, clock
        require(corpus.get('schema') == 'omc-public-browser-corpus/1', 'Invalid corpus')
        docs = corpus.get('documents')
        require(isinstance(docs, list) and 0 < len(docs) <= 512, 'Corpus count')
        self.docs = {}
        total = 0
        for doc in docs:
            require(set(doc) == {'id', 'title', 'text', 'publicationScope'}, 'Invalid document')
            require(doc['publicationScope'] == 'PUBLIC_SHIPPABLE', 'Public documents only')
            require(isinstance(doc['id'], str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', doc['id']), 'Invalid document ID')
            require(isinstance(doc['title'], str) and 0 < len(doc['title']) <= 200, 'Invalid title')
            require(isinstance(doc['text'], str) and 0 < len(doc['text'].encode()) <= LIMITS['inputBytes'], 'Document budget')
            expected = audit(doc['text'])
            key = sha((doc['id'] + ':' + expected['sha256']).encode())
            require(key not in self.docs, 'Duplicate input')
            self.docs[key] = {**doc, 'key': key, 'expected': expected}
            total += expected['bytes']
        require(total <= 4 * 1024 * 1024, 'Corpus budget')
        self.revision = sha(json.dumps(docs, ensure_ascii=False, sort_keys=True).encode())
        # This is the existing broker connection, not a new SQLite path/ledger.
        with broker.transaction() as con:
            con.execute('CREATE TABLE IF NOT EXISTS browser_participants (principal TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS browser_audits (id TEXT PRIMARY KEY, principal TEXT NOT NULL, input_key TEXT NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL)')
            con.execute('CREATE INDEX IF NOT EXISTS browser_audit_input ON browser_audits(input_key,state)')

    def _save(self, con, participant):
        con.execute('INSERT OR REPLACE INTO browser_participants VALUES (?,?)',
                    (participant['principal'], json.dumps(participant)))

    def _job(self, con, job):
        con.execute('INSERT OR REPLACE INTO browser_audits VALUES (?,?,?,?,?)',
                    (job['id'], job['principal'], job['inputKey'], job['state'], json.dumps(job)))

    def _expire(self, con, now):
        for (raw,) in con.execute("SELECT payload FROM browser_audits WHERE state='ASSIGNED'"):
            job = json.loads(raw)
            if job['expiresAt'] <= now:
                # Protocol assignment expired; no claim of remote CPU termination.
                job.update(state='EXPIRED', remoteTermination='UNKNOWN')
                self._job(con, job)

    def call(self, action, principal, body):
        require(re.fullmatch(r'[a-f0-9]{64}', principal or '') is not None, 'Invalid principal')
        require(isinstance(body, dict), 'Object required')
        require(action in ('join', 'next', 'result', 'stop', 'status'), 'Unknown action')
        now = int(self.clock() * 1000)
        with self.broker.transaction() as con:
            self._expire(con, now)
            row = con.execute('SELECT payload FROM browser_participants WHERE principal=?', (principal,)).fetchone()
            p = json.loads(row[0]) if row else None
            if action == 'join':
                require(set(body) == {'policy', 'accepted'} and body['policy'] == POLICY and body['accepted'] is True, 'Consent required')
                require(p is not None or con.execute('SELECT COUNT(*) FROM browser_participants').fetchone()[0] < 10000, 'Participant capacity')
                p = p or {'principal': principal, 'accepted': 0, 'verifiedBytes': 0, 'lastAssigned': 0}
                p.update(policy=POLICY, active=True, expiresAt=now + LIMITS['leaseMs'], consentAt=now)
                self._save(con, p)
            if action in ('next', 'result'):
                require(p and p.get('active') and p['expiresAt'] > now and p['policy'] == POLICY, 'Active contribution required')
            if action == 'stop':
                require(set(body) <= {'workerTerminated'}, 'Unexpected stop fields')
                if p:
                    p.update(active=False, expiresAt=now)
                    self._save(con, p)
                    for (raw,) in con.execute("SELECT payload FROM browser_audits WHERE principal=? AND state='ASSIGNED'", (principal,)):
                        job = json.loads(raw)
                        job.update(state='CANCELLED', remoteTermination='BROWSER_REPORTED' if body.get('workerTerminated') is True else 'UNKNOWN')
                        self._job(con, job)
            task = None
            if action == 'result':
                require(set(body) == {'jobId', 'result', 'elapsedMs'}, 'Unexpected result fields')
                require(isinstance(body['jobId'], str) and len(body['jobId']) <= 64, 'Invalid job')
                require(type(body['elapsedMs']) in (int, float) and 0 <= body['elapsedMs'] <= LIMITS['taskTimeoutMs'], 'Invalid elapsed time')
                row = con.execute('SELECT payload FROM browser_audits WHERE id=? AND principal=?', (body['jobId'], principal)).fetchone()
                require(row is not None, 'Unknown assignment')
                job = json.loads(row[0])
                doc = self.docs.get(job['inputKey'])
                require(doc and job['corpusRevision'] == self.revision, 'Input revision changed')
                require(job['state'] in ('ASSIGNED', 'ACCEPTED'), 'Assignment ended')
                result = body['result']
                require(isinstance(result, dict) and set(result) == {'sha256', 'bytes', 'characters', 'lines'}, 'Invalid result shape')
                require(isinstance(result['sha256'], str) and all(type(result[k]) is int for k in ('bytes', 'characters', 'lines')), 'Invalid result types')
                require(body['result'] == doc['expected'], 'Incorrect audit result')
                if job['state'] != 'ACCEPTED':
                    job.update(state='ACCEPTED', completedAt=now, result=body['result'],
                               browserElapsedMs=body['elapsedMs'], measurementAuthority='BROWSER_REPORTED',
                               validation='OWNER_VERIFIED_EXACT_RESULT', remoteTermination='BROWSER_REPORTED')
                    self._job(con, job)
                    p['accepted'] += 1
                    p['verifiedBytes'] += doc['expected']['bytes']
                    self._save(con, p)
            if action == 'next':
                require(body == {}, 'Unexpected next fields')
                p['expiresAt'] = now + LIMITS['leaseMs']
                self._save(con, p)
                row = con.execute("SELECT payload FROM browser_audits WHERE principal=? AND state='ASSIGNED'", (principal,)).fetchone()
                job = json.loads(row[0]) if row else None
                if not job and now - p['lastAssigned'] >= LIMITS['minimumIntervalMs']:
                    require(con.execute('SELECT COUNT(*) FROM browser_audits').fetchone()[0] < 20000, 'Audit retention capacity')
                    for key, doc in self.docs.items():
                        rows = con.execute("SELECT principal FROM browser_audits WHERE input_key=? AND state IN ('ASSIGNED','ACCEPTED')", (key,)).fetchall()
                        if len(rows) >= 2 or any(r[0] == principal for r in rows):
                            continue
                        job = {'id': 'browser-' + uuid.uuid4().hex, 'principal': principal, 'inputKey': key,
                               'corpusRevision': self.revision, 'state': 'ASSIGNED', 'assignedAt': now,
                               'expiresAt': now + LIMITS['leaseMs'], 'template': 'public-corpus-audit/v1'}
                        self._job(con, job)
                        p['lastAssigned'] = now
                        self._save(con, p)
                        break
                if job:
                    doc = self.docs.get(job['inputKey'])
                    if doc:
                        task = {'jobId': job['id'], 'inputKey': doc['key'], 'corpusRevision': self.revision,
                                'title': doc['title'], 'text': doc['text'], 'template': job['template'], 'expiresAt': job['expiresAt']}
            active = bool(p and p.get('active') and p['expiresAt'] > now)
            outstanding = con.execute("SELECT 1 FROM browser_audits WHERE principal=? AND state='ASSIGNED' LIMIT 1", (principal,)).fetchone() is not None
            return {'schema': 'omc-browser-participation/1', 'policy': POLICY, 'active': active,
                    'expiresAt': p['expiresAt'] if active else 0, 'limits': LIMITS, 'task': task,
                    'accepted': p['accepted'] if p else 0, 'verifiedBytes': p['verifiedBytes'] if p else 0,
                    'corpusRevision': self.revision, 'state': 'WORK_ASSIGNED' if active and outstanding else 'AVAILABLE' if active else 'STOPPED',
                    'resultAuthority': 'OWNER_VERIFIED' if action == 'result' else 'OWNER_REPORTED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--port', type=int, default=19128)
    args = parser.parse_args()
    from rebalance_broker import verify_shared_owner
    owner = Path(args.owner).resolve()
    verify_shared_owner(owner)
    sys.path.insert(0, str(owner / 'scripts'))
    from resource_broker import Broker
    config_path = Path(args.config)
    config = read_json(config_path, 8192)
    token_path = Path(config['tokenFile'])
    require(token_path.stat().st_mode & 0o777 == 0o600, 'Private token file required')
    token = token_path.read_text().strip()
    require(re.fullmatch(r'[a-f0-9]{64}', token) is not None, 'Invalid owner token')
    service = BrowserContribution(Broker(root=owner), read_json(Path(config['corpusFile']), 8 * 1024 * 1024))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                self.connection.settimeout(5)
                require(hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token), 'Unauthorized')
                length = int(self.headers.get('Content-Length', '0'))
                require(0 < length <= 8192, 'Request budget')
                raw = self.rfile.read(length)
                require(len(raw) == length, 'Incomplete body')
                value = json.loads(raw)
                require(set(value) == {'principal', 'body'}, 'Invalid envelope')
                action = self.path.removeprefix('/v1/browser/')
                current = read_json(config_path, 8192)
                require(action in ('stop', 'status') or current.get('enabled') is True, 'Owner revoked')
                result = service.call(action, value['principal'], value['body'])
                if current.get('enabled') is not True:
                    result.update(active=False, expiresAt=0, state='REVOKED')
                status = 200
            except (ValueError, KeyError, TypeError, OSError):
                status, result = 409, {'error': 'OMC_REQUEST_REJECTED'}
            data = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
