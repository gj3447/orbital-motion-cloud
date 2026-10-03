# Axis B — Token primitives

> ERC-721/1155/2981 + Tessera + Unlock + Lit + PaymentSplitter

## B1 — 공식 docs

**4글자 → 5 contract stack**:
- 옴 = ERC-721 + ERC-2981 royalty (contract-address + tokenId globally unique)
- 마 (fractional) = Tessera FERC1155 vault (ERC-721 deposit → ERC-1155 fractional, 100% buyout-redeem)
- 니/반 (read) = Unlock PublicLock NFT-membership (expiration-based recurring, balanceOf=true read-gate, 옴 holder allowlist)
- 메/훔 (write+revenue) = Lit Protocol ACC encryption (write-gate: 옴 holder publishes encrypted, decryption key released to PublicLock holder) + OZ PaymentSplitter (pull-model split)

**Gap**: ERC-2981 marketplace voluntary / Tessera 측 permission module 커스텀 / fractional holder 측 read-gate 자동 propagation 부재.

**Confidence**: HIGH

## B2 — Production cases

| Project | Outcome |
|---|---|
| BAYC / CryptoPunks | 4년 floor 90% drawdown — unique 1:1 가능하나 speculative volatility dominant |
| **Tessera/Fractional** | **2023-05 shutdown** (Paradigm $20M backed, Andy Chorlian: "targets to profitability didn't add up") |
| Unlock Protocol (Forbes ads-free) | **working production** — Guardian fund invested, time-bound NFT membership transferable on OpenSea |
| Lit Protocol | $422M AUM + 587,500 Lit Action requests Q4 2024 (107% QoQ) + 70+ projects + 7,000 agent wallets 2025 |
| **Friend.tech** (token-gated chat) | 2024-04 v2 → 2024-09 contract null address, deposits $52M → $4M crash, $44M creator walkaway |
| Aave dividend | 2025 $50M annual buyback, weekly $250k-$1.75M, GHO 50/20 split, sGHO 265M staked |
| OpenSea royalty | **2024-03 enforcement abandon** (Blur royalty-free 측 volume overtake 압력) |

**Verdict**: 옴마니반메훔 stack = ERC-721 (BAYC pattern) + Unlock fork (subscription) + Lit Protocol (access) + Aave staking pattern (revenue).
**CRITICAL**: fractional layer 측 NOT recommend (Tessera precedent + Paradigm $20M sunk).
Royalty 측 marketplace 측 NOT trust — on-chain ERC-721 `_beforeTokenTransfer` override 측 only durable.
Social token-gated chat (Friend.tech) 측 avoid — speculation volatility 측 retention kill.

**Confidence**: HIGH

## B3 — Pitfalls

**6 fatal pitfalls**:

| # | Issue | Reference |
|---|---|---|
| P1 | ERC-2981 royalty marketplace opt-in (Blur Seaport bypass) | OpenSea Operator Filter 2023 폐기 |
| P2 | Tessera/Fractional shutdown 2023-05 — Paradigm-backed, secondary market 측 economic unviability | Tessera shutdown announcement |
| P3 | **Beanstalk 2022-04 $182M flashloan governance attack** — 즉시-투표 token-weighted DAO 측 51% 측 single-tx trivial | Beanstalk hack analysis |
| P4 | DRM analog hole — 화면-카메라 leak 차단 불가, industry consensus 측 100% leak-proof 불가능 | Watermark deterrent only |
| P5 | Reentrancy on dividend (DAO 2016, Lendf.Me 2020, BurgerSwap 2021, Orion 2023) | pull-payment 미적용 시 |
| P6 | ETH L1 gas $5-50/tx — 소수점 1/1000 NFT 양도 economic floor | Micro-fractional 불가 |

**가장 치명적** = **P3** (token-weighted ≥절반 승인 측 flashloan governance takeover).

**Mitigation 4-layer**:
- M1: Revenue share = on-chain protocol-enforced split (Manifold / 0xSplits) + L2 settlement
- M2: Fractional 측 ERC-1155 share token 직접 + 자체 AMM, 또는 NFT 1:1 only
- M3: Governance = (a) 1 NFT = 1 vote quadratic + (b) 24-72h timelock + (c) Snapshot off-chain + (d) Worldcoin/Gitcoin Passport
- M4: Token-gated content = "access guarantee 아닌 community ritual" reframing — DRM 약속 회수, watermark + social norm

**Confidence**: HIGH

## B4 — Benchmarks

**Economic threshold**:
- L1 ETH 측 옴마니반메훔 4-layer = **modal collapse** (옴 mint $15-50, 100-holder distribution gas $30-100+, sustainability 0)
- L2 (Polygon/zkSync/Arbitrum/Base) 측 NFT mint <$0.10 (90-99% gas reduction) + ERC-1155 batch 80-90% gas saving + Merkle distributor (recipient-pays-claim) + Unlock gasless on Polygon/Gnosis (Unlock Labs covers gas)

**권장**:
- PRIMARY chain = Polygon PoS or zkSync Era
- 옴 ERC-721 on Polygon (~$0.003/mint) or zkSync (~$0.05)
- 소수점 양도 = ERC-1155 vault wrapper (80-90% gas savings)
- R/W 구독 = Unlock on Polygon (gasless via Unlock Labs sponsorship)
- Revenue share = Merkle distributor (distributor $0.10-1 to post root, claimant $0.05)
- **Economic threshold**: 옴 unit price > $5 to amortize 1 mint + 1 claim + 1 royalty cycle on L2 (vs $200 break-even on L1)
- **DO NOT deploy on Ethereum L1**

**Confidence**: HIGH
