# API Extensions for City Information
# This file contains route handlers that should be added to app.py

# Add these imports to app.py:
# from chatbot_enhanced import get_city_recommendations, search_cities_by_crop, search_cities_by_soil, get_enhanced_help

# Add these routes to app.py (before if __name__ == "__main__"):

"""
@app.route("/city-info/<city>", methods=["GET"])
def city_info(city):
    '''Get comprehensive agricultural information for a city.'''
    from chatbot_enhanced import get_city_recommendations
    info = get_city_recommendations(city)
    return jsonify({"city": city, "info": info})

@app.route("/search-by-crop/<crop>", methods=["GET"])
def search_by_crop(crop):
    '''Find all cities growing a specific crop.'''
    from chatbot_enhanced import search_cities_by_crop
    result = search_cities_by_crop(crop)
    return jsonify({"crop": crop, "result": result})

@app.route("/search-by-soil/<soil>", methods=["GET"])
def search_by_soil(soil):
    '''Find all cities with a specific soil type.'''
    from chatbot_enhanced import search_cities_by_soil
    result = search_cities_by_soil(soil)
    return jsonify({"soil": soil, "result": result})

@app.route("/city-crops/<city>", methods=["GET"])
def city_crops(city):
    '''Get crops for a specific city.'''
    from city_crop_soil_data import get_city_crops, get_city_soil, get_city_region
    crops = get_city_crops(city)
    soil = get_city_soil(city)
    region = get_city_region(city)
    return jsonify({"city": city, "crops": crops, "soil": soil, "region": region})
"""

# Enhanced chatbot queries to add to chatbot_response() function:

"""
# Add these BEFORE the "# Default fallback" section in chatbot_response():

# City information queries
if 'tell me about' in msg_lower or 'info about' in msg_lower or 'agricultural profile' in msg_lower:
    # Extract city name from message
    from chatbot_enhanced import get_city_recommendations
    words = msg_lower.split()
    for i, word in enumerate(words):
        if word in ['about', 'for']:
            if i + 1 < len(words):
                city_name = ' '.join(words[i+1:]).title()
                result = get_city_recommendations(city_name)
                if "❌" not in result:
                    return result
    return "Please specify a city. Try: 'Tell me about Mumbai' or 'Info about Pune'"

# Search by crop
if 'find cities' in msg_lower and 'grow' in msg_lower:
    from chatbot_enhanced import search_cities_by_crop
    words = msg_lower.split()
    for i, word in enumerate(words):
        if word == 'growing' or (word == 'grow' and i + 1 < len(words)):
            idx = i + 1
            crop_name = ' '.join(words[idx:]).strip()
            if crop_name:
                return search_cities_by_crop(crop_name)
    return "Please specify a crop. Try: 'Find cities growing Cotton' or 'Which cities grow Rice?'"

# Search by soil
if any(x in msg_lower for x in ['which cities have', 'cities with', 'soil type']):
    from chatbot_enhanced import search_cities_by_soil
    for soil_type in ['alluvial', 'black soil', 'red soil', 'loamy', 'sandy', 'laterite']:
        if soil_type in msg_lower:
            return search_cities_by_soil(soil_type)
    return "Which soil type? Try: 'Cities with black soil' or 'Which cities have alluvial soil?'"

# City-specific crop queries
city_names = ['Mumbai', 'Delhi', 'Bengaluru', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata', 
              'Lucknow', 'Kanpur', 'Amritsar', 'Jaipur', 'Ahmedabad', 'Indore', 'Mysuru',
              'Gurugram', 'Visakhapatnam', 'Guntur', 'Kochi', 'Guwahati', 'Cuttack',
              'Bhubaneswar', 'Coimbatore', 'Madurai', 'Siliguri', 'Rajkot', 'Surat',
              'Jodhpur', 'Udaipur', 'Hisar', 'Agra', 'Varanasi', 'Nashik', 'Kolhapur',
              'Belagavi', 'Nagpur', 'Jalandhar', 'Gwalior', 'Bhopal']

for city in city_names:
    if city.lower() in msg_lower:
        from chatbot_enhanced import get_city_recommendations
        return get_city_recommendations(city)
"""

print("✓ API routes and chatbot enhancements ready for integration into app.py")
