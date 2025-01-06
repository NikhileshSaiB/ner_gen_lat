import os
import json
from azure.storage.blob import BlobServiceClient
# import fitz
import json
import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv



load_dotenv()     
azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
azure_oai_key = os.getenv("AZURE_OAI_KEY")
azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")


# Configuration
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=formrecogdxcdemo;AccountKey=BmgQ1ohc4CIxOdsReik+Io+EJ5zFciGMUExz3I5fdBqLs1Ew5875YqSmqXLgTNrsAi84tpxxHybF+ASt20QrwA==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "ner-docs"

# Initialize Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Upload document to Blob Storage
def upload_document(file):
    container_client.upload_blob(file.filename, file.stream, overwrite=True)

# def read_pdf_document(blob_name):
#     blob_client = container_client.get_blob_client(blob_name)
#     with open("temp.pdf", "wb") as temp_file:
#         blob_client.download_blob().readinto(temp_file)
#     # Extract text from PDF
#     text = ""
#     with fitz.open("temp.pdf") as pdf_document:
#         for page in pdf_document:
#             text += page.get_text()
#     return text

import pdfplumber

def read_pdf_document(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    with open("temp.pdf", "wb") as temp_file:
        blob_client.download_blob().readinto(temp_file)

    text = ""
    with pdfplumber.open("temp.pdf") as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


# Perform Named Entity Recognition
def perform_ner(text):

    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
            azure_endpoint = azure_oai_endpoint, 
            api_key=azure_oai_key,  
            api_version="2023-03-15-preview"
        )

    message_text = [
    {
        "role": "system",
        "content": "You are a highly intelligent and accurate Named-entity recognition(NER) system for insurance domain. I will provide you the definition of the entities you need to extract and the sentence from which you need to extract the entities and the output only as json format as specified within the examples. You take Passage as input and your task is to recognize and extract specific types of predefined named entities in that given passage."
    },
    {
        "role": "user",
        "content": "Entity Definition:\n"
        "1. Maximum: Maximum dollar amount an employee can receive for Life Benefits."
        "2. AD&D Maximum Amount: Maximum dollar amount an employee can receive for AD&D Benefits."
        "3. Acceleration Max %: benefit allows employees who are diagnosed as being terminally ill to receive a percentage of portion of their life benefit before they become deceased\n"
        "4. Acceleration Max Amount: benefit allows employees who are diagnosed as being terminally ill to receive a portion of their life benefit before they become deceased\n"
        "5. Elimination Period: Elimination period for the Waiver of Premium benefit.  The number of months an employee must be disabled prior to the Waiver of Premium benefit beginning​\n"
        "6. Coverage Termination Age: Termination age for the Waiver of Premium benefit.  The age when an employee’s Waiver of Premium benefit will end​."
        "\n"
    },
    {
        "role": "assistant",
        "content": "I will extract only from provided predefined entities based on the definition"
    },
    {
        "role": "user",
        "content": "\nLIFE INSURANCE\nBenefit Amount\nPersonal Life Insurance\nTwo times Basic Annual Earnings, rounded to the next higher\n$1,000; subject to a maximum of $500,000. AD&D INSURANCE\nBenefit Amount\nAD&D Insurance Principal Sum\nTwo times Basic Annual Earnings, rounded to the next higher\n$1,000; subject to a maximum of $500,000\n ACCELERATED DEATH BENEFIT.\nYou may elect to withdraw an Accelerated\nDeath Benefit in any $1,000 increment. The amount is subject to:\n(1)\na minimum of $50,000 or 25% of your amount of Personal Life Insurance (whichever is less);\nand\n(2)\na maximum of $250,000 or 75%"
    },
    {
        "role": "assistant",
        "content": '{"Maximum": "$500,000", "AD&D Maximum Amount": "$500,000", "Acceleration Max %": "75%","Acceleration Max Amount":"$250,000","Elimination Period":"None", "Coverage Termination Age" : "None"}'
    },
    {
        "role": "user",
        "content": "WAIVER OF PREMIUM IN EVENT OF TOTAL DISABILITY\nWe will extend the Amount of Insurance during a period of Total \nDisability for one (1) year if:\n(1) you become totally disabled prior to age 60;\n(2) the Total Disability begins while you are insured;\n(3) the Total Disability begins while the Policy is in force;\n(4) the Total Disability lasts for at least 9 months LIFE INSURANCE LIVING BENEFIT RIDER .......... 15.0\nLRS-6441-1 Ed. 9/89\nPage 1.0\nSCHEDULE OF BENEFITS\nEFFECTIVE DATE:  April 1, 2015\nELIGIBLE CLASSES:  Each active, Full-time Employee, except any \nperson employed on a temporary or seasonal basis.\nWAITING PERIOD:  5 weeks of continuous employment.\nINDIVIDUAL EFFECTIVE DATE:  The day immediately following \ncompletion of the Waiting Period.\nINDIVIDUAL REINSTATEMENT:  6 months\nAMOUNT OF INSURANCE:\nBasic Life and Accidental Death and Dismemberment:  100% of \nEarnings, rounded to the next higher $1,000, subject to a minimum \nAmount of Insurance of $1,000 and a maximum Amount of Insurance of \n$150,000 Living Benefit will be an \namount equal to 75% of the Death Benefit applicable to the Insured under \nthe Policy on the date of the Certification of Terminal Illness, subject to a \nmaximum benefit of $500,000"
    },
    {
        "role": "assistant",
        "content": '{"Maximum": "$150,000", "AD&D Maximum Amount": "$150,000", "Acceleration Max %": "75%","Acceleration Max Amount":"$500,000","Elimination Period":"9 months", "Coverage Termination Age" : "60"}'
    },
    {
        "role": "user",
        "content": text
    }
    ]
    response = client.chat.completions.create(
            model=azure_oai_deployment,
            temperature=0.6,
            messages=message_text
        )
    generated_text = response.choices[0].message.content
    print(f'generatedtest-{generated_text}')
    # generated_text[generated_text.find('{'):generated_text.rfind('}')+1]
    entities_json = json.loads(generated_text[generated_text.find('{'):generated_text.rfind('}')+1])
    print(f'generatejson-{entities_json}')
    entities_df = pd.DataFrame.from_dict(entities_json,orient='index').rename_axis('Entity',axis=1).rename(columns = {0:'Value'})
    entities_df = entities_df.to_html()
    return entities_json, entities_df,generated_text

# Write output to a file and upload to Blob Storage
def upload_output(ner_result,file_name):
    output_blob_client = container_client.get_blob_client(file_name+".json")
    output_data = json.dumps(ner_result)
    output_blob_client.upload_blob(output_data, overwrite=True)