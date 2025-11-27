from app import app, predict
import json

with app.test_request_context('/predict', method='POST', data={'city': 'Mumbai'}):
    resp = predict()
    # predict() may return a Flask Response or a tuple
    status = None
    data = None
    if isinstance(resp, tuple):
        # (response, status)
        response_obj = resp[0]
        status = resp[1] if len(resp) > 1 else None
    else:
        response_obj = resp
    try:
        data = response_obj.get_json()
    except Exception:
        try:
            data = response_obj
        except Exception:
            data = str(response_obj)
    print('Status:', status if status else '200 or no explicit status')
    print(json.dumps(data, indent=2))
