import copy
import json
import unittest
from scripts import placement_graph as p


class PlacementGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = json.loads((p.ROOT / 'graph/placement.json').read_text())
        self.contract = json.loads((p.ROOT / 'graph/placement-contract.json').read_text())

    def test_sources_contracts_and_exact_competency_answers(self):
        self.assertEqual(p.validate(self.graph, self.contract), [])

    def test_broken_endpoint_and_unregistered_predicate(self):
        self.graph['edges'][0]['target'] = 'missing'
        self.graph['edges'][1]['type'] = 'UNREGISTERED'
        errors = p.validate(self.graph, self.contract)
        self.assertIn('Missing endpoint', errors)
        self.assertIn('Unknown predicate', errors)

    def test_duplicate_native_identity_rejected(self):
        self.graph['nodes'].append(copy.deepcopy(self.graph['nodes'][0]))
        self.assertTrue(any('Duplicate node' in x for x in p.validate(self.graph, self.contract)))

    def test_stale_user_source_not_promoted(self):
        self.graph['nodes'][0]['sha256'] = '0' * 64
        self.assertTrue(any('Stale source' in x for x in p.validate(self.graph, self.contract)))

    def test_ai_interpretation_cannot_become_user_utterance(self):
        next(n for n in self.graph['nodes'] if n['type'] == 'Capability')['authority'] = 'USER_PRIMARY'
        self.assertIn('AI graph interpretation promoted to user source', p.validate(self.graph, self.contract))

    def test_count_only_answer_is_insufficient(self):
        self.graph['competency_questions'][0]['expected'][0] = 'omc:placement:executor'
        self.assertTrue(any('Wrong competency answer' in x for x in p.validate(self.graph, self.contract)))

    def test_projection_keeps_native_endpoints_and_named_roles(self):
        result = p.project(self.graph)
        self.assertEqual({r['id'] for r in result['resources']}, {n['uid'] for n in self.graph['nodes']})
        for original, projected in zip(self.graph['edges'], result['links']):
            self.assertEqual(projected['id'], original['uid'])
            self.assertEqual(projected['participants'], [{'role': 'source', 'resource': original['source']},
                                                        {'role': 'target', 'resource': original['target']}])


if __name__ == '__main__': unittest.main()
