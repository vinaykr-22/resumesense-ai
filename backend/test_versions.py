import json
import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

from routes.resume_routes import get_resume_versions, compare_versions
from database.redis_client import redis_client

# Define mock test data
redis_client.set('resume:res_v1_test', json.dumps({'user_email': 'test@test.com', 'version': 1}))
redis_client.set('result:res_v1_test', json.dumps({'analysis_data': {'ats_score': 30.0, 'extracted_skills': ['css']}}))

redis_client.set('resume:res_v2_test', json.dumps({'user_email': 'test@test.com', 'version': 2}))
redis_client.set('result:res_v2_test', json.dumps({'analysis_data': {'ats_score': 85.0, 'extracted_skills': ['css', 'python']}}))

async def run():
    print("Versions:", await get_resume_versions('test@test.com'))
    print("Compare:", await compare_versions('res_v1_test', 'res_v2_test', 'test@test.com'))
    
if __name__ == '__main__':
    asyncio.run(run())
