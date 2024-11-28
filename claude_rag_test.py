from langchain_community.vectorstores import MyScale, MyScaleSettings
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoModel, AutoTokenizer
from dotenv import load_dotenv
import os
import anthropic


load_dotenv()
## Setting up the vector database connections
os.environ["MYSCALE_HOST"] = os.getenv('MYSCALE_HOST')
os.environ["MYSCALE_PORT"] = os.getenv('MYSCALE_PORT')
os.environ["MYSCALE_USERNAME"] = os.getenv('MYSCALE_USERNAME')
os.environ["MYSCALE_PASSWORD"] = os.getenv('MYSCALE_PASSWORD')
## Claude 3
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
client = anthropic.Anthropic(api_key=anthropic_api_key)


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

## Connect Myscal vector database
base_model = "ckiplab/bert-base-chinese"
config = MyScaleSettings()
config.table = "verdict"
docsearch = MyScale(
    embedding=get_embeddings(base_model),
    config=config,
    )

# Testing Document Search
query =  "我因為合夥關係被對方起訴，應該怎麼處理？"
docs = docsearch.similarity_search(query, 5)
# print(docs)

## Preparing the Query Context
stre = "".join(doc.page_content for doc in docs)

## Setting the Model
model = 'claude-3-5-haiku-latest'

## Generating the Answer
response = client.messages.create(
        system =  "You are a professional legal advisor specializing in Taiwanese law. You will be shown data from a legal knowledge base, such as case law and verdicts. Your goal is to answer the user's query based on the provided data or, if no relevant data is found, using your own legal expertise. Be clear and provide practical legal advice that suits the Taiwanese context.",
        messages=[
                    {"role": "user", "content":  "Context: " + stre + "\\\\n\\\\n Query: " + query},
                ],
        model= model,
        temperature=0,
        max_tokens=1000
    )
# print(response)
print(response.content[0].text)
