import os
import boto3
from botocore.exceptions import ClientError
from langchain.embeddings.bedrock import BedrockEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders.fs.pdf import PDFLoader
from langchain.vectorstores.lancedb import LanceDB

# # Env vars
# lance_db_src = os.environ['s3BucketName']
# lance_db_table = os.environ['lanceDbTable']
# aws_region = os.environ['region']

# splitter = CharacterTextSplitter(chunkSize=1000, chunkOverlap=200)

# embeddings = BedrockEmbeddings(region=aws_region, model='amazon.titan-embed-text-v1')

# s3_client = boto3.client('s3', region_name=aws_region)


# def download_object(bucket_name, object_key, download_path):
#     try:
#         # Get the object from the Amazon S3 bucket
#         response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
#         # Stream the object to a file
#         with open(download_path, 'wb') as f:
#             f.write(response['Body'].read())
#         print(f'File downloaded to {download_path}')
#     except ClientError as e:
#         print('Error:', e)


# async def create_directory():
#     tmp_path = os.path.join('/tmp', 'documents')
#     try:
#         os.makedirs(tmp_path, exist_ok=True)
#         print(f'Directory created at: {tmp_path}')
#     except OSError as e:
#         print('Error creating directory:', e)


# async def lambda_handler(event, context):
#     # The S3 event contains details about the uploaded object
#     bucket_name = event['Records'][0]['s3']['bucket']['name']
#     object_key = event['Records'][0]['s3']['object']['key'].replace('+', ' ')
#     file_path = f'/tmp/{object_key}'

#     await create_directory()

#     download_object(bucket_name, object_key, file_path)

#     try:
#         loader = PDFLoader(file_path, splitPages=False)
#         docs = await loader.load_and_split(splitter)
#     except Exception as e:
#         print('Error loading documents:', e)
#         return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

#     dir = f's3://{lance_db_src}/embeddings'
#     create_table = False

#     try:
#         db = LanceDB(dir)
#     except Exception as e:
#         print('Error connecting to LanceDB:', e)
#         return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

#     try:
#         table = db.open_table(lance_db_table)
#     except Exception as e:
#         create_table = True
#         print('Table not found with error', e)

#     if create_table:
#         print(f'{lance_db_table} table not found. Creating it.')
#         try:
#             table = db.create_table(lance_db_table, [
#                 {'vector': [0] * 1536, 'text': 'sample'}
#             ])
#         except Exception as e:
#             print(f'Error connecting to LanceDB table {lance_db_table} :', e)
#             return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

#     docs = [{'pageContent': doc.pageContent, 'metadata': {}} for doc in docs]

#     await LanceDB.from_documents(docs, embeddings, table=table)

#     return {'statusCode': 201, 'body': json.dumps({'message': 'OK'})}
