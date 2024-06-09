import boto3
import json
from langchain_aws import BedrockLLM
from langchain import hub
from langchain_community.vectorstores import LanceDB
from botocore.exceptions import ClientError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# Env vars
lance_db_src = os.environ['s3BucketName']
lance_db_table = os.environ['lanceDbTable']
aws_region = os.environ['region']

# Clients
s3_client = boto3.client('s3', region_name=aws_region)

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def lambda_handler(event, context):
    
    try:
        vector_store = LanceDB(
            uri=lance_db_src,
            region=aws_region,
            table_name=lance_db_table
            )
    except Exception as e:
        print('Error connecting to LanceDB:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

    retriever = vector_store.as_retriever()
    
    # Create prompt
    prompt = hub.pull("rlm/rag-prompt")

    # Initialize the Bedrock LLM
    bedrock_llm = BedrockLLM(
        model_id="anthropic.claude-v2:1"
    )

    # Create RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | bedrock_llm
        | StrOutputParser()
    )

    # Query the RAG chain
    response = rag_chain.invoke("List all the bedrock models available?")

    # Print response
    print("Response: " + response)

    return {'statusCode': 201, 'body': json.dumps({'message': 'OK'})}