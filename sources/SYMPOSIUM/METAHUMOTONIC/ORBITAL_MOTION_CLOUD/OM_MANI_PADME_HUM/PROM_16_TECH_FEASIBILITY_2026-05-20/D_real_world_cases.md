# Axis D — Real-world cases

> Mirror / Lens / Farcaster / Friend.tech / BitClout/DeSo / Steemit

## D1 — Protocol docs

**Web3 creator-economy 측 옴마니반메훔 axis 별 isolation cover**:
- Lens = social graph + collect NFT
- Mirror = writing/subscription NFT
- Friend.tech / DeSo = bonding-curve coin
- Farcaster = hub + Frame interaction
- **No single protocol unifies 4글자**

**가장 가까운 unification = Lens V2** (Profile + Collect + Follow + Open Actions) 측 3 of 4 axes natively cover. 기-axis (bonding curve) 측 external module bolt-on.

**4글자 매핑**:
- 만 = FollowNFT contract (per-profile, DAO-capable voting/delegation) + Farcaster Hub mass-storage of casts/links
- 옴 = Mirror Writing NFT (Arweave-anchored, minimal mint, seed publication) OR Lens Post→Collect
- 이 = Lens Collect Module (collector mints NFT linked to publisher's ContentURI = explicit creator↔collector edge) + Open Actions
- 기 = Friend.tech quadratic bonding curve (price = supply²/16000 ETH, non-transferable keys) OR DeSo Creator Coin (locked-treasury AMM)

**🔴 Genuine gap (S03)**: **mantra-repetition semantic (recursive utterance accumulating merit)** 측 모든 surveyed protocol 측 absent. 현 bonding curve 측 *scarcity* price, *repetition-as-merit* primitive 측 없음.

**Confidence**: MEDIUM

## D2 — Case studies

**3 stack production-tested 측 reuse 가능**:

| Layer | Production case | 정량 |
|---|---|---|
| 옴 (bonding curve) | Friend.tech P=S²/16000 quadratic curve | 100th key $62.5 / 200th $250 verified |
| 이/기 (revenue split) | Mirror Writing NFT 측 2.5% platform + 97.5% creator + referrer/first-collector | 700+ ETH paid 2023 |
| 만 (distribution) | Farcaster Frames v1 in-cast embedded action | 400% DAU surge 5k → 24.7k 1주, 2k unique users in 48h Facebreaker |

**Anti-pattern**: BitClout V1 doubling-per-1M bonding curve 측 insider front-running failure (V2 측 order-book 측 retreat) = 옴마니반메훔 측 reference.

**3-layer reuse-ready stack**:
1. 옴 = Friend.tech quadratic curve **fork** (P=S²/k, k tunable, default 16000 Base-deployed) on L2 (Base/Optimism). **BitClout V1 lesson 측 mandatory order-book escape after stake threshold N** (e.g. 256 keys) 측 prevent insider capture
2. 이/기 = Lens v2 Collect Module pattern (`UpdatableOwnableFeeCollectModule`, `AuctionCollectModule`). 97.5/2.5 Mirror split + 1st-collector + referrer bonus
3. 만 = Farcaster Frame v2 mini-app fork. 검색 결과 측 in-cast embedded action

DAO governance = Snapshot off-chain voting (gasless, <10% turnout default expected, 100+ voter active threshold).

**Confidence**: HIGH

## D3 — Failure modes

**5 cross-platform converging failure**:

| # | Failure | Case |
|---|---|---|
| F1 | **Speculation-over-utility death spiral** | Friend.tech revenue $2M/day Sep23 → $2K/day Aug24 (-99%) once token greed exhausted, FRIEND -98%, team cashed 19,477 ETH ($52M). BitClout creator coin pump-dump, no BTCLT→BTC exit liquidity |
| F2 | **Founder/whale custody asymmetry** | Steemit centralized stake → Justin Sun (Tron Feb20) coordinated exchanges to swap witnesses → forced Hive hard-fork exodus Mar20. On-chain governance worthless if token concentration + CEX collusion |
| F3 | **Decentralization cost curve** | Farcaster Hub full-replication projected $3.5K → $45K → $575K → $6.9M /operator at 5% WoW growth. Without incentive layer, hub operators evaporate, full-replication asymptotically infeasible >~100 hubs |
| F4 | **Migration combinatorics** | Lens v1→v2 needed ~20M txs and surfaced 2 critical bugs (handle-collision frontrun bricking, self-follow via tryMigrate, follow-NFT frontrun-transfer attack). State-migration = P0 attack surface |
| F5 | **Consent/scraping violations** | BitClout auto-minted profiles for non-consenting Twitter users → killed legitimacy before product-market fit |

**옴마니반메훔 측 5 mandatory 회피**:
- a. **No speculative token at launch** — utility-credits or non-transferable points only. Token after Sticky DAU plateau ≥6mo
- b. Founder/team vesting ≥4yr cliff + on-chain dump-rate cap ≤1% supply/quarter
- c. Stake-cap + multi-sig recovery (no single entity >5% governance, witness/validator rotation with social-recovery override)
- d. Sharded/sub-graph replication from day 1 (Farcaster retrofit)
- e. Opt-in only profile creation + migration-rehearsal harness (Code4rena-style audit + adversarial frontrun simulation on testnet fork)

**Confidence**: HIGH (Farcaster + Lens v2 = alive, included for cost-curve and migration-bug lessons not as failures)

## D4 — Quantitative comparison

**5 ref protocol 비대칭 성과 (2026-05 snapshot)**:

| Protocol | DAU/MAU | Revenue | Key metric |
|---|---|---|---|
| **Farcaster** | DAU 40-60k / MAU 250k (2025-12) / power-badge real 4,360 | $2.8M cumulative protocol revenue / Pro $120/yr 첫 10k 6시간 매진 $1.2M | 0.2 DAU/MAU < healthy 0.3-0.4. **cube-root weighting** anti-gaming. 100% Pro→creator pool redistribution |
| **Friend.tech** | hourly active 4,700 → <600 10일내 (10x decay) | peak $1M/day fees Sep23 → $21/30day Sep24 (**99.9% decline**), $44M creator walkout | linear bonding curve 50/50 pump-dump |
| Lens Protocol | V2 mainnet 2025-04, 8 client (Lenster/Phaver/Lensta 분산) | 정량 opacity, $15M Polygon-based raise | multi-app ecosystem, single-client capture immune |
| Mirror.xyz | Paragraph merger | creator-revenue unpublished | silent pivot, not collapse |
| BitClout/DeSo | post-relaunch metric 미검증 | SEC dismissal Mar 2026, V2 Creator Coins relaunch | legal overhang 해소 |

**Sustainability 결정 요인**:
1. Anti-Sybil reward distribution math — Farcaster cube-root vs Friend.tech linear bonding curve
2. Revenue redistribution % — Farcaster 100% Pro→creator pool vs Friend.tech 50/50 pump-dump
3. DAU/MAU stickiness — Farcaster 0.2 mediocre vs Friend.tech <0.05 collapse

**가장 가까운 ref = Farcaster** (protocol-layer + multi-client + Pro subscription redistributive, NOT speculative bonding).

**Mimic 권장 5 metric**:
- DAU/MAU ≥ 0.3 (Farcaster 0.2 미달 능가 target)
- Cube-root reward weighting (Farcaster anti-gaming math)
- 100% subscription → creator-pool redistribution (Friend.tech 50/50 반대)
- Power-badge or equivalent quality-engagement metric (DAU 표면수치 < real engagement 4,360/60,000 = 7.3% 측 정직 공시)
- Protocol revenue per MAU ≥ $15 (Farcaster $11.2 baseline)

**Reject**: Friend.tech bonding curve (99.9% decay 증명), BitClout speculative creator-coin.

**Confidence**: MEDIUM (Lens/Mirror/DeSo 정량 metric 측 official dashboard opacity. Friend.tech vs Farcaster 측 동일 시점 cross-section 비교 impossible — life-cycle stage 별 비교 필수)
