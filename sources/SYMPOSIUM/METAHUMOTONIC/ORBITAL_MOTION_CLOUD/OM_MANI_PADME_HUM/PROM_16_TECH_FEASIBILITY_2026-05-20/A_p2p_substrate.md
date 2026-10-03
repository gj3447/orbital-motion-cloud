# Axis A — P2P substrate

> 4 cell: 공식 docs / production cases / pitfalls / benchmarks

## A1 — 공식 docs

**Mechanism**: content-addressing (CID multihash) + gossip pubsub + DHT + per-agent signed source chain (Holochain/Nostr NIP-01) + endowment-funded blob (Arweave/Filecoin deal).

**권장 stack 측 4글자 매핑**:
- 만 = Nostr NIP-01 kind:1 event + `#t` tag (NIP-12 generic + NIP-50 search), secp256k1 sig ~50μs verify
- 옴 = ERC-721 tokenURI 측 IPFS CID v1 (sha-256 multihash) + Arweave permanent mirror
- 이/기 = libp2p gossipsub topic ACL + Nostr NIP-42 AUTH + on-chain ERC-721 ownership gate
- fractional + ≥절반 = ERC-1155 + multisig / BLS threshold sig (FIP-0105)

**Caveats**: IPFS CID immutability ≠ availability (pinning 필수). Nostr relay 측 NIP-42 AUTH 측 mitigation. Arweave 200-year endowment 측 assumption-dependent. Holochain 측 ERC-721 호환 측 bridge 필요.

**Confidence**: HIGH

## A2 — Production cases

**6 substrate compared (2025-2026)**:
| Stack | 측정값 |
|---|---|
| BitTorrent DHT | 30일 IP 3.15M, 십수년 검증 |
| IPFS | Cloudflare gateway 1000+ req/s, gateway market $62.3M→$172M (2024-2032) |
| Filecoin | 3.0 EiB committed / 1110 PiB active / 35.2M deals (Q3 2025) |
| Nostr | 21K total / 3.7K DAU (strict) ~ 16M / 780K DAU (loose), 1005 relays |
| Mastodon/ActivityPub | 9856 instances / 9.96M total / 763K MAU |
| Holochain Holoport | production 진행 중, Holochain alpha 측 차단 |

**Verdict**: 옴마니반메훔 측 *public-post + broadcast + signed-event + relay-pluggable + monetization* 측 **Nostr 측 가장 close** (zaps = revenue primitive, NIP-99 paid content, signed event = 1:1 authorship). NFT 1:1 + fractional + ≥절반 governance 측 EVM/Cosmos L2 측 별도. Holochain alpha + Mastodon governance friction 측 NOT primary.

**Confidence**: HIGH

## A3 — Pitfalls / limits

**6 failure modes**:
1. IPFS pinning longevity (콘텐츠 garbage collection)
2. **Sybil attack** — 단일 컴퓨터 측 IPFS DHT 측 CID 접근 차단 가능 (arxiv 2505.01139, ACM 3664476.3664482). 완전 방어 불가 — 강한 identity (DID/PoH) 또는 trusted authority 필수
3. Kademlia DHT first-hop congestion (ETH DAS류 high-throughput)
4. **P2P 검색 indexing 부재** — DHT = key→value, full-text inverted index 아님 (YaCy 18년차에도 quality 갭)
5. NAT traversal 실측 ~70% (IPFS DCUtR, arxiv 2510.27500). Symmetric NAT 측 TURN relay 필수 = 부분 중앙화
6. Nostr relay 95% cost-uncovered, default relay 측 de-facto centralization

**옴 측 가장 위협** = Sybil (단일 actor 측 옴 CID 주변 keyspace 측 포위 → coin identity censorable).
**만 측 가장 위협** = full-text search 부재.

**Verdict**: P2P-only 측 옴마니반메훔 모든 요구사항 동시 충족 **불가**. 하이브리드 mandatory:
- 옴 identity = L1 블록체인 (Sybil PoS 외부화)
- 콘텐츠 = IPFS + Filecoin (≥3 pinning provider)
- 만 = centralized indexer (The Graph + Algolia mirror) + Merkle commitment
- NAT = TURN relay 또는 libp2p Circuit Relay v2
- Nostr = 사용자 본인 relay 운영 incentive (revenue share)

**Confidence**: HIGH

## A4 — Benchmarks

**Quantitative trade-offs**:
- NFT mint cost chain 측 ~10⁵x 변동 — ETH L1 ~$30 vs Solana ~$0.00025
- Public post storage permanence model 측 ~6000x — Arweave one-time $9-12/GB vs Filecoin $0.002/GB/year
- Subscription read latency — DHT (libp2p Kad ~100ms-수초 p99) vs relay-pull (Nostr 100 req/s default, ClickHouse 50K-200K events/s)

**권장 stack**:
- 옴 mint = Solana ($0.00025) or Polygon PoS ($0.0009) — ETH L1 micro-NFT 측 비현실
- 만 storage = Arweave one-time $9-12/GB + IPFS CID
- 이/기 = Nostr relay pool + ETH L2 (Arbitrum/Base ~$0.05-0.08/tx) for 배당 settlement
- BitTorrent 측 >10MB media 보조

**Confidence**: MEDIUM (TPS theoretical vs sustained 측 10-100x 차이)
