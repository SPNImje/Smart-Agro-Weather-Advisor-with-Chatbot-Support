# 🌾 Smart Agro-Weather Advisor with Chatbot Support

A modern, intelligent web application that predicts crop suitability based on 7-day weather forecasts across Indian cities. Features real-time weather data, AI-powered crop recommendations, and an interactive chatbot for agricultural guidance.

## Features

✨ **Core Capabilities**
- 🌤️ **7-Day Weather Forecast**: Real-time data from WeatherAPI for 8 major Indian cities
- 🌾 **Crop Suitability Prediction**: Automatic recommendation of best crops based on temperature and rainfall
- 💬 **AI Chatbot**: Interactive assistant providing crop, weather, and fertilizer guidance
- 📊 **Dark-Themed Dashboard**: Modern, responsive UI with weather cards and forecast grid
- 🌡️ **Dual Temperature Units**: Switch between Celsius and Fahrenheit

### Supported Cities
- Mumbai
- Delhi
- Bengaluru
- Hyderabad
- Chennai
- Kolkata
- Pune
- Ahmedabad

### Supported Crops
- **Wheat**: Best in cool climates (10–25°C, 20mm rain)
- **Rice**: Thrives in warm, wet conditions (20–35°C, 100mm rain)
- **Corn**: Versatile crop (18–30°C, 50mm rain)
- **Soybean**: Nitrogen-fixing (15–30°C, 40mm rain)
- **Tomato**: Year-round suitable (18–30°C, 20mm rain)

## Chatbot Features

The integrated chatbot provides:
- 📚 **Crop Information**: Temperature, rainfall, and growth requirements
- 🧪 **Fertilizer Recommendations**: NPK ratios, application timing, and weather-specific strategies
- 🌡️ **Weather Guidance**: How weather affects crops and fertilizer selection
- 🤔 **General Help**: User guide and feature overview

### Example Chatbot Queries
- "Tell me about wheat fertilizer"
- "Rice in hot weather"
- "What fertilizer for tomato in cold weather?"
- "Corn wet conditions"
- "Help"

## Installation

