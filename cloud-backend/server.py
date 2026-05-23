import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: GENERATE DISTINCT PATHS ---
base_lat = 34.0522
base_lng = -118.2437

def create_path(id_num):
    # This creates a unique shape based on the ID
    path = []
    lat, lng = base_lat, base_lng
    
    # Offset start position so they don't all start at exact same spot
    lat += (id_num % 3) * 0.01 
    lng += (id_num % 4) * 0.01

    for i in range(15): # 15 steps per path
        path.append([lat, lng])
        
        # DIFFERENT LOGIC FOR DIFFERENT TYPES
        if id_num in [2, 5, 8, 11]: # FIRE/HAZMAT (Zig Zag)
            if i % 2 == 0: lat += 0.003
            else: lng += 0.003
            
        elif id_num in [3, 9, 12]: # POLICE (Straight Fast Lines)
            lat += 0.005
            lng += 0.001
            
        elif id_num == 15: # UFO (Crazy Pattern)
            lat += random.choice([-0.005, 0.005])
            lng += 0.005
            
        else: # AMBULANCE (Standard City Block movement)
            if i < 7: lng += 0.002
            else: lat += 0.002
            
    return path

# --- THE 15 SCENARIOS DATABASE ---
SCENARIOS = {
    "1": {"vehicle": "AMBULANCE", "color": "#00e676", "desc": "🚑 Cardiac Arrest (Downtown)", "jam": False},
    "2": {"vehicle": "FIRE", "color": "#ff4444", "desc": "🔥 Factory Fire (Zig-Zag Route)", "jam": True},
    "3": {"vehicle": "POLICE", "color": "#2979ff", "desc": "🚓 High Speed Pursuit (Highway)", "jam": False},
    "4": {"vehicle": "HELICOPTER", "color": "#aa00ff", "desc": "🚁 Air Medivac (Direct Line)", "jam": False},
    "5": {"vehicle": "HAZMAT", "color": "#ffea00", "desc": "☣️ Chemical Spill Evac", "jam": True},
    "6": {"vehicle": "CONVOY", "color": "#000000", "desc": "🕴️ VIP Presidential Escort", "jam": False},
    "7": {"vehicle": "AMBULANCE", "color": "#00e676", "desc": "🚑 Multi-Car Pileup", "jam": True},
    "8": {"vehicle": "FIRE", "color": "#ff4444", "desc": "🚒 Forest Fire Response", "jam": False},
    "9": {"vehicle": "POLICE", "color": "#2979ff", "desc": "🚓 Bank Robbery Intercept", "jam": True},
    "10": {"vehicle": "AMBULANCE", "color": "#00e676", "desc": "🚑 Organ Transport", "jam": False},
    "11": {"vehicle": "FIRE", "color": "#ff4444", "desc": "🚒 5-Alarm Blaze", "jam": True},
    "12": {"vehicle": "POLICE", "color": "#2979ff", "desc": "🚓 Prisoner Transport", "jam": False},
    "13": {"vehicle": "RESCUE", "color": "#00bcd4", "desc": "🌊 Flood Rescue Unit", "jam": True},
    "14": {"vehicle": "AMBULANCE", "color": "#00e676", "desc": "🚑 Neonatal ICU Transfer", "jam": False},
    "15": {"vehicle": "ALIEN", "color": "#6200ea", "desc": "🛸 Area 51 Transport", "jam": False},
}

class ScenarioRequest(BaseModel):
    id: str

@app.post("/api/run_scenario")
def run_scenario(req: ScenarioRequest):
    sid = str(req.id)
    if sid in SCENARIOS:
        data = SCENARIOS[sid]
        # Generate the specific path for this ID
        data["path"] = create_path(int(sid))
        return {"status": "SUCCESS", "data": data}
    return {"status": "ERROR"}

# Stats for the dashboard
@app.get("/api/dashboard_stats")
def get_stats():
    return {
        "cpu": random.randint(20, 50),
        "memory": random.randint(40, 70),
        "active_nodes": 241,
        "efficiency": random.randint(85, 99)
    }

# Junction status
@app.get("/api/junction_status")
def get_junc():
    # Simulate random sensors triggering
    return {f"J{i}": (random.random() > 0.9) for i in range(1, 11)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)