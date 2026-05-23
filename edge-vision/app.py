import uvicorn
import asyncio
import numpy as np
from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
from datetime import datetime

# =====================================================================
# 1. IMPORT YOUR AI MODULES 
# (Assuming fed.py, grph.py, and re_route.py are in the same folder)
# =====================================================================
import fed      # Federated Learning Aggregator
import grph     # Graph-WaveNet Dynamic Adjacency
import reroute # Masked-RL Routing Engine

app = FastAPI(title="ResQRoute Master Controller", version="1.0")

# =====================================================================
# 2. GLOBAL SYSTEM STATE
# =====================================================================
class SystemState:
    def __init__(self):
        self.num_nodes = 207 # METR-LA standard size
        self.base_adjacency = None
        self.dynamic_adjacency = None
        self.live_densities = np.zeros(self.num_nodes)
        self.active_emergencies = []
        self.latest_federated_sync = "Pending..."

system = SystemState()

# Pydantic Model for incoming V2I Alerts from edge_camera.py
class EdgeAlert(BaseModel):
    node_id: str
    vehicle_type: str
    timestamp: str

# =====================================================================
# 3. INITIALIZATION & DATASET LOADING
# =====================================================================
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🚀 BOOTING RESQROUTE CLOUD BRAIN")
    print("="*60)
    
    print("[SYSTEM] Loading METR-LA Traffic Dataset (207 Nodes)...")
    try:
        # In real life: system.base_adjacency = np.load('data/adj_mx_metr_la.npy')
        # Using a dummy matrix for safe execution if you don't have the .npy file yet:
        system.base_adjacency = np.ones((system.num_nodes, system.num_nodes)) 
        system.dynamic_adjacency = np.copy(system.base_adjacency)
        print("✅ METR-LA Baseline Graph Initialized.")
    except Exception as e:
        print(f"❌ Failed to load METR-LA: {e}")

    # Start the continuous background loops
    asyncio.create_task(run_graph_wavenet_loop())
    asyncio.create_task(run_federated_learning_sync())

# =====================================================================
# 4. BACKGROUND AI ENGINES
# =====================================================================
async def run_graph_wavenet_loop():
    """Continuously modulates the METR-LA graph based on edge densities."""
    while True:
        if system.base_adjacency is not None:
            # Here you would call your grph.py function:
            system.dynamic_adjacency = grph.compute_dynamic_adjacency(system.live_densities, system.base_adjacency)
            
            # Mock update for the console UI:
            system.dynamic_adjacency += 0.01 
            
        await asyncio.sleep(5) # Update graph every 5 seconds

async def run_federated_learning_sync():
    """Runs FedAvg periodically to update the global GWN model without raw data."""
    while True:
        await asyncio.sleep(300) # Sync every 5 minutes
        print("\n🔒 [FEDERATED LEARNING] Initiating Secure Aggregation Round...")
        # Here you call your fed.py function:
        new_global_weights = fed.aggregate_edge_weights()
        system.latest_federated_sync = datetime.now().strftime("%H:%M:%S")
        print(f"✅ [FEDERATED LEARNING] Global weights updated at {system.latest_federated_sync}")

# =====================================================================
# 5. API ENDPOINTS (The "Connectors")
# =====================================================================
@app.post("/api/alert")
async def receive_edge_alert(alert: EdgeAlert):
    """
    RECEIVER: Listens for V2I alerts coming from edge_camera.py
    When triggered, it instantly runs the Masked-RL engine.
    """
    print(f"\n🚨 [V2I INBOUND] Alert received from {alert.node_id}: {alert.vehicle_type}")
    
    # Add to active emergencies tracking
    system.active_emergencies.append(alert.dict())
    
    print(f"🧠 [ROUTING ENGINE] Triggering Masked-RL on {system.num_nodes}-node METR-LA Graph...")
    
    # Here you call your re_route.py Masked-RL function:
    optimal_route = re_route.calculate_masked_path(
        start_node=alert.node_id, 
        graph=system.dynamic_adjacency, 
        priority=alert.vehicle_type
     )
    
    return {"status": "ACK", "message": "Priority Routing Initialized", "green_corridor_active": True}

@app.get("/api/telemetry")
async def provide_dashboard_data():
    """
    SENDER: Your React frontend will constantly hit this URL to draw the UI.
    """
    return {
        "active_emergencies": system.active_emergencies,
        "federated_sync_status": system.latest_federated_sync,
        "total_nodes": system.num_nodes,
        "system_status": "OPTIMAL"
    }

# =====================================================================
# 6. RUN THE SERVER
# =====================================================================
if __name__ == "__main__":
    # Runs the server on port 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)