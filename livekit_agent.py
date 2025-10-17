import asyncio
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore
from livekit import rtc
from livekit_api import AccessToken, VideoGrant

# --- LiveKit Configuration ---
LIVEKIT_URL = "wss://human-in-the-loop-lro67xex.livekit.cloud" 
LIVEKIT_API_KEY = "APIGHhPPPNMXMSC"
LIVEKIT_API_SECRET = "PS8f1KIH5bf5vM75fQ52hVXWyYidV7LUf7o73HTgxftF"

# --- Firebase Setup ---
cred = credentials.Certificate('service-account-key.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Backend API URL ---
API_URL = "http://127.0.0.1:8000"

# --- Agent's Initial Knowledge ---
INITIAL_KNOWLEDGE_BASE = {
    "what are your hours?": "We are open from 9 AM to 6 PM, Monday to Saturday.",
    "where are you located?": "We are located at 123 Salon Street.",
    "do you accept walk-ins?": "Yes, we accept walk-ins, but appointments are recommended."
}

async def main():
    room_name = "salon-support-call"
    agent_identity = "ai-salon-agent"

    print(f"🤖 AI Agent '{agent_identity}' is attempting to join room '{room_name}'...")

    room = rtc.Room()

    # Event handler for when the agent receives a data message (a "question")
    @room.on("data_received")
    async def on_data_received(data: rtc.DataPacket):
        payload_str = data.data.decode('utf-8')
        payload = json.loads(payload_str)
        question = payload.get("question")
        customer_id = data.participant.identity

        if not question:
            return

        print(f"\n Incoming question from Customer '{customer_id}': '{question}'")
        
        normalized_question = question.lower().strip()
        answer = None

        # 1. Check initial knowledge
        if normalized_question in INITIAL_KNOWLEDGE_BASE:
            answer = INITIAL_KNOWLEDGE_BASE[normalized_question]
            print(f" Found in initial knowledge. Responding...")
        # 2. Check learned knowledge base in Firestore
        else:
            kb_ref = db.collection("knowledge_base").stream()
            for item in kb_ref:
                kb_item = item.to_dict()
                if kb_item.get("question", "").lower().strip() == normalized_question:
                    answer = kb_item.get("answer")
                    print(f"📚 Found in learned knowledge. Responding...")
                    break
        
        # If we have an answer, send it back to the user
        if answer:
            response_payload = json.dumps({"answer": answer})
            await room.local_participant.publish_data(response_payload)
            print(f"   Sent response: '{answer}'")
        
        # 3. If no answer is found, escalate to human
        else:
            print(" I don't know the answer. Escalating to supervisor...")
            await room.local_participant.publish_data(json.dumps({"answer": "Let me check with my supervisor and get back to you."}))
            
            try:
                # Trigger the "request help" event by calling our backend
                requests.post(
                    f"{API_URL}/help-requests",
                    json={"customer_id": customer_id, "question": question}
                )
                print("   Escalation successful. Request sent to supervisor.")
            except requests.exceptions.ConnectionError:
                print("   ---! CONNECTION ERROR !--- Could not connect to the backend.")

    # Generate a token for the agent to join the room
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
    .with_identity(agent_identity) \
    .with_name("AI Salon Agent") \
    .with_grant(VideoGrant(room_join=True, room=room_name)) \
    .to_jwt()

    try:
        await room.connect(LIVEKIT_URL, token)
        print(f" Agent connected to room '{room.name}'. Waiting for calls...")
        # Keep the agent running indefinitely to listen for events
        await room.run()
    except Exception as e:
        print(f" Failed to connect to LiveKit room: {e}")
    finally:
        await room.disconnect()
        print("Agent has disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
