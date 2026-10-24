import importlib.util
import json
from pathlib import Path
import sqlite3
import unittest
from contextlib import contextmanager

spec = importlib.util.spec_from_file_location('browser_contribution', Path(__file__).parents[1] / 'scripts/browser_contribution.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class Ledger:
    def __init__(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield self.db
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.time = 100
        self.ledger = Ledger()
        self.doc = {'id': 'test', 'title': '공개 문서', 'text': '한글 😀\nabc', 'publicationScope': 'PUBLIC_SHIPPABLE'}
        self.corpus = {'schema': 'omc-public-browser-corpus/1', 'documents': [self.doc]}
        self.service = api.BrowserContribution(self.ledger, self.corpus, lambda: self.time)
        self.p = 'a' * 64

    def join(self, principal=None):
        return self.service.call('join', principal or self.p, {'policy': api.POLICY, 'accepted': True})

    def test_no_consent_no_work_and_wrong_policy(self):
        for action, body in [('next', {}), ('join', {'policy': 'old', 'accepted': True}), ('join', {'policy': api.POLICY, 'accepted': False})]:
            with self.assertRaises(ValueError): self.service.call(action, self.p, body)
        self.assertEqual(self.ledger.db.execute('SELECT count(*) FROM browser_audits').fetchone()[0], 0)

    def test_exact_result_replay_and_idle_preserve_receipt(self):
        self.join()
        task = self.service.call('next', self.p, {})['task']
        self.assertEqual(task, self.service.call('next', self.p, {})['task'])
        body = {'jobId': task['jobId'], 'result': api.audit(self.doc['text']), 'elapsedMs': 0.3}
        for _ in range(2):
            result = self.service.call('result', self.p, body)
            self.assertEqual(result['accepted'], 1)
            self.assertEqual(result['resultAuthority'], 'OWNER_VERIFIED')
        self.time += 11
        self.assertIsNone(self.service.call('next', self.p, {})['task'])
        reopened = api.BrowserContribution(self.ledger, self.corpus, lambda: self.time)
        self.assertEqual(reopened.call('status', self.p, {})['accepted'], 1)

    def test_foreign_forged_and_cancelled_results_rejected(self):
        self.join(); self.join('b' * 64)
        task = self.service.call('next', self.p, {})['task']
        body = {'jobId': task['jobId'], 'result': api.audit(self.doc['text']), 'elapsedMs': 1}
        with self.assertRaises(ValueError): self.service.call('result', 'b' * 64, body)
        with self.assertRaises(ValueError): self.service.call('result', self.p, {**body, 'result': {'sha256': '0' * 64}})
        stopped = self.service.call('stop', self.p, {'workerTerminated': True})
        self.assertFalse(stopped['active'])
        self.join()
        with self.assertRaises(ValueError): self.service.call('result', self.p, body)
        row = json.loads(self.ledger.db.execute('SELECT payload FROM browser_audits').fetchone()[0])
        self.assertEqual(row['state'], 'CANCELLED')
        self.assertEqual(row['remoteTermination'], 'BROWSER_REPORTED')

    def test_expired_assignment_does_not_claim_remote_termination(self):
        self.join(); self.service.call('next', self.p, {})
        self.time += 46
        result = self.service.call('status', self.p, {})
        self.assertFalse(result['active'])
        row = json.loads(self.ledger.db.execute('SELECT payload FROM browser_audits').fetchone()[0])
        self.assertEqual(row['state'], 'EXPIRED')
        self.assertEqual(row['remoteTermination'], 'UNKNOWN')

    def test_replication_is_bounded_and_revision_changes_create_new_work(self):
        for principal in [self.p, 'b' * 64]:
            self.join(principal)
            self.assertIsNotNone(self.service.call('next', principal, {})['task'])
        self.join('c' * 64)
        self.assertIsNone(self.service.call('next', 'c' * 64, {})['task'])
        changed = {**self.corpus, 'documents': [{**self.doc, 'text': 'new revision'}]}
        new = api.BrowserContribution(self.ledger, changed, lambda: self.time)
        self.assertIsNotNone(new.call('next', 'c' * 64, {})['task'])

    def test_private_oversize_and_executable_fields_rejected(self):
        for doc in [{**self.doc, 'publicationScope': 'PRIVATE'}, {**self.doc, 'text': 'x' * 65537}, {**self.doc, 'code': 'bad'}]:
            with self.assertRaises(ValueError): api.BrowserContribution(self.ledger, {**self.corpus, 'documents': [doc]})


if __name__ == '__main__': unittest.main()
