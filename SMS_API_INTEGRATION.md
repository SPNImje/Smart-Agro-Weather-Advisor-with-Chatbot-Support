# SMS API Integration Guide

## Overview
The Crop-Friendly Weather Predictor now uses **Twilio SMS API** for sending weather alerts to Indian farmers. This integration provides reliable SMS delivery with comprehensive error handling.

---

## Current Configuration

### Environment Variables (`.env`)
```env
TWILIO_ACCOUNT_SID=AC8d24d2544e897a232b904cd7ac6f5950
TWILIO_AUTH_TOKEN=b72108b07530d1da76b8800a2c14ab59
TWILIO_PHONE=+919325582876
TWILIO_SMS_ENABLED=true
```

### Dependencies
- **twilio** (9.1.0): Official Twilio Python SDK
- **requests**: HTTP library (already installed)
- **Flask**: Web framework (already installed)

### Verification
✅ **SMS Integration Status:** READY  
✅ **Twilio Account:** Active  
✅ **API Connection:** Validated  

---

## Features

### 1. Alert Types Supported
- 🔥 **Heatwave Warning** - High temperature alerts
- 🌧️ **Heavy Rain Warning** - Rainfall alerts

### 2. SMS Message Templates

**Heatwave Alert:**
```
WEATHER ALERT {City}: Heatwave warning. Max temp {Temp}°C. 
Stay hydrated. Reduce outdoor work.
```

**Heavy Rain Alert:**
```
WEATHER ALERT {City}: Heavy rain expected. Total rainfall {Rain}mm. 
Secure crops. Avoid travel.
```

### 3. Country Support
- 🇮🇳 **India** - +91 (Primary focus)
- Default country code auto-applied to 10-digit numbers

---

## How SMS Alerts Work

### Step 1: User Submits Alert Request
```javascript
// Frontend (script.js)
sendWeatherAlert() {
  - Select alert type (Heatwave or Heavy Rain)
  - Enter phone number (10 digits, auto-adds +91)
  - Click "Send SMS"
}
```

### Step 2: Backend Processing
```python
# Backend (app.py)
@app.route('/send-alert', methods=['POST'])
def send_alert():
    phone = request.json.get('phone')
    alert_type = request.json.get('alert_type')
    
    # Generate formatted message
    message = generate_alert_message(alert_type, city)
    
    # Send via SMS API
    result = send_sms_alert(phone, message)
    return jsonify(result)
```

### Step 3: Twilio SMS Delivery
```python
# SMS Function (app.py)
def send_sms_alert(phone_number, message):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    sms = client.messages.create(
        body=message,
        from_=TWILIO_PHONE,        # Sender (Twilio number)
        to=phone_number            # Recipient (farmer's number)
    )
    
    return {
        "status": "success",
        "sms_id": sms.sid,
        "recipient": phone_number,
        "timestamp": datetime.now().isoformat()
    }
```

### Step 4: User Receives SMS
```
From: +919325582876
Message: WEATHER ALERT Mumbai: Heatwave warning. Max temp 42°C. 
         Stay hydrated. Reduce outdoor work.
```

---

## Error Handling

### Common Error Codes

| Error Code | Issue | Solution |
|-----------|-------|----------|
| **21211** | Invalid phone number format | Use +91XXXXXXXXXX format |
| **21212** | Invalid 'From' number | Update TWILIO_PHONE in .env |
| **21266** | Sender = Recipient | Use different phone for TWILIO_PHONE |
| **20003** | Invalid credentials | Check ACCOUNT_SID & AUTH_TOKEN in .env |

### Demo Mode
When Twilio credentials are missing, the system automatically switches to **Demo Mode**:
- Shows success message to user
- Logs SMS action
- Doesn't send actual SMS
- Useful for testing without Twilio setup

---

## Testing

### Run Integration Test
```bash
python test_sms_integration.py
```

**Expected Output:**
```
============================================================
SMS API INTEGRATION TEST
============================================================

[CHECK 1] Credentials Loaded
  ✓ Account SID: AC8d24d254...
  ✓ Auth Token: b72108b075...
  ✓ Sender Phone: +919325582876

[CHECK 2] Twilio Client Connection
  ✓ Connected to Twilio account: My first Twilio account
  ✓ Account Status: active

[CHECK 3] SMS Configuration
  ✓ All credentials validated
  ✓ SMS integration ready

INTEGRATION STATUS: READY
============================================================
```

