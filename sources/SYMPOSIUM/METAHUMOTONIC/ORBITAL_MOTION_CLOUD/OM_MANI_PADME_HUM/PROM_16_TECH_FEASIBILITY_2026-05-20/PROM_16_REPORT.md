# PROM 16 — 옴마니반메훔 기술 feasibility 종합 보고서

> 4×4 = 16 cell. 16/16 subagent finding 수확. Consensus 14건 / Conflict 0건 / Singleton 3건.
> Cycle: `prom16-ommanibanmehoom-tech-feasibility-2026-05-20`

## 0. 사전 지식

- 사용자 라경준 본인 design (영상 `pWIINh4TlHk`, "눈물이 납니다...")
- 4 글자 4 기능: 만(인스타 해시태그) / 옴(NFT 1:1 unique info coin) / 이(read 구독권) / 기홈(write 구독권)
- 핵심: P2P + NFT-1:1 mining + fractional 양도 + ≥절반 승인 governance + R/W 구독 + revenue share
- 법적 제외 (사용자 verdict 2026-05-20)

## 1. Consensus (14 themes)

### 🔴 C03 STRONGEST (5 findings agree)
**Friend.tech bonding curve speculation-only = 99.9% decay 증명. utility loop + recurring income mandatory.**

5 finding 만장일치: Friend.tech (deposits $52M→$4M, fees $2M/day→$2K/day, FRIEND -98%) + BitClout 측 다 fail. → utility-credits launch only, speculative token 측 Sticky DAU ≥6mo 후 도입.

### HIGH consensus (3 findings each)

| ID | Theme | Support |
|---|---|---|
| **C01** | L1 ETH 비현실, L2 (Polygon/zkSync/Base) 측 only economically feasible | A4, B4, D2 |
| **C02** | 순수 P2P 불가, hybrid (L1 coin + IPFS+Filecoin + centralized verifiable indexer) mandatory | A3, A4, B2 |
| **C05** | Fractional NFT (Tessera) production fail — NFT 1:1 only OR ERC-1155 share 직접 발행 | B1, B2, B3 |
| **C11** | 가장 가까운 ref = Lens V2 + Farcaster + Mirror hybrid (NOT Friend.tech/BitClout) | D1, D2, D4 |
| **C12** | 만 = Farcaster Frame mini-app + 측 centralized verifiable indexer (The Graph + Algolia mirror) | A1, A3, D1 |

### MEDIUM consensus (2 findings each)

| ID | Theme | Support |
|---|---|---|
| C04 | ≥50% governance flashloan vulnerable — Soulbound (SBT) + PoP + N-block delay | B3, C3 |
| C06 | Cold start self-ref 해결 = 외부 anchor + subsidy + ve-lock | C1, C2 |
| C09 | Founder vesting ≥4yr cliff + multi-sig + on-chain dump-rate cap ≤1%/quarter | C2, D3 |
| C10 | NFT royalty marketplace enforce NOT trust — on-chain transfer hook only | B2, B3 |
| C13 | 이/기 R/W subscription = Unlock Protocol + Lit Protocol access control | B1, B2 |
| **C14** | **사용자 본인 차익률 순환 비판 측 옴 자기 동일 trap (정보가치=옴사용자수 self-ref)** — 자기-언급 인정 | C1, C2 |

### 단일 cell consensus (1 finding)

| ID | Theme | Cell |
|---|---|---|
| C07 | Sustainability 5/5 gate: DAU≥5K + DAU/MAU≥0.25 + ≥50 channel + CAC≤$50 + time-to-half>12mo | C4 |
| C08 | DRM analog hole = leak-proof 불가, watermark + social norm 수준 | B3 |

## 2. Conflicts

**0건.** 표면적 ref protocol divergence (Lens V2 vs Farcaster vs Friend.tech-style) 측 *complementary* (다른 axis cover). NFT-1:1 only vs ERC-1155 fractional 측 trade-off, contradiction 아님.

## 3. Singletons (low-confidence, 단일 cell 측 surface)

| ID | Theme | Cell |
|---|---|---|
| S01 | Steemit Justin Sun founder dump → Hive hard-fork exodus | D3 |
| S02 | BitClout 측 consent violation auto-mint non-consenting Twitter users | D3 |
| **S03** | **Mantra-repetition semantic (recursive utterance accumulating merit) — 모든 surveyed protocol 측 absent. genuine gap.** | D1 |

S03 측 *옴마니반메훔 측 unique novel design space* — 현 bonding curve 측 *scarcity* price, *repetition-as-merit* primitive 측 없음.

## 4. Open Questions

| Q | 질문 | 비고 |
|---|---|---|
| Q1 | 만트라 반복-as-merit primitive 측 어떻게 design? (S03) | novel research direction |
| Q2 | "정보 가치" 외부 oracle 측 어떻게 구현? (학술 cite count / sha256 / DOI / human curation) | C06+C14 측 unblock 측 mandatory |
| Q3 | 다단계 정보 공유 측 graph topology (DAG/tree/free)? attack surface 측 topology-dependent | C3 측 D2 unblock |
| Q4 | Lens V2 / Farcaster / Mirror 측 어떤 layer 측 fork, 어떤 측 use-as-is? | D1+D2 측 production deploy decision |
| Q5 | "이/기 read/write 분리" 측 사용자 design 측 *왜* — strict R/W separation 측 token-gated content 측 의미 | C08 측 DRM analog hole 측 leak 회피 의도? |

## 5. 권장 stack (consensus 기반 reference architecture)

**ActionPlan**: `plan-omc-tech-reference-architecture-2026-05-20` (FUTURE/MEDIUM)

| Layer | 권장 |
|---|---|
| Chain | Polygon PoS or zkSync Era (L1 ETH 측 NOT) |
| 옴 (NFT) | ERC-721 1:1 mining (BAYC pattern). fractional 측 abandon (Tessera 실패) |
| 만 (hashtag) | Farcaster Frame mini-app + The Graph subgraph + Algolia mirror (centralized verifiable indexer) |
| 이 (read 구독) | Unlock Protocol PublicLock (Forbes ads-free 측 verified) |
| 기홈 (write) | Unlock write-gated + Lit Protocol encryption ($422M AUM) |
| Revenue share | 0xSplits / Manifold on-chain enforced + Merkle distributor pull-payment |
| Governance | Soulbound (SBT) + PoP (Worldcoin/BrightID/Gitcoin Passport) + 2-phase commit + N-block delay + absolute majority of total |
| Cold start | divide-conquer subsidy + 외부 정보-가치 oracle (Q2 측 design 후) + ve-lock 4-year |
| Founder | 4-year vesting cliff + dump-rate cap ≤1%/quarter + multi-sig + no entity >5% governance |
| Launch | utility-credits only, speculative token 측 Sticky DAU ≥6mo 후 |
| Storage | IPFS + Filecoin ≥3 pinning provider |
| Sustainability gate | DAU≥5K + DAU/MAU≥0.25 + ≥50 channel + CAC≤$50 + time-to-half>12mo |

## 6. Crystallized seeds (9)

| Priority | Name | Theme |
|---|---|---|
| **CRITICAL** | `seed-omc-no-speculation-bonding-curve-2026-05-20` | C03 — utility loop mandatory |
| HIGH | `seed-omc-L2-mandatory-2026-05-20` | C01 |
| HIGH | `seed-omc-hybrid-substrate-2026-05-20` | C02 |
| HIGH | `seed-omc-governance-soulbound-pop-2026-05-20` | C04 |
| HIGH | `seed-omc-no-fractional-tessera-2026-05-20` | C05 |
| HIGH | `seed-omc-cold-start-external-anchor-2026-05-20` | C06+C14 |
| HIGH | `seed-omc-founder-vesting-2026-05-20` | C09 |
| HIGH | `seed-omc-on-chain-royalty-enforce-2026-05-20` | C10 |
| HIGH | `seed-omc-ref-stack-lens-farcaster-mirror-2026-05-20` | C11+C12+C13 |

## 7. 가장 honest 한 줄

**기술적으로는 가능.** 모든 primitive 측 production-ready. 단:
- 사용자 본인 비판한 *차익률 순환논증* 측 옴 자기 측 *정보가치=옴사용자수 self-ref* 측 동일 trap (C14 자기-언급 인정)
- Friend.tech 측 99.9% decay 측 *speculation-only* 모델 측 reference case
- **utility loop + 외부 정보-가치 oracle + founder commitment** 3가지 측 사용자 design 측 OR 측 implementation 측 *해결되지 않음 시* 같은 운명
- **mantra-repetition primitive** 측 surveyed 모든 protocol 측 absent = novel research direction (S03)

— AI 측 build-or-not propose 자제. 결정 측 사용자 sole authority. 열린 채로.
