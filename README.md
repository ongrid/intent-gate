# Intent Client Reference Gateway

[![Code Quality Checks](https://github.com/ongrid/intent-gate/actions/workflows/workflow.yml/badge.svg)](https://github.com/ongrid/intent-gate/actions/workflows/workflow.yml)
[![Python Versions](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Components Diagram

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