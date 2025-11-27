# Enhanced Chatbot Module with City-Crop-Soil Information

from city_crop_soil_data import get_city_info, get_city_crops, get_city_soil, get_city_region
import requests
import urllib.parse
import os

def get_city_recommendations(city_name):
    """Generate crop and soil recommendations for a city."""
    info = get_city_info(city_name)
    if not info:
        return f"❌ Sorry, I don't have detailed information for {city_name} yet. Try other major cities."
    
    crops_str = ", ".join(info.get("crops", []))
    soil = info.get("soil", "Unknown")
    region = info.get("region", "Unknown")
    state = info.get("state", "Unknown")
    
    response = f"""
🌾 **{city_name.upper()}** - Agricultural Profile

📍 **Location:** {region}, {state}
🌱 **Famous Crops:** {crops_str}
🌍 **Best Soil:** {soil}

🌿 **Region Characteristics:**
• This region is known for cultivating {crops_str}
• Soil type: {soil}
• Well-suited for the regional climate and water availability

💡 **Recommendations:**
• Focus on {info['crops'][0]} for highest yield potential
• Ensure soil type is {soil} (or amend accordingly)
• Use region-specific crop varieties for better adaptation
• Consider local agricultural extension services for best practices

📞 **For Detailed Support:**
Ask about:
• Fertilizer needs for specific crops
• Best season to plant
• Weather-based recommendations
• Pest and disease management
"""
    return response.strip()


def search_cities_by_crop(crop_name):
    """Find cities where a specific crop is grown."""
    from city_crop_soil_data import CITY_CROP_SOIL_REGION
    
    matching_cities = []
    for city, info in CITY_CROP_SOIL_REGION.items():
        if crop_name.lower() in [c.lower() for c in info.get("crops", [])]:
            matching_cities.append({
                "city": city,
                "state": info["state"],
                "region": info["region"]
            })
    
    if not matching_cities:
        return f"❌ No major cities found growing {crop_name}. Try asking about specific cities."
    
    response = f"🌾 **Cities Growing {crop_name}:**\n\n"
    for item in matching_cities:
        response += f"• **{item['city']}** ({item['region']}, {item['state']})\n"
    
    response += f"\n💡 **Total:** {len(matching_cities)} major cities\n"
    response += "Ask for specific city details or soil requirements!"
    
    return response


def search_cities_by_soil(soil_type):
    """Find cities with specific soil types."""
    from city_crop_soil_data import CITY_CROP_SOIL_REGION
    
    matching_cities = []
    for city, info in CITY_CROP_SOIL_REGION.items():
        if soil_type.lower() in info.get("soil", "").lower():
            matching_cities.append({
                "city": city,
                "state": info["state"],
                "soil": info["soil"]
            })
    
    if not matching_cities:
        return f"❌ No cities found with {soil_type}. Try similar soil types."
    
    response = f"🌾 **Cities with {soil_type}:**\n\n"
    for item in matching_cities:
        response += f"• **{item['city']}** - {item['soil']} ({item['state']})\n"
    
    response += f"\n💡 **Total:** {len(matching_cities)} cities\n"
    response += "Ask for fertilizer recommendations for these soils!"
    
    return response


def get_enhanced_help():
    """Provide comprehensive help with city information."""
    return """
📚 **SMART AGRO-WEATHER ADVISOR - COMPLETE GUIDE**

🌍 **CITY & REGION INFORMATION:**
• "Tell me about [City name]" - Get crops, soil, and region info
• "What's grown in [City name]?" - Learn about local crops
• "Find cities growing [Crop name]" - Find all cities for a crop
• "Which cities have [Soil type]?" - Find by soil type

🌾 **CROP QUERIES:**
• "Wheat fertilizer" - Detailed fertilizer guide
• "Rice in low rainfall" - Drought strategies
• "[Crop] in [weather]" - Weather-specific advice
• "Best crops for [soil type]" - Soil-based recommendations

🌡️ **WEATHER & FERTILIZER:**
• "Heatwave strategy" - Handle high temperatures
• "Cold weather crops" - Winter recommendations
• "Biofertilizers" - Organic and microbial fertilizers
• "Low rainfall strategy" - Drought management

🔍 **AVAILABLE CITIES:**
Maharashtra: Mumbai, Pune, Nagpur, Nashik, Kolhapur
Uttar Pradesh: Lucknow, Kanpur, Varanasi, Agra
Punjab: Amritsar, Ludhiana, Jalandhar
Haryana: Gurugram, Hisar
Rajasthan: Jaipur, Udaipur, Jodhpur
Gujarat: Ahmedabad, Surat, Rajkot
Madhya Pradesh: Indore, Bhopal, Gwalior
Karnataka: Bengaluru, Mysuru, Belagavi
Tamil Nadu: Chennai, Coimbatore, Madurai
West Bengal: Kolkata, Siliguri
Odisha: Bhubaneswar, Cuttack
Andhra Pradesh: Visakhapatnam, Guntur
Telangana: Hyderabad
Kerala: Kochi
Assam: Guwahati

💡 Try: "Tell me about Mumbai" or "Find cities growing Cotton"
"""
def fetch_wikipedia_summary(topic, sentences=3):
        """Fetch a short summary from Wikipedia REST API for the given topic.

        Returns a short string summary or None if not found or on error.
        """
        try:
            title = urllib.parse.quote(topic)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            r = requests.get(url, timeout=6)
            if r.status_code != 200:
                return None
            data = r.json()
            extract = data.get("extract")
            if not extract:
                return None
            # Optionally truncate to requested sentences
            parts = extract.split('. ')
            if len(parts) > sentences:
                return '. '.join(parts[:sentences]).strip() + '.'
            return extract.strip()
        except Exception:
            return None


def enhanced_reply(user_message):
        """Produce an enhanced chatbot reply using local knowledge + Wikipedia lookups.

        Returns a string reply or None when no enhancement is available.
        """
        msg = user_message.strip()
        if not msg:
            return None

        lower = msg.lower()

        # If user asks for help, return enhanced help
        if any(x in lower for x in ["help", "what can you do", "commands", "options"]):
            return get_enhanced_help()

        # City requests: "tell me about <city>" or "about <city>"
        if lower.startswith("tell me about ") or lower.startswith("about "):
            # extract topic
            if lower.startswith("tell me about "):
                topic = msg[len("tell me about "):].strip()
            else:
                topic = msg[len("about "):].strip()
            # Try city recommendations first
            city_info = get_city_info(topic)
            if city_info:
                return get_city_recommendations(topic)
            # otherwise fall back to Wikipedia
            wiki = fetch_wikipedia_summary(topic)
            if wiki:
                return f"📚 Quick summary for **{topic.title()}**:\n\n{wiki}\n\nIf you want local crop/soil tips, ask 'Tell me about <CityName>'"
            return None

        # Crop queries: look for common crop words and provide wiki + local tips
        common_crops = ["wheat", "rice", "corn", "maize", "soybean", "tomato", "cotton", "sugarcane", "potato"]
        for crop in common_crops:
            if crop in lower:
                wiki = fetch_wikipedia_summary(crop.title())
                cities = get_city_crops(crop.title()) if callable(getattr(__import__('city_crop_soil_data'), 'get_city_crops', None)) else None
                resp = []
                if wiki:
                    resp.append(f"📚 {crop.title()} — {wiki}")
                if cities:
                    sample = ", ".join(cities[:5])
                    resp.append(f"🌾 Major local cities: {sample} ({len(cities)} total) — ask 'Find cities growing {crop.title()}' for full list.")
                fert_hint = {
                    'wheat': 'Use split N applications; consider 120kg/ha N and balanced P/K.',
                    'rice': 'High N demand; consider 3 splits and maintain proper water management.',
                    'corn': 'Split N; prioritize phosphorus for root development.',
                    'soybean': 'Use Rhizobium inoculation; moderate P and K.',
                    'tomato': 'High K for fruit quality; control N for balance.'
                }.get(crop, None)
                if fert_hint:
                    resp.append(f"💡 Quick tip: {fert_hint}")
                return "\n\n".join(resp)

        # Generic 'what is X' or 'who is' -> wiki
        if lower.startswith("what is ") or lower.startswith("who is ") or lower.startswith("define "):
            parts = msg.split()
            topic = ' '.join(parts[2:]) if len(parts) > 2 else msg
            wiki = fetch_wikipedia_summary(topic)
            if wiki:
                return f"📚 {wiki}"
            return None

        return None
