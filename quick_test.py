from app import app, index

with app.test_request_context('/'):
	resp = index()
	# `index()` returns rendered HTML string via render_template
	print('OK: index rendered, length=', len(resp))
	print(resp[:500])

with app.test_request_context('/predict', method='POST', data={'city': 'Pune'}):
	from app import predict
	resp = predict()
	# `predict()` returns a Flask Response (jsonify)
	try:
		data = resp.get_json()
	except Exception:
		data = None
	print('\n/predict response keys:', list(data.keys()) if isinstance(data, dict) else type(resp))
