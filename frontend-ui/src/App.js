import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// --- 1. PROFESSIONAL ICONS ---
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const getIcon = (type, status) => {
    let url = 'https://img.icons8.com/fluency/48/ambulance.png';
    if (type === 'FIRE') url = 'https://img.icons8.com/fluency/48/fire-truck.png';
    if (type === 'VIP') url = 'https://img.icons8.com/color/48/suv.png'; 
    
    return new L.Icon({ 
        iconUrl: url, 
        iconSize: [35, 35], 
        iconAnchor: [17, 17],
        className: status === 'WAITING' ? 'vehicle-stopped' : ''
    });
};

const jamIcon = new L.Icon({ 
    iconUrl: 'https://img.icons8.com/color/48/roadblock.png', 
    iconSize: [40, 40] 
});

// --- 2. DEMO COORDINATES ---
const LOCS = {
    MAIN_START: [34.0522, -118.2437], 
    MAIN_END: [34.0407, -118.2468],   
    DETOUR_MID: [34.0450, -118.2410], 
    CROSS_START: [34.0450, -118.2350],
    CROSS_END: [34.0450, -118.2550]
};

// --- 3. DYNAMIC MULTI-POINT API FETCH ---
const fetchPathAPI = async (points) => {
    const coordsString = points.map(p => `${p[1]},${p[0]}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsString}?overview=full&geometries=geojson`;
    
    const res = await fetch(url);
    if (!res.ok) throw new Error("API Blocked");
    
    const data = await res.json();
    return data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
};

function MapController({ center }) {
    const map = useMap();
    useEffect(() => {
        if(center) map.flyTo(center, 16, { duration: 1, easeLinearity: 0.5 }); 
    }, [center, map]);
    return null;
}

function App() {
    const [isReady, setIsReady] = useState(false);
    const [routes, setRoutes] = useState({});
    const [jamIndexPoint, setJamIndexPoint] = useState(0); 
    
    const [vehicles, setVehicles] = useState([]);
    const [alert, setAlert] = useState(null);
    const [scenarioTitle, setScenarioTitle] = useState("INITIALIZING AI PIPELINE...");
    const [telemetry, setTelemetry] = useState({
        speed: 0, status: 'BOOTING...', gwnetPred: 'N/A', nodesMasked: 0, flSync: 'Connecting...'
    });

    const [blockedPath, setBlockedPath] = useState(null);
    const [detourPath, setDetourPath] = useState(null);
    const [jamLocation, setJamLocation] = useState(null);
    const simRef = useRef(null);

    // --- PRE-LOADER ---
    useEffect(() => {
        const loadRoutes = async () => {
            try {
                const main = await fetchPathAPI([LOCS.MAIN_START, LOCS.MAIN_END]);
                await new Promise(r => setTimeout(r, 600)); 
                
                const jamIdx = Math.floor(main.length * 0.35);
                setJamIndexPoint(jamIdx);
                const jamCoordinate = main[jamIdx];

                const detour = await fetchPathAPI([jamCoordinate, LOCS.DETOUR_MID, LOCS.MAIN_END]);
                await new Promise(r => setTimeout(r, 600));

                const cross = await fetchPathAPI([LOCS.CROSS_START, LOCS.CROSS_END]);

                setRoutes({ main, detour, cross });
                setIsReady(true);
                setScenarioTitle("SYSTEM READY");
                setTelemetry({ speed: 0, status: 'STANDBY', gwnetPred: 'Network Scanned', nodesMasked: 0, flSync: 'Synced to GCP' });

            } catch (e) {
                console.error(e);
                setScenarioTitle("API RATE LIMIT HIT - REFRESH IN 60s");
            }
        };
        loadRoutes();
    }, []);

    const reset = () => {
        if(simRef.current) clearInterval(simRef.current);
        setVehicles([]); setAlert(null); setBlockedPath(null); setDetourPath(null); setJamLocation(null);
        setTelemetry({ speed: 0, status: 'STANDBY', gwnetPred: 'Monitoring...', nodesMasked: 0, flSync: 'Synced 1s ago' });
    };

    // =======================================================
    // SCENARIO 1: DYNAMIC REROUTING
    // =======================================================
    const runJamScenario = (type) => {
        if (!isReady) return;
        reset();
        setScenarioTitle(type === 'JAM' ? "🚑 SCENARIO 1: DYNAMIC REROUTING" : "🌊 SCENARIO 2: FLOODED UNDERPASS");
        
        const path = routes.main;
        setVehicles([{ id: 'v1', type: 'AMBULANCE', path, idx: 0, status: 'MOVING' }]);
        setTelemetry(t => ({ ...t, speed: 45, status: 'EN ROUTE', gwnetPred: 'Clear (12%)' }));

        let tick = 0;
        // SLOWED DOWN: Interval from 100ms to 200ms
        simRef.current = setInterval(() => {
            tick++;

            if(tick < jamIndexPoint - 5) setTelemetry(t => ({ ...t, speed: Math.floor(Math.random() * (50 - 40 + 1) + 40) }));

            if(tick === jamIndexPoint) {
                clearInterval(simRef.current);
                setAlert(type === 'JAM' ? "⚠️ TRAFFIC CONGESTION DETECTED" : "⚠️ SEVERE WATERLOGGING DETECTED");
                setTelemetry({ speed: 0, status: 'BLOCKED', gwnetPred: 'SEVERE (98%)', nodesMasked: 0, flSync: 'Pushing Alert...' });
                
                setBlockedPath(path.slice(jamIndexPoint)); 
                setJamLocation(path[jamIndexPoint + 5]); 

                setTimeout(() => {
                    setAlert("✅ OPTIMIZED BYPASS ROUTE ENGAGED");
                    setDetourPath(routes.detour); 
                    setTelemetry({ speed: 0, status: 'REROUTING', gwnetPred: 'Bypass Clear', nodesMasked: 14, flSync: 'Global Model Updated' });
                    
                    let subTick = 0; 
                    // SLOWED DOWN
                    simRef.current = setInterval(() => {
                        subTick++;
                        setTelemetry(t => ({ ...t, speed: 35, status: 'EN ROUTE (DETOUR)' }));
                        
                        if(subTick < routes.detour.length) {
                            setVehicles([{ id: 'v1', type: 'AMBULANCE', path: routes.detour, idx: subTick, status: 'MOVING' }]);
                        } else { 
                            clearInterval(simRef.current); 
                            setTelemetry(t => ({ ...t, speed: 0, status: 'ARRIVED' })); 
                        }
                    }, 200); 
                    setTimeout(() => setAlert(null), 2000);
                }, 1500);
            } else if(tick < path.length) {
                setVehicles(prev => [{...prev[0], idx: tick}]);
            }
        }, 350);
    };

    
    // =======================================================
    // SCENARIO 3: PLATOON VS VIP (BRUTE-FORCE VISUAL GUARANTEE)
    // =======================================================
    const runPlatoonVsVIP = () => {
        if (!isReady) return;
        reset();
        setScenarioTitle("🚨 SCENARIO 3: PLATOON VS VIP CONVOY");

        // Set initial positions
        let fireIdx = 25; // Fire Truck in the lead
        let ambIdx = 0;   // Ambulance trailing
        let vipIdx = 0;   // VIP driving perpendicular

        setVehicles([
            { id: 'fire', type: 'FIRE', path: routes.main, idx: fireIdx, status: 'MOVING' }, 
            { id: 'amb', type: 'AMBULANCE', path: routes.main, idx: ambIdx, status: 'MOVING' }, 
            { id: 'vip', type: 'VIP', path: routes.cross, idx: vipIdx, status: 'MOVING' } 
        ]);

        let tick = 0;
        let vipIsLocked = false;
        let platoonHasCleared = false;

        simRef.current = setInterval(() => {
            tick++;

            // 1. Initial Alert
            if (tick === 5) {
                setAlert("⚠️ FIRE PLUS AMBULANCE ON THE WAY! VIP ROUTE INTERSECTED.");
            }

            // 2. Hard-lock the VIP right before the intersection
            if (vipIdx === 25 && !platoonHasCleared) {
                vipIsLocked = true;
                if (tick > 10) { // Just to ensure it doesn't immediately overwrite the first alert
                    setAlert("🛑 VIP CONVOY HALTED - YIELDING TO PLATOON");
                    setTelemetry(t => ({ ...t, speed: 0, status: 'VIP HALTED', gwnetPred: 'Platoon Passing' }));
                }
            }

            // 3. Unlock the VIP only when the trailing ambulance clears the intersection (index 70)
            if (ambIdx === 70) {
                platoonHasCleared = true;
                vipIsLocked = false;
                setAlert("✅ PLATOON CLEARED - VIP RESUMING");
                setTelemetry(t => ({ ...t, speed: 45, status: 'RESUMING' }));
                setTimeout(() => setAlert(null), 3000);
            }

            // 4. Update coordinates based on locks
            if (fireIdx < 99) fireIdx++;
            if (ambIdx < 99) ambIdx++;
            if (!vipIsLocked && vipIdx < 99) vipIdx++;

            // 5. Render to screen
            setVehicles([
                { id: 'fire', type: 'FIRE', path: routes.main, idx: fireIdx, status: 'MOVING' },
                { id: 'amb', type: 'AMBULANCE', path: routes.main, idx: ambIdx, status: 'MOVING' },
                { id: 'vip', type: 'VIP', path: routes.cross, idx: vipIdx, status: vipIsLocked ? 'WAITING' : 'MOVING' }
            ]);

            // End simulation when everyone reaches the end
            if (fireIdx >= 99 && ambIdx >= 99 && vipIdx >= 99) {
                clearInterval(simRef.current);
            }

        }, 350); 
    };

    // =======================================================
    // STANDARD INTERSECTIONS
    // =======================================================
    const runIntersection = (v1Type, v2Type, winner, title) => {
        if (!isReady) return;
        reset();
        setScenarioTitle(title);
        
        const p1 = routes.cross;
        const p2 = routes.main;

        setVehicles([
            { id: 'v1', type: v1Type, path: p1, idx: 0, status: 'MOVING' },
            { id: 'v2', type: v2Type, path: p2, idx: 0, status: 'MOVING' }
        ]);

        let tick = 0;
        // SLOWED DOWN
        simRef.current = setInterval(() => {
            tick++;
            const CONFLICT = Math.floor(p2.length * 0.45); 
            
            if(tick === CONFLICT - 10) setAlert("⚠️ INTERSECTION CONFLICT DETECTED");

            if(tick >= CONFLICT - 5 && tick <= CONFLICT + 15) {
                if(tick === CONFLICT - 4) setAlert(`🛑 STOPPING ${v2Type} (LOWER PRIORITY)`);

                setVehicles(prev => prev.map(v => {
                    if(v.type === winner) return {...v, idx: v.idx + 1 < v.path.length ? v.idx + 1 : v.idx}; 
                    else return {...v, status: 'WAITING'}; // Loser waits
                }));
            } else {
                if(tick === CONFLICT + 16) setAlert("✅ INTERSECTION CLEAR");
                if(tick === CONFLICT + 25) setAlert(null);
                setVehicles(prev => prev.map(v => ({...v, idx: v.idx + 1 < v.path.length ? v.idx + 1 : v.idx, status: 'MOVING'})));
            }
        }, 350); 
    };

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#111', color: 'white', fontFamily: 'Arial, sans-serif' }}>
            
            {alert && (
                <div style={{
                    position: 'absolute', top: '15%', left: '50%', transform: 'translate(-50%, -50%)',
                    zIndex: 9999, background: 'rgba(50, 0, 0, 0.95)', padding: '20px 40px',
                    border: '2px solid red', borderRadius: '8px', textAlign: 'center', boxShadow: '0 0 30px rgba(255,0,0,0.8)'
                }}>
                    <h2 style={{margin:0, fontSize:'22px', color:'#ff4d4d', fontWeight:'bold', textTransform: 'uppercase'}}>{alert}</h2>
                </div>
            )}

            <div style={{ padding: '15px 20px', background: '#0a0a0a', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ margin: 0, fontSize: '20px', letterSpacing:'1px', fontWeight: '900' }}>ResQRoute <span style={{color:'#00e676', fontWeight: '400'}}>ENGINEERING DEMO</span></h1>
                <div style={{ fontSize: '14px', fontWeight:'bold', color: isReady ? '#00e676' : '#ffb700', backgroundColor: isReady ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255, 183, 0, 0.1)', padding: '5px 15px', borderRadius: '20px' }}>
                    {scenarioTitle}
                </div>
            </div>

            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                <div style={{ width: '280px', background: '#151515', padding: '20px', borderRight:'1px solid #333', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
                    <div style={{color:'#888', fontSize:'12px', letterSpacing: '1px', fontWeight: 'bold', textTransform:'uppercase', marginBottom:'5px'}}>Simulations</div>
                    
                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={() => runJamScenario('JAM')}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🚑 1. Dynamic Rerouting</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>Flawless mid-route turn off</div>
                    </button>

                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={() => runJamScenario('FLOOD')}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🌊 2. FL Weather Event</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>Flooded underpass global mask</div>
                    </button>

                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={runPlatoonVsVIP}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🚨 3. Platoon vs VIP</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>VIP yields to Fire + Ambulance</div>
                    </button>
                    
                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={() => runIntersection('FIRE', 'AMBULANCE', 'FIRE', '🔥 4: FIRE VS AMBULANCE')}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🔥 4. Fire vs Ambulance</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>Priority 1 overrides Priority 2</div>
                    </button>

                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={() => runIntersection('AMBULANCE', 'VIP', 'AMBULANCE', '🚨 5: VIP VS AMBULANCE')}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🚨 5. VIP vs Ambulance</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>VIP Convoy yields to Medics</div>
                    </button>

                    <button style={btnStyle(isReady)} disabled={!isReady} onClick={() => runIntersection('FIRE', 'VIP', 'FIRE', '🚒 6: FIRE VS VIP')}>
                        <div style={{fontWeight:'bold', fontSize: '14px'}}>🚒 6. Fire Engine vs VIP</div>
                        <div style={{fontSize:'11px', color:'#aaa', marginTop: '4px'}}>Convoy halted for Fire response</div>
                    </button>
                    
                    <button style={{...btnStyle(isReady), border: '1px solid #666', marginTop: '10px'}} disabled={!isReady} onClick={reset}>
                        <div style={{fontWeight:'bold', fontSize: '14px', textAlign:'center'}}>⏹️ RESET SYSTEM</div>
                    </button>
                </div>

                <div style={{ flex: 1, position: 'relative' }}>
                    <MapContainer center={LOCS.MAIN_START} zoom={16} style={{ height: '100%', width: '100%', background: '#f5f5f5' }}>
                        <TileLayer 
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" 
                            attribution='&copy; OpenStreetMap contributors'
                        />
                        
                        {vehicles.length > 0 && vehicles[0].path && vehicles[0].path[vehicles[0].idx] && (
                            <MapController center={vehicles[0].path[vehicles[0].idx]} />
                        )}
                        
                        {blockedPath && <Polyline positions={blockedPath} color="#000000" weight={7} opacity={0.6} dashArray="10, 10" />}
                        {detourPath && <Polyline positions={detourPath} color="#00cc00" weight={7} opacity={0.9} />}
                        {jamLocation && <Marker position={jamLocation} icon={jamIcon} />}

                        {vehicles.map(v => {
                            if(!v.path || !v.path[v.idx]) return null;
                            
                            let lineColor = '#0055ff'; 
                            if (v.type === 'FIRE') lineColor = '#cc0000'; 
                            if (v.type === 'VIP') lineColor = '#4a0080'; 

                            return (
                                <React.Fragment key={v.id}>
                                    <Polyline positions={v.path} color={lineColor} weight={6} opacity={0.8} />
                                    <Marker position={v.path[v.idx]} icon={getIcon(v.type, v.status)}>
                                        <Popup>{v.type}</Popup>
                                    </Marker>
                                </React.Fragment>
                            );
                        })}
                    </MapContainer>
                </div>

                <div style={{ width: '300px', background: '#151515', padding: '20px', borderLeft:'1px solid #333', display: 'flex', flexDirection: 'column' }}>
                    <div style={{color:'#888', fontSize:'12px', letterSpacing: '1px', fontWeight: 'bold', textTransform:'uppercase', borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '20px'}}>
                        📡 Live Telemetry
                    </div>

                    <div style={telemetryBox}>
                        <div style={telemetryLabel}>VEHICLE STATUS</div>
                        <div style={{fontSize: '18px', fontWeight: 'bold', color: telemetry.status.includes('BLOCKED') || telemetry.status.includes('YIELDING') || telemetry.status.includes('HALTED') ? '#ff4d4d' : '#00e676'}}>{telemetry.status}</div>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                        <div style={{...telemetryBox, flex: 1, marginBottom: 0}}>
                            <div style={telemetryLabel}>SPEED</div>
                            <div style={{fontSize: '24px', fontWeight: 'bold'}}>{telemetry.speed} <span style={{fontSize: '12px', color: '#888'}}>km/h</span></div>
                        </div>
                        <div style={{...telemetryBox, flex: 1, marginBottom: 0}}>
                            <div style={telemetryLabel}>LATENCY</div>
                            <div style={{fontSize: '24px', fontWeight: 'bold', color: '#00bfff'}}>12 <span style={{fontSize: '12px', color: '#888'}}>ms</span></div>
                        </div>
                    </div>

                    <div style={telemetryBox}>
                        <div style={telemetryLabel}>GRAPH-WAVENET FORECAST</div>
                        <div style={{fontSize: '16px', color: '#ffb700'}}>{telemetry.gwnetPred}</div>
                    </div>

                    <div style={telemetryBox}>
                        <div style={telemetryLabel}>RL NODES MASKED</div>
                        <div style={{fontSize: '20px', fontWeight: 'bold'}}>{telemetry.nodesMasked} <span style={{fontSize: '12px', color: '#888'}}>edges dropped</span></div>
                    </div>

                    <div style={{...telemetryBox, borderLeft: '4px solid #b142f5'}}>
                        <div style={telemetryLabel}>FEDERATED LEARNING SYNC</div>
                        <div style={{fontSize: '14px', color: '#ccc'}}>{telemetry.flSync}</div>
                    </div>
                </div>
            </div>

            <style>{`
                .vehicle-stopped { filter: grayscale(100%) brightness(50%); transition: all 0.3s; }
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-track { background: #111; }
                ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
                ::-webkit-scrollbar-thumb:hover { background: #555; }
            `}</style>
        </div>
    );
}

const btnStyle = (isReady) => ({
    width: '100%', padding: '12px 15px', background: isReady ? '#252525' : '#1a1a1a', 
    color: isReady ? '#fff' : '#555', border: '1px solid #444', borderRadius: '8px', cursor: isReady ? 'pointer' : 'not-allowed', textAlign: 'left',
    transition: 'all 0.2s', boxShadow: isReady ? '0 4px 6px rgba(0,0,0,0.3)' : 'none'
});

const telemetryBox = {
    background: '#222', padding: '15px', borderRadius: '8px', marginBottom: '15px', border: '1px solid #333'
};

const telemetryLabel = {
    fontSize: '10px', color: '#888', marginBottom: '5px', fontWeight: 'bold'
};

export default App;