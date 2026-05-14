import requests

key = "removed"

r = requests.get(
    'https://openrouter.ai/api/v1/models',
    headers={'Authorization': f'Bearer {key}'}
)

models = r.json()['data']

for m in models:
    model_id = m['id']
    if ':free' in model_id and any(x in model_id.lower() for x in ['vision', 'vl', 'llava', 'qwen', 'gemini', 'gpt-4', 'claude']):
        print(model_id)