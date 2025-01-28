# Beer Game Environment

A PettingZoo-compatible implementation of the Beer Distribution Game, a simulation of a supply chain with multiple agents.

## Installation

```bash
pip install beergame
```

## Usage

```python
from beergame import beergame_v0

env = beergame_v0.beergame_v0(render_mode="rgb_array")
env.reset()

# Example interaction loop
for agent in env.agent_iter():
    observation, reward, termination, truncation, info = env.last()
    
    if termination or truncation:
        action = None
    else:
        # Your agent policy here
        action = env.action_space(agent).sample()
    
    env.step(action)

env.close()
```

## Environment Parameters

- `holding_cost`: Cost per unit of inventory held per week
- `backorder_cost`: Cost per unit of backlogged orders per week
- `init_inv_level`: Initial inventory levels for each player
- `init_orders`: Initial order quantities
- `init_shipments`: Initial shipment quantities
- `info_sharing`: Whether to share information between players

## Observation Space

Each agent receives a dictionary observation with:
- `inventory`: Current inventory level
- `backlog`: Current backlog level
- `orders`: Current order quantity
- `incoming_shipments`: Expected incoming shipments

## Action Space

Actions are continuous values representing order quantities (0 to 50 units).

## Rewards

Rewards are negative costs, calculated as:
```
reward = -(holding_cost * inventory + backorder_cost * backlog)
```