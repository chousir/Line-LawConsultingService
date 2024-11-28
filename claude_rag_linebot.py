from langchain_community.vectorstores import MyScale, MyScaleSettings
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoModel, AutoTokenizer
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, 
    TextMessage, 
    TextSendMessage
    )
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
claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
## Line
api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_SECRET'))

app = Flask(__name__)

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

@app.post("/")
def callback():
    # 取得 X-Line-Signature 表頭電子簽章內容
    signature = request.headers['X-Line-Signature']

    # 以文字形式取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 比對電子簽章並處理請求內容
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("電子簽章錯誤, 請檢查密鑰是否正確？")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("收到的消息內容：", event.message.text)  # 調試打印

    # 使用 MyScale 搜索相似文檔
    query =  event.message.text
    docs = docsearch.similarity_search(query, 5)
    print(docs)

    # if not docs:
    #     api.reply_message(event.reply_token, TextSendMessage(text="無法找到相關的資料。"))
    #     return

    # 準備檢索到的文書內容作為上下文
    stre = "".join(doc.page_content for doc in docs)

    # 使用 Claude 生成回答
    try:
        model = 'claude-3-5-sonnet-20241022'
        response = claude_client.messages.create(
        system = (
            "You are a professional legal advisor specializing in Taiwanese law. You will be shown data from a legal knowledge base, such as case law and verdicts. "
            "Your goal is to answer the user's query based on the provided data or, if no relevant data is found, using your own legal expertise. "
            "Be clear and provide practical legal advice that suits the Taiwanese context. "
            "If there are any relevant verdicts or case law available, please provide those as references and explain how they could influence the potential ruling in the user's case."
        ),
        messages=[
                    {"role": "user", "content":  "Context: " + stre + "\\\\n\\\\n Query: " + query},
                ],
        model= model,
        temperature=0,
        max_tokens=1000
        )
        reply = response.content[0].text
    except Exception as e:
        print(f"Claude 生成回答失敗: {e}")
        reply = "對不起，我無法生成回答。"

    # 發送回覆給 Line 使用者
    api.reply_message(event.reply_token, TextSendMessage(text=reply))
    print("生成的回覆：", reply)  # 調試打印

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
