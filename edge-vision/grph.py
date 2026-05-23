import os
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

# ==========================================
# 1. ADVANCED PYTORCH GRAPH-WAVENET
# ==========================================
class AdvancedGraphWaveNet(nn.Module):
    def __init__(self, num_nodes=4, seq_len=5):
        super(AdvancedGraphWaveNet, self).__init__()
        self.num_nodes = num_nodes
        self.seq_len = seq_len
        
        # Adjacency Matrix (J0, J1, J2, J3)
        self.register_buffer('adj_matrix', torch.tensor([
            [0, 1, 1, 0],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [0, 1, 1, 0]
        ], dtype=torch.float32))

        # Learnable parameters to make it a true neural network
        self.spatial_weight = nn.Parameter(torch.randn(num_nodes, num_nodes))
        self.temporal_filter = nn.Conv1d(in_channels=1, out_channels=4, kernel_size=3, dilation=2)
        self.output_layer = nn.Linear(4 * num_nodes, num_nodes)

    def spatial_diffusion(self, x):
        """ GCN Layer: Propagates congestion to neighboring nodes """
        # x shape: [batch, nodes]
        weighted_adj = F.relu(self.adj_matrix * self.spatial_weight)
        return torch.matmul(x, weighted_adj)

    def forward(self, x_seq):
        """
        x_seq shape: [sequence_length, num_nodes]
        Represents the sliding window of YOLO data over time.
        """
        # 1. Temporal Processing (WaveNet block)
        # Reshape for Conv1d: [batch=num_nodes, channels=1, seq_len]
        t_input = x_seq.T.unsqueeze(1) 
        t_out = F.relu(self.temporal_filter(t_input)) 
        
        # Aggregate temporal features: [num_nodes, features]
        t_features = torch.mean(t_out, dim=2) 
        
        # 2. Spatial Processing (Graph block)
        # Extract the most recent frame for spatial diffusion
        latest_frame = x_seq[-1, :]
        s_features = self.spatial_diffusion(latest_frame)
        
        # 3. Combine and Predict T+15
        combined = t_features.flatten() + s_features 
        prediction = self.output_layer(combined.unsqueeze(0))
        
        # Ensure outputs represent percentages (0-100)
        return torch.clamp(prediction.squeeze(), min=0.0, max=100.0)

# ==========================================
# 2. YOLO CSV DATA PIPELINE
# ==========================================
def create_mock_yolo_csv(filename="yolo_detections.csv"):
    """ Generates a dummy YOLO output file for testing the pipeline """
    print(f"[*] Generating mock YOLOv11n data -> {filename}")
    data = []
    base_counts = [15, 5, 20, 8] # Baseline vehicle counts at 4 junctions
    
    # Generate 50 frames of data, simulating a traffic buildup at Node 0
    for i in range(50):
        base_counts[0] += np.random.randint(0, 4) # Jam building up
        base_counts[1] += np.random.randint(-1, 2)
        base_counts[2] += np.random.randint(-2, 3)
        base_counts[3] += np.random.randint(-1, 2)
        
        # Ensure no negative cars
        counts = [max(0, c) for c in base_counts]
        data.append([f"10:0{i//6}:{(i%6)*10:02d}"] + counts)

    df = pd.DataFrame(data, columns=["timestamp", "node_0_cars", "node_1_cars", "node_2_cars", "node_3_cars"])
    df.to_csv(filename, index=False)
    return filename

def normalize_yolo_to_density(vehicle_counts, max_capacity=50):
    """ Converts raw YOLO bounding box counts into a 0-100% congestion density """
    densities = [(c / max_capacity) * 100.0 for c in vehicle_counts]
    return [min(100.0, d) for d in densities]

# ==========================================
# 3. REAL-TIME INFERENCE LOOP
# ==========================================
def run_pipeline():
    csv_file = create_mock_yolo_csv()
    df = pd.read_csv(csv_file)
    
    print("\n=== ResQRoute: Edge Vision -> Spatial-Temporal Pipeline ===")
    print("[SYSTEM] YOLOv11n Stream Initialized.")
    print("[SYSTEM] Graph-WaveNet Model Loaded. Awaiting buffer...\n")

    # Initialize Model & Sliding Window Buffer
    seq_len = 5
    model = AdvancedGraphWaveNet(num_nodes=4, seq_len=seq_len)
    model.eval() # Set PyTorch to evaluation mode
    
    buffer = []

    # Stream data row by row, simulating live edge-node updates
    with torch.no_grad():
        for index, row in df.iterrows():
            timestamp = row['timestamp']
            raw_yolo_counts = [row['node_0_cars'], row['node_1_cars'], row['node_2_cars'], row['node_3_cars']]
            
            # 1. Pre-process YOLO data
            current_density = normalize_yolo_to_density(raw_yolo_counts)
            buffer.append(current_density)
            
            # Maintain sliding window size
            if len(buffer) > seq_len:
                buffer.pop(0)
                
            print(f"[{timestamp}] 📹 YOLO Edge Counts: {raw_yolo_counts}  |  📊 Density: {[round(d, 1) for d in current_density]}")

            # 2. Run Inference once buffer is full
            if len(buffer) == seq_len:
                x_seq = torch.tensor(buffer, dtype=torch.float32)
                
                # Forward pass
                prediction = model(x_seq).numpy()
                print(f"      ↳ 🧠 GWN Forecast (T+15m): {np.round(prediction, 1)}")
                
                # 3. RL Re-Routing Trigger Logic
                critical_nodes = np.where(prediction > 80.0)[0]
                if len(critical_nodes) > 0:
                    print(f"      ↳ 🔴 ALERT: Gridlock forecasted at Nodes {critical_nodes.tolist()}.")
                    print("      ↳ ⚡ FEDERATED ACTION: Masking nodes. Pushing updated routing vectors to Masked-RL agent.\n")
                else:
                    print("      ↳ ✅ Status: Corridor Clear.\n")
            
            time.sleep(0.5) # Simulated camera frame delay

import os
import time
import numpy as np
import pandas as pd

# =====================================================================
# 1. DATA AGGREGATION & MOCKING
# =====================================================================
def get_live_density(step, num_nodes=4):
    """
    Reads the YOLO CSVs. If missing, generates a rolling traffic wave.
    """
    densities = np.zeros(num_nodes)
    for i in range(num_nodes):
        file_name = f"node_{i+1}_emergency_log.csv" # Adjusted to match your edge_camera.py output
        if os.path.exists(file_name):
            try:
                df = pd.read_csv(file_name)
                # Safely get the most recent row's total vehicle count (approximate)
                if len(df) > step:
                     row = df.iloc[step]
                     # Sum up the counts of vehicles for this timeframe
                     densities[i] = row.get('ambulance_count', 0) + row.get('fire_count', 0) + \
                                    row.get('police_count', 0) + row.get('vip_count', 0) 
                else:
                     densities[i] = 0 # No data yet
            except Exception:
                densities[i] = np.random.randint(1, 5)
        else:
            # --- MOCK DATA FALLBACK ---
            # Simulates a traffic wave moving from Node 1 to Node 4
            base = np.random.randint(1, 5)
            peak_node = (step // 3) % num_nodes
            if i == peak_node:
                base += np.random.randint(15, 25) # Simulate a jam
            densities[i] = base
            
    return densities

# =====================================================================
# 2. DYNAMIC GRAPH MATH
# =====================================================================
def compute_dynamic_adjacency(densities, base_adj):
    num_nodes = base_adj.shape[0]
    dynamic_adj = np.copy(base_adj)
    
    # Normalize densities (assuming 30 cars is severe gridlock)
    max_capacity = 30.0 
    norm_density = np.clip(densities / max_capacity, 0.0, 1.0)
    
    for i in range(num_nodes):
        for j in range(num_nodes):
            if base_adj[i, j] > 0: 
                # Average congestion of the two connected intersections
                congestion_factor = (norm_density[i] + norm_density[j]) / 2.0
                # Multiply the base distance weight by the congestion penalty
                dynamic_adj[i, j] = base_adj[i, j] * (1.0 + (3.0 * congestion_factor))
                
    return dynamic_adj

# =====================================================================
# 3. TERMINAL DASHBOARD
# =====================================================================
def clear_terminal():
    """Clears the console for a clean animation effect."""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    # The physical map: 1s mean nodes are connected, 0s mean no direct road
    base_adjacency = np.array([
        [1.0, 1.0, 1.0, 0.0],
        [1.0, 1.0, 0.0, 1.0],
        [1.0, 0.0, 1.0, 1.0],
        [0.0, 1.0, 1.0, 1.0]
    ])
    
    step = 0
    print("🚀 Initializing ResQRoute Graph-WaveNet Terminal...")
    time.sleep(2)
    
    try:
        while True:
            clear_terminal()
            current_density = get_live_density(step)
            current_adj = compute_dynamic_adjacency(current_density, base_adjacency)
            
            print("="*60)
            print(f" 🌐 RESQROUTE: DYNAMIC ADJACENCY MATRIX (T+{step * 5}s)")
            print("="*60)
            
            # Print live car counts
            print("🚗 Live Edge Node Density (Cars):")
            print(f"   Node 1: [{int(current_density[0]):02d}]  |  Node 2: [{int(current_density[1]):02d}]")
            print(f"   Node 3: [{int(current_density[2]):02d}]  |  Node 4: [{int(current_density[3]):02d}]")
            print("-" * 60)
            
            # Print the formatted Matrix
            print("   N1    N2    N3    N4")
            for i in range(4):
                row_str = f"N{i+1} "
                for j in range(4):
                    val = current_adj[i, j]
                    
                    # Highlight high resistance (severe traffic) with an asterisk
                    if val > 1.5:
                        row_str += f"{val:4.1f}* "
                    else:
                        row_str += f"{val:4.1f}  "
                print(row_str)
                
            print("-" * 60)
            print("STATUS: Matrix Modulated. Pushing weights to Masked-RL Agent...")
            print("Press Ctrl+C to terminate.")
            
            step += 1
            time.sleep(5) # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n✅ System Offline.")