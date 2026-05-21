import logging
from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from dataclasses import dataclass

from apps.trips.domain import (
    Coordinate, 
    FuelStationDTO, 
    FuelStop, 
    VehicleConfig, 
    OptimizationResult,
    RouteMetadata
)
from services.fuel.candidate_reduction import CandidateStation

logger = logging.getLogger("services.fuel")

@dataclass
class Node:
    """Represents a node in the optimization graph."""
    id: str
    distance_along_route: float
    price_per_gallon: float
    station: Optional[FuelStationDTO] = None

class FuelOptimizerService:
    """
    Solves the min-cost fuel stop problem using Dynamic Programming.
    Optimized for long-distance routes with a vehicle range constraint.
    """

    def optimize(
        self,
        route_metadata: RouteMetadata,
        candidates: List[CandidateStation],
        vehicle_config: VehicleConfig = VehicleConfig()
    ) -> OptimizationResult:
        """
        Runs the optimization algorithm.
        Constructs a DAG and finds the shortest (cheapest) path.
        """
        logger.info(f"Optimizing fuel stops for route: {route_metadata.origin} -> {route_metadata.destination}")
        
        # 1. Prepare Nodes: Start + Candidates + End
        nodes = self._prepare_nodes(route_metadata, candidates)
        
        # 2. Run Dynamic Programming (Shortest Path in DAG)
        # min_cost[i] = (total_cost, parent_index)
        n = len(nodes)
        min_cost = [float('inf')] * n
        parents = [-1] * n
        
        min_cost[0] = 0.0
        
        for i in range(n):
            if min_cost[i] == float('inf'):
                continue
                
            # Look ahead for reachable nodes
            for j in range(i + 1, n):
                distance = nodes[j].distance_along_route - nodes[i].distance_along_route
                
                # Check if reachable within max range
                if distance > vehicle_config.max_range_miles:
                    # Since nodes are sorted by distance, we can break early
                    break
                
                # Calculate cost to travel this segment
                # We assume for this phase we refuel at node i to reach node j
                gallons_needed = distance / vehicle_config.miles_per_gallon
                cost_of_segment = gallons_needed * nodes[i].price_per_gallon
                
                new_total_cost = min_cost[i] + cost_of_segment
                
                if new_total_cost < min_cost[j]:
                    min_cost[j] = new_total_cost
                    parents[j] = i

        # 3. Reconstruct Path
        if min_cost[-1] == float('inf'):
            logger.error("No valid fuel path found within vehicle range constraints.")
            return self._empty_result(route_metadata, vehicle_config)

        path_indices = []
        curr = parents[-1]
        while curr != -1:
            if nodes[curr].station:  # Don't include the 'Start' node as a fuel stop
                path_indices.append(curr)
            curr = parents[curr]
        path_indices.reverse()

        # 4. Generate Fuel Stops
        fuel_stops = self._build_fuel_stops(nodes, path_indices, parents, vehicle_config)
        
        total_gallons = route_metadata.total_distance_miles / vehicle_config.miles_per_gallon
        
        return OptimizationResult(
            route_metadata=route_metadata,
            fuel_stops=fuel_stops,
            total_fuel_cost=round(min_cost[-1], 2),
            total_gallons=round(total_gallons, 2),
            vehicle_config=vehicle_config
        )

    def _prepare_nodes(
        self, 
        route: RouteMetadata, 
        candidates: List[CandidateStation]
    ) -> List[Node]:
        """Creates a sorted list of nodes including start, candidates, and end."""
        nodes = []
        
        # Start node (we assume starting with full tank, but price 0 for calculation if needed)
        # Actually, the cost is incurred at the stop. 
        # If we start at NYC, we don't pay anything there to reach the first stop?
        # Requirement: "Return total money spent on fuel"
        # Let's assume we start with 0 fuel or pay at the start. 
        # Usually, for these assignments, you pay for what you consume.
        # We'll use the average price of the first stop or a baseline.
        # Senior approach: Use a "virtual" start node with the first station's price 
        # or the cheapest nearby station's price at the origin.
        
        # To simplify, we'll assume the vehicle pays the price of the 'origin' station 
        # for the first segment. If no origin price is provided, we use the first stop's price.
        # But wait, the dataset only has truck stops.
        
        # Practical compromise: The start node has the price of the first reachable station.
        first_price = float(candidates[0].station.price_per_gallon) if candidates else 0.0
        
        nodes.append(Node(id="START", distance_along_route=0.0, price_per_gallon=first_price))
        
        for c in candidates:
            nodes.append(Node(
                id=str(c.station.id),
                distance_along_route=c.distance_along_route,
                price_per_gallon=float(c.station.price_per_gallon),
                station=c.station
            ))
            
        nodes.append(Node(
            id="END", 
            distance_along_route=route.total_distance_miles, 
            price_per_gallon=0.0 # No cost at the destination
        ))
        
        # Sort by distance (candidates should already be sorted)
        nodes.sort(key=lambda x: x.distance_along_route)
        return nodes

    def _build_fuel_stops(
        self, 
        nodes: List[Node], 
        path_indices: List[int], 
        parents: List[int],
        vehicle_config: VehicleConfig
    ) -> List[FuelStop]:
        """
        Converts the optimal sequence of nodes into intelligent FuelStop DTOs.
        Implements the 'Greedy with Lookahead' purchasing strategy:
        1. If a cheaper station exists ahead in the path, buy just enough to reach it.
        2. If this is the cheapest station ahead, fill the tank to maximize savings.
        """
        stops = []
        
        # 1. Reconstruct the sequence: Start -> S1 -> S2 -> ... -> End
        sequence_indices = []
        curr = len(nodes) - 1
        while curr != -1:
            sequence_indices.append(curr)
            curr = parents[curr]
        sequence_indices.reverse()
        
        # 2. Iterate through the sequence and decide how much to buy at each station
        # fuel_level_miles track how many miles the vehicle can currently travel
        fuel_level_miles = 0.0
        
        for i in range(len(sequence_indices) - 1):
            curr_idx = sequence_indices[i]
            next_idx = sequence_indices[i+1]
            
            curr_node = nodes[curr_idx]
            next_node = nodes[next_idx]
            
            # If this is not a fuel station (e.g. START), skip stop creation
            # but update fuel level (we assume starting with 0 or a fixed amount)
            if not curr_node.station:
                distance_to_next = next_node.distance_along_route - curr_node.distance_along_route
                fuel_level_miles = max(0, fuel_level_miles - distance_to_next)
                continue

            # Intelligent Purchasing Strategy:
            # Look ahead in the remaining path to see if there's a cheaper station
            cheaper_ahead_idx = -1
            for j in range(i + 1, len(sequence_indices)):
                lookahead_node = nodes[sequence_indices[j]]
                if lookahead_node.station and lookahead_node.price_per_gallon < curr_node.price_per_gallon:
                    cheaper_ahead_idx = sequence_indices[j]
                    break
            
            distance_to_next = next_node.distance_along_route - curr_node.distance_along_route
            
            if cheaper_ahead_idx != -1:
                # A cheaper station exists ahead. 
                # Strategy: Buy just enough to reach the cheaper station (or the next stop)
                # To be safe and simple, we'll buy just enough to reach the next stop in our optimal sequence.
                # Since the DP already picked this sequence, we know it's reachable.
                
                miles_needed = max(0, distance_to_next - fuel_level_miles)
                gallons_to_buy = miles_needed / vehicle_config.miles_per_gallon
                
                # After buying and traveling to next:
                new_fuel_level_miles = 0.0 # Arrive empty at next
            else:
                # This is the cheapest station reachable in our path.
                # Strategy: Fill the tank to the maximum capacity.
                
                miles_to_fill = vehicle_config.max_range_miles - fuel_level_miles
                gallons_to_buy = miles_to_fill / vehicle_config.miles_per_gallon
                
                # After buying and traveling to next:
                new_fuel_level_miles = vehicle_config.max_range_miles - distance_to_next

            cost = gallons_to_buy * curr_node.price_per_gallon
            
            stops.append(FuelStop(
                station=curr_node.station,
                gallons_to_buy=round(gallons_to_buy, 2),
                cost=round(cost, 2),
                distance_from_start=curr_node.distance_along_route,
                remaining_range_after_refuel=round(fuel_level_miles + (gallons_to_buy * vehicle_config.miles_per_gallon), 2)
            ))
            
            fuel_level_miles = new_fuel_level_miles

        return stops

    def _empty_result(self, route: RouteMetadata, config: VehicleConfig) -> OptimizationResult:
        return OptimizationResult(
            route_metadata=route,
            fuel_stops=[],
            total_fuel_cost=0.0,
            total_gallons=0.0,
            vehicle_config=config
        )