### Prerequisites
- Python 3.8+
- WeatherAPI key (free tier available at https://www.weatherapi.com)
- Internet connection for real-time weather data

### Step 1: Clone or Download Project
```bash
cd "s:\MINI PROJECT\Crop-Friendly Weather Predictor"
```

### Step 2: Create Virtual Environment
```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
```

### Step 3: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 4: Configure WeatherAPI Key
Create a `.env` file in the project root:
```
WEATHERAPI_KEY=your_api_key_here
```

Get your free key from: https://www.weatherapi.com/signup.aspx

### Step 5: Run the Application
```powershell
& ".\.venv\Scripts\python.exe" app.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

## Usage

### Weather & Crop Prediction
1. Select a city from the dropdown
2. Choose temperature unit (°C or °F)
3. Click "Predict" to fetch the 7-day forecast
4. View crop suitability (Highly Suitable, Moderately Suitable, Not Suitable)
5. Check daily forecast cards with temperature and rainfall

### Chatbot Interaction
1. Look for the "🌾 Crop Assistant" panel in the bottom-right corner
2. Click to expand/collapse the chat
3. Type your question about crops, weather, or fertilizers
4. Get instant recommendations and guidance

### Crop Suitability Legend
- 🟢 **Highly Suitable**: Ideal conditions for the crop
- 🟡 **Moderately Suitable**: Some concerns (temp or rain issues)
- 🔴 **Not Suitable**: Poor conditions for the crop

## Project Structure

```
Crop-Friendly Weather Predictor/
├── app.py                 # Flask backend with chatbot logic
├── requirements.txt       # Python dependencies
├── .env                   # API keys (create this file)
├── data/
│   └── crops.csv         # Crop temperature/rainfall data
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── style.css         # Dark-themed styling
│   └── script.js         # Frontend logic & chatbot UI
└── README.md             # This file
```

## Technologies Used

### Backend
- **Flask 2.3.2**: Python web framework
- **Requests**: HTTP client for WeatherAPI calls
- **Python-dotenv**: Environment variable management
- **CSV**: Built-in data format for crop specs

### Frontend
- **HTML5**: Modern markup
- **CSS3**: Gradient, flexbox, dark theme styling
- **JavaScript (ES6+)**: Real-time chat, weather updates, temperature conversion

### APIs
- **WeatherAPI**: 7-day forecast data for Indian cities

## API Endpoints

### GET `/`
Returns the main HTML interface.

### POST `/predict`
Predicts crop suitability for a selected city.
```json
{
  "city": "Mumbai"
}
```
Response:
```json
{
  "forecast": [ { "dt": 1764134643, "temp": {"day": 27.1}, "rain": 29.2 }, ... ],
  "results": [ { "crop": "Rice", "status": "Highly Suitable" }, ... ]
}
```

### POST `/chat`
Sends a user message and gets a chatbot response.
```json
{
  "message": "Tell me about wheat fertilizer"
}
```
Response:
```json
{
  "reply": "Wheat needs nitrogen-rich fertilizers (urea 46% N) at 120kg/ha..."
}
```

## Fertilizer Recommendations

The chatbot provides detailed fertilizer guidance including:
- **NPK Ratios**: Nitrogen, Phosphorus, Potassium percentages
- **Application Rates**: kg/ha (kilograms per hectare)
- **Timing**: When to apply (planting, tillering, flowering, etc.)
- **Weather Adjustments**: Hot, cold, wet weather strategies

### Example: Wheat Fertilizer
- **General**: 120kg/ha urea (46% N), split application
- **Hot Weather**: Slow-release nitrogen, +potassium for drought resistance
- **Wet Weather**: Organic phosphorus-rich amendments, avoid excess N
- **Cold Weather**: Liquid fertilizers for faster absorption, NPK 10:26:26

## Environment Variables

Create a `.env` file with:
```env
WEATHERAPI_KEY=your_api_key_here
```

Optional (for OpenWeather fallback):
```env
OPENWEATHER_API_KEY=your_openweather_key_here
```

The app prioritizes WeatherAPI if both are set.

## Demo Mode

Without an API key, the app uses city-biased synthetic weather data for demos/testing:
- Run normally and select a city
- View realistic crop predictions based on typical climate data
- Full chatbot functionality available

## Troubleshooting

### Issue: "Invalid city" error
- Ensure you're selecting from the predefined city list
- Verify your WeatherAPI key is valid
- Check internet connection

### Issue: Chatbot not responding
- Verify `/chat` endpoint is accessible
- Check browser console (F12) for JavaScript errors
- Ensure app server is running

### Issue: Forecast not loading
- Confirm WeatherAPI key in `.env`
- Check that the city name is spelled correctly in the API
- Verify internet connectivity

### Issue: Python venv activation fails
For PowerShell, you may need to allow script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Future Enhancements

- 🌱 **Soil Analysis**: Integrate soil type recommendations
- 🦗 **Pest Management**: Disease/pest alerts based on weather
- 📱 **Mobile App**: React Native or Flutter version
- 🌍 **Global Support**: Expand beyond Indian cities
- 🔐 **User Accounts**: Save preferences and history
- 📈 **Analytics**: Crop yield forecasting with ML
- 🎤 **Voice Chat**: Voice-based chatbot queries

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

## License

This project is open-source and available under the MIT License.

## Support

For issues, feature requests, or questions:
- Check the troubleshooting section above
- Review API documentation at https://www.weatherapi.com/docs/
- Contact the development team

## Credits

- **WeatherAPI**: Real-time weather data
- **Flask**: Web framework
- **Modern UI Design**: Inspired by contemporary weather apps

---

**Last Updated**: November 26, 2025  
**Version**: 1.0.0
