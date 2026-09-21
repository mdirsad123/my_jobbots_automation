from fastapi import FastAPI
from pydantic import BaseModel

from search_chatgpt_screenshot_problem import ask_question_to_chatgpt
app = FastAPI()

@app.post("/ask_chatgpt")
async def ask_chatgpt_endpoint(request: dict):
    # You can extract parameters from the request if needed
    # For this example, we will just call the function directly
    try:
        # msg = ask_question_to_chatgpt()
        msg = 'Function called successfully'

    except Exception as e:
        return {"error": str(e)}

    return {"message": msg}