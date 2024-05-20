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


# Env vars
lance_db_src = os.environ['s3BucketName']
lance_db_table = os.environ['lanceDbTable']
aws_region = os.environ['region']

text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

embeddings = BedrockEmbeddings()

s3_client = boto3.client('s3', region_name=aws_region)


def download_object(bucket_name, object_key, download_path):
    try:
        # Get the object from the Amazon S3 bucket
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        # Stream the object to a file
        with open(download_path, 'wb') as f:
            f.write(response['Body'].read())
        print(f'File downloaded to {download_path}')
    except ClientError as e:
        print('Error:', e)

async def create_directory():
    tmp_path = os.path.join('/tmp', 'documents')
    try:
        os.makedirs(tmp_path, exist_ok=True)
        print(f'Directory created at: {tmp_path}')
    except OSError as e:
        print('Error creating directory:', e)

def lambda_handler(event, context):
    # The S3 event contains details about the uploaded object
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key'].replace('+', ' ')
    file_path = f'/tmp/{object_key}'
    
    asyncio.run(create_directory())

    download_object(bucket_name, object_key, file_path)
    
    try:
        loader = PyPDFLoader(file_path)
        #docs = asyncio.run(loader.load_and_split(splitter))
    except Exception as e:
        print('Error loading documents:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

    print("Hello world")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
