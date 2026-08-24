"""
Generator Peta Panas Curah Hujan Indonesia

Skrip ini mengambil data curah hujan real-time untuk kota-kota di Indonesia
menggunakan Open-Meteo API dan membuat visualisasi heatmap interaktif
dengan kontrol lapisan untuk membedakan daerah hujan dan tidak hujan.
"""
import json
import requests
import folium
from folium.plugins import HeatMap
from folium import LinearColormap, FeatureGroup, LayerControl
from datetime import datetime

"""
1. Load data kota
"""
with open('cities.json', 'r') as f:
    cities = json.load(f)

# Separate data points for rainy and non-rainy areas
rainy_heat_data = []      # Points with rain > 0mm
dry_heat_data = []        # Points with rain == 0mm
rain_values = []          # Track rainfall values for color scaling (rainy points only)
total_cities = len(cities)

print(f"Memulai pengambilan data cuaca untuk {total_cities} wilayah di Indonesia...\n")

# Menggunakan enumerate untuk melihat nomor urut (index)
for index, city in enumerate(cities, start=1):
    lat, lon = city['lat'], city['lon']
    city_name = city['name']

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,rain"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        rain = data.get('current', {}).get('rain', 0)

        # Tampilkan status per kota ke terminal
        if rain > 0:
            print(f"[{index}/{total_cities}] {city_name} -> 🌧️ Hujan ({rain} mm)")
            # Add to rainy heatmap data
            rainy_heat_data.append([lat, lon, float(rain)])
            rain_values.append(float(rain))
        else:
            print(f"[{index}/{total_cities}] {city_name} -> ☀️ Tidak hujan")
            # Add to dry heatmap data (for visualization of all points)
            dry_heat_data.append([lat, lon, 0.0])  # Use 0.0 for consistent formatting

    except Exception as e:
        print(f"[{index}/{total_cities}] {city_name} -> ❌ Gagal memuat ({e})")

print(f"\nSelesai! Data dari {len(rain_values)} wilayah hujan dan {len(dry_heat_data)} wilayah tidak hujan berhasil diproses.")

# 2. Buat Peta Indonesia
# Create Indonesia map
indonesia_map = folium.Map(location=[-2.5489, 118.0149], zoom_start=5, tiles='CartoDB Positron')

# 3. Buat Layer Control untuk menangkal antara daerah hujan dan tidak hujan
# Buat grup fitur untuk setiap lapisan
rainy_layer = folium.FeatureGroup(name='Daerah Hujan (Curah hujan > 0 mm)', show=True)
dry_layer = folium.FeatureGroup(name='Daerah Tidak Hujan (Curah hujan = 0 mm)', show=False)

# Tambahkan heatmap untuk daerah hujan saja ke lapisan hujan
if rainy_heat_data and rain_values:
    # Buat skala warna continuo untuk daerah hujan
    min_rain = min(rain_values)
    max_rain = max(rain_values)

    # Handle case where all values are the same
    if min_rain == max_rain:
        max_rain = min_rain + 1  # Avoid division by zero

    # Heatmap untuk daerah hujan dengan gradasi kuning ke biru ke merah/purple
    HeatMap(
        rainy_heat_data,
        radius=15,
        blur=10,
        max_zoom=1,
        gradient={0.0: '#ffff00', 0.3: '#add8e6', 0.5: '#1e90ff', 0.7: '#ff0000', 1.0: '#800080'}  # Yellow to blue to red to purple
    ).add_to(rainy_layer)

# Tambahkan heatmap untuk daerah tidak hujan saja ke lapisan tidak hujan
if dry_heat_data:
    # Untuk daerah tidak hujan, gunakan satu warna abu-abu terang
    HeatMap(
        dry_heat_data,
        radius=15,
        blur=10,
        max_zoom=1,
        gradient={0.0: '#f0f0f0', 1.0: '#f0f0f0'}  # Uniform light gray for all dry points
    ).add_to(dry_layer)

# Tambahkan semua lapisan ke peta
rainy_layer.add_to(indonesia_map)
dry_layer.add_to(indonesia_map)

# Tambahkan kontrol layer
folium.LayerControl(collapsed=False).add_to(indonesia_map)

# Tambahkan legenda untuk skala curah hujan ke peta langsung
legends_added = []

if rainy_heat_data and rain_values:
    # Legenda untuk skala curah hujan (dari 0mm ke max)
    min_rain_legend = 0  # Always start from 0 for dry areas
    max_rain_legend = max(rain_values) if rain_values else 0
    if max_rain_legend == 0:
        max_rain_legend = 1  # Avoid zero range

    rainfall_colormap = LinearColormap(
        colors=['#f0f0f0', '#ffff00', '#add8e6', '#1e90ff', '#ff0000', '#800080'],  # Gray -> Yellow -> Blue -> Red -> Purple
        vmin=min_rain_legend,
        vmax=max_rain_legend,
        caption='Curah Hujan (mm) - Skala Lengkap (0=Gray, >0=Yellow-Blue-Red-Purple)'
    )
    indonesia_map.add_child(rainfall_colormap)
    legends_added.append(('rainfall', rainfall_colormap.caption))

# Judul dan waktu update di peta
title_html = f'''
             <h3 align="center" style="font-size:16px; color:white;"><b>Peta Sebaran Hujan Indonesia</b> - Pembaruan: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</h3>
             '''
indonesia_map.get_root().html.add_child(folium.Element(title_html))

# 4. Simpan hasil ke file index.html
indonesia_map.save("index.html")
print("Peta index.html berhasil diperbarui!")
if legends_added:
    print(f"Legend ditambahkan: {legends_added}")