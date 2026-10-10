"""Counterexamples to graph provenance and hypothesis boundary violations."""
from copy import deepcopy
import unittest
from scripts.flywheel import answers, read_inputs, render, validate


class FlywheelContractTests(unittest.TestCase):
    def setUp(self):
        self.graph, self.contract = read_inputs()

    def test_design_cycles_and_evidence_queries(self):
        self.assertEqual(validate(self.graph, self.contract), [])
        result = {x['id']: x['answers'] for x in answers(self.graph)}
        self.assertEqual(result['evidence-status'][0]['status'], 'PLANNED')
        self.assertIn('failed calls and retries', result['token-accounting'][0]['accounting'])
        self.assertEqual({n['authority'] for n in result['premise-evidence']}, {'USER_PRIMARY', 'SECONDARY_AI'})
        self.assertIn('```mermaid', render(self.graph))

    def test_source_tampering_and_path_escape(self):
        for key, value, message in [('sha256', '0' * 64, 'digest mismatch'),
                                    ('path', '../outside.txt', 'escapes owner')]:
            with self.subTest(key=key):
                graph = deepcopy(self.graph)
                graph['nodes'][0][key] = value
                self.assertTrue(any(message in e for e in validate(graph, self.contract)))

    def test_no_user_authority_or_fake_performance_promotion(self):
        for kind, key, value in [('Claim', 'authority', 'USER_PRIMARY'),
                                 ('Claim', 'epistemic_state', 'PROVEN'),
                                 ('Evaluation', 'result', {'improved': True})]:
            with self.subTest(kind=kind, key=key):
                graph = deepcopy(self.graph)
                next(n for n in graph['nodes'] if n['type'] == kind)[key] = value
                self.assertTrue(validate(graph, self.contract))

    def test_dependency_cycle_is_rejected_but_flywheel_is_allowed(self):
        graph = deepcopy(self.graph)
        edge = deepcopy(next(e for e in graph['edges'] if e['type'] == 'REQUIRES'))
        edge.update(uid='counterexample:cycle', source=edge['target'], target=edge['source'])
        graph['edges'].append(edge)
        self.assertIn('forbidden dependency cycle: REQUIRES', validate(graph, self.contract))

    def test_missing_premise_relation_and_bad_domain(self):
        graph = deepcopy(self.graph)
        graph['edges'] = [e for e in graph['edges'] if not (e['type'] == 'REQUIRES' and e['target'].endswith('claim:premise'))]
        self.assertTrue(any('competency query mismatch' in e for e in validate(graph, self.contract)))
        graph = deepcopy(self.graph)
        graph['edges'][0]['target'] = graph['nodes'][0]['uid']
        self.assertTrue(any('domain/range' in e for e in validate(graph, self.contract)))

    def test_duplicate_endpoint_and_unattributed_loop(self):
        for mutation, expected in [('duplicate', 'duplicate node'), ('endpoint', 'missing endpoint'),
                                    ('condition', 'missing conditional claim')]:
            with self.subTest(mutation=mutation):
                graph = deepcopy(self.graph)
                if mutation == 'duplicate':
                    graph['nodes'].append(deepcopy(graph['nodes'][0]))
                elif mutation == 'endpoint':
                    graph['edges'][0]['target'] = 'missing:node'
                else:
                    next(e for e in graph['edges'] if e['type'] == 'MAY_ENABLE')['claim_uid'] = 'missing:claim'
                self.assertTrue(any(expected in e for e in validate(graph, self.contract)))


if __name__ == '__main__':
    unittest.main()
