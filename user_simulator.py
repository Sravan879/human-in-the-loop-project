import asyncio
import json
from livekit import rtc
from livekit_api import AccessToken, VideoGrant

# --- LiveKit Configuration ---
LIVEKIT_URL = "wss://human-in-the-loop-lro67xex.livekit.cloud" 
LIVEKIT_API_KEY = "APIGHhPPPNMXMSC" 
LIVEKIT_API_SECRET = "PS8f1KIH5bf5vM75fQ52hVXWyYidV7LUf7o73HTgxftF"

async def main():
    room_name = "salon-support-call"
    user_identity = "CUST-LIVE-001"

    print(f" User '{user_identity}' is attempting to join room '{room_name}'...")
    room = rtc.Room()

    @room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        # This function listens for the agent's response
        payload = json.loads(data.data.decode('utf-8'))
        answer = payload.get("answer")
        print(f"💬 Agent responded: '{answer}'")

    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
    .with_identity(user_identity) \
    .with_name("Customer") \
    .with_grant(VideoGrant(room_join=True, room=room_name)) \
    .to_jwt()

    try:
        await room.connect(LIVEKIT_URL, token)
        print(f" User connected to room '{room.name}'.")
    except Exception as e:
        print(f" Failed to connect user to room: {e}")
        return

    # --- Simulate Asking Questions ---
    # Question 1: Agent knows this one
    await asyncio.sleep(2)
    question1 = "What are your hours?"
    print(f"\n> Asking: '{question1}'")
    await room.local_participant.publish_data(json.dumps({"question": question1}))

    # Question 2: Agent does NOT know this one, will escalate
    await asyncio.sleep(5)
    question2 = "Do you offer manicures?"
    print(f"\n> Asking: '{question2}'")
    await room.local_participant.publish_data(json.dumps({"question": question2}))

    # Wait a bit to receive the final answer before disconnecting
    await asyncio.sleep(5)
    await room.disconnect()
    print("\n Call ended. User has disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
