from dotenv import load_dotenv
load_dotenv('.env')

import json
from database.redis_client import redis_client

# Clear test keys if present
redis_client.delete('resume:res_t_1', 'resume:res_t_2')

# Setup initial mocked resumes
redis_client.set('resume:res_t_1', json.dumps({'user_email': 'test_ver@demo.com', 'version': 1}))
redis_client.set('resume:res_t_2', json.dumps({'user_email': 'test_ver@demo.com', 'version': 2}))

# Replicate the logic from resume_routes.py
current_user = 'test_ver@demo.com'
cursor = '0'
version_count = 0
while cursor != 0:
    cursor, keys = redis_client.scan(cursor=cursor, match="resume:res_*", count=100)
    for k in keys:
        try:
            data_str = redis_client.get(k)
            if data_str:
                d = json.loads(data_str)
                if d.get("user_email") == current_user:
                    version_count += 1
        except Exception as e:
            pass
    if cursor == 0 or cursor == b'0':
        break

next_version = version_count + 1
print(f"Total found assigned to {current_user}: {version_count}")
print(f"Net new version flag generated: {next_version}")