### Send Test SMS (Manual)
```python
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("AC8d24d2544e897a232b904cd7ac6f5950"),
    os.getenv("b72108b07530d1da76b8800a2c14ab59")
)

message = client.messages.create(
    body="Test SMS from Crop-Friendly Weather Predictor",
    from_=os.getenv("TWILIO_PHONE"),
    to="+91XXXXXXXXXX"  # Your phone number
)

print(f"✓ SMS Sent - SID: {message.sid}")
```

---

## Production Setup

### 1. Get Twilio Account
- Visit [twilio.com](https://www.twilio.com)
- Sign up for free trial
- Verify phone number
- Get: Account SID, Auth Token, Twilio Phone Number

### 2. Update `.env`
```env
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE=+1XXXXXXXXXX  # Your Twilio number
TWILIO_SMS_ENABLED=true
```

### 3. Test Connection
```bash
python test_sms_integration.py
```

### 4. Deploy
```bash
python app.py
```

---

## Best Practices

✅ **Always Validate Phone Numbers**
- Check for +91 country code
- Validate 10-digit format for India
- Strip formatting (spaces, dashes)

✅ **Include Alert Context**
- City name
- Temperature/rainfall values
- Recommended actions

✅ **Handle Rate Limiting**
- Twilio allows ~100 SMS/sec
- Alert system already has built-in delays
- Monitor logs for send failures

✅ **Secure Credentials**
- Never commit `.env` to git
- Use `.gitignore` to exclude `.env`
- Rotate tokens periodically

✅ **Monitor SMS Costs**
- India SMS: ~₹0.50-1.00 per message
- Monitor Twilio dashboard for usage
- Set billing alerts in Twilio console

---

## Troubleshooting

### Issue: SMS not sending

**Check 1:** Credentials valid?
```bash
python test_sms_integration.py
```

**Check 2:** Phone number format?
- Should be: +91XXXXXXXXXX (for India)
- Or: 10 digits (auto-adds +91)

**Check 3:** Twilio balance?
- Free trial: Limited credits
- Check Twilio dashboard for balance

**Check 4:** Logs
```bash
# Check app logs for error messages
tail -f app.log
```

### Issue: "Sender and recipient are the same"

**Solution:** 
- TWILIO_PHONE must be a Twilio-assigned number
- Cannot be your personal phone number
- Update TWILIO_PHONE in `.env`

---

## Integration Points

### Frontend (script.js)
```javascript
// Send SMS alert to backend
sendWeatherAlert() {
  fetch('/send-alert', {
    method: 'POST',
    body: JSON.stringify({
      phone: countryCode + phone,
      alert_type: alertType,
      city: selectedCity
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'success') {
      showSuccessMessage("SMS sent!");
    } else {
      showErrorMessage(data.message);
    }
  })
}
```

### Backend (app.py)
```python
# Receive alert request and send SMS
@app.route('/send-alert', methods=['POST'])
def send_alert():
    phone = request.json['phone']
    alert_type = request.json['alert_type']
    city = request.json['city']
    
    message = generate_alert_message(alert_type, city)
    result = send_sms_alert(phone, message)
    
    return jsonify(result)
```

### Twilio API
```
POST /2010-04-01/Accounts/{AccountSid}/Messages.json
From: +919325582876
To: +919876543210
Body: WEATHER ALERT...
```

---

## Monitoring & Analytics

### View SMS Logs in App
```python
# Check app.logger output
grep "\[SMS\]" app.log
```

### Twilio Dashboard
- Login to [twilio.com/console](https://twilio.com/console)
- View sent messages
- Monitor costs
- Check delivery status

### Typical Log Output
```
[SMS] Sending SMS from +919325582876 to +919876543210
[SMS] ✓ Success - SID: SM12345..., Status: queued
```

---

## Future Enhancements

🔄 **Scheduled Alerts** - Auto-send alerts at specific times  
📊 **Analytics** - Track delivery success rates  
🔔 **Multiple Recipients** - Send to groups of farmers  
💰 **Cost Tracking** - Monitor SMS expenses  
🌐 **Multi-Language** - Support regional languages  

---

## Support

For issues:
1. Run `python test_sms_integration.py`
2. Check `.env` configuration
3. Review app logs: `grep "\[SMS\]" app.log`
4. Verify Twilio account: [twilio.com/console](https://twilio.com/console)

