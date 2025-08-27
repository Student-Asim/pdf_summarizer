from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import requests
import io
import PyPDF2
import uvicorn


app=FastAPI()

# store the summary;
last_summary=" "

# openrouter api key
OPENROUTER_API_KEY="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"
OPENROUTER_URL="https://openrouter.ai/api/v1/chat/completions"

def summarize_with_openrouter(text:str)->str:
    headers={
        "Authorization":f"Bearer {OPENROUTER_API_KEY}",
        "content-Type":"application/json"
    }
    payload={
        "model":"mistralai/mistral-7b-instruct",
        "message":[
            {"role":"system","content":"You are a helpful assistant that summarizes PDFs."},
            {"role":"user","content": f"Summarize the following text in only 100 words:\n{text}"}
        ]
    }
    response=requests.post(OPENROUTER_URL,json=payload,headers=headers)
    result=response.json()
    try:
        return result["choices"][0]["message"]["content"]
    except:
        return "Failed to summarie with Openrouter API."
@app.post("/upload")

async def upload_file(file:UploadFile=File(...)):
    global last_summary
    # ensure pdf
    if not file.filename.endswith(".pdf"):
        return {"error":"only pdf files are supported."}
    # read pdf content
    pdf_content=await file.read()
    pdf_reader=PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text="\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])

    if not text.strip():
        return {"error":"Failed to extract text from PDF"}
    # summarize
    summary=summarize_with_openrouter(text)
    last_summary=summary

    return {"filename":file.filename, "summary":summary}
    



@app.post("/query")
def get_content():
    if not last_summary:
        return {"message":"No summary available yet. Please upload a PDF first."}
    return {"summary":last_summary}



if __name__=="__main__":
    
    uvicorn.run(app,host="127.0.0.1",port=8000)


