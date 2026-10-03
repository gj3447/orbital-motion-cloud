# Axis C — Cold start + sustainability

> 학문 이론 + Friend.tech post-mortem + attack vectors + benchmarks

## C1 — 학문 이론

**옴 가치 = 정보 가치 × 옴 사용자 수** 측 **self-referential**.
→ Rochet-Tirole (2003) chicken-egg two-sided market 표준 실패 모드.
→ Markus (1987) critical mass theory 측 reciprocal interdependence + public good non-excludability.
→ Caillaud-Jullien (2003) 측 비배타 multi-homing 측 winner-take-all.

**🔴 자기-언급 finding**: 사용자 본인 영상 측 비판한 *암호화폐 차익률 = 차익률 순환논증* 측 옴 자기 측 *정보가치 = 옴 사용자 수* 측 동일 trap.

**3-stage hybrid bootstrap 권장**:
1. **Divide-and-Conquer subsidization** (Caillaud-Jullien 2003) — 한 측 (info contributor) negative price (subsidy / retro airdrop) 후 dividend-recipient monetize
2. **External Anchor via call-option airdrop** (Fan et al. 2025 arxiv 2503.14316) — 정보 가치 외부 oracle (학술 cite count / sha256 timestamping / DOI) 측 self-ref 깨고 exogenous floor
3. **ve-lock commitment** (Curve veCRV 2020) — 4-year vote-escrow 측 long-term holder 측 voting power grant 측 sell-pressure 흡수

Sybil 측 transaction-graph clustering + minimum holding period gate.

**Mandatory precondition**: "정보 가치 measurement function" 측 외부 binding spec.

**Confidence**: HIGH

## C2 — Friend.tech post-mortem

**Root causes (5)**:

| # | Cause | Quantitative |
|---|---|---|
| R1 | Ponzi bonding curve (P=S²/16000) — 신규 유입 cease 시 collapse | deposits $52M → $4M (92% drop Oct23→Sep24) |
| R2 | Token-gated chat retention 부재 — 인플루언서 1회 dump 후 dormant | daily fees $2M → <$100 (4-order magnitude) |
| R3 | V2/FRIEND airdrop botched — 95% users claim 실패, whale Murphys1d 55K dump | 50% intraday crash, 98% from launch |
| R4 | Dev abandonment — Racer/Shrimp 측 contract ownership null transfer, $44M fee walkaway, social silent | $44M creator walkaway |
| R5 | Single-mechanic novelty trap — 8개월간 "clubs" 1 feature 측 stagnation | feature velocity 0 |

**옴마니반메훔 측 회피 mandatory**:
- (a) Token-gated reward = recurring utility (정보 freshness / productive cashflow). bonding curve speculation-only 절대 금지
- (b) 다단계 정보 공유 측 cohort 별 token vesting + early-exit penalty (whale dump buffer)
- (c) Founder = multi-sig + dev fund vesting cliff (24mo+) + on-chain commitment (reputational hostage)
- (d) Retention metric = daily-active-engagement (not TVL). Friend.tech TVL hype 측 1차 metric trap
- (e) Feature velocity ≥ 1 substantive update/month

**Confidence**: HIGH

## C3 — Attack vectors

**옴마니반메훔 cold-start (holder N 작음 + ≥50% + 다단계 양도) 측 4 attack 동시 노출**:

| Attack | Vector |
|---|---|
| Sybil flooding | 10+ wallet 측 1 actor trivial. N<50 시 attacker 측 majority capture ~$0 cost |
| Flash-loan governance capture | Beanstalk 2022 $182M (1 block delay 부재 측 vulnerability). 옴 transferable 시 동일 attack surface |
| Voter apathy × low quorum | DAO turnout <10% mean (Uniswap 4% quorum, 2-3% turnout). ≥50% threshold 측 sleeping holders default-NO/abstain 측 5% active cartel 측 capture |
| Information asymmetry | early 옴 holder 측 access-right hoarding 측 cold-start phase insider monopoly 결정화 |

**4-layer defense mandatory before launch**:
- D1: **Proof-of-Personhood gate** (Worldcoin/BrightID/Gitcoin Passport) 측 옴 mint prerequisite — Sybil cost raise
- D2: **Soulbound (SBT)** 또는 양도 시 2-phase commit + N-block delay (Beanstalk flash-loan attack 차단)
- D3: ≥50% threshold = **"absolute majority of total"** (not active denominator) — voter apathy capture 차단
- D4: Cold-start phase (N<100) 측 founder multisig emergency veto + 정보 접근권 transparency audit log (insider hoarding 가시화)

추가: 다단계 양도 측 N-hop limit + per-hop time decay 측 cartel formation 차단.

**Confidence**: HIGH

## C4 — Benchmarks

**SocialFi cold-start empirical pattern**:

| Project | Trajectory |
|---|---|
| Friend.tech | 539K tx/day → 2.4K in 3mo = **99.5% decay** |
| Farcaster | DAU 100K → 60K in 14mo, DAU/MAU 0.2 (< healthy 0.3-0.4) |
| Lens Protocol | 650K accounts → 20K DAU = 3.1% activation |
| BitClout | 250K MAU peak → 94% creator coin collapse |

**Failure modes**:
- FOMO-driven token speculation without utility loop → time-to-half-DAU = 3-6 months from peak
- Reward-incentivized acquisition produces mercenary users (CAC $500-1000 for poor airdrops vs DeFi baseline $85, Web3 CAC 3-7x Web2)
- Metcalfe n² empirically validated (Tencent/Facebook 2013-2015), Reed's 2^n **never observed** → group-forming value bounded by n²

**Minimum sustainability gate (5/5)**:

| Gate | Threshold |
|---|---|
| DAU floor | ≥ 5,000 genuinely-engaged (Farcaster Power Badge 4,360 + safety) |
| DAU/MAU ratio | ≥ 0.25 (healthy 0.3-0.4, spiritual/weekly 0.15-0.20 acceptable) |
| Active recurring channels | ≥ 50 contributors (Mantra 108 bead round-down) |
| CAC + ARPU | CAC ≤ $50/user AND ARPU ≥ $5/month sustained 6+mo → payback ≤ 10mo |
| Time-to-half-DAU | > 12 months from peak (Friend.tech 3mo vs Farcaster 14mo = 4.7x survival differential) |

**Composite**: 5/5 sustainable / 3-4/5 monitored / ≤2/5 degenerating (Lakatos).

**Confidence**: MEDIUM (옴마니반메훔 spiritual/contemplative positioning 측 SocialFi financial-speculation baseline 측 direct comparable 불확실)
