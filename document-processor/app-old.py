import os
import boto3
import tempfile
import json
import asyncio
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import LanceDB
from botocore.exceptions import ClientError



async def create_directory():
    tmp_path = os.path.join('/tmp', 'documents')
    try:
        os.makedirs(tmp_path, exist_ok=True)
        print(f'Directory created at: {tmp_path}')
    except OSError as e:
        print('Error creating directory:', e)

async def tester():
    print("hello async")

def lambda_handler():
    # The S3 event contains details about the uploaded object
    
    asyncio.run(tester())
    #asyncio.run(create_directory())


    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

if __name__ == '__main__':
    lambda_handler()