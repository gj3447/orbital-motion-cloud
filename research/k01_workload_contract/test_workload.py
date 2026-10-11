import copy
import struct
import unittest

from workload import (ContractError, HEADER, MAX_I64, MIN_I64, MAX_ITEMS,
                      canonical, decode_input, encode_input, execute, make_spec,
                      semantic_digest, sha256, verify_result)


class WorkloadTests(unittest.TestCase):
    def setup_case(self, values):
        payload = encode_input(values)
        return make_spec('workload:example', payload), payload

    def test_int64_wire_roundtrip(self):
        values = [MIN_I64, -1, 0, 1, MAX_I64, (1 << 53)+1]
        self.assertEqual(decode_input(encode_input(values)), tuple(values))
        self.assertEqual(encode_input([1])[12:], b'\x01'+b'\x00'*7)

    def test_non_integer_inputs_are_rejected(self):
        for values in ([True], [1.0], ['1'], [MAX_I64+1], [MIN_I64-1], (1,)):
            with self.subTest(values=values), self.assertRaises(ContractError):
                encode_input(values)

    def test_malformed_payloads_are_rejected(self):
        good = encode_input([1])
        for bad in (b'', good[:-1], good+b'\x00', b'X'+good[1:], HEADER+struct.pack('<I', MAX_ITEMS+1), bytearray(good)):
            with self.subTest(bad=repr(bad)), self.assertRaises(ContractError):
                decode_input(bad)

    def test_bound_and_empty(self):
        self.assertEqual(len(decode_input(encode_input([0]*MAX_ITEMS))), MAX_ITEMS)
        with self.assertRaises(ContractError): encode_input([0]*(MAX_ITEMS+1))
        spec, payload = self.setup_case([])
        r = execute(spec, payload, 'scalar-exact-v1', 'attempt:empty')
        self.assertEqual(r['result'], {'outcome':'OK','sum_decimal':'0','count':0})

    def test_changed_input_cannot_reuse_spec(self):
        spec, _ = self.setup_case([1])
        with self.assertRaises(ContractError): execute(spec, encode_input([2]), 'scalar-exact-v1', 'a1')

    def test_contract_and_effect_changes_are_rejected(self):
        spec, payload = self.setup_case([1])
        for key, value in [('effect','EXTERNAL_WRITE'), ('contract_revision',2), ('input_items',True), ('input_encoding','json'), ('extra','field')]:
            bad = dict(spec); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ContractError):
                execute(bad, payload, 'scalar-exact-v1', 'a1')

    def test_variants_and_attempts_preserve_semantics(self):
        spec, payload = self.setup_case([MAX_I64, 1, -1])
        candidates = [execute(spec,payload,'scalar-exact-v1','a1'), execute(spec,payload,'chunked-exact-v1','a2',chunk_size=2)]
        for r in candidates: self.assertTrue(verify_result(spec,payload,r))
        self.assertEqual(candidates[0]['semantic_sha256'],candidates[1]['semantic_sha256'])
        self.assertNotEqual(candidates[0]['attempt_uid'],candidates[1]['attempt_uid'])
        self.assertEqual(candidates[1]['result']['sum_decimal'],str(MAX_I64))

    def test_distinct_requests_remain_distinct(self):
        a,payload = self.setup_case([1])
        b = make_spec('workload:another',payload)
        self.assertNotEqual(semantic_digest(a),semantic_digest(b))
        with self.assertRaises(ContractError): verify_result(b,payload,execute(a,payload,'scalar-exact-v1','a1'))

    def test_final_overflow_is_semantic_error(self):
        for values in ([MAX_I64,1],[MIN_I64,-1]):
            spec,payload=self.setup_case(values)
            for variant in ['scalar-exact-v1','chunked-exact-v1']:
                r=execute(spec,payload,variant,'a1')
                self.assertEqual(r['result'], {'outcome':'DOMAIN_ERROR','code':'SUM_OUT_OF_I64_RANGE'})
                self.assertTrue(verify_result(spec,payload,r))

    def test_wrong_result_with_matching_hash_is_rejected(self):
        spec,payload=self.setup_case([(1<<53),1])
        r=execute(spec,payload,'scalar-exact-v1','a1')
        r['result']['sum_decimal']=str(1<<53)
        r['result_sha256']=sha256(canonical(r['result']))
        with self.assertRaises(ContractError): verify_result(spec,payload,r)

    def test_unknown_variants_and_bad_chunk_sizes_are_rejected(self):
        spec,payload=self.setup_case([1])
        with self.assertRaises(ContractError): execute(spec,payload,'untrusted-code','a1')
        for n in [0,-1,True,1.0,MAX_ITEMS+1]:
            with self.subTest(n=n), self.assertRaises(ContractError): execute(spec,payload,'chunked-exact-v1','a1',chunk_size=n)

    def test_cancelled_candidate_cannot_be_verified(self):
        spec,payload=self.setup_case([1])
        r=execute(spec,payload,'scalar-exact-v1','a1')
        with self.assertRaises(ContractError): verify_result(spec,payload,r,cancelled=True)
        self.assertTrue(verify_result(spec,payload,r))  # local predicate, not durable cancellation ownership

    def test_candidate_pins_and_schema_are_checked(self):
        spec,payload=self.setup_case([1])
        original=execute(spec,payload,'chunked-exact-v1','a1')
        for key,value in [('artifact_sha256','0'*64),('input_sha256','0'*64),('schema','other'),('definition_sha256','0'*64),('attempt_uid',''),('execution',{'chunk_size':True}),('extra',1)]:
            bad=copy.deepcopy(original); bad[key]=value
            with self.subTest(key=key), self.assertRaises(ContractError): verify_result(spec,payload,bad)

    def test_canonical_output_is_required(self):
        spec,payload=self.setup_case([1])
        for result in [{'outcome':'OK','sum_decimal':'01','count':1}, {'outcome':'OK','sum_decimal':'1','count':True}, {'outcome':'OK','sum_decimal':1,'count':1}]:
            r=execute(spec,payload,'scalar-exact-v1','a1'); r['result']=result; r['result_sha256']=sha256(canonical(result))
            with self.subTest(result=result), self.assertRaises(ContractError): verify_result(spec,payload,r)


if __name__ == '__main__':
    unittest.main()
