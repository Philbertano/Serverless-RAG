import os
import boto3
import tempfile
from langchain.embeddings.bedrock import BedrockEmbeddings
from langchain.text_splitter import CharacterTextSplitter
#from langchain.document_loaders import PDFLoader
#from vectordb import connect, LanceDB
from botocore.exceptions import ClientError

def handler(event, context):
    print("Hello world")
