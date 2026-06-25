import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google import genai

app = FastAPI()

# 🔑 ULTRA CORZ PATCH: This forces the browser to accept responses even when loading a local file!
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Set the key directly in python runtime
# Pulls the key safely from Render's cloud settings instead of hardcoding it!
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


class InterventionRequest(BaseModel):
    paragraph_text: str
    arm: str

# Handle the pre-flight check requests sent by browsers
@app.options("/generate-intervention")
async def options_handler():
    return JSONResponse(content="OK")

@app.post("/generate-intervention")
async def generate_intervention(request: InterventionRequest):
    strategies = {
        "A_definition": "Identify the most complex technical word or phrase in this paragraph and provide a short, clear vocabulary definition for a student.",
        "B_summary": "Provide a single-sentence, simple summary highlighting the main core concept of this paragraph.",
        "C_rephrase": "Rewrite this paragraph using much easier language, short sentences, and simple words suitable for someone struggling to read it.",
        "D_analogy": "Provide a creative, relatable, real-life analogy or comparison that explains the logic behind this paragraph."
    }

    if request.arm not in strategies:
        raise HTTPException(status_code=400, detail="Invalid intervention strategy")

    prompt = f"""
    You are an expert, empathetic AI reading assistant. 
    The student is struggling to understand the following paragraph:
    {request.paragraph_text}
    
    Task: {strategies[request.arm]}
    
    Rules: 
    - Output ONLY the direct support text. 
    - Do not add any introduction or meta-commentary.
    - Keep it concise, helpful, and directly tailored to the reader.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {"support_text": response.text.strip()}
    except Exception as e:
        print(f"\n[ERROR] Gemini API Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    # Port is dynamically assigned by the cloud provider, fallback to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)