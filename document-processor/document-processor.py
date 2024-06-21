import os
import boto3
import tempfile
import json
import pathlib
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_community.document_loaders import JSONLoader
#from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
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
    file_type = pathlib.Path(file_path).suffix

    create_directory()

    download_object(bucket_name, object_key, file_path)

    try:
        if file_type == '.csv':
            print(f'CSV loader in progress')
            loader = CSVLoader(file_path)
        elif file_type == '.pdf':
            print(f'PDF loader in progress')
            loader = PyPDFLoader(file_path)
        elif file_type == '.html':
            print(f'HTML loader in progress')
            loader = UnstructuredHTMLLoader(file_path)
        elif file_type == '.json':
            print(f'JSON loader in progress')
            loader = JSONLoader(file_path)
        else:
            raise Exception('Invalid file type uploaded')
            
        #endpoint = "<endpoint>"
        #key = "<key>"
        #loader = AzureAIDocumentIntelligenceLoader(
        #           api_endpoint=endpoint, api_key=key, file_path=file_path, api_model="prebuilt-layout"
        #            )
        docs = loader.load_and_split(text_splitter)
    except Exception as e:
        print('Error loading documents:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

    dir = f's3://{lance_db_src}/embeddings'
    
    try:
        #db = LanceDB(uri=dir, region=aws_region, embedding=embeddings, table_name=lance_db_table)
        vector_store = LanceDB(
                            uri=dir,
                            embedding=embeddings,
                            table_name=lance_db_table
                            )
    except Exception as e:
        print('Error connecting to LanceDB:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
    
    try:
        db = vector_store.add_documents(docs)
    except Exception as e:
        print('Error persisting to LanceDB:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
    
    
    return {'statusCode': 201, 'body': json.dumps({'message': 'OK'})}