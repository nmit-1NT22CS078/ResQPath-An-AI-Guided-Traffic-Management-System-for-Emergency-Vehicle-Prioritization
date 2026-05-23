import numpy as np
import heapq
import time

# =====================================================================
# 1. PRIORITY CONGESTION TOLERANCE MATRIX
# =====================================================================
PRIORITY_CONFIG = {
    "FIRE_PRIORITY": {"level": 1, "tolerance": 3.0},       
    "AMBULANCE_PRIORITY": {"level": 2, "tolerance": 2.5},  
    "POLICE_PRIORITY": {"level": 3, "tolerance": 2.0},     
    "VIP_PRIORITY": {"level": 4, "tolerance": 1.2}         
}

# =====================================================================
# 2. THE RL ACTION MASK GENERATOR
# =====================================================================
def generate_action_mask(dynamic_graph, vehicle_type):
    num_nodes = dynamic_graph.shape[0]
    mask = np.zeros((num_nodes, num_nodes))
    config = PRIORITY_CONFIG.get(vehicle_type, {"tolerance": 1.5})
    max_tolerance = config["tolerance"]

    for i in range(num_nodes):
        for j in range(num_nodes):
            if dynamic_graph[i, j] > 0.0:
                if dynamic_graph[i, j] <= max_tolerance:
                    mask[i, j] = 1.0 
                else:
                    mask[i, j] = 0.0 
    return mask

# =====================================================================
# 3. OPTIMAL POLICY EXTRACTION (Masked Routing)
# =====================================================================
def calculate_masked_path(start_node, target_node, dynamic_graph, vehicle_type, silent=False):
    num_nodes = dynamic_graph.shape[0]
    action_mask = generate_action_mask(dynamic_graph, vehicle_type)
    masked_q_space = np.where(action_mask == 1.0, dynamic_graph, np.inf)
    
    distances = {node: float('inf') for node in range(num_nodes)}
    distances[start_node] = 0
    priority_queue = [(0, start_node)]
    previous_nodes = {node: None for node in range(num_nodes)}
    
    while priority_queue:
        current_dist, current_node = heapq.heappop(priority_queue)
        if current_node == target_node: break 
        if current_dist > distances[current_node]: continue
            
        for neighbor in range(num_nodes):
            edge_weight = masked_q_space[current_node, neighbor]
            if edge_weight != np.inf: 
                new_dist = current_dist + edge_weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_dist, neighbor))
                    
    path = []
    curr = target_node
    while curr is not None:
        path.append(curr)
        curr = previous_nodes[curr]
    path.reverse()
    
    if path[0] != start_node:
        if not silent: print(f"   ❌ [ROUTING FAILED] Complete gridlock for {vehicle_type}.")
        return {"status": "FAILED", "path": [], "estimated_cost": float('inf')}
    
    return {
        "status": "SUCCESS",
        "vehicle_type": vehicle_type,
        "path": path,
        "estimated_cost": distances[target_node]
    }

def calculate_cost_of_specific_path(path, dynamic_graph):
    total_cost = 0.0
    for i in range(len(path) - 1):
        weight = dynamic_graph[path[i], path[i+1]]
        if weight == 0.0 or weight == np.inf: return float('inf') 
        total_cost += weight
    return total_cost

# =====================================================================
# 4. THE REAL-TIME MONITORING ENGINE
# =====================================================================
def monitor_active_route(vehicle_id, start_node, target_node, vehicle_type, initial_graph, simulation_steps):
    print(f"\n📡 [TELEMETRY] Initializing Live Tracking for {vehicle_id} ({vehicle_type})")
    
    current_graph = np.copy(initial_graph)
    route_data = calculate_masked_path(start_node, target_node, current_graph, vehicle_type)
    current_path = route_data["path"]
    
    print(f"   📍 INITIAL ROUTE: {' ➔ '.join([f'N{n}' for n in current_path])}")
    
    HYSTERESIS_THRESHOLD = 0.5 
    path_index = 0
    current_node = current_path[path_index]

    for step, new_traffic_graph in enumerate(simulation_steps):
        # Simulate 10-second polling interval visually in terminal
        time.sleep(1.5) 
        time_elapsed = (step + 1) * 10
        print(f"\n⏳ [T+{time_elapsed}s] Polling Graph-WaveNet Data...")
        
        if path_index < len(current_path) - 1:
            path_index += 1
            current_node = current_path[path_index]
        print(f"   🚑 {vehicle_id} is currently at Node_{current_node}")

        if current_node == target_node:
            print(f"   🏁 {vehicle_id} HAS ARRIVED SAFELY at Hospital (Node {target_node}).")
            break

        remaining_old_path = current_path[path_index:]
        old_path_new_cost = calculate_cost_of_specific_path(remaining_old_path, new_traffic_graph)
        
        new_route_data = calculate_masked_path(current_node, target_node, new_traffic_graph, vehicle_type, silent=True)
        best_new_path = new_route_data["path"]
        best_new_cost = new_route_data["estimated_cost"]

        time_saved = old_path_new_cost - best_new_cost
        
        if time_saved > HYSTERESIS_THRESHOLD:
            print(f"   ⚠️ TRAFFIC EVENT DETECTED AHEAD!")
            print(f"   🔄 REROUTING {vehicle_id} dynamically... (Saves {time_saved:.1f} traffic weight)")
            current_path = best_new_path
            path_index = 0 
            print(f"   📍 NEW ROUTE : {' ➔ '.join([f'N{n}' for n in current_path])}")
        else:
            print(f"   ✅ Path clear. Maintaining current route.")

# =====================================================================
# 5. DEMONSTRATION: 2-MINUTE 5x5 GRID SCENARIO
# =====================================================================
def create_city_grid():
    """Creates a 5x5 grid (25 nodes: 0 to 24) representing city blocks."""
    graph = np.zeros((25, 25))
    for i in range(25):
        row, col = i // 5, i % 5
        if col < 4: # Connect right
            graph[i, i+1] = 1.0; graph[i+1, i] = 1.0
        if row < 4: # Connect down
            graph[i, i+5] = 1.0; graph[i+5, i] = 1.0
    return graph

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ResQRoute: 2-Minute Dynamic Edge Routing Simulation")
    print("="*60)
    
    base_graph = create_city_grid()
    steps = []

    # T+10s to T+20s: Normal Driving
    steps.extend([np.copy(base_graph), np.copy(base_graph)])
    
    # T+30s (Event 1): Massive accident on the main diagonal path (Nodes 7, 8, 12)
    s_30 = np.copy(base_graph)
    s_30[7, 8] = s_30[8, 7] = 4.0
    s_30[7, 12] = s_30[12, 7] = 4.0
    steps.append(s_30)
    
    # T+40s: Still rerouting
    steps.append(np.copy(s_30))
    
    # T+50s (Event 2): The detour (Node 11 to 16) gets congested too!
    s_50 = np.copy(s_30)
    s_50[11, 16] = s_50[16, 11] = 3.5
    steps.append(s_50)
    
    # T+60s to T+70s: Driving on outer ring
    steps.extend([np.copy(s_50), np.copy(s_50)])
    
    # T+80s (Event 3): Original central accident clears! Highway opens up.
    s_80 = np.copy(s_50)
    s_80[7, 8] = s_80[8, 7] = 1.0
    s_80[7, 12] = s_80[12, 7] = 1.0
    steps.append(s_80)
    
    # T+90s: Driving back to the fast route
    steps.append(np.copy(s_80))
    
    # T+100s (Event 4): Minor jam at Node 19.
    s_100 = np.copy(s_80)
    s_100[18, 19] = s_100[19, 18] = 2.5
    steps.append(s_100)
    
    # T+110s to T+120s: Final approach to Node 24
    steps.extend([np.copy(s_100), np.copy(s_100)])

    # RUN THE 2-MINUTE SIMULATION
    monitor_active_route(
        vehicle_id="AMBULANCE_ALPHA",
        start_node=0,
        target_node=24,
        vehicle_type="AMBULANCE_PRIORITY", 
        initial_graph=base_graph,
        simulation_steps=steps
    )
    print("="*60)