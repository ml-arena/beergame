# Directory: beergame/
# File: beergame/env/beergame.py
import pygame
import functools
import numpy as np
from gymnasium.spaces import Box, Dict
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
from .renderer import BeerGameRenderer


class raw_env(AECEnv):
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "beergame_v0",
        "render_fps": 2,
    }

    def __init__(self, 
                render_mode=None,
                holding_cost=[1.0, 1.0, 1.0, 1.0],
                backorder_cost=[2.0, 2.0, 2.0, 2.0],
                init_inv_level=[12, 12, 12, 12],
                init_orders=[0, 0, 0, 0],
                init_shipments=[4, 4, 4, 4],
                info_sharing=False,
                base_demand=8.0,
                seed=None):
        """Initialize the Beer Game environment."""
        if seed is not None:
            np.random.seed(seed)
            
        self.render_mode = render_mode
        if self.render_mode == "rgb_array":
            self.renderer = BeerGameRenderer()
        
        self.num_players = 4
        self.holding_cost = holding_cost
        self.backorder_cost = backorder_cost
        self.init_inv_level = init_inv_level
        self.init_orders = init_orders
        self.init_shipments = init_shipments
        self.info_sharing = info_sharing
        self.base_demand = base_demand
        self.total_beers = 0
        
        self.possible_agents = ["retailer", "wholesaler", "distributor", "factory"]
        
        self._action_spaces = {
            agent: Box(low=0, high=50, shape=(1,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        self._observation_spaces = {
            agent: Dict({
                "inventory": Box(low=0, high=float('inf'), shape=(1,)),  # Changed lower bound to 0
                "backorders": Box(low=0, high=float('inf'), shape=(1,)),  # Added separate backorders
                "orders": Box(low=0, high=float('inf'), shape=(1,)),
                "incoming_shipments": Box(low=0, high=float('inf'), shape=(1,)),
                "holding_cost": Box(low=0, high=float('inf'), shape=(1,)),
                "backorder_cost": Box(low=0, high=float('inf'), shape=(1,))
            })
            for agent in self.possible_agents
        }
        self.customer = {
                "orders": 0,
                "incoming_shipments": 0,
        }
    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self._action_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self._observation_spaces[agent]

    def _generate_customer_demand(self):
        """
        Generate customer demand for the retailer using a base demand with random variations.
        The demand follows a pattern that includes:
        - Base demand level
        - Seasonal variations
        - Random fluctuations
        - Occasional demand spikes
        """
        # Base demand parameters
        base_demand = self.base_demand
        seasonal_amplitude = 2.0
        random_noise_std = 1.0
        spike_probability = 0.1
        max_spike = 10.0

        # Calculate seasonal component using sine wave (52 weeks cycle)
        seasonal_factor = seasonal_amplitude * np.sin(2 * np.pi * self.week / 52)
        
        # Generate random noise
        random_noise = np.random.normal(0, random_noise_std)
        
        # Occasionally add demand spikes
        spike = max_spike * np.random.binomial(1, spike_probability)
        
        # Combine all components and ensure non-negative demand
        demand = max(0, base_demand + seasonal_factor + random_noise + spike)
        
        return float(demand)
    def step(self, action):
        """Execute one step in the environment."""
        if (
            self.terminations[self.agent_selection]
            or self.truncations[self.agent_selection]
        ):
            return self._was_dead_step(action)

        agent = self.agent_selection
        agent_idx = self.possible_agents.index(agent)
        
        self.orders[agent_idx] = float(action)
        
        if self._agent_selector.is_last():
            self._update_state()
            self.week += 1
            
            if self.week >= 52:
                self.terminations = {agent: True for agent in self.agents}

        reward = self._calculate_reward(agent_idx)
        self.rewards[agent] = reward
        
        self._cumulative_rewards[agent] = 0
        self.agent_selection = self._agent_selector.next()
        self._accumulate_rewards()
    def reset(self, seed=None, options=None):
        """Reset the environment to initial state."""
        self.agents = self.possible_agents[:]
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        # Initialize game state
        self.week = 0
        self.inventory_levels = np.array(self.init_inv_level, dtype=np.float32)
        self.backorders = np.zeros(self.num_players, dtype=np.float32)  # New: track backorders separately
        self.orders = np.array(self.init_orders, dtype=np.float32)
        self.incoming_shipments = np.array(self.init_shipments, dtype=np.float32)
        
        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.next()

        return self.observe(self.agent_selection)

    def observe(self, agent):
        """Return observation for the specified agent."""
        if agent not in self.agents:
            return None
            
        agent_idx = self.possible_agents.index(agent)
        
        obs = {
            "inventory": np.array([self.inventory_levels[agent_idx]], dtype=np.float32),
            "backorders": np.array([self.backorders[agent_idx]], dtype=np.float32),
            "orders": np.array([self.orders[agent_idx]], dtype=np.float32),
            "incoming_shipments": np.array([self.incoming_shipments[agent_idx]], dtype=np.float32),
            "holding_cost": np.array([self.holding_cost[agent_idx]], dtype=np.float32),
            "backorder_cost": np.array([self.backorder_cost[agent_idx]], dtype=np.float32)
        }
        
        return obs

    def _update_state(self):
        """Update the game state after all agents have acted."""
        # Initialize temporary array for incoming shipments to children
        self.customer['orders'] = self._generate_customer_demand()
        max_possible_shipment = np.zeros(self.num_players, dtype=np.float32)
        # First loop: Process backorders and determine shipments
        for i in range(self.num_players):
            # Update backorders with orders from downstream
            # For retailer (i=0), use customer orders
            if i == 0:
                self.backorders[i] += self.customer['orders']
            else:
                self.backorders[i] += self.orders[i-1]
            
            # Update inventory with production/shipments
            self.inventory_levels[i] += self.incoming_shipments[i]
            
            # Calculate shipments to downstream
            max_possible_shipment[i] = self.inventory_levels[i] - max(self.inventory_levels[i] - self.backorders[i], 0)
            
            # Update inventory and backorders
            self.inventory_levels[i] -= max_possible_shipment[i]
            self.backorders[i] -= max_possible_shipment[i]
        
        # Second loop: Update incoming shipments for each agent
        for i in range(self.num_players):
            if i == 0:
                # Retailer ships to customer
                self.customer['incoming_shipments'] = max_possible_shipment[i]
                self.total_beers += max_possible_shipment[i]
            else:
                # Update incoming shipments for other agents
                self.incoming_shipments[i-1] = max_possible_shipment[i]
        
        # Factory's incoming shipments are based on its orders
        self.incoming_shipments[-1] = self.orders[-1]

    def _calculate_reward(self, agent_idx):
        """Calculate reward for an agent based on costs."""
        holding_cost = self.holding_cost[agent_idx] * self.inventory_levels[agent_idx]
        backorder_cost = self.backorder_cost[agent_idx] * self.backorders[agent_idx]
        
        return -(holding_cost + backorder_cost)

    def render(self):
        """Render the current state of the environment."""
        if self.render_mode == "rgb_array":
            state = {
                'week': self.week,
                'inventory_levels': self.inventory_levels,
                'backorders': self.backorders,  # Added backorders to rendering
                'orders': self.orders,
                'shipments': self.incoming_shipments,
                'holding_cost': [self.holding_cost[i] * self.inventory_levels[i] 
                               for i in range(self.num_players)],
                'backorder_cost': [self.backorder_cost[i] * self.backorders[i]
                                 for i in range(self.num_players)],
                'customer': self.customer,
                'total_beers': self.total_beers
            }
            return self.renderer.render(state)
        else:
            return None

    def close(self):
        if hasattr(self, 'renderer'):
            self.renderer.close()

from pettingzoo.utils import wrappers

def env(**kwargs):
    """
    The env function wraps the environment in 3 wrappers by default.
    """
    env = raw_env(**kwargs)
    # Provides a wide variety of helpful user errors
    env = wrappers.AssertOutOfBoundsWrapper(env)
    env = wrappers.OrderEnforcingWrapper(env)
    return env