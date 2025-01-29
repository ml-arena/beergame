import numpy as np
from collections import deque

class Agent:
    def __init__(self, env, player_name=None):
        self.env = env
        self.player_name = player_name if player_name else env.agents[0]
        self.action_space = self.env.action_space(self.player_name)
        
        # Agent position in supply chain (0=retailer to 3=factory)
        self.position = env.possible_agents.index(self.player_name)
        
        # Configuration parameters
        self.safety_stock_factor = 1.5
        self.target_inventory_days = 14
        self.smoothing_factor = 0.3
        self.lead_time = self._estimate_lead_time()
        
        # Initialize tracking variables
        self.demand_history = deque(maxlen=8)  # Track last 8 weeks of demand
        self.last_orders = deque(maxlen=4)     # Track last 4 orders
        self.avg_demand = None
        
        # Define observation keys order to match the Box space
        self.obs_keys = [
            "inventory",
            "backorders",
            "orders",
            "incoming_shipments",
            "holding_cost",
            "backorder_cost"
        ]

    def _array_to_dict_obs(self, obs_array):
        """Convert flat array observation to dictionary format
        
        Args:
            obs_array (np.ndarray): Flat array of shape (6,) containing observation values
            
        Returns:
            dict: Dictionary with named observation values
        """
        return {
            key: np.array([value], dtype=np.float32)
            for key, value in zip(self.obs_keys, obs_array)
        }

    def _estimate_lead_time(self):
        """Estimate lead time based on position in supply chain"""
        base_lead_time = 2  # Base processing time
        position_factor = self.position * 1.5  # Additional delay based on position
        return base_lead_time + position_factor

    def _calculate_safety_stock(self, demand_std):
        """Calculate safety stock based on demand variability"""
        service_level_z = 1.96  # 95% service level
        return service_level_z * demand_std * np.sqrt(self.lead_time)

    def _estimate_demand(self, observation):
        """Estimate demand using exponential smoothing"""
        current_demand = float(observation['orders'][0])
        self.demand_history.append(current_demand)
        
        if self.avg_demand is None:
            self.avg_demand = current_demand
        else:
            self.avg_demand = (self.smoothing_factor * current_demand + 
                             (1 - self.smoothing_factor) * self.avg_demand)
        
        return self.avg_demand

    def _calculate_order_quantity(self, observation):
        """Calculate order quantity using a modified base-stock policy"""
        # Current inventory position
        current_inventory = float(observation['inventory'][0])
        backorders = float(observation['backorders'][0])
        incoming_shipments = float(observation['incoming_shipments'][0])
        
        # Estimate demand and variability
        expected_demand = self._estimate_demand(observation)
        demand_std = np.std(list(self.demand_history)) if len(self.demand_history) > 1 else expected_demand * 0.2
        
        # Calculate components
        safety_stock = self._calculate_safety_stock(demand_std)
        pipeline_stock = expected_demand * self.lead_time
        target_stock = safety_stock + pipeline_stock
        
        # Calculate net inventory position
        inventory_position = (current_inventory - backorders + incoming_shipments + 
                            sum(self.last_orders))
        
        # Calculate base order quantity
        order_quantity = max(0, expected_demand + (target_stock - inventory_position))
        
        # Apply smoothing to avoid bullwhip effect
        if self.last_orders:
            last_order = self.last_orders[-1]
            order_quantity = (0.7 * order_quantity + 0.3 * last_order)
        
        # Adjust based on position in supply chain
        if self.position > 0:  # Not retailer
            order_quantity *= (1 + 0.1 * self.position)  # Slightly increase orders upstream
        
        # Ensure order is within action space bounds
        order_quantity = min(max(order_quantity, 0), self.action_space.high[0])
        
        return float(order_quantity)

    def choose_action(self, observation, reward=0.0, terminated=False, truncated=False, info=None, action_mask=None):
        """Choose action based on current observation
        
        Args:
            observation (np.ndarray): Flat array observation of shape (6,)
            reward (float): Current reward
            terminated (bool): Whether episode is terminated
            truncated (bool): Whether episode is truncated
            info (dict): Additional info
            action_mask (list): Optional action mask
            
        Returns:
            float: Order quantity
        """
        if terminated or truncated:
            return 0.0
            
        # Convert array observation to dictionary format
        obs_dict = self._array_to_dict_obs(observation)
        
        # Calculate order quantity using dictionary observation
        order_quantity = self._calculate_order_quantity(obs_dict)
        
        # Track order history
        self.last_orders.append(order_quantity)
        
        return order_quantity