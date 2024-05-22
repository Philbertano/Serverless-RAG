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


def lambda_handler():
    # The S3 event contains details about the uploaded object
    
    region_name ="us-east-1"
    credentials_profile_name = "default"
    model_id = "amazon.titan-embed-text-v1"

    embeddings = BedrockEmbeddings(
        credentials_profile_name=credentials_profile_name,
        region_name=region_name,
        model_id=model_id
        )
    
    #db = LanceDB(connection="/documents/bedrock-docs-2012.10.20.pdf". embedding=embeddings)
    #asyncio.run(create_directory())
    vector_store = LanceDB(
        uri="documents/embeddings",
        region="us-west-1",
        embedding=embeddings,
        table_name='langchain_test'
        )
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

if __name__ == '__main__':
    lambda_handler()