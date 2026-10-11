# K01 local workload contract experiment

The [research note](../../docs/research/K01_WORKLOAD_CONTRACT.md) defines the supported scope and mathematical reasoning. This directory is a standard-library-only research fixture, separate from the operational placement CLI.

```sh
python3 -m unittest discover -s research/k01_workload_contract -p 'test_*.py' -v
python3 research/k01_workload_contract/run_study.py --output .local/k01-reproduction.json
```

The output path must not already exist. The study is finite and fixed: 4,115 inputs, five execution settings per input, 209 additional reversed-input checks and five targeted incorrect variants. It records the interpreter, architecture, seed and source/corpus digests. It does not run Ray, Kubernetes, a network worker, a hardware benchmark or reward transactions.

`verify_result` validates a candidate's locally checkable result. It provides no distributed commitment, authentication, remote execution attestation or sandbox for untrusted programs. The retry trace is an explicit state model with an assumed atomic receiver transition. Cancellation is a verifier input, not a durable cancellation service.
