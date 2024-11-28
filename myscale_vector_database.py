from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import MyScale, MyScaleSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from transformers import AutoModel, AutoTokenizer
# from huggingface_hub import login
from dotenv import load_dotenv
import os
import json


load_dotenv()
## Setting up the vector database connections
os.environ["MYSCALE_HOST"] = os.getenv('MYSCALE_HOST')
os.environ["MYSCALE_PORT"] = os.getenv('MYSCALE_PORT')
os.environ["MYSCALE_USERNAME"] = os.getenv('MYSCALE_USERNAME')
os.environ["MYSCALE_PASSWORD"] = os.getenv('MYSCALE_PASSWORD')
## Setting up the API key for Hugging Face
# huggingface_token = os.getenv('HUGGINGFACE_HUB_TOKEN')
# login(token=huggingface_token)


## Data preprocessing
def print_json_files(directory):
    docs = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as json_file:
                    try:
                        data = json.load(json_file)
                        jfull_content = data.get("JFULL", "")
                        if jfull_content:
                            cleaned_content = jfull_content.replace("\r\n", "").replace(" ", "").replace("\u3000", "")
                            if len(cleaned_content) > 100:
                                docs.append(Document(page_content=cleaned_content))
                            # print(f"JFULL Content: {cleaned_content}\n")

                            ## batch upload to MyScale
                            if len(docs) >= 1000:
                                upload_to_myscale(docs)
                                docs = []
                    except json.JSONDecodeError as e:
                        print(f"Error reading JSON file {file_path}: {e}")
    return docs

## emmbedding model
def get_embeddings(base_model):
    model_name_or_path = "./models/" + base_model
    if not hasattr(get_embeddings, "model"):
        if not os.path.exists(model_name_or_path):
            print("Downloading and saving the model locally...")
            # Save and load from local
            tokenizer = AutoTokenizer.from_pretrained(base_model)
            model = AutoModel.from_pretrained(base_model)
            tokenizer.save_pretrained(model_name_or_path)
            model.save_pretrained(model_name_or_path)
        else:
            print("Loading model from local storage...")
        # load from local
        get_embeddings.model = HuggingFaceEmbeddings(model_name=model_name_or_path)
    return get_embeddings.model

## Import data to Myscale vector database
def upload_to_myscale(docs):
    # Split documents into chunks
    character_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    split_docs = character_splitter.split_documents(docs)

    # Connect Myscale vector database
    base_model = "ckiplab/bert-base-chinese"
    config = MyScaleSettings()
    config.table = "verdict"
    docsearch = MyScale(
        embedding=get_embeddings(base_model),
        config=config,
    )

    # Load external data to MyScale
    docsearch.add_documents(split_docs)

if __name__ == "__main__":
    download_directory = "data/"
    print_json_files(download_directory)
