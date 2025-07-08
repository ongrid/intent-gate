# Open Intent Gate

[![Code Quality Checks](https://github.com/ongrid/intent-gate/actions/workflows/workflow.yml/badge.svg)](https://github.com/ongrid/intent-gate/actions/workflows/workflow.yml)
[![Python Versions](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is OIG?

**OIG** is an open-source market maker gateway that connects liquidity providers to intent-based trading infrastructure. It enables market making across multiple EVM chains by receiving trading requests (RFQs) from the intent platforms, generating and cryptographically signing quotes and submitting them back.

Currently, OIG operates through [Liquorice Protocol](https://liquorice.tech), which acts as an aggregator connecting market makers to various solvers who compete to find the best execution paths and settle trades in intent-based protocols (CoW, bebop, etc.).

## Quick Start

### Prerequisites

- **Docker and Docker Compose** [installed](https://docs.docker.com/compose/install/) - for containerized deployment
- **Liquorice Credentials** - Get `MAKER_SESS_ID` and `MAKER_SESS_AUTH` from Liquorice team
- **Signer** Ethereum address (EOA) with hexadecimal private key `SIGNER_PRIV_KEY` used for quote signatures. Recommended to have zero balances on it.
- **[SKeeper](https://github.com/ongrid/skeeper) Contract(s)** deployed on target EVM chains
- **Permissions Setup**:
     - Signer MUST have `SIGNER_ROLE` granted on SKeeper contracts for `ERC-1271` signature validation
     - SKeeper contracts must hold ERC-20 token reserves for market making
     - All tokens should have ERC-20 allowances given for Liquorice [Balance Manager](https://liquorice.gitbook.io/liquorice-docs/links/smart-contracts)s `0x38E1E461dadA062C202Cb63b1AC8Be09b95340CD`
- **RPC Endpoints** - WebSocket-enabled EVM RPC endpoints for each chain (`***_WS_URL` environment variables)

### Environment Configuration

- Copy `.env.example` template to `.env` and replace rpc settings, contract addresses and credentials with your values.
- Each active chain requires both `***_WS_URL` and `***_SKEEPER`. Othervise the chain will be inactive.
- Set `LOG_LEVEL` to `INFO` to reduce verbose logging if needed

### Build and Start

```
docker compose build
docker compose up -d
```

### Monitor the logs

```
docker compose logs -f
```


## Components Diagram

```
                    ┌─────────────────┐            ┌──────────────┐                     
                    │ QuoterService   │            │ ChainService │                     
                    │                 │            │              │                     
                    │                 │            │              │  Transfer  Web3 RPC 
                    │                 │            │              │  events   │         
                    │                 │            │ ┌─────────┐◄─┼───────────◄─        
                    │                 │            │ │Read     │  │           │         
                    │                 │            │ │spendable├──┼───────────┼─┐       
                    │                 │            │ │balances │  │ multicall │ │       
                    │                 │   Balances │ │         │  │           │ │       
                    │   ┌─────────────┼────────────┼─┼─────────┼──┼───────────◄─┘       
                    │   │             │            │ └─────────┘  │           │         
                    │   │             │            │              │Settlement │         
                    │   │             │            │ ┌─────────┐◄─┼───────────◄─        
                    │   │             │            │ │Parse    │  │  events   │         
                    │   │             │            │ │Settlement──┼───────────┴──┐      
                    │   │             │            │ │Metadata │  │ debug_traceTx│      
                    │   │             │      Trade │ │         │  │ (optional)│  │      
                    │   │             │     ┌──────┼─┼─────────┼──┼───────────◄──┘      
                    │   │             │     │      │ └─────────┘  │           │         
                    │   │             │     │      │              │           │Web3 RPC 
       Periodic     │   │             │     │      └──────────────┘           │         
       PriceLevels  │ ┌─▼───────────┐ │     │                                           
     │ Updates      │ │ Balances &  │ │     │                                           
     ├──────────────┼►┤ LevelsCache │ │     ▼                                           
     │              │ │             │ │            ┌──────────────┐                     
     │              │ │             │ │            │     ┌──┐     │   RFQ     │         
     │              │ │ ┌───────┐   │ │            │     ├──┤◄────┼───────────◄─        
     │              │ └─┼───────▲───┘ │            │     ├──┤     │           │         
     │              │ ┌─┼───────┼───┐ │  RFQMessage│     ├──┤     │           │         
     │              │ │ ▼       └───┼◄┼────────────┼─────┼──┤     │           │         
     │              │ │ │ Reply with│ │            │     └──┘     │           │         
     │              │ │ │ Quote or  │ │            │              │           │         
Maker│              │ │ │ Ignore??? │ │            │              │           │         
Client              │ └─┼───────────┘ │            │              │           │         
     │              │   │             │            │   Liquorice  │ JSON o. WS│Liquorice
     │              │   │             │            │   WS Client  │           │maker v2 
     │              │ ┌─▼───────────┐ │            │              │           │         
     │              │ │ │ Sign quote│ │            │              │           │         
     │              │ │ │ w.EIP-712 │ │            │              │           │         
     │              │ │ │ signature │ │            │              │           │         
     │              │ │ │           │ │  RFQQuote  │     ┌──┐     │           │         
     │              │ │ └───────────►─┼────────────┼────►├──┤     │           │         
     │              │ └─────────────┘ │            │     ├──┤     │           │         
     │ Trade Notifs │                 │Trade│      │     ├──┤     │   Quote   │         
     │◄─────────────┤◄────────────────┼─────┘      │     ├──┼─────┼───────────┼►        
     │              │                 │            │     └──┘     │           │         
                    └─────────────────┘            └──────────────┘           │         
```

## Contributors and License

Contributors:

* [Kirill Varlamov](https://github.com/ongrid)

The code released under permissive [MIT License](LICENSE).
Contributions are welcome!