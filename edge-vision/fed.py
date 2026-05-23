import time
import random
import json

class ResQRouteGlobalServer:
    def __init__(self):
        self.global_weights = {"weights": [random.uniform(0, 1) for _ in range(5)]}
        self.round = 0

    def aggregate(self, local_updates):
        print(f"\n[GLOBAL SERVER] Round {self.round} - Aggregating updates from {len(local_updates)} Edge Nodes...")
        # Simulating Federated Averaging (FedAvg)
        new_weights = []
        for i in range(5):
            avg = sum(u["weights"][i] for u in local_updates) / len(local_updates)
            new_weights.append(avg)
        self.global_weights["weights"] = new_weights
        self.round += 1
        print(f"[GLOBAL SERVER] Global Model Updated. Broadcasted to all junctions.")

class EdgeJunctionNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.local_data_size = random.randint(100, 500)

    def train_locally(self, global_weights):
        print(f"  [NODE {self.node_id}] Training on {self.local_data_size} local traffic samples...")
        time.sleep(1) # Simulating compute time
        # Simulate local weight adjustment based on "local congestion patterns"
        noise = random.uniform(-0.05, 0.05)
        local_weights = [w + noise for w in global_weights["weights"]]
        return {"node": self.node_id, "weights": local_weights}

def run_federated_demo():
    print("--- ResQRoute Federated Intelligence Engine ---")
    server = ResQRouteGlobalServer()
    nodes = [EdgeJunctionNode("J-North"), EdgeJunctionNode("J-South"), EdgeJunctionNode("J-West")]

    try:
        while True:
            local_updates = []
            print(f"\n--- Starting Communication Round {server.round} ---")
            
            for node in nodes:
                # 1. Local Training
                update = node.train_locally(server.global_weights)
                local_updates.append(update)
            
            # 2. Aggregation
            server.aggregate(local_updates)
            
            print("\n[SYSTEM] Synchronizing weights across V2X network...")
            time.sleep(3) # Wait before next round
            
    except KeyboardInterrupt:
        print("\n[SYSTEM] Federated training suspended.")

if __name__ == "__main__":
    run_federated_demo()