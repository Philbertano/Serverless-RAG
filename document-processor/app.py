import os
import boto3
import tempfile
import json
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

s3_client = boto3.client('s3', region_name=aws_region)

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)

model_id = "amazon.titan-embed-text-v1"

embeddings = BedrockEmbeddings(
    client=bedrock_client,
    model_id=model_id
    )

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


def create_directory():
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

    create_directory()

    download_object(bucket_name, object_key, file_path)

    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load_and_split(text_splitter)
    except Exception as e:
        print('Error loading documents:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

    dir = f's3://{lance_db_src}/embeddings'
    
    try:
        db = LanceDB(uri=dir, region=aws_region, embedding=embeddings, table_name=lance_db_table)
    except Exception as e:
        print('Error connecting to LanceDB:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

    docs = [{'pageContent': doc.page_content, 'metadata': doc.metadata} for doc in docs]

    LanceDB.from_documents(docs, embeddings, table=table)

    return {'statusCode': 201, 'body': json.dumps({'message': 'OK'})}