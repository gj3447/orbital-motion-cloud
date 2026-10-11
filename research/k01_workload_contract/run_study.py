"""Finite, reproducible K01 correctness study; not a placement/performance benchmark."""
import argparse
import datetime
import itertools
import json
import platform
import random
import sys
from pathlib import Path

from workload import (ContractError, DEFINITION_SHA256, MAX_I64, MIN_I64,
                      canonical, encode_input, execute, make_spec, oracle,
                      outcome, sha256, verify_result)

SEED = 20261011
HERE = Path(__file__).resolve().parent


def corpus():
    # Exhaustive only over this small alphabet/length, not over the int64 domain.
    for size in range(6):
        for row in itertools.product([-2,-1,0,1,2], repeat=size):
            yield 'finite-alphabet', list(row)
    for row in [[MAX_I64,1,-1],[MIN_I64,-1,1],[MAX_I64,1],[MIN_I64,-1],
                [1<<53,1],[MAX_I64,MAX_I64,-MAX_I64],[MIN_I64,MAX_I64],
                [MAX_I64,1,MIN_I64],[0]*65536]:
        yield 'boundary', row
    rng = random.Random(SEED)
    for _ in range(200):
        yield 'seeded', [rng.randint(MIN_I64,MAX_I64) for _ in range(rng.randrange(257))]


def run():
    digest = __import__('hashlib').sha256()
    count = verified = permutations = 0
    groups = {}
    for group, values in corpus():
        payload = encode_input(values)
        # Length-prefix the concatenation to identify the ordered finite corpus.
        digest.update(len(payload).to_bytes(4,'little')); digest.update(payload)
        spec = make_spec('workload:case-'+str(count),payload)
        candidates = [execute(spec,payload,'scalar-exact-v1','a0')]
        candidates += [execute(spec,payload,'chunked-exact-v1','a'+str(c),chunk_size=c) for c in [1,2,7,64]]
        for candidate in candidates:
            assert verify_result(spec,payload,candidate)
            verified += 1
        if group != 'finite-alphabet':
            other=encode_input(list(reversed(values)))
            other_spec=make_spec('workload:permuted-'+str(count),other)
            r=execute(other_spec,other,'chunked-exact-v1','permuted',chunk_size=7)
            assert verify_result(other_spec,other,r)
            assert r['result']==candidates[0]['result']
            # Value equality is not a license to merge input/request identities.
            permutations += 1
        count += 1; groups[group]=groups.get(group,0)+1

    def strict_partial(values):
        total=0
        for v in values:
            total += v
            if not MIN_I64 <= total <= MAX_I64:
                return {'outcome':'DOMAIN_ERROR','code':'SUM_OUT_OF_I64_RANGE'}
        return outcome(total,len(values))

    mutants = [
        ('float-rounding',[1<<53,1],lambda v:outcome(int(sum(float(x) for x in v)),len(v))),
        ('wrapped-overflow',[MAX_I64,1],lambda v:outcome((sum(v)+(1<<63))%(1<<64)-(1<<63),len(v))),
        ('saturated-overflow',[MAX_I64,1],lambda v:outcome(min(MAX_I64,max(MIN_I64,sum(v))),len(v))),
        ('premature-partial-overflow',[MAX_I64,1,-1],strict_partial),
        ('dropped-element',[1,2,3],lambda v:outcome(sum(v[:-1]),len(v))),
    ]
    mutation_results=[]
    for name,values,fn in mutants:
        payload=encode_input(values); spec=make_spec('workload:mutation',payload)
        candidate=execute(spec,payload,'scalar-exact-v1','mutated')
        candidate['result']=fn(values)
        candidate['result_sha256']=sha256(canonical(candidate['result']))
        try:
            verify_result(spec,payload,candidate)
        except ContractError as exc:
            mutation_results.append({'name':name,'input_decimal':[str(v) for v in values],
                                     'wrong_result':candidate['result'],'expected':oracle(values),
                                     'rejected':True,'reason':str(exc)})
        else:
            raise AssertionError('Mutant escaped: '+name)

    # Explicit state-model counterexample, not a real network/DB fault test.
    count_without_dedup=0
    count_without_dedup += 1  # destination effect commits; response is lost
    count_without_dedup += 1  # caller repeats because it did not observe success
    effects, recorded = 0, set()
    for attempt in range(2):
        if 'operation:one' not in recorded:
            # This model assumes the update and key record form ONE atomic transition.
            effects += 1; recorded.add('operation:one')
    retry_model={'kind':'SIMULATED_STATE_TRACE','without_receiver_dedup':count_without_dedup,
                 'with_atomic_receiver_dedup':effects,
                 'assumptions':['effect and operation key commit atomically','same operation key across retry'],
                 'limitations':['no real RPC, durable storage, crash injection, concurrency or reward transaction tested']}
    assert count_without_dedup==2 and effects==1
    return {'schema':'omc-k01-study-result/1','authority':'SECONDARY_AI','state':'OBSERVED_LOCAL',
            'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'environment':{'python':sys.version,'implementation':platform.python_implementation(),'machine':platform.machine(),'system':platform.system()},
            'seed':SEED,'scope':'ONE_LOCAL_PYTHON_RUNTIME; CORRECTNESS_ONLY',
            'source_sha256':{p.name:sha256(p.read_bytes()) for p in [HERE/'workload.py',HERE/'contract.json',Path(__file__)]},
            'definition_sha256':DEFINITION_SHA256,'corpus_sha256':digest.hexdigest(),
            'input_cases':count,'groups':groups,'verified_candidates':verified,
            'permutation_checks':permutations,'chunk_sizes':[1,2,7,64],
            'mutants':mutation_results,'retry_model':retry_model,
            'outcome':'PASS','heterogeneous_hardware':'NOT_RUN','performance_comparison':'NOT_RUN',
            'distributed_single_result_commit':'NOT_IMPLEMENTED','untrusted_code_isolation':'NOT_IMPLEMENTED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New JSON record path; refuses to overwrite evidence.')
    args=parser.parse_args()
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['outcome','input_cases','groups','verified_candidates','permutation_checks','corpus_sha256']}))


if __name__=='__main__':
    main()
