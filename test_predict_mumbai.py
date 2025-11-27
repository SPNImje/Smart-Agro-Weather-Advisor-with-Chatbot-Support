from app import app
import json

with app.test_client() as client:
    resp = client.post('/predict', data={'city': 'Mumbai'})
    print('Status:', resp.status_code)
    try:
        print(json.dumps(resp.get_json(), indent=2))
    except Exception:
        print(resp.data.decode())
