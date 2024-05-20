import os
import boto3
import tempfile
from langchain.embeddings.bedrock import BedrockEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders.fs.pdf import PDFLoader
from vectordb import connect, LanceDB
from botocore.exceptions import ClientError

# Set environment variables
lance_db_src = os.environ['s3BucketName']
lance_db_table = os.environ['lanceDbTable']
aws_region = os.environ['region']

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=aws_region)

# Initialize LangChain components
splitter = CharacterTextSplitter(chunkSize=1000, chunkOverlap=200)
embeddings = BedrockEmbeddings(region=aws_region, model='amazon.titan-embed-text-v1')

def download_object(bucket_name, object_key, download_path):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
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

async def handler(event, context):
    # Extract details from S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key'].replace('+', ' ')
    file_path = os.path.join('/tmp', object_key)

    # Create directory for downloaded files
    await create_directory()

    # Download the object from S3
    download_object(bucket_name, object_key, file_path)

    # Load and split PDF documents
    try:
        loader = PDFLoader(file_path, splitPages=False)
        docs = await loader.loadAndSplit(splitter)
    except Exception as e:
        print('Error loading documents:', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }

    # Connect to LanceDB
    dir = f's3://{lance_db_src}/embeddings'
    try:
        db = await connect(dir)
    except Exception as e:
        print('Error connecting to LanceDB:', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }

    # Open or create LanceDB table
    try:
        table = await db.openTable(lance_db_table)
    except Exception as e:
        print('Table not found with error:', e)
        create_table = True

    if create_table:
        print(f'{lance_db_table} table not found. Creating it.')
        try:
            table = await db.createTable(lance_db_table, [
                {'vector': [None] * 1536, 'text': 'sample'}
            ])
        except Exception as e:
            print(f'Error connecting to LanceDB table {lance_db_table}:', e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': str(e)})
            }

    # Process documents and store in LanceDB
    docs = [{'pageContent': doc.pageContent, 'metadata': {}} for doc in docs]
    await LanceDB.fromDocuments(docs, embeddings, table=table)

    return {
        'statusCode': 201,
        'body': json.dumps({'message': 'OK'})
    }
