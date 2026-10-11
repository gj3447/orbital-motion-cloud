"""K01 research prototype: bounded pure integer task and independent result check.

No network, placement, subprocess execution, result publication or reward writes.
The functions are trusted local code; metadata is not authentication or a sandbox.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import struct

MIN_I64, MAX_I64 = -(1 << 63), (1 << 63) - 1
MAX_ITEMS = 65536
HEADER = b'OMCI64\x00\x01'
DEFINITION_PATH = Path(__file__).with_name('contract.json')
DEFINITION_SHA256 = 'c5f9acbbfa57a0c93133d05df5dc4bc440dce03cc825ab8a6208d881b3fd7cd2'
if hashlib.sha256(DEFINITION_PATH.read_bytes()).hexdigest() != DEFINITION_SHA256:
    raise RuntimeError('Contract definition changed; implementation review and explicit revision required')
CONTRACT_UID = 'omc:workload:sum-i64-exact'
SUPPORTED_VARIANTS = ('scalar-exact-v1', 'chunked-exact-v1')
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9:._-]{0,127}\Z')


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('ascii')
    except (TypeError, ValueError) as exc:
        raise ContractError('canonical JSON value required') from exc


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def artifact_digest():
    return sha256(Path(__file__).read_bytes())


def encode_input(values):
    require(type(values) is list and len(values) <= MAX_ITEMS, 'bounded list required')
    require(all(type(v) is int and MIN_I64 <= v <= MAX_I64 for v in values), 'signed int64 values required; bool/float rejected')
    return HEADER + struct.pack('<I', len(values)) + b''.join(struct.pack('<q', v) for v in values)


def decode_input(payload):
    require(type(payload) is bytes and 12 <= len(payload) <= 12 + 8*MAX_ITEMS, 'payload bounds/type')
    require(payload[:8] == HEADER, 'input encoding revision')
    count = struct.unpack('<I', payload[8:12])[0]
    require(count <= MAX_ITEMS and len(payload) == 12 + 8*count, 'count or trailing/truncated bytes')
    return tuple(v[0] for v in struct.iter_unpack('<q', payload[12:]))


def make_spec(workload_uid, payload):
    require(type(workload_uid) is str and TOKEN.fullmatch(workload_uid), 'workload UID')
    values = decode_input(payload)
    return {'schema':'omc-workload-spec/1', 'workload_uid':workload_uid,
            'contract_uid':CONTRACT_UID, 'contract_revision':1,
            'definition_sha256':DEFINITION_SHA256, 'model':'TASK', 'effect':'PURE',
            'input_encoding':'omc-i64le/1', 'input_sha256':sha256(payload), 'input_items':len(values)}


def validate_spec(spec, payload):
    require(type(spec) is dict, 'spec object')
    expected = make_spec(spec.get('workload_uid'), payload)
    # Byte comparison also rejects bool-as-int, added fields and non-integer revisions.
    require(canonical(spec) == canonical(expected), 'spec contract/input mismatch')
    return decode_input(payload)


def semantic_digest(spec):
    return sha256(canonical(spec))


def outcome(total, count):
    if not MIN_I64 <= total <= MAX_I64:
        return {'outcome':'DOMAIN_ERROR', 'code':'SUM_OUT_OF_I64_RANGE'}
    return {'outcome':'OK', 'sum_decimal':str(total), 'count':count}


def scalar_exact(values):
    total = 0
    for value in values:
        total += value
    return outcome(total, len(values))


def chunked_exact(values, chunk_size):
    # Partial sums stay unbounded: a chunk can overflow int64 while the final sum fits.
    total = sum(sum(values[i:i+chunk_size]) for i in range(0, len(values), chunk_size))
    return outcome(total, len(values))


def oracle(values):
    """Independent grouping by multiplicity, using exact Python integers."""
    total = sum(value * count for value, count in Counter(values).items())
    if MIN_I64 <= total <= MAX_I64:
        return {'outcome':'OK', 'sum_decimal':str(total), 'count':len(values)}
    return {'outcome':'DOMAIN_ERROR', 'code':'SUM_OUT_OF_I64_RANGE'}


def execute(spec, payload, variant, attempt_uid, *, chunk_size=32):
    values = validate_spec(spec, payload)
    require(variant in SUPPORTED_VARIANTS, 'unregistered variant')
    require(type(attempt_uid) is str and TOKEN.fullmatch(attempt_uid), 'attempt UID')
    require(type(chunk_size) is int and 1 <= chunk_size <= MAX_ITEMS, 'chunk bounds')
    result = scalar_exact(values) if variant == 'scalar-exact-v1' else chunked_exact(values, chunk_size)
    return {'schema':'omc-result-candidate/1', 'semantic_sha256':semantic_digest(spec),
            'input_sha256':sha256(payload), 'definition_sha256':DEFINITION_SHA256,
            'variant':variant, 'artifact_sha256':artifact_digest(), 'attempt_uid':attempt_uid,
            'execution':{'chunk_size':chunk_size} if variant == 'chunked-exact-v1' else {},
            'result':result, 'result_sha256':sha256(canonical(result))}


def verify_result(spec, payload, candidate, *, cancelled=False):
    """Checks a candidate, not durable single-result commitment or authenticity."""
    require(type(cancelled) is bool and not cancelled, 'cancelled or invalid cancellation state')
    values = validate_spec(spec, payload)
    fields = {'schema','semantic_sha256','input_sha256','definition_sha256','variant',
              'artifact_sha256','attempt_uid','execution','result','result_sha256'}
    require(type(candidate) is dict and set(candidate) == fields, 'candidate fields')
    require(candidate['schema'] == 'omc-result-candidate/1', 'candidate schema')
    require(candidate['semantic_sha256'] == semantic_digest(spec), 'wrong workload identity')
    require(candidate['input_sha256'] == spec['input_sha256'], 'wrong input identity')
    require(candidate['definition_sha256'] == DEFINITION_SHA256, 'wrong definition')
    require(candidate['variant'] in SUPPORTED_VARIANTS and candidate['artifact_sha256'] == artifact_digest(), 'unregistered artifact')
    require(type(candidate['attempt_uid']) is str and TOKEN.fullmatch(candidate['attempt_uid']), 'attempt identity')
    settings = candidate['execution']
    if candidate['variant'] == 'scalar-exact-v1':
        require(settings == {}, 'scalar settings')
    else:
        require(type(settings) is dict and set(settings) == {'chunk_size'}, 'chunked settings')
        require(type(settings['chunk_size']) is int and 1 <= settings['chunk_size'] <= MAX_ITEMS, 'chunk bounds')
    require(candidate['result_sha256'] == sha256(canonical(candidate['result'])), 'result bytes changed')
    # Matching a self-reported hash alone is insufficient; validate the result semantics.
    require(canonical(candidate['result']) == canonical(oracle(values)), 'result violates contract')
    return True
