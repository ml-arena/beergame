import pygame
import numpy as np
import os
from typing import Dict, List, Tuple

class BeerGameRenderer:
    def __init__(self, screen_width: int = 1024, screen_height: int = 768):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.Surface((screen_width, screen_height))
        
        # Colors
        self.COLORS = {
            'background': (240, 248, 255),    # Alice Blue
            'box': (220, 220, 220),           # Light Gray
            'text': (60, 60, 60),             # Dark Gray
            'panel': (255, 255, 255),         # White
            'panel_border': (200, 200, 200),  # Light Gray
            'arrow_order': (243, 156, 18),    # Orange for orders
            'arrow_shipment': (41, 128, 185), # Blue for shipments
            'positive': (46, 204, 113),       # Green
            'negative': (231, 76, 60),        # Red
            'cost': (155, 89, 182),          # Purple
            'line': (189, 195, 199),         # Light Gray
            'customer_order': (52, 152, 219), # Blue
            'info_text': (127, 140, 141)      # Gray
        }

        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.header_font = pygame.font.Font(None, 32)
        self.value_font = pygame.font.Font(None, 28)
        self.label_font = pygame.font.Font(None, 24)
        self.cost_font = pygame.font.Font(None, 20)
        self.info_font = pygame.font.Font(None, 22)
        
        # Layout
        self.margin = 20
        self.box_width = 180
        self.box_height = 120
        self.box_spacing = 220  # Space between boxes
        self.start_x_offset = 50  # Reduced from 200 to move everything left
        self.arrow_offset = 30
        
        # Updated image dimensions to maintain square aspect ratio
        self.image_size = min(self.box_width, self.box_height - 40)
        self.image_box_gap = 10

        # Load images
        self.images = {}
        image_size = (self.image_size, self.image_size)  # Square images
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_paths = {
            'Retailer': os.path.join(current_dir, 'retailer.png'),
            'Wholesaler': os.path.join(current_dir, 'wholesaler.png'),
            'Distributor': os.path.join(current_dir, 'distributor.png'),
            'Factory': os.path.join(current_dir, 'factory.png'),
            'Beer':  os.path.join(current_dir, 'beer.png'),
        }
        
        for name, path in image_paths.items():
            try:
                image = pygame.image.load(path)
                if name != 'Beer':
                    self.images[name] = pygame.transform.scale(image, image_size)
                else:
                    self.images[name] = pygame.transform.scale(image, (self.image_size//2, self.image_size//2))
            except pygame.error as e:
                print(f"Warning: Could not load image {path}: {e}")
                self.images[name] = None
    def _draw_customer_box(self, x: int, y: int):
        """Draw the customer box as a round-cornered box below the main row"""
        box_width = 120
        box_height = 80
        radius = 20
        
        # Calculate position (centered below retailer)
        box_x = x + (self.box_width - box_width) // 2
        box_y = y + self.box_height + 60  # Move below main row
        
        # Draw rounded rectangle
        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, self.COLORS['panel'], rect, border_radius=radius)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], rect, 1, border_radius=radius)
        
        # Title
        title_text = self.header_font.render("Customer", True, self.COLORS['text'])
        title_rect = title_text.get_rect(centerx=rect.centerx, top=rect.top + 5)
        self.screen.blit(title_text, title_rect)
        
        return box_x, box_y, box_width, box_height 
    def _draw_actor_box(self, x: int, y: int, title: str, data: dict):
        """Draw an actor box with costs displayed above the image"""
        # Draw costs first (above everything)
        holding_cost = data.get('holding_cost', 0)
        backorder_cost = data.get('backorder_cost', 0)
        cost_y = y - self.image_size - self.image_box_gap - 25  # Position above image
        
        cost_text = self.cost_font.render(
            f"H: ${holding_cost:.1f} | B: ${backorder_cost:.1f}",
            True,
            self.COLORS['cost']
        )
        cost_rect = cost_text.get_rect(centerx=x + self.box_width//2, top=cost_y)
        self.screen.blit(cost_text, cost_rect)

        # Draw image
        if self.images.get(title):
            image_y = y - self.image_size - self.image_box_gap
            image_rect = self.images[title].get_rect(
                centerx=x + self.box_width//2,
                top=image_y
            )
            self.screen.blit(self.images[title], image_rect)

        # Main box
        rect = pygame.Rect(x, y, self.box_width, self.box_height)
        pygame.draw.rect(self.screen, self.COLORS['panel'], rect)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], rect, 1)

        # Title
        title_y = rect.top + 5
        title_text = self.header_font.render(title, True, self.COLORS['text'])
        title_rect = title_text.get_rect(centerx=rect.centerx, top=title_y)
        self.screen.blit(title_text, title_rect)

        # Inventory value
        inventory_color = self.COLORS['positive'] if data['inventory'] >= 0 else self.COLORS['negative']
        inventory_text = self.value_font.render(f"Stock: {int(data['inventory'])}", True, inventory_color)
        inventory_rect = inventory_text.get_rect(
            centerx=rect.centerx,
            top=title_rect.bottom + 10
        )
        self.screen.blit(inventory_text, inventory_rect)

        # Backorder info
        if data['backorders'] > 0:
            backorder_text = self.value_font.render(
                f"Backorders: {int(data['backorders'])}",
                True,
                self.COLORS['negative']
            )
            backorder_rect = backorder_text.get_rect(
                centerx=rect.centerx,
                top=inventory_rect.bottom + 10
            )
            self.screen.blit(backorder_text, backorder_rect)
    def _draw_cost_summary(self, x: int, y: int, holding_cost: float, backorder_cost: float):
        """Draw a small cost summary below the actor box"""
        text = self.cost_font.render(
            f"H: ${holding_cost:.1f} | B: ${backorder_cost:.1f}",
            True,
            self.COLORS['text']
        )
        rect = text.get_rect(centerx=x + self.box_width/2, top=y + self.box_height + 5)
        self.screen.blit(text, rect)

    def _draw_arrow_with_value(self, start: tuple, end: tuple, value: float, arrow_type: str):
        """Draw an arrow with a value bubble"""
        color = self.COLORS['arrow_shipment'] if arrow_type == "shipment" else self.COLORS['arrow_order']
        
        # Draw the main line
        pygame.draw.line(self.screen, color, start, end, 2)
        
        # Draw arrow head
        angle = np.arctan2(end[1] - start[1], end[0] - start[0])
        arrow_size = 10
        arrow_points = [
            end,
            (end[0] - arrow_size * np.cos(angle - np.pi/6),
             end[1] - arrow_size * np.sin(angle - np.pi/6)),
            (end[0] - arrow_size * np.cos(angle + np.pi/6),
             end[1] - arrow_size * np.sin(angle + np.pi/6))
        ]
        pygame.draw.polygon(self.screen, color, arrow_points)

        # Draw value bubble
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        if value:
            value_text = self.label_font.render(f"{value:.1f}", True, color)
        else:
            value_text = self.label_font.render(f"{0}", True, color)
        value_rect = value_text.get_rect(center=(mid_x, mid_y))
        
        # White background for better readability
        padding = 5
        bg_rect = value_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(self.screen, self.COLORS['panel'], bg_rect)
        pygame.draw.rect(self.screen, color, bg_rect, 1)
        self.screen.blit(value_text, value_rect)
        
    def _draw_arrow(self, start: Tuple[int, int], end: Tuple[int, int], 
                   value: float, arrow_type: str = "order"):
        """Draw an arrow with value between two points"""
        color = (self.COLORS['arrow_order'] if arrow_type == "order" 
                else self.COLORS['arrow_shipment'])
        arrow_size = 10
        
        # Draw main line
        pygame.draw.line(self.screen, color, start, end, 2)
        
        # Calculate arrow head
        angle = np.arctan2(end[1] - start[1], end[0] - start[0])
        arrow_points = [
            end,
            (end[0] - arrow_size * np.cos(angle - np.pi/6),
             end[1] - arrow_size * np.sin(angle - np.pi/6)),
            (end[0] - arrow_size * np.cos(angle + np.pi/6),
             end[1] - arrow_size * np.sin(angle + np.pi/6))
        ]
        pygame.draw.polygon(self.screen, color, arrow_points)
        
        # Draw value bubble
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        radius = 15
        
        # Draw circular background
        pygame.draw.circle(self.screen, self.COLORS['panel'], (int(mid_x), int(mid_y)), radius)
        pygame.draw.circle(self.screen, color, (int(mid_x), int(mid_y)), radius, 1)
        
        # Draw value
        value_text = self.label_font.render(f"{value:.1f}", True, color)
        value_rect = value_text.get_rect(center=(mid_x, mid_y))
        self.screen.blit(value_text, value_rect)
        
    def _draw_info_panel(self, week: int, costs: Dict[str, float]):
        """Draw information panel with game status"""
        panel_width = 250
        panel_height = 120
        
        # Draw panel background with subtle shadow
        shadow_offset = 3
        shadow_rect = pygame.Rect(self.margin + shadow_offset, 
                                self.margin + shadow_offset, 
                                panel_width, panel_height)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], shadow_rect)
        
        # Main panel
        rect = pygame.Rect(self.margin, self.margin, panel_width, panel_height)
        pygame.draw.rect(self.screen, self.COLORS['panel'], rect)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], rect, 1)
        
        # Draw week
        week_text = self.header_font.render(f"Week {week}", True, self.COLORS['text'])
        self.screen.blit(week_text, (rect.left + 10, rect.top + 10))
        
        # Draw total costs
        y = rect.top + 45
        for label, value in costs.items():
            text = self.label_font.render(f"Total {label}: ${value:,.2f}", 
                                        True, self.COLORS['text'])
            self.screen.blit(text, (rect.left + 10, y))
            y += 25
    def _draw_actor_with_box(self, x: int, y: int, title: str, inventory: float, 
                           holding_cost: float, backorder_cost: float):
        """Draw an actor with image above and box below including costs"""
        # Draw image above the box if available
        if self.images.get(title):
            image_rect = pygame.Rect(x, y - self.image_height, self.box_width, self.image_height)
            self.screen.blit(self.images[title], image_rect)
        
        # Draw box below
        box_rect = pygame.Rect(x, y, self.box_width, self.box_height)
        
        # Draw box with slight shadow
        shadow_offset = 2
        shadow_rect = box_rect.copy()
        shadow_rect.move_ip(shadow_offset, shadow_offset)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], shadow_rect)
        pygame.draw.rect(self.screen, self.COLORS['panel'], box_rect)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], box_rect, 1)
        
        # Draw title
        title_text = self.header_font.render(title, True, self.COLORS['text'])
        title_rect = title_text.get_rect(centerx=box_rect.centerx, top=box_rect.top + 5)
        self.screen.blit(title_text, title_rect)
        
        # Draw inventory value
        color = self.COLORS['positive'] if inventory >= 0 else self.COLORS['negative']
        inventory_text = self.value_font.render(f"Stock: {int(inventory)}", True, color)
        inventory_rect = inventory_text.get_rect(
            centerx=box_rect.centerx, 
            top=title_rect.bottom + 10
        )
        self.screen.blit(inventory_text, inventory_rect)
        
        # Draw costs
        y_offset = inventory_rect.bottom + 5
        
        # Holding cost
        holding_text = self.cost_font.render(
            f"Hold: ${holding_cost:.2f}", True, self.COLORS['cost']
        )
        holding_rect = holding_text.get_rect(
            centerx=box_rect.centerx,
            top=y_offset
        )
        self.screen.blit(holding_text, holding_rect)
        
        # Backorder cost
        backorder_text = self.cost_font.render(
            f"Back: ${backorder_cost:.2f}", True, self.COLORS['cost']
        )
        backorder_rect = backorder_text.get_rect(
            centerx=box_rect.centerx,
            top=holding_rect.bottom + 5
        )
        self.screen.blit(backorder_text, backorder_rect)
    def render(self, state: dict) -> np.ndarray:
        """Render the current state of the beer game"""
        self.screen.fill(self.COLORS['background'])
        
        # Calculate layout
        center_y = self.screen_height // 2 - 50  # Move everything up to make room for customer
        start_x = self.start_x_offset
        
        # Draw actors and arrows
        positions = []
        names = ["Retailer", "Wholesaler", "Distributor", "Factory"]
        
        for i, name in enumerate(names):
            x = start_x + i * self.box_spacing
            y = center_y - self.box_height // 2
            positions.append((x, y))
            
            # Prepare data for actor box
            actor_data = {
                'inventory': state['inventory_levels'][i],
                'backorders': state.get('backorders', [0, 0, 0, 0])[i],
                'holding_cost': state['holding_cost'][i],
                'backorder_cost': state['backorder_cost'][i]
            }
            
            self._draw_actor_box(x, y, name, actor_data)

        # Draw customer box below retailer
        customer_box = self._draw_customer_box(positions[0][0], positions[0][1])
        
        # Draw arrows between positions
        for i in range(len(positions) - 1):
            # Orange order arrows (downstream to upstream)
            order_start = (positions[i][0] + self.box_width, positions[i][1] + self.arrow_offset)
            order_end = (positions[i+1][0], positions[i+1][1] + self.arrow_offset)
            self._draw_arrow_with_value(order_start, order_end, state['orders'][i], "order")
            
            # Blue shipment arrows (upstream to downstream)
            ship_start = (positions[i+1][0], positions[i+1][1] - self.arrow_offset)
            ship_end = (positions[i][0] + self.box_width, positions[i][1] - self.arrow_offset)
            self._draw_arrow_with_value(ship_start, ship_end, state['shipments'][i+1], "shipment")
        
        # Factory self-loops
        factory_pos = positions[-1]
        
        # Factory order self-loop (orange)
        self._draw_arrow_with_value(
            (factory_pos[0] + self.box_width, factory_pos[1] + self.arrow_offset * 2),
            (factory_pos[0] + self.box_width - 30, factory_pos[1] + self.arrow_offset * 2),
            state['orders'][-1],
            "order"
        )
        
        # Factory shipment self-loop (blue)
        self._draw_arrow_with_value(
            (factory_pos[0] + self.box_width - 30, factory_pos[1] - self.arrow_offset * 2),
            (factory_pos[0] + self.box_width, factory_pos[1] - self.arrow_offset * 2),
            state['shipments'][-1],
            "shipment"
        )

        # Draw arrows between customer and retailer
        customer_box_x, customer_box_y, customer_box_width, customer_box_height = customer_box

        # Orange order arrow from customer to retailer (bottom to top)
        order_start = (customer_box_x + customer_box_width//3, customer_box_y)  # From top of customer
        order_end = (positions[0][0] + self.box_width//3, positions[0][1] + self.box_height)  # To bottom of retailer
        self._draw_arrow_with_value(
            order_start, 
            order_end, 
            state.get('customer', {}).get('orders', 0), 
            "order"
        )

        # Blue shipment arrow from retailer to customer (bottom to top)
        ship_start = (positions[0][0] + 2*self.box_width//3, positions[0][1] + self.box_height)  # From bottom of retailer
        ship_end = (customer_box_x + 2*customer_box_width//3, customer_box_y)  # To top of customer
        self._draw_arrow_with_value(
            ship_start, 
            ship_end, 
            state.get('customer', {}).get('incoming_shipments', 0),
            "shipment"
        )

        # Draw game stats
        self._draw_game_stats(state['week'], {
            "Total Holding Cost": sum(state['holding_cost']),
            "Total Backorder Cost": sum(state['backorder_cost'])
        })
        self._legend(int(state['total_beers']))
        return np.transpose(
            pygame.surfarray.array3d(self.screen),
            (1, 0, 2)
        )
    def _legend(self, total_beers : int):  # Add state parameter
        # Draw legend in bottom right
        legend_x = self.screen_width - 250  # Position from right edge
        legend_y = self.screen_height - 200  # Position from bottom

        # Draw shipping arrow example (blue)
        ship_start = (legend_x, legend_y)
        ship_end = (legend_x + 50, legend_y)
        self._draw_arrow_with_value(ship_start, ship_end, 0, "shipment")
        ship_text = self.label_font.render("Shipping", True, self.COLORS['arrow_shipment'])
        self.screen.blit(ship_text, (legend_x + 70, legend_y - 10))

        # Draw order arrow example (orange)
        order_start = (legend_x, legend_y + 40)
        order_end = (legend_x + 50, legend_y + 40)
        self._draw_arrow_with_value(order_start, order_end, 0, "order")
        order_text = self.label_font.render("Order", True, self.COLORS['arrow_order'])
        self.screen.blit(order_text, (legend_x + 70, legend_y + 30))

        # Draw beer icon and total (using already loaded image)
        beer_rect = self.images['Beer'].get_rect(topleft=(legend_x, legend_y + 80))
        self.screen.blit(self.images['Beer'], beer_rect)

        # Draw total beers text
        total_text = self.label_font.render(f"Total beers delivered : {total_beers}", 
                                        True, self.COLORS['text'])
        self.screen.blit(total_text, (legend_x + 35, legend_y + 82))
    def _draw_game_stats(self, week: int, costs: dict):
        """Draw game statistics with proper width and alignment"""
        panel_width = 300  # Increased width
        panel_height = 120
        
        # Draw panel with shadow effect
        shadow_offset = 3
        shadow_rect = pygame.Rect(
            self.margin + shadow_offset,
            self.margin + shadow_offset,
            panel_width,
            panel_height
        )
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], shadow_rect)
        
        # Main panel
        rect = pygame.Rect(self.margin, self.margin, panel_width, panel_height)
        pygame.draw.rect(self.screen, self.COLORS['panel'], rect)
        pygame.draw.rect(self.screen, self.COLORS['panel_border'], rect, 1)
        
        # Draw week number
        week_text = self.header_font.render(f"Week {week}", True, self.COLORS['text'])
        week_rect = week_text.get_rect(left=rect.left + 15, top=rect.top + 15)
        self.screen.blit(week_text, week_rect)
        
        # Draw costs with proper spacing
        y = week_rect.bottom + 15
        for label, value in costs.items():
            text = self.info_font.render(
                f"{label}: ${value:,.2f}",
                True,
                self.COLORS['info_text']
            )
            text_rect = text.get_rect(left=rect.left + 15, top=y)
            self.screen.blit(text, text_rect)
            y += 25  # Increased vertical spacing

    def close(self):
        pygame.quit()