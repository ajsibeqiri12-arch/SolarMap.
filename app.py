from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

def get_solar_data(lat, lon):
    # NASA POWER API for solar irradiation
    url = (
        f"https://power.larc.nasa.gov/api/temporal/climatology/point"
        f"?parameters=ALLSKY_SFC_SW_DWN"
        f"&community=RE"
        f"&longitude={lon}&latitude={lat}"
        f"&format=JSON"
    )
    response = requests.get(url, timeout=15)
    data = response.json()
    annual = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["ANN"]
    return annual

def calculate_solar(roof_m2, lat, lon):
    solar_kwh_per_m2_per_day = get_solar_data(lat, lon)
    
    panel_efficiency = 0.20    
    performance_ratio = 0.80   
    price_per_kwh = 0.12       
    install_cost_m2 = 180      
    co2_factor = 0.35          
    
    annual_kwh = solar_kwh_per_m2_per_day * 365 * roof_m2 * panel_efficiency * performance_ratio
    
    savings_eur = annual_kwh * price_per_kwh
    install_cost = roof_m2 * install_cost_m2
    
    payback_years = install_cost / savings_eur if savings_eur > 0 else 0
    
  
    co2_kg = annual_kwh * co2_factor
    
    return {
        "annual_kwh": round(annual_kwh),
        "savings_eur": round(savings_eur),
        "co2_kg": round(co2_kg),
        "payback_years": round(payback_years, 1),
        "install_cost": round(install_cost)
    }

def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "SolarMapAlbania/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        results = response.json()
        if not results:
            return None, None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        return None, None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze")
def analyze():
    try:
        address = request.args.get("address", "")
        roof_m2 = float(request.args.get("roof_m2", 80))

        lat, lon = geocode_address(address)
        if lat is None:
            return jsonify({"error": "Adresa nuk u gjet. Provo me specifike."}), 400

        result = calculate_solar(roof_m2, lat, lon)
        result["lat"] = lat
        result["lon"] = lon
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)