import os
import requests
import csv
import time
import random
import pkgutil
import importlib.util
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from twilio.rest import Client
from datetime import datetime

# Compatibility shim: Python 3.14 removed `pkgutil.get_loader` which
# older Flask versions expect. Provide a simple replacement that
# returns the module loader (or None) using importlib.
if not hasattr(pkgutil, "get_loader"):
    def _compat_get_loader(name):
        try:
            spec = importlib.util.find_spec(name)
        except Exception:
            return None
        return getattr(spec, "loader", None) if spec is not None else None
    pkgutil.get_loader = _compat_get_loader
from dotenv import load_dotenv
import os as _os
# Explicitly load the .env located next to this file and allow it to override existing env vars
_dotenv_path = _os.path.join(_os.path.dirname(__file__), '.env')
load_dotenv(_dotenv_path, override=True)
# If for some reason dotenv didn't populate the keys (some environments restrict override),
# load essential keys manually from the .env file as a fallback.
try:
    if _os.path.exists(_dotenv_path):
        with open(_dotenv_path, 'r', encoding='utf-8') as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith('#'):
                    continue
                if '=' not in _line:
                    continue
                _k, _v = _line.split('=', 1)
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                if _k in ("WEATHERAPI_KEY", "OPENWEATHER_API_KEY"):
                    _os.environ[_k] = _v
except Exception:
    pass

app = Flask(__name__)

# Prefer WeatherAPI by default; fallback to OpenWeather if provided
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
API_PROVIDER = None
if WEATHERAPI_KEY:
    API_PROVIDER = "weatherapi"
elif OPENWEATHER_KEY:
    API_PROVIDER = "openweather"
CLEAN = True
print("APP START: API_PROVIDER=", API_PROVIDER, "WEATHERAPI_KEY present=", bool(WEATHERAPI_KEY), "OPENWEATHER_KEY present=", bool(OPENWEATHER_KEY))
CROP_FILE = "data/crops.csv"

# Complete India State-City Mapping (28 states + 8 UTs)
STATE_CITIES = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kakinada", "Rajahmundry", "Tirupati", "Anantapur", "Kadapa"],
    "Arunachal Pradesh": ["Itanagar", "Tawang", "Pasighat", "Naharlagun"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tezpur", "Tinsukia"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Purnia"],
    "Chhattisgarh": ["Raipur", "Bilaspur", "Bhilai", "Durg", "Korba", "Raigarh"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar"],
    "Haryana": ["Chandigarh", "Gurugram", "Faridabad", "Ambala", "Hisar", "Karnal"],
    "Himachal Pradesh": ["Shimla", "Dharamshala", "Mandi", "Kullu", "Solan"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh"],
    "Karnataka": ["Bengaluru", "Mangalore", "Mysuru", "Hubli", "Dharwad", "Belagavi", "Kalaburagi"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Kannur"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Thane", "Kolhapur"],
    "Manipur": ["Imphal", "Churachandpur", "Bishnupur"],
    "Meghalaya": ["Shillong", "Tura", "Jowai"],
    "Mizoram": ["Aizawl", "Lunglei"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Puri", "Sambalpur"],
    "Punjab": ["Amritsar", "Ludhiana", "Jalandhar", "Patiala", "Bathinda"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur", "Kota", "Ajmer", "Alwar"],
    "Sikkim": ["Gangtok", "Namchi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Erode", "Vellore"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar"],
    "Tripura": ["Agartala", "Dharmanagar"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Meerut", "Allahabad", "Ghaziabad", "Noida"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Rishikesh", "Haldwani"],
    "West Bengal": ["Kolkata", "Siliguri", "Durgapur", "Asansol", "Howrah"],
    "Andaman & Nicobar Islands": ["Port Blair"],
    "Chandigarh": ["Chandigarh"],
    "Dadra & Nagar Haveli & Daman & Diu": ["Daman", "Silvassa"],
    "Delhi": ["New Delhi", "Dwarka", "Rohini", "Karol Bagh"],
    "Jammu & Kashmir": ["Jammu", "Srinagar"],
    "Ladakh": ["Leh", "Kargil"],
    "Lakshadweep": ["Kavaratti"],
    "Puducherry": ["Pondicherry", "Karaikal"]
}

# Flat list of all cities for backwards compatibility
CITIES = [city for cities in STATE_CITIES.values() for city in cities]

# Approximate coordinates for major cities
CITY_COORDS = {
    "Mumbai": (19.075983, 72.877655), "Pune": (18.520430, 73.856743), "Nagpur": (21.145578, 79.088860),
    "Delhi": (28.704060, 77.102493), "New Delhi": (28.613939, 77.209021), "Bengaluru": (12.971599, 77.594566),
    "Hyderabad": (17.385044, 78.486671), "Chennai": (13.082680, 80.270718), "Kolkata": (22.572645, 88.363892),
    "Ahmedabad": (23.022505, 72.571362), "Guwahati": (26.195687, 91.736412), "Lucknow": (26.846523, 80.946144),
    "Jaipur": (26.912434, 75.787270), "Visakhapatnam": (17.690591, 83.218482), "Kochi": (9.931233, 76.267303),
    "Coimbatore": (11.005411, 76.965999), "Chandigarh": (30.735515, 76.779418), "Indore": (22.719568, 75.857277),
    "Vadodara": (22.307394, 73.181701), "Surat": (21.170240, 72.831062), "Patna": (25.595141, 85.137566),
    "Ranchi": (23.344815, 85.309562)
}

# Base climate bias (mean temperature, mean weekly rain mm) used when API key missing
CITY_BASE = {
    "Mumbai": (28, 20), "Delhi": (25, 10), "New Delhi": (25, 10), "Bengaluru": (22, 5),
    "Hyderabad": (27, 8), "Chennai": (29, 15), "Kolkata": (28, 18), "Pune": (23, 6),
    "Ahmedabad": (30, 4), "Guwahati": (26, 15), "Lucknow": (27, 8), "Jaipur": (27, 6),
    "Chandigarh": (23, 8), "Indore": (26, 6), "Surat": (28, 12), "Patna": (27, 10)
}

# Location to state mapping for auto-crop suggestions (auto-built from STATE_CITIES)
CITY_TO_STATE = {}
for state, cities in STATE_CITIES.items():
    for city in cities:
        CITY_TO_STATE[city] = state

# State-based crop recommendations
STATE_CROPS = {
    "Andhra Pradesh": ["Rice", "Groundnut", "Sugarcane", "Maize"],
    "Arunachal Pradesh": ["Rice", "Maize", "Ginger", "Turmeric"],
    "Assam": ["Rice", "Tea", "Jute", "Mustard"],
    "Bihar": ["Rice", "Wheat", "Maize", "Lentil"],
    "Chhattisgarh": ["Rice", "Soybean", "Maize", "Cotton"],
    "Goa": ["Coconut", "Cashew", "Arecanut", "Spices"],
    "Gujarat": ["Cotton", "Groundnut", "Wheat", "Maize"],
    "Haryana": ["Wheat", "Rice", "Maize", "Bajra"],
    "Himachal Pradesh": ["Wheat", "Maize", "Apple", "Papryka"],
    "Jharkhand": ["Rice", "Wheat", "Maize", "Pulses"],
    "Karnataka": ["Coffee", "Sugarcane", "Maize", "Groundnut"],
    "Kerala": ["Coconut", "Rubber", "Spices", "Tea"],
    "Madhya Pradesh": ["Soybean", "Wheat", "Chickpea", "Maize"],
    "Maharashtra": ["Soybean", "Cotton", "Wheat", "Jowar"],
    "Manipur": ["Rice", "Maize", "Pulses", "Vegetables"],
    "Meghalaya": ["Rice", "Maize", "Potatoes", "Ginger"],
    "Mizoram": ["Rice", "Maize", "Turmeric", "Chili"],
    "Nagaland": ["Rice", "Maize", "Ginger", "Turmeric"],
    "Odisha": ["Rice", "Sugarcane", "Maize", "Pulses"],
    "Punjab": ["Wheat", "Rice", "Cotton", "Sugarcane"],
    "Rajasthan": ["Wheat", "Bajra", "Mustard", "Pulses"],
    "Sikkim": ["Cardamom", "Ginger", "Organic crops", "Tea"],
    "Tamil Nadu": ["Rice", "Sugarcane", "Coconut", "Groundnut"],
    "Telangana": ["Maize", "Cotton", "Soybean", "Groundnut"],
    "Tripura": ["Rice", "Maize", "Rubber", "Vegetables"],
    "Uttar Pradesh": ["Wheat", "Rice", "Sugarcane", "Potato"],
    "Uttarakhand": ["Wheat", "Rice", "Mandarin", "Ginger"],
    "West Bengal": ["Rice", "Wheat", "Maize", "Jute"],
    "Andaman & Nicobar Islands": ["Coconut", "Arecanut", "Spices"],
    "Chandigarh": ["Wheat", "Vegetables", "Flowers"],
    "Dadra & Nagar Haveli & Daman & Diu": ["Cotton", "Groundnut", "Sugarcane"],
    "Delhi": ["Wheat", "Rice", "Maize", "Vegetables"],
    "Jammu & Kashmir": ["Rice", "Wheat", "Maize", "Apples"],
    "Ladakh": ["Barley", "Wheat", "Peas", "Potatoes"],
    "Lakshadweep": ["Coconut", "Fish", "Spices"],
    "Puducherry": ["Rice", "Sugarcane", "Coconut", "Groundnut"]
}

# Soil type characteristics and crop suitability
SOIL_CROP_SUITABILITY = {
    "Clay": {
        "crops": ["Rice", "Wheat", "Cotton"],
        "note": "Retains moisture well; good for water-loving crops",
        "fertilizer_tip": "Prone to waterlogging; use controlled-release N, add organic matter"
    },
    "Sandy": {
        "crops": ["Corn", "Groundnut", "Soybean"],
        "note": "Drains quickly; suitable for crops tolerating drought",
        "fertilizer_tip": "Poor retention; use frequent, light N applications; add organic matter"
    },
    "Loamy": {
        "crops": ["Wheat", "Corn", "Soybean", "Tomato"],
        "note": "Ideal balanced soil; suitable for most crops",
        "fertilizer_tip": "Balanced fertility; standard NPK applications work best"
    },
    "Red soil": {
        "crops": ["Corn", "Soybean", "Cotton", "Groundnut"],
        "note": "Acidic, poor in N/K; requires amendments",
        "fertilizer_tip": "Add lime to reduce acidity; increase K application (K2O 60kg/ha)"
    },
    "Black soil": {
        "crops": ["Cotton", "Soybean", "Wheat", "Jowar"],
        "note": "High in Fe, Mg; excellent water retention",
        "fertilizer_tip": "Rich in nutrients; may need less N; monitor micronutrient balance"
    }
}

# Weather risk alert thresholds
WEATHER_RISK_ALERTS = {
    "heatwave": {"temp_threshold": 35, "description": "🔴 Heatwave Risk: Temp >35°C may stress crops"},
    "heavy_rain": {"rain_threshold": 50, "description": "🔵 Heavy Rain Risk: >50mm may cause waterlogging"},
    "low_rain": {"rain_threshold": 10, "description": "🟡 Low Rainfall Risk: <10mm may stress moisture-loving crops"},
    "low_temp": {"temp_threshold": 10, "description": "❄️ Low Temperature Risk: Temp <10°C may slow growth"}
}

def get_weather_risk_alerts(forecast_data):
    """Analyze 7-day forecast and return weather risk alerts."""
    alerts = []
    if not forecast_data or "list" not in forecast_data:
        return alerts
    
    temps = []
    rains = []
    for day_data in forecast_data["list"]:
        temps.append(day_data.get("main", {}).get("temp", 0))
        rains.append(day_data.get("rain", {}).get("3h", 0))
    
    avg_temp = sum(temps) / len(temps) if temps else 0
    total_rain = sum(rains)
    max_daily_rain = max(rains) if rains else 0
    
    # Heatwave risk
    if avg_temp > WEATHER_RISK_ALERTS["heatwave"]["temp_threshold"]:
        alerts.append({
            "type": "heatwave",
            "message": WEATHER_RISK_ALERTS["heatwave"]["description"],
            "severity": "high",
            "value": f"{avg_temp:.1f}°C"
        })
    
    # Heavy rain risk
    if max_daily_rain > WEATHER_RISK_ALERTS["heavy_rain"]["rain_threshold"]:
        alerts.append({
            "type": "heavy_rain",
            "message": WEATHER_RISK_ALERTS["heavy_rain"]["description"],
            "severity": "high",
            "value": f"{max_daily_rain:.1f}mm"
        })
    
    # Low rainfall risk
    if total_rain < WEATHER_RISK_ALERTS["low_rain"]["rain_threshold"]:
        alerts.append({
            "type": "low_rain",
            "message": WEATHER_RISK_ALERTS["low_rain"]["description"],
            "severity": "medium",
            "value": f"{total_rain:.1f}mm"
        })
    
    # Low temperature risk
    if avg_temp < WEATHER_RISK_ALERTS["low_temp"]["temp_threshold"]:
        alerts.append({
            "type": "low_temp",
            "message": WEATHER_RISK_ALERTS["low_temp"]["description"],
            "severity": "high",
            "value": f"{avg_temp:.1f}°C"
        })
    
    return alerts

def get_soil_based_recommendations(soil_type):
    """Return crop recommendations based on soil type."""
    if soil_type in SOIL_CROP_SUITABILITY:
        return SOIL_CROP_SUITABILITY[soil_type]
    return None

def get_state_from_city(city):
    """Get state name from city."""
    return CITY_TO_STATE.get(city, None)

def get_location_based_crops(city):
    """Get crop recommendations based on city/state location."""
    state = get_state_from_city(city)
    if state and state in STATE_CROPS:
        return STATE_CROPS[state]
    return []

def generate_planting_calendar(forecast_data, city):
    """Generate planting calendar (7-day view with color coding)."""
    calendar = []
    if not forecast_data or "list" not in forecast_data:
        return calendar
    
    for i, day_data in enumerate(forecast_data["list"]):
        dt = day_data.get("dt", 0)
        temp = day_data.get("main", {}).get("temp", 0)
        rain = day_data.get("rain", {}).get("3h", 0)
        
        # Determine suitability color
        if temp < 10 or temp > 35 or rain > 40:
            color = "red"  # Risky
            label = "Risky"
        elif temp < 15 or temp > 30 or rain > 20:
            color = "yellow"  # Moderate
            label = "Moderate"
        else:
            color = "green"  # Suitable
            label = "Suitable"
        
        import time as time_module
        day_name = time_module.strftime("%a", time_module.localtime(dt))
        date_str = time_module.strftime("%b %d", time_module.localtime(dt))
        
        calendar.append({
            "day": i + 1,
            "date": date_str,
            "day_name": day_name,
            "temp": round(temp, 1),
            "rain": round(rain, 1),
            "color": color,
            "label": label
        })
    
    return calendar

def detect_pest_risk(forecast_data, crop=None):
    """Detect pest risk based on weather conditions."""
    pest_risks = []
    if not forecast_data or "list" not in forecast_data:
        return pest_risks
    
    temps = []
    rains = []
    for day_data in forecast_data["list"]:
        temps.append(day_data.get("main", {}).get("temp", 0))
        rains.append(day_data.get("rain", {}).get("3h", 0))
    
    avg_temp = sum(temps) / len(temps) if temps else 0
    total_rain = sum(rains)
    
    # Pest risk patterns based on temperature and humidity (rain indicates moisture)
    if 18 <= avg_temp <= 28 and total_rain > 30:
        pest_risks.append({
            "type": "armyworm",
            "description": "Armyworm risk high (warm + wet)",
            "severity": "high"
        })
    
    if 20 <= avg_temp <= 30 and total_rain > 20:
        pest_risks.append({
            "type": "fungal_disease",
            "description": "Fungal disease risk (warm + humid)",
            "severity": "high"
        })
    
    if avg_temp >= 25 and total_rain < 15:
        pest_risks.append({
            "type": "spider_mite",
            "description": "Spider mite risk (hot + dry)",
            "severity": "medium"
        })
    
    if avg_temp < 10:
        pest_risks.append({
            "type": "frost",
            "description": "Frost risk (cold snap)",
            "severity": "high"
        })
    
    return pest_risks

def format_alert_message(alert_type, value, city):
    """Format alert message for SMS/WhatsApp."""
    messages = {
        "heatwave": f"HEATWAVE ALERT {city}: Temperature {value}. Increase irrigation. Use mulch. Stay hydrated.",
        "heavy_rain": f"HEAVY RAIN ALERT {city}: {value} expected. Drain fields. Spray fungicides. Monitor crops.",
        "low_rain": f"DROUGHT ALERT {city}: Low rainfall {value}. Water crops. Apply mulch. Monitor soil moisture.",
        "frost": f"FROST ALERT {city}: Below-freezing temperatures. Protect tender crops. Apply frost prevention measures.",
        "armyworm": f"PEST ALERT {city}: Armyworm risk high. Scout fields. Apply bio-pesticide. Monitor daily.",
        "fungal_disease": f"DISEASE ALERT {city}: Fungal disease risk. Improve drainage. Spray fungicide. Remove infected plants.",
        "spider_mite": f"PEST ALERT {city}: Spider mite risk. Apply neem oil. Increase irrigation. Monitor undersides of leaves.",
    }
    return messages.get(alert_type, f"WEATHER ALERT {city}: {alert_type}")

def send_sms_alert(phone_number, message):
    """Send SMS alert via Twilio with demo mode fallback.

    Reads `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE` from env.
    If credentials are missing the function falls back to demo mode.
    Returns a dict with `status` == 'success' or 'error'.
    """
    try:
        TWILIO_ACCOUNT_SID = os.getenv("AC8d24d2544e897a232b904cd7ac6f5950")
        TWILIO_AUTH_TOKEN = os.getenv("b72108b07530d1da76b8800a2c14ab59")
        TWILIO_PHONE = os.getenv("TWILIO_PHONE")

        # Demo mode when Twilio credentials not configured
        if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE):
            app.logger.warning("[SMS][Twilio] Missing Twilio credentials - Demo mode active")
            return {
                "status": "success",
                "message": f"✓ SMS alert would be sent to {phone_number}",
                "mode": "demo"
            }

        # Normalize recipient and sender
        recipient_normalized = ''.join(c for c in phone_number if c.isdigit())
        sender_normalized = ''.join(c for c in TWILIO_PHONE if c.isdigit())

        if len(recipient_normalized) < 10:
            return {"status": "error", "message": "Invalid phone number"}

        # Prevent sending from same number
        if recipient_normalized == sender_normalized:
            app.logger.error(f"[SMS][Twilio] sender and recipient are the same ({sender_normalized})")
            return {"status": "error", "message": "Sender and recipient are the same"}

        # Ensure E.164 formatting (assume +91 for 10-digit local numbers)
        to_number = phone_number if phone_number.startswith('+') else ("+91" + recipient_normalized if len(recipient_normalized) == 10 else "+" + recipient_normalized)
        from_number = TWILIO_PHONE if TWILIO_PHONE.startswith('+') else "+" + sender_normalized

        # Initialize Twilio client and send
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        app.logger.info(f"[SMS][Twilio] Sending from {from_number} to {to_number}")
        sms = client.messages.create(body=message, from_=from_number, to=to_number)

        app.logger.info(f"[SMS][Twilio] ✓ Success - SID: {sms.sid}, Status: {getattr(sms, 'status', 'unknown')}")
        return {
            "status": "success",
            "message": "✓ SMS sent successfully",
            "sms_id": getattr(sms, 'sid', None),
            "recipient": to_number,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        app.logger.exception("[SMS][Twilio] Exception while sending SMS")
        return {"status": "error", "message": str(e)}


def get_coordinates(city):
    """Convert city name to latitude & longitude."""
    # Only used when provider is OpenWeather (it has a separate geocoding endpoint)
    if API_PROVIDER != "openweather":
        return None
    if not OPENWEATHER_KEY:
        return None

    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": city, "limit": 1, "appid": OPENWEATHER_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    if not data:
        return None
    return data[0].get("lat"), data[0].get("lon")

def get_weather(lat, lon):
    """Fetch 7-day forecast."""
    # Only used for OpenWeather provider
    if API_PROVIDER != "openweather" or not OPENWEATHER_KEY:
        return sample_forecast()

    try:
        url = "https://api.openweathermap.org/data/2.5/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "exclude": "current,minutely,hourly,alerts",
            "appid": OPENWEATHER_KEY
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("daily", [])
    except Exception:
        return sample_forecast()


def get_weather_by_city_weatherapi(city):
    """Fetch 7-day forecast from WeatherAPI and convert to internal format.
    
    Returns: list of daily forecast dicts or None on error
    Logs: all API responses, errors, and validation issues
    """
    if not WEATHERAPI_KEY:
        app.logger.warning(f"[WeatherAPI] WEATHERAPI_KEY not configured")
        return None
    
    try:
        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {"key": WEATHERAPI_KEY, "q": city, "days": 7, "aqi": "no", "alerts": "no"}
        
        app.logger.info(f"[WeatherAPI] Requesting forecast for city='{city}'")
        app.logger.debug(f"[WeatherAPI] URL: {url}, params keys: {list(params.keys())}")
        
        r = requests.get(url, params=params, timeout=10)
        
        # Log response status and headers
        app.logger.info(f"[WeatherAPI] Response status: {r.status_code}")
        app.logger.debug(f"[WeatherAPI] Response headers: {dict(r.headers)}")
        
        # Check for HTTP errors
        if r.status_code != 200:
            app.logger.error(f"[WeatherAPI] HTTP {r.status_code} for city '{city}'")
            try:
                error_data = r.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                app.logger.error(f"[WeatherAPI] Error message: {error_msg}")
                # If it's an auth error (401), log more info about the key
                if r.status_code == 401:
                    app.logger.error(f"[WeatherAPI] Authorization failed - check if API key is valid and has forecast access")
                return None
            except Exception as e:
                app.logger.error(f"[WeatherAPI] Response text: {r.text[:500]}")
                return None
        
        # Parse JSON response
        try:
            data = r.json()
        except Exception as e:
            app.logger.error(f"[WeatherAPI] Failed to parse JSON response for '{city}': {e}")
            app.logger.error(f"[WeatherAPI] Response text: {r.text[:500]}")
            return None
        
        # Validate response structure
        if not isinstance(data, dict):
            app.logger.error(f"[WeatherAPI] Response is not a dict for '{city}': {type(data)}")
            return None
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            app.logger.error(f"[WeatherAPI] API error for '{city}': {error_msg}")
            return None
        
        if 'forecast' not in data:
            app.logger.error(f"[WeatherAPI] 'forecast' key missing in response for '{city}'")
            app.logger.debug(f"[WeatherAPI] Response keys: {list(data.keys())}")
            return None
        
        forecastday_list = data.get('forecast', {}).get('forecastday', [])
        if not forecastday_list:
            app.logger.warning(f"[WeatherAPI] Empty forecastday list for '{city}'")
            return None
        
        app.logger.info(f"[WeatherAPI] Successfully fetched {len(forecastday_list)} days for '{city}'")
        
        # Convert WeatherAPI forecast to list of daily dicts with 'dt', 'temp':{'day':...}, optional 'rain'
        out = []
        for fd in forecastday_list:
            try:
                date_str = fd.get('date')
                if not date_str:
                    app.logger.warning(f"[WeatherAPI] Missing 'date' in forecastday for '{city}'")
                    continue
                
                # convert date to unix timestamp (start of day)
                try:
                    from datetime import datetime
                    dt = int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=None).timestamp())
                except Exception as e:
                    app.logger.warning(f"[WeatherAPI] Failed to parse date '{date_str}' for '{city}': {e}")
                    dt = int(time.time())
                
                day = fd.get('day', {})
                temp_c = day.get('avgtemp_c')
                
                # If avgtemp_c is missing, try to get it from maxtemp_c and mintemp_c
                if temp_c is None:
                    max_temp = day.get('maxtemp_c')
                    min_temp = day.get('mintemp_c')
                    if max_temp is not None and min_temp is not None:
                        temp_c = (max_temp + min_temp) / 2
                
                if temp_c is None:
                    app.logger.warning(f"[WeatherAPI] Missing temperature for date '{date_str}' in '{city}': {day.keys()}")
                    continue
                
                # Convert to float if needed
                temp_c = float(temp_c)
                
                rain_mm = day.get('totalprecip_mm', 0)
                if rain_mm is None:
                    rain_mm = 0
                else:
                    rain_mm = float(rain_mm)
                
                # Get max/min temps for additional detail
                max_temp = float(day.get('maxtemp_c', temp_c))
                min_temp = float(day.get('mintemp_c', temp_c))
                
                entry = {'dt': dt, 'temp': {'day': temp_c, 'max': max_temp, 'min': min_temp}}
                if rain_mm and rain_mm > 0:
                    entry['rain'] = rain_mm
                
                out.append(entry)
            except Exception as e:
                app.logger.error(f"[WeatherAPI] Error processing forecastday entry for '{city}': {e}")
                continue
        
        if not out:
            app.logger.error(f"[WeatherAPI] Failed to extract any valid forecast data for '{city}'")
            return None
        
        app.logger.info(f"[WeatherAPI] Successfully converted {len(out)} forecast entries for '{city}'")
        return out
        
    except requests.exceptions.Timeout:
        app.logger.error(f"[WeatherAPI] Request timeout for city '{city}'")
        return None
    except requests.exceptions.RequestException as e:
        app.logger.error(f"[WeatherAPI] Request exception for city '{city}': {e}")
        return None
    except Exception as e:
        app.logger.exception(f"[WeatherAPI] Unexpected exception for city '{city}': {e}")
        return None


def sample_forecast():
    """Return a simple 7-day synthetic forecast for demo/testing when API key missing.
    Uses city base climate if provided (biases temperatures and probability of rain).
    """
    # Default generic base
    now = int(time.time())
    def build_for_city(city=None):
        base_temp, base_rain = CITY_BASE.get(city, (22, 5))
        forecast = []
        for i in range(7):
            temp_day = round(random.gauss(base_temp, 3), 1)
            rain_chance = min(0.8, 0.25 + base_rain / 50)
            rain = round(random.uniform(0, base_rain * 1.5), 1) if random.random() < rain_chance else 0
            day = {
                "dt": now + i * 86400,
                "temp": {"day": temp_day},
                **({"rain": rain} if rain > 0 else {})
            }
            forecast.append(day)
        return forecast

    # Default no-city forecast
    return build_for_city(None)

def sample_forecast_for_city(city):
    now = int(time.time())
    base_temp, base_rain = CITY_BASE.get(city, (22, 5))
    forecast = []
    for i in range(7):
        temp_day = round(random.gauss(base_temp, 3), 1)
        rain_chance = min(0.8, 0.25 + base_rain / 50)
        rain = round(random.uniform(0, base_rain * 1.5), 1) if random.random() < rain_chance else 0
        day = {
            "dt": now + i * 86400,
            "temp": {"day": temp_day},
            **({"rain": rain} if rain > 0 else {})
        }
        forecast.append(day)
    return forecast

def load_crops():
    crops = []
    with open(CROP_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # convert numeric fields to floats for comparisons
            try:
                row["Temp_Min"] = float(row["Temp_Min"]) if row.get("Temp_Min") not in (None, "") else None
                row["Temp_Max"] = float(row["Temp_Max"]) if row.get("Temp_Max") not in (None, "") else None
                row["Rain_Min_mm"] = float(row["Rain_Min_mm"]) if row.get("Rain_Min_mm") not in (None, "") else 0.0
            except Exception:
                row["Temp_Min"] = None
                row["Temp_Max"] = None
                row["Rain_Min_mm"] = 0.0
            crops.append(row)
    return crops

def check_crop_suitability(crop, forecast):
    """Check if crop fits weather conditions."""
    temp_range = (crop["Temp_Min"], crop["Temp_Max"])
    rain_need = crop["Rain_Min_mm"]

    avg_temp = sum(day["temp"]["day"] for day in forecast[:7]) / 7
    total_rain = sum(day.get("rain", 0) for day in forecast[:7])

    temp_ok = temp_range[0] <= avg_temp <= temp_range[1]
    rain_ok = total_rain >= rain_need

    if temp_ok and rain_ok:
        return "Highly Suitable"
    elif temp_ok:
        return "Moderately Suitable (Low Rain)"
    elif rain_ok:
        return "Moderately Suitable (Temp Issue)"
    else:
        return "Not Suitable"

def chatbot_response(user_message):
    """Rule-based chatbot with comprehensive crop, weather, and fertilizer recommendations."""
    msg_lower = user_message.lower()
    
    # Comprehensive fertilizer information with scientific backing and brands
    fertilizer_info = {
        'wheat': {
            'general': "Wheat needs nitrogen-rich fertilizers (urea 46% N) at 120kg/ha. Apply half at sowing and half at tillering stage.",
            'low_rain': "🌾 LOW-RAINFALL CONDITIONS (Moderately Suitable):\nWheat requires balanced NPK (120:60:60 kg/ha) for stress tolerance. Use Shriram Farm Solutions' Neem-coated urea for steady nitrogen release. Add potassium (K2O 40kg/ha) to improve drought resistance. Incorporate organic matter and biofertilizers to enhance soil moisture retention. Key: Controlled-release fertilizers minimize loss in dry conditions.\nBased on: FAO Soil Fertility Guidelines, TNAU Fertilizer Guide",
            'hot': "In hot weather (>25°C), use slow-release nitrogen fertilizers to prevent nutrient loss. Add potassium (K2O 40-50kg/ha) to improve drought resistance.",
            'wet': "In wet conditions, avoid excess nitrogen to prevent fungal diseases. Use organic phosphorus-rich amendments (superphosphate 16% P2O5).",
            'cold': "In cold weather (<15°C), use liquid fertilizers for faster absorption. Apply NPK 10:26:26 to boost early growth."
        },
        'rice': {
            'general': "Rice needs high nitrogen (urea 200-250kg/ha). Split into 3-4 applications: 25% at transplanting, rest at tillering, panicle initiation, and flowering.",
            'low_rain': "🌾 LOW-RAINFALL CONDITIONS (Moderately Suitable - Low Rain Issue):\nRice requires balanced NPK 100:50:50 kg/ha with emphasis on phosphorus for root development and potassium for stress tolerance. Use Shriram Farm Solutions' crop-specific rice formulations. Apply 50% N at planting, 50% at panicle initiation. Add biofertilizers (azospirillum) to improve nutrient availability. Include micronutrients: Zn 5kg/ha, B 2kg/ha for deficit moisture.\nScientific basis: Cereals in moisture-limited environments require phosphorus for root architecture and K for osmotic adjustment (TNAU, FAO guidelines). Biofertilizers enhance nutrient use efficiency by 20-30%.",
            'hot': "In hot weather, increase potassium (K2O 60-80kg/ha) to reduce heat stress. Use zinc sulfate 25kg/ha to prevent deficiency.",
            'wet': "In wet conditions, maintain proper N:P:K ratio (4:2:2). Avoid waterlogging by ensuring adequate drainage.",
            'cold': "In cold weather, use warm-soluble fertilizers and add micronutrients (Mn, Fe, Zn). Keep soil moisture moderate."
        },
        'corn': {
            'general': "Corn requires NPK 120:60:60 kg/ha. Apply nitrogen in splits: 50% at planting, 50% at tasseling.",
            'low_rain': "🌾 LOW-RAINFALL CONDITIONS (Moderately Suitable - Low Rain Issue):\nCorn (cereal) thrives with balanced NPK 100:50:50 kg/ha. Prioritize phosphorus (P2O5 60kg/ha) for strong root development—critical in moisture-limited soils. Potassium (K2O 40kg/ha) improves water-use efficiency and stress resilience. Recommend Shriram Farm Solutions' maize-specific formulation with controlled-release nitrogen (Neem-coated urea). Add sulfur 20kg/ha and micronutrients (Fe, Zn, Mn 2kg/ha each). Use biofertilizers (Bacillus) to enhance phosphorus mobilization.\nRationale: Strong root systems and P-efficient uptake are critical for cereals under drought (FAO Maize Guidelines). Controlled-release formulations reduce leaching in low-rainfall zones.",
            'hot': "In hot weather, increase phosphorus (P2O5 80kg/ha) for root development. Use mulching to retain soil moisture.",
            'wet': "In wet conditions, use controlled-release fertilizers to minimize leaching. Add sulfur 20kg/ha to improve nutrient uptake.",
            'cold': "In cold weather, start with phosphorus-rich fertilizers (DAP 20:46:0) to stimulate early growth."
        },
        'soybean': {
            'general': "Soybeans need phosphorus (P2O5 60kg/ha) and potassium (K2O 40kg/ha). Nitrogen fixing through rhizobia, but add 20kg N/ha for faster establishment.",
            'low_rain': "🌾 LOW-RAINFALL CONDITIONS (Moderately Suitable - Low Rain Issue):\nSoybean (legume) requires phosphorus-rich strategy: P2O5 60kg/ha, K2O 40kg/ha, minimal N (0-20kg/ha as legumes fix nitrogen). Use Rhizobium-based biofertilizers (1 packet per 10kg seed) to maximize nodulation and nitrogen fixation—crucial in moisture-stressed soils. Phosphorus mobilizes effectively with biofertilizers. Add micronutrients: Zn 5kg/ha, B 2kg/ha. Seed treatment with Bacillus and Pseudomonas bioformulates improves drought tolerance by 15-20%.\nScientific support: Legumes rely on microbial partnerships; biofertilizers are 40-50% more effective than synthetic N in water-scarce regions (Biofertilizer Research, TNAU). Phosphorus enhances water-use efficiency in legumes.",
            'hot': "In hot weather, use potassium and organic matter to improve water retention. Add sulfur 20kg/ha for sulfur-loving legumes.",
            'wet': "In wet conditions, ensure good drainage and add zinc (Zn 5-10kg/ha) to prevent deficiency in waterlogged soils.",
            'cold': "In cold weather, inoculate seeds with Bradyrhizobium and apply P-rich fertilizers (SSP 16% P2O5) for better nodulation."
        },
        'tomato': {
            'general': "Tomatoes need balanced NPK 100:50:50 kg/ha. Apply nitrogen in splits: 50% pre-planting, 50% at flowering.",
            'low_rain': "🌾 LOW-RAINFALL CONDITIONS (Moderately Suitable - Low Rain Issue):\nTomato (horticultural crop) requires precise NPK: N 100kg/ha (nitrate-based preferred), P2O5 60kg/ha, K2O 80kg/ha (potassium critical for fruit quality and stress tolerance). Use Shriram Farm Solutions' horticulture-specific fertilizers with balanced K:N ratios. Split N: 40% pre-planting, 30% flowering, 30% fruit-set. Add Ca 200kg/ha (lime/gypsum) and Mg 25kg/ha to prevent blossom-end rot. Micronutrients: B 2kg/ha (improves fruiting), Zn 3kg/ha, Fe 2kg/ha. Use drip fertirrigation with controlled-release formulations.\nBasis: High potassium (Haifa Group Tomato Nutrition Guide) and calcium are critical for fruit quality under water stress. Balanced nitrogen (NO3- vs NH4+) improves taste and shelf-life. Deficit irrigation with precision nutrients is the modern approach.",
            'hot': "In hot weather, increase potassium (K2O 80kg/ha) and calcium (lime 2t/ha) to prevent blossom-end rot. Use drip irrigation with fertigation.",
            'wet': "In wet conditions, reduce nitrogen to prevent vegetative growth. Add copper 2kg/ha and sulfur to prevent fungal diseases.",
            'cold': "In cold weather, use warm liquid fertilizers and add boron (B 2-3kg/ha) to improve fruiting. Apply phosphorus for root development."
        }
    }
    
    # Low-rainfall scenario query (new)
    if any(x in msg_lower for x in ['low rain', 'drought', 'dry', 'low moisture', 'water stress', 'moisture-limited']):
        return """🌾 LOW-RAINFALL & DROUGHT-STRESS FERTILIZER STRATEGY:

For crops in moisture-limited environments, the key approach is **balanced NPK + biofertilizers + organic matter**, supported by scientific research from TNAU, FAO, and Haifa Group.

**GENERAL PRINCIPLES:**
• Use controlled-release fertilizers (e.g., Neem-coated urea) to minimize losses
• Emphasize phosphorus for root development and potassium for stress tolerance
• Incorporate biofertilizers to improve soil strength and nutrient efficiency (+20-30%)
• Add organic amendments to enhance water-holding capacity
• Micronutrients (Zn, B, Fe, Mn) become critical in stressed soils

**BY CROP:**
• **Rice/Corn (Cereals)**: Balanced NPK + P for roots, K for resilience. Shriram Farm Solutions' crop-specific formulations recommended.
• **Soybean (Legume)**: Rhizobium biofertilizer + P-rich (no excess N), since they fix their own nitrogen. +40-50% efficiency vs synthetic N alone.
• **Tomato (Vegetable)**: Nitrate-based N + high K (Haifa recommendations) for fruit quality. Calcium critical to prevent blossom-end rot.

**RECOMMENDED BRANDS:**
✓ Shriram Farm Solutions (crop-specific NPK formulations)
✓ Neem-coated urea for slow release
✓ Biofertilizers: Azospirillum, Rhizobium, Bacillus, Pseudomonas
✓ Micronutrient mixes from certified suppliers

**SOIL PREPARATION:**
→ Conduct soil test BEFORE fertilization to avoid over-application
→ Mix in 5-10t/ha organic matter (compost, FYM) to improve moisture retention
→ Use mulching (5cm straw/plastic) to reduce evaporation

**SOURCES:**
TNAU Fertilizer Guide | FAO Soil Fertility & Maize Guidelines | Haifa Group Tomato Nutrition | Biofertilizer Research"""
    
    # Crop-specific low-rain queries
    if any(x in msg_lower for x in ['wheat', 'rice', 'corn', 'soybean', 'tomato']):
        if 'wheat' in msg_lower:
            if any(x in msg_lower for x in ['low rain', 'drought', 'dry']):
                return "Wheat in low-rainfall conditions is **NOT SUITABLE** (requires 10–25°C and consistent 20mm rain).\n" + fertilizer_info['wheat']['low_rain']
            base = "Wheat is best grown in temperatures between 10–25°C with at least 20mm of rain. It prefers cooler climates.\n"
            fert = "\n📋 Fertilizer: " + fertilizer_info['wheat']['general']
            return base + fert
        elif 'rice' in msg_lower:
            if any(x in msg_lower for x in ['low rain', 'drought', 'dry']):
                return "Rice in low-rainfall conditions is **MODERATELY SUITABLE** (prefers warm, wet conditions).\n" + fertilizer_info['rice']['low_rain']
            base = "Rice thrives in warm conditions (20–35°C) and needs abundant water—at least 100mm of rain.\n"
            fert = "\n📋 Fertilizer: " + fertilizer_info['rice']['general']
            return base + fert
        elif 'corn' in msg_lower:
            if any(x in msg_lower for x in ['low rain', 'drought', 'dry']):
                return "Corn in low-rainfall conditions is **MODERATELY SUITABLE** (prefers 50mm rain minimum).\n" + fertilizer_info['corn']['low_rain']
            base = "Corn grows well in 18–30°C with 50mm rainfall needed. It's versatile and used for food, feed, and biofuel.\n"
            fert = "\n📋 Fertilizer: " + fertilizer_info['corn']['general']
            return base + fert
        elif 'soybean' in msg_lower:
            if any(x in msg_lower for x in ['low rain', 'drought', 'dry']):
                return "Soybean in low-rainfall conditions is **MODERATELY SUITABLE** (prefers 40mm rain minimum).\n" + fertilizer_info['soybean']['low_rain']
            base = "Soybeans prefer 15–30°C temperatures and 40mm rainfall. They're nitrogen-fixing and great for crop rotation.\n"
            fert = "\n📋 Fertilizer: " + fertilizer_info['soybean']['general']
            return base + fert
        elif 'tomato' in msg_lower:
            if any(x in msg_lower for x in ['low rain', 'drought', 'dry']):
                return "Tomato in low-rainfall conditions is **MODERATELY SUITABLE** (requires careful irrigation management).\n" + fertilizer_info['tomato']['low_rain']
            base = "Tomatoes are warm-season crops (18–30°C) needing 20mm rain. They're suitable year-round in many regions.\n"
            fert = "\n📋 Fertilizer: " + fertilizer_info['tomato']['general']
            return base + fert
    
    # Biofertilizer queries
    if any(x in msg_lower for x in ['biofertilizer', 'bio-fertilizer', 'microbial', 'rhizobium', 'azospirillum', 'bacillus']):
        return """🌱 BIOFERTILIZER GUIDE:

Biofertilizers contain beneficial microorganisms that enhance nutrient availability and improve crop resilience under stress.

**COMMON TYPES:**
• **Rhizobium**: For legumes (soybean, peas)—fixes atmospheric nitrogen (+40-50% efficiency in moisture stress)
• **Azospirillum**: For cereals (rice, corn, wheat)—improves root development and nutrient uptake
• **Bacillus/Pseudomonas**: Phosphate-solubilizing bacteria—unlock soil phosphorus, critical in drought
• **Mycorrhiza**: Fungal partners—expand root surface area (+20% water absorption)

**BENEFITS:**
✓ Increase nutrient use efficiency by 20-30%
✓ Improve soil structure and water retention
✓ Enhance stress tolerance (drought, heat, cold)
✓ Cost-effective and eco-friendly
✓ Reduce chemical fertilizer dependency by 20-30%

**APPLICATION:**
→ Seed treatment: 1 packet per 10kg seed
→ Soil application: 5 kg/ha mixed with FYM
→ Best results: Combine with organic matter (compost, FYM)

**RECOMMENDED FOR:**
• Legumes (soybean): Rhizobium essential for nitrogen fixation
• Cereals in drought: Azospirillum + Bacillus for P mobilization
• All crops: Improved stress resilience

**SOURCES:** Biofertilizer Research (Wikipedia), TNAU, Agricultural Universities"""
    
    # Fertilizer-specific questions
    if any(x in msg_lower for x in ['fertilizer', 'nutrient', 'npk', 'nitrogen', 'phosphorus', 'potassium', 'brand', 'shriram']):
        return """🧪 FERTILIZER RECOMMENDATIONS:

I can provide detailed guidance on:
• General NPK strategies for each crop
• Low-rainfall/drought-stress fertilizer plans
• Hot/cold/wet weather adjustments
• Biofertilizers and organic amendments
• Recommended brands: Shriram Farm Solutions, Neem-coated urea, etc.
• Micronutrient deficiency prevention
• Soil testing importance

**Example queries:**
• "Wheat in drought conditions"
• "Rice low-rainfall strategy"
• "Soybean biofertilizer guide"
• "Tomato fertilizer for stress"
• "Tell me about nitrogen in hot weather"

**SCIENTIFIC BACKING:**
→ TNAU Fertilizer Guide
→ FAO Soil Fertility & Crop Guidelines
→ Haifa Group Nutrient Research
→ Biofertilizer & Soil Microbiology Studies"""
    
    # Weather questions
    if any(x in msg_lower for x in ['temperature', 'temp', 'how hot', 'how cold']):
        return "Temperature affects crop growth and fertilizer efficiency significantly. Most crops thrive in 18–28°C. Ask me about fertilizer strategies for hot/cold/dry conditions!"
    if any(x in msg_lower for x in ['rain', 'rainfall', 'precipitation', 'water', 'moisture']):
        return "Rainfall critically impacts nutrient availability and fertilizer strategy. Moisture-limited conditions require special approaches: biofertilizers, controlled-release N, emphasis on P and K. Ask about 'low rainfall strategy' for specific guidance!"
    if any(x in msg_lower for x in ['forecast', 'weather', 'predict']):
        return "Select your city and click 'Predict' to see the 7-day forecast and crop suitability. Based on rain/temp, I can recommend tailored fertilizer strategies!"
    
    # General
    if any(x in msg_lower for x in ['hello', 'hi', 'hey']):
        return "Hi! I'm the Smart Agro-Weather Advisor. Ask me about crops, weather, fertilizers, biofertilizers, or low-rainfall strategies!"
    if any(x in msg_lower for x in ['help', 'what can you do']):
        return """📚 I CAN HELP WITH:

🌾 **Crop Information**: Temperature, rainfall, suitability for 5 crops
📋 **Fertilizer Strategies**: NPK, brands, application timing, soil testing
🌱 **Biofertilizers**: Rhizobium, Azospirillum, Bacillus benefits & usage
🌡️ **Weather Effects**: How heat/cold/drought impact fertilization
💧 **Low-Rainfall Plans**: Comprehensive drought strategies with scientific backing
🧪 **Micronutrient Deficiencies**: Zn, Fe, Boron, Calcium prevention
🏭 **Recommended Brands**: Shriram Farm Solutions, Neem-coated urea, biofertilizers

**Example queries:**
• "Wheat fertilizer"
• "Rice in low rainfall"
• "Soybean drought strategy"
• "Tomato hot weather"
• "Tell me about biofertilizers"
• "How do I prevent blossom-end rot?"

**SOURCES:** TNAU | FAO | Haifa Group | Agricultural Research"""
    
    # Default fallback
    return """I'm here to help with crops, fertilizers, and weather! Try asking:
• "Low rainfall strategy"
• "Soybean biofertilizer"
• "[Crop name] in [weather condition]"
• "What's the best fertilizer for [crop]?"
• "Help" (for full list)"""


def _find_city_in_text(text):
    """Try to find a known city name in the user text (case-insensitive).
    Returns the matched city name or None.
    """
    if not text:
        return None
    txt = text.lower()
    # match longer city names first to avoid partial matches
    for city in sorted(CITIES, key=lambda x: -len(x)):
        if city.lower() in txt:
            return city
    return None


def _handle_weather_query(message, city=None):
    """Return a friendly weather summary for `city` using available forecast functions."""
    if not city:
        city = _find_city_in_text(message)
    if not city:
        return None

    # Try to fetch forecast using configured provider
    forecast = None
    if API_PROVIDER == 'weatherapi':
        forecast = get_weather_by_city_weatherapi(city)
    elif API_PROVIDER == 'openweather':
        coords = get_coordinates(city)
        if coords:
            forecast = get_weather(coords[0], coords[1])
    # Fallback to sample forecast for city
    if not forecast:
        forecast = sample_forecast_for_city(city) if city in CITY_COORDS else sample_forecast()

    # Compute simple summary
    try:
        temps = [d.get('temp', {}).get('day', 0) for d in forecast[:7]]
        rains = [d.get('rain', 0) for d in forecast[:7]]
        avg_temp = round(sum(temps) / len(temps), 1) if temps else 'N/A'
        total_rain = round(sum(rains), 1)
        first = forecast[0] if len(forecast) > 0 else None
        first_temp = first.get('temp', {}).get('day') if first else None
        first_rain = first.get('rain', 0) if first else 0
        reply = f"7-day forecast for {city}: average {avg_temp}°C, total rain ~{total_rain} mm."
        if first is not None:
            reply += f" Today: {first_temp}°C, rain {first_rain} mm."

        # Add simple alerts
        alerts = get_weather_risk_alerts({'list': [{'main': {'temp': t}, 'rain': {'3h': r}} for t, r in zip(temps, rains)]})
        if alerts:
            reply += " Alerts: " + ", ".join([a['message'] for a in alerts])
        return reply
    except Exception:
        return "I could not fetch the weather right now. Try again later."


def _handle_crop_query(message, city=None):
    """Return crop suitability suggestions for a city using existing crop logic."""
    if not city:
        city = _find_city_in_text(message)
    if not city:
        return None

    # Get forecast (same as weather handler)
    forecast = None
    if API_PROVIDER == 'weatherapi':
        forecast = get_weather_by_city_weatherapi(city)
    elif API_PROVIDER == 'openweather':
        coords = get_coordinates(city)
        if coords:
            forecast = get_weather(coords[0], coords[1])
    if not forecast:
        forecast = sample_forecast_for_city(city) if city in CITY_COORDS else sample_forecast()

    # Load crop master list and run suitability for a few recommended crops for the location
    crops_master = load_crops()
    # Prefer location-based state crops
    loc_crops = get_location_based_crops(city)
    if not loc_crops:
        # fallback: choose top 5 crops from master list
        loc_crops = [c.get('Crop') for c in crops_master[:5]]

    results = []
    for crop_name in loc_crops:
        # find crop entry
        crop_entry = next((c for c in crops_master if c.get('Crop', '').lower() == crop_name.lower()), None)
        if crop_entry:
            status = check_crop_suitability(crop_entry, forecast)
        else:
            status = 'Unknown (no detailed data)'
        results.append({'crop': crop_name, 'status': status})

    # Build reply
    lines = [f"Crop suitability for {city} based on upcoming 7-day forecast:"]
    for r in results:
        lines.append(f"• {r['crop']}: {r['status']}")
    return '\n'.join(lines)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """JSON API for chatbot. Input: {"message":"..."}. Output: {"reply":"..."} """
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_msg = (data.get('message') or '').strip()
    except Exception:
        user_msg = ''

    if not user_msg:
        return jsonify({'reply': "Please send a message in JSON: {\"message\": \"your text\"}"}), 400

    # Try enhanced reply first
    try:
        from chatbot_enhanced import enhanced_reply
        enhanced = enhanced_reply(user_msg)
        if enhanced:
            return jsonify({'reply': enhanced})
    except Exception:
        app.logger.debug('[api/chat] enhanced_reply not available or failed')

    msg_lower = user_msg.lower()
    # If RapidAPI chatbot integration is configured, forward the message there first
    rapidapi_url = os.getenv('RAPIDAPI_URL')
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    rapidapi_host = os.getenv('RAPIDAPI_HOST')
    if rapidapi_url and rapidapi_key:
        try:
            # Build headers expected by RapidAPI
            headers = {
                'Content-Type': 'application/json',
                'x-rapidapi-key': rapidapi_key
            }
            if rapidapi_host:
                headers['x-rapidapi-host'] = rapidapi_host

            payload = {'message': user_msg}
            app.logger.info(f"[api/chat] Forwarding to RapidAPI: {rapidapi_url}")
            r = requests.post(rapidapi_url, json=payload, headers=headers, timeout=8)
            # treat 2xx as success
            if r.status_code >= 200 and r.status_code < 300:
                try:
                    jr = r.json()
                    # Common response shapes: {reply: '...'} or {message: '...'} or {'response': '...'}
                    for k in ('reply', 'message', 'response', 'result'):
                        if isinstance(jr, dict) and k in jr and jr[k]:
                            return jsonify({'reply': str(jr[k])})
                    # fallback to raw text
                    text = jr if isinstance(jr, str) else None
                    if not text:
                        text = r.text
                    return jsonify({'reply': str(text)})
                except Exception:
                    # Not JSON, return text
                    return jsonify({'reply': r.text})
            else:
                app.logger.warning(f"[api/chat] RapidAPI returned status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            app.logger.exception('[api/chat] RapidAPI forward failed')
    # Weather intent
    if any(k in msg_lower for k in ['weather', 'forecast', 'temperature', 'temp']):
        city = _find_city_in_text(user_msg)
        weather_reply = _handle_weather_query(user_msg, city)
        if weather_reply:
            return jsonify({'reply': weather_reply})

    # Crop intent
    if any(k in msg_lower for k in ['which crop', 'suitable', 'best crop', 'which crops', 'suitability']):
        city = _find_city_in_text(user_msg)
        crop_reply = _handle_crop_query(user_msg, city)
        if crop_reply:
            return jsonify({'reply': crop_reply})

    # Greetings and general
    if any(x in msg_lower for x in ['hello', 'hi', 'hey']):
        return jsonify({'reply': chatbot_response(user_msg)})

    # Fallback to general chatbot_response
    reply = chatbot_response(user_msg)
    return jsonify({'reply': reply})

@app.route("/get-cities/<state>", methods=["GET"])
def get_cities(state):
    """Get list of cities for a given state."""
    state = state.strip()
    if state in STATE_CITIES:
        return jsonify({"cities": STATE_CITIES[state]})
    else:
        return jsonify({"error": f"State '{state}' not found"}), 404

@app.route("/get-states", methods=["GET"])
def get_states():
    """Get list of all states/UTs."""
    return jsonify({"states": list(STATE_CITIES.keys())})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Chatbot endpoint."""
    user_msg = request.form.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400
    
    # Try enhanced reply first (uses wikipedia and city data)
    try:
        from chatbot_enhanced import enhanced_reply
        enhanced = enhanced_reply(user_msg)
        if enhanced:
            return jsonify({"reply": enhanced})
    except Exception:
        # If enhanced module fails, fall back to built-in reply
        app.logger.exception("[chat] enhanced_reply failed")

    bot_reply = chatbot_response(user_msg)
    return jsonify({"reply": bot_reply})

@app.route("/predict", methods=["POST"])
def predict():
    # Wrap entire prediction logic in try/except so any server-side error returns JSON
    city = request.form.get("city", "").strip()
    soil_type = request.form.get("soil_type", "").strip()

    if not city:
        return jsonify({"error": "Invalid city. Please enter a valid city name."}), 400

    try:
        # If WeatherAPI is configured, use it (validate city via WeatherAPI)
        if API_PROVIDER == "weatherapi":
            app.logger.info(f"[predict] Using WeatherAPI for city '{city}'")
            forecast = get_weather_by_city_weatherapi(city)
            if not forecast:
                # WeatherAPI failed (invalid key, network issue, etc.); fall back to city-biased sample forecast
                app.logger.warning(f"[predict] WeatherAPI failed for '{city}', using sample forecast instead")
                forecast = sample_forecast_for_city(city) if city in CITY_COORDS else sample_forecast()
            else:
                app.logger.info(f"[predict] WeatherAPI succeeded for '{city}', got {len(forecast)} days")
        elif API_PROVIDER == "openweather":
            # Use OpenWeather geocoding + onecall
            coords = get_coordinates(city)
            if not coords:
                # geocoding failed -> fallback to city sample forecast instead of error
                app.logger.warning(f"[predict] OpenWeather geocoding failed for '{city}', using sample forecast")
                forecast = sample_forecast_for_city(city) if city in CITY_COORDS else sample_forecast()
            else:
                lat, lon = coords
                forecast = get_weather(lat, lon)
        else:
            # No external API configured: perform a basic sanity check on the city string
            import re
            # allow letters (including many latin letters), numbers, spaces, commas, periods, hyphens and apostrophes
            # require at least 2 characters
            if not re.match(r"^[A-Za-zÀ-ž0-9 .,'-]{2,}$", city):
                return jsonify({"error": "Invalid city. Please enter a valid city name."}), 400
            # pass sanity check -> if city in predefined list, use its city-biased sample forecast
            if city in CITY_COORDS:
                forecast = sample_forecast_for_city(city)
            else:
                forecast = sample_forecast()

        crops = load_crops()

        results = []
        for crop in crops:
            suitability = check_crop_suitability(crop, forecast)
            results.append({
                "crop": crop.get("Crop"),
                "status": suitability
            })

        # Get weather risk alerts
        weather_alerts = get_weather_risk_alerts(forecast)
        
        # Get location-based crop recommendations
        location_crops = get_location_based_crops(city)
        
        # Get soil-based crop recommendations if soil type provided
        soil_recommendations = None
        if soil_type:
            soil_recommendations = get_soil_based_recommendations(soil_type)
        
        # Generate planting calendar
        calendar = generate_planting_calendar(forecast, city)
        
        # Detect pest risks
        pest_risks = detect_pest_risk(forecast)

        return jsonify({
            "forecast": forecast,
            "results": results,
            "weather_alerts": weather_alerts,
            "location_crops": location_crops,
            "soil_recommendations": soil_recommendations,
            "calendar": calendar,
            "pest_risks": pest_risks
        })
    except Exception as e:
        app.logger.exception(f'Error during /predict for city {city}')
        # Return JSON error so frontend can render a helpful message instead of an HTML traceback
        error_msg = f"Failed to generate forecast for '{city}': {str(e)}"
        app.logger.error(f"[predict] Returning error: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/send-alert", methods=["POST"])
def send_alert():
    """Send SMS or WhatsApp alert."""
    alert_type = request.form.get("alert_type", "").strip()
    phone = request.form.get("phone", "").strip()
    method = request.form.get("method", "sms").strip()  # sms or whatsapp
    city = request.form.get("city", "").strip()
    value = request.form.get("value", "").strip()
    
    # Validate required fields: alert_type and phone (city is optional)
    if not alert_type:
        return jsonify({"status": "error", "message": "Alert type is required"}), 400
    if not phone:
        return jsonify({"status": "error", "message": "Phone number is required"}), 400
    
    # Extract digits from phone and validate length
    phone_digits = ''.join(c for c in phone if c.isdigit())
    if len(phone_digits) < 10:
        return jsonify({"status": "error", "message": "Phone number must have at least 10 digits"}), 400
    
    # Ensure phone has country code format for Twilio
    if not phone.startswith('+'):
        phone = '+' + phone_digits
    
    # Default city if not provided
    if not city:
        city = "Unknown Location"
    
    # Format message
    message = format_alert_message(alert_type, value, city)
    
    # Send via selected method (SMS only now)
    result = send_sms_alert(phone, message)
    
    return jsonify(result)


@app.route("/test-sms", methods=["POST"])
def test_sms():
    """Test SMS alert with hardcoded values for testing."""
    data = request.get_json()
    test_phone = data.get("phone", "+919876543210")
    test_alert_type = data.get("alert_type", "heatwave")
    test_city = data.get("city", "Mumbai")
    test_value = data.get("value", "42")
    
    # Normalize phone
    phone_digits = ''.join(c for c in test_phone if c.isdigit())
    if len(phone_digits) < 10:
        return jsonify({"status": "error", "message": "Invalid phone number"}), 400
    
    if not test_phone.startswith('+'):
        test_phone = '+' + phone_digits
    
    # Generate alert message
    test_message = format_alert_message(test_alert_type, test_value, test_city)
    
    # Send SMS
    app.logger.info(f"[TEST SMS] Sending test alert to {test_phone}")
    result = send_sms_alert(test_phone, test_message)
    
    # Log result
    if result.get("status") == "success":
        app.logger.info(f"[TEST SMS] ✓ Success: {result}")
    else:
        app.logger.warning(f"[TEST SMS] Failed: {result}")
    
    return jsonify(result)


@app.route('/alert-popup')
def alert_popup():
    # Render a small popup window with alert form. 'method' query param can be 'whatsapp' or 'sms'.
    from flask import request
    method = request.args.get('method', 'whatsapp')
    return render_template('alert_popup.html', method=method)


@app.route('/city-crops/<city>', methods=['GET'])
def api_city_crops(city):
    """Return crops, soil and region for a given city."""
    city = city.strip()
    from city_crop_soil_data import get_city_crops, get_city_soil, get_city_region
    crops = get_city_crops(city)
    soil = get_city_soil(city)
    region = get_city_region(city)
    if not crops and soil == 'Unknown' and region == 'Unknown':
        return jsonify({'error': f"City '{city}' not found"}), 404
    return jsonify({
        'city': city,
        'crops': crops,
        'soil': soil,
        'region': region
    })


@app.route('/city-info/<city>', methods=['GET'])
def api_city_info(city):
    """Return a human-friendly string with city agricultural profile (for quick use)."""
    city = city.strip()
    from chatbot_enhanced import get_city_recommendations
    resp = get_city_recommendations(city)
    if resp.startswith('❌'):
        return jsonify({'error': resp}), 404
    return jsonify({'city': city, 'profile': resp})

if __name__ == "__main__":
    app.run(debug=True)
