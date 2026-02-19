"""Quick visual test: generates an HTML map of all cities in PostGIS."""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ochv2:ochv2_secure_password@localhost:5433/ochv2_geo"
)

async def export_cities():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT name, ST_Y(location) as lat, ST_X(location) as lng, population
            FROM cities ORDER BY population DESC
        """))
        rows = result.fetchall()
    
    await engine.dispose()

    cities_data = [[r.name, float(r.lat), float(r.lng), r.population] for r in rows]

    html = """<!DOCTYPE html>
<html><head>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body { margin: 0; background: #0a0a0a; }
#map { height: 100vh; }
.leaflet-popup-content-wrapper { background: rgba(0,0,0,0.85); color: #00ff88; border: 1px solid #00ff88; border-radius: 8px; font-family: monospace; }
.leaflet-popup-tip { background: rgba(0,0,0,0.85); }
h2 { color: #00ff88; font-family: monospace; position: fixed; top: 10px; left: 50%%; transform: translateX(-50%%); z-index: 1000; background: rgba(0,0,0,0.7); padding: 8px 20px; border-radius: 8px; border: 1px solid #00ff88; }
</style>
</head><body>
<h2>OurCityHealth V2 — %d Cities Loaded</h2>
<div id="map"></div>
<script>
var map = L.map('map', { preferCanvas: true }).setView([20, 0], 2);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: 'CartoDB',
    maxZoom: 19
}).addTo(map);

var cities = %s;
cities.forEach(function(c) {
    var pop = c[3] ? c[3].toLocaleString() : 'N/A';
    L.circleMarker([c[1], c[2]], {
        radius: Math.max(3, Math.min(10, Math.log10(c[3] || 1))),
        color: '#00ff88',
        fillColor: '#00ff88',
        fillOpacity: 0.7,
        weight: 1
    }).bindPopup('<b>' + c[0] + '</b><br>Pop: ' + pop + '<br>Lat: ' + c[1].toFixed(4) + ' Lng: ' + c[2].toFixed(4)).addTo(map);
});
</script></body></html>""" % (len(cities_data), cities_data)

    output_path = os.path.join(os.path.dirname(__file__), '..', 'city_map.html')
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ Map saved with {len(cities_data)} cities!")
    print(f"   Run: open city_map.html")

asyncio.run(export_cities())
