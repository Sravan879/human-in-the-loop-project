import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import datetime

# --- Firebase Setup ---
KEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'service-account-key.json')

cred = credentials.Certificate(KEY_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- FastAPI App ---
app = FastAPI()

# --- CORS Middleware ---
# This allows our React frontend (running on a different port) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Data Models (using Pydantic) ---
# This defines how the data should look for requests
class HelpRequest(BaseModel):
    customer_id: str
    question: str

class SupervisorResponse(BaseModel):
    answer: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Salon AI Supervisor API is running"}

# Endpoint for the AI agent to create a help request
@app.post("/help-requests")
def create_help_request(request: HelpRequest):
    new_request = {
        "customer_id": request.customer_id,
        "question": request.question,
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "supervisor_answer": None,
        "resolved_at": None
    }
    # Add to Firestore and get the document reference
    update_time, doc_ref = db.collection("help_requests").add(new_request)
    print(f" Created help request {doc_ref.id} for question: '{request.question}'")
    
    # Simulate texting the supervisor
    print(f" SUPERVISOR ALERT: Need help answering '{request.question}' for customer {request.customer_id}")
    
    return {"request_id": doc_ref.id, "data": new_request}

# Endpoint for the supervisor UI to get all requests
@app.get("/help-requests")
def get_all_help_requests():
    requests_ref = db.collection("help_requests").stream()
    requests = []
    for req in requests_ref:
        request_data = req.to_dict()
        request_data["id"] = req.id # Add the document ID to the dictionary
        requests.append(request_data)
    return sorted(requests, key=lambda r: r['created_at'], reverse=True)

# Endpoint for the supervisor to respond and resolve a request
@app.put("/help-requests/{request_id}")
def resolve_help_request(request_id: str, response: SupervisorResponse):
    request_ref = db.collection("help_requests").document(request_id)
    request_doc = request_ref.get()

    if not request_doc.exists:
        raise HTTPException(status_code=404, detail="Help request not found")

    # 1. Update the help request status
    request_ref.update({
        "status": "resolved",
        "supervisor_answer": response.answer,
        "resolved_at": datetime.datetime.now(datetime.timezone.utc)
    })
    
    request_data = request_doc.to_dict()
    
    # 2. Simulate texting back the customer
    print("\n" + "="*50)
    print(f" IMMEDIATE FOLLOW-UP to customer {request_data['customer_id']}:")
    print(f" Regarding your question '{request_data['question']}', the answer is: '{response.answer}'")
    print("="*50 + "\n")

    # 3. Update the Knowledge Base
    kb_ref = db.collection("knowledge_base").document()
    kb_ref.set({
        "question": request_data["question"],
        "answer": response.answer,
        "learned_on": datetime.datetime.now(datetime.timezone.utc)
    })
    print(f" Knowledge base updated with the new answer.")
    
    return {"message": f"Request {request_id} resolved and knowledge base updated."}

# Endpoint to view the knowledge base
@app.get("/knowledge-base")
def get_knowledge_base():
    kb_ref = db.collection("knowledge_base").stream()
    entries = [entry.to_dict() for entry in kb_ref]
    return entries
