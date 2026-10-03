# SOURCES — PROM 16 옴마니반메훔 기술 feasibility

## 1차 소스 (USER_PRIMARY)

| Source | URL | KG |
|---|---|---|
| YouTube 영상 "눈물이 납니다..." (라경준, 메타휴모토닉 채널) | https://www.youtube.com/watch?v=pWIINh4TlHk | `metahumotonic-video-tears-pWIINh4TlHk-2026-05-20` |
| 영상 transcript ko (yt-dlp auto-sub) | local `/tmp/yt_meta/pWIINh4TlHk.ko.clean.txt` (288 lines) | — |
| 사용자 발화 "오움마니 반메홈 눈물이 납니다 astast" | session 2026-05-20 | `user-utterance-ommanibanmehoom-emotion-2026-05-20` |

## 2차 소스 — 16 finding citations (axis × sub-axis)

### A. P2P substrate

| Cell | Sources |
|---|---|
| A1 (공식 docs) | [IPFS specs](https://specs.ipfs.tech/), [libp2p Kad-DHT](https://github.com/libp2p/specs/blob/master/kad-dht/README.md), [Arweave whitepaper](https://whitepaper.arweave.net/), [Nostr NIP-01](https://nips.nostr.com/1), [Filecoin spec](https://spec.filecoin.io/), [Filecoin FIPs](https://github.com/filecoin-project/FIPs) |
| A2 (production) | [Filecoin Q3 2025](https://messari.io/report/state-of-filecoin-q3-2025), [Nostr overview](https://www.glukhov.org/post/2025/10/nostr-overview-and-statistics/), [BitTorrent DHT 2025](https://torrentfreak.com/bittorrents-dht-and-how-customers-of-major-isps-help-keep-it-vibrant-alive-250927/), [Fediverse 2026](https://fediview.com/articles/fediverse-in-numbers-mastodon-stats-2026/), [Cloudflare IPFS](https://blog.cloudflare.com/cloudflares-public-ipfs-gateways-and-supporting-interplanetary-shipyard/), [Holochain reality check](https://soushi888.github.io/alternef-digital-garden/blog/holochain-ecosystem-reality-check-2025) |
| A3 (pitfalls) | [arxiv 2505.01139 IPFS Sybil](https://arxiv.org/html/2505.01139), [ACM Sybil](https://dl.acm.org/doi/10.1145/3664476.3664482), [Kademlia limits](https://arxiv.org/pdf/2402.09993), [NAT hole-punching arxiv 2510.27500](https://arxiv.org/html/2510.27500v1), [Nostr 95% relay deficit](https://dev.to/jonathan_greenallidoizc/95-of-nostr-relays-cant-cover-costs-heres-why-that-matters-189l), [IPFS persistence docs](https://docs.ipfs.tech/concepts/persistence/) |
| A4 (benchmarks) | [L2 comparison](https://blockeden.xyz/blog/2026/02/18/ethereum-layer-2-solutions-comparison-arbitrum-optimism-zksync/), [Arweave vs IPFS Filecoin](https://akord.com/learn/arweave-versus-ipfs-filecoin), [Nostr relay perf](https://code.pobblelabs.org/nostr_relay/doc/tip/docs/performance.md), [Shugur relay](https://github.com/Shugur-Network/relay), [NFT chain comparison](https://www.block3finance.com/best-blockchains-for-nft-minting-ethereum-vs-solana-vs-polygon), [L2 gas fee](https://coinlaw.io/gas-fee-markets-on-layer-2-statistics/) |

### B. Token primitives

| Cell | Sources |
|---|---|
| B1 (공식 docs) | [EIP-721](https://eips.ethereum.org/EIPS/eip-721), [EIP-1155](https://eips.ethereum.org/EIPS/eip-1155), [EIP-2981](https://eips.ethereum.org/EIPS/eip-2981), [Unlock docs](https://docs.unlock-protocol.com/core-protocol/), [Lit Protocol ACC](https://developer.litprotocol.com/sdk/access-control/intro), [OZ PaymentSplitter](https://docs.openzeppelin.com/contracts/4.x/api/finance), [Fractional vault](https://docs.fractional.art/fractional/smart-contract-breakdown/token-vault) |
| B2 (production) | [Tessera shutdown 2023-05](https://www.coindesk.com/web3/2023/05/12/paradigm-backed-nft-ownership-platform-tessera-is-shutting-down), [Unlock Forbes ads-free](https://unlock-protocol.com/blog/forbes-ads-free), [Friend.tech 측 shut-down](https://www.dlnews.com/articles/defi/friend-tech-shuts-down-after-revenue-and-users-plummet/), [OpenSea royalty abandon](https://decrypt.co/121638/opensea-drops-fees-royalty-protections-blur-rises), [Aave 2025 recap](https://aave.com/blog/aave-2025-recap), [Lit Q4 2024](https://messari.io/report/state-of-lit-protocol-q4-2024), [BAYC floor](https://nftpricefloor.com/bored-ape-yacht-club) |
| B3 (pitfalls) | [OpenSea royalty tool retreat](https://nftplazas.com/opensea-royalty-tool/), [Tessera shutdown](https://www.coindesk.com/web3/2023/05/12/paradigm-backed-nft-ownership-platform-tessera-is-shutting-down), [Beanstalk $182M flashloan attack](https://blog.verichains.io/p/how-to-stole-an-election-beanstalk), [a16z DAO attacks](https://a16zcrypto.com/posts/article/dao-governance-attacks-and-how-to-avoid-them/), [OWASP SC05 reentrancy](https://owasp.org/www-project-smart-contract-top-10/2025/en/src/SC05-reentrancy-attacks.html), [Chainlink DAO hack](https://blog.chain.link/reentrancy-attacks-and-the-dao-hack/), [DRM analog hole 2025](https://inkryptvideos.com/screen-recording-protection-with-drm-in-2025/) |
| B4 (benchmarks) | [L2 comparison](https://blockeden.xyz/blog/2026/02/18/ethereum-layer-2-solutions-comparison-arbitrum-optimism-zksync/), [ERC-721 vs 1155](https://www.nadcab.com/blog/smart-contract-standards-erc-721-vs-erc-1155), [Unlock gasless](https://unlock-protocol.com/blog/gasless-minting), [Merkle airdrop](https://blog.sablier.com/airdrop-distribution-models-comparison-2025), [Lit Protocol latency](https://arxiv.org/pdf/2409.08190), [OZ payment](https://docs.openzeppelin.com/contracts/3.x/api/payment) |

### C. Cold start + sustainability

| Cell | Sources |
|---|---|
| C1 (학문) | [Rochet-Tirole 2003](https://web.mit.edu/14.271/www/rochet_tirole.pdf), [Markus 1987 critical mass](https://journals.sagepub.com/doi/10.1177/009365087014005003), [Caillaud-Jullien chicken-egg](https://www.edegan.com/pdfs/Caillaud%20Jullien%20(2003)%20-%20Chicken%20and%20Egg.pdf), [Resilient airdrop arxiv 2503.14316](https://arxiv.org/pdf/2503.14316), [Token incentive arxiv](https://arxiv.org/pdf/2312.02752), [Curve veCRV](https://docs.curve.finance/curve_dao/voting-escrow/voting-escrow/) |
| C2 (Friend.tech) | [Friend.tech shutdown](https://www.dlnews.com/articles/defi/friend-tech-shuts-down-after-revenue-and-users-plummet/), [Bloomberg 98% crash](https://www.bloomberg.com/news/articles/2024-05-03/crypto-s-social-media-friend-tech-saw-token-value-crashed-98), [Decrypt token launch chaos](https://decrypt.co/229273/friend-tech-community-in-uproar-amid-token-and-v2-launch), [Crypto Briefing](https://cryptobriefing.com/friend-token-crisis-low/), [Final shot retrospective](https://0xgreythorn.medium.com/friend-tech-a-final-shot-at-shaping-the-future-of-social-media-ac2f7fb07110), [BitClout post-mortem](https://protos.com/bitclout-deso-diamondhands-blockchain-crypto-marketing-gimmick/) |
| C3 (attacks) | [Beanstalk Immunefi analysis](https://medium.com/immunefi/hack-analysis-beanstalk-governance-attack-april-2022-f42788fc821e), [a16z DAO attacks](https://a16zcrypto.com/posts/article/dao-governance-attacks-and-how-to-avoid-them/), [Sybil in DAOs](https://www.outlookindia.com/xhub/blockchain-insights/why-are-sybil-attacks-difficult-to-prevent-in-token-based-daos), [DAO failures whales apathy](https://lopetaku.medium.com/dao-governance-failures-whales-low-turnout-attacks-d1375c556384), [arxiv 2505.00888](https://arxiv.org/html/2505.00888v1), [Sybil dropper](https://droppables.beehiiv.com/p/sybil) |
| C4 (benchmarks) | [Friend.tech DefiLlama](https://defillama.com/protocol/friend.tech), [Farcaster 2025](https://blockeden.xyz/blog/2025/10/28/farcaster-in-2025-the-protocol-paradox/), [Farcaster vs Lens](https://blockeden.xyz/blog/2026/01/13/farcaster-vs-lens-socialfi-web3-social-graph/), [SocialFi failure analysis](https://www.bitget.com/news/detail/12560604275814), [Tokens as CAC](https://tomtunguz.com/tokens-as-cac/), [Crypto CAC](https://www.growthchain.io/blog/crypto-customer-acquisition-cost), [Metcalfe empirical](https://link.springer.com/article/10.1007/s11390-015-1518-1) |

### D. Real-world cases

| Cell | Sources |
|---|---|
| D1 (protocol docs) | [Lens docs](https://docs.lens.xyz/), [Lens modules](https://github.com/lens-protocol/modules), [Farcaster docs](https://docs.farcaster.xyz/), [DeSo creator coins](https://docs.deso.org/deso-features/creator-coins), [Mirror $WRITE](https://dev.mirror.xyz/5gt60vKFJZ_tR1BjoJ7-Y0sNw7REebStHjzFU5x73J0), [Mirror NFT mechanics](https://mirror.xyz/basedtoschi.eth/C-8I58Fh_hU5bVACjpMmXy4O9atUG1PLsEqLHn5sO3w) |
| D2 (case studies) | [Friend.tech mechanics](https://www.codezeros.com/inside-friendtech-discovering-web3s-social-media-gem), [Mirror revenue split](https://dev.mirror.xyz/8MThiFhn391cfgffQtiRoSpS-Op93IR71rYgf6YEzBc), [Farcaster Frame v2](https://www.bankless.com/read/farcaster-frames-v2), [Lens Collect Module source](https://github.com/lens-protocol/modules/blob/master/contracts/collect/UpdatableOwnableFeeCollectModule.sol), [DeSo V2 token mechanics](https://docs.deso.org/focus/next-generation-token-mechanics), [Bonding curve arxiv](https://arxiv.org/pdf/2211.15993) |
| D3 (failure modes) | [Friend.tech DLNews](https://www.dlnews.com/articles/defi/friend-tech-shuts-down-after-revenue-and-users-plummet/), [Bankless dead](https://www.bankless.com/friend-tech-dead), [BitClout dark](https://www.paioaito.com/p/bitclouts-rise-and-demise-the-dark), [Wikipedia BitClout](https://en.wikipedia.org/wiki/BitClout), [Code4rena Lens audit](https://code4rena.com/reports/2023-07-lens), [Farcaster hub costs](https://hackmd.io/@farcasterxyz/ry0QL4M4o), [Steem Hive fork](https://medium.com/bitcoin-news-today-gambling-news/steem-fork-what-happened-with-hive-steemit-justin-sun-14c1f3d52a94), [SocialFi failure structural](https://miniapp.gate.com/learn/articles/from-explosive-growth-to-stagnation-the-rise-disillusionment-and-structural-failure-of-socialfi/15341), [SocialFi market failure](https://www.ainvest.com/news/socialfi-market-failure-fate-creator-coins-2601/) |
| D4 (benchmarks) | [Farcaster 2025](https://blockeden.xyz/blog/2025/10/28/farcaster-in-2025-the-protocol-paradox/), [DeFiant Farcaster DAU](https://thedefiant.io/news/nfts-and-web3/how-many-users-does-farcaster-actually-have), [TheBlock Farcaster $600K](https://www.theblock.co/post/277013/farcaster-revenue-hits-600000-during-protocols-second-wave-of-attention), [CryptoSlate Friend.tech $21](https://cryptoslate.com/generating-only-21-in-revenue-in-30-days-friendtech-relinquishes-control-of-contracts/), [Friend.tech DLNews](https://www.dlnews.com/articles/defi/friend-tech-shuts-down-after-revenue-and-users-plummet/), [Farcaster vs Lens 2026](https://blockeden.xyz/blog/2026/01/13/farcaster-vs-lens-socialfi-web3-social-graph/) |

## 3차 소스 (cross-ref)

- 이전 cycle: `ommanibanmehoom-feasibility-3layer-2026-05-20` (3-layer 분석, 법적 + 기술 + 경제)
- 옴마니반메훔 commander: `commander-om-mani-padme-hum-omc-2026-05-19`
- KG mirror: `engineboy-canonical-2026-05-19` + 5 commander roster
