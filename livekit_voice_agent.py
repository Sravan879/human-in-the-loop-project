import asyncio
import os
import json
import requests
import firebase_admin
import logging
from firebase_admin import credentials, firestore
from livekit import rtc
from livekit_api import AccessToken, VideoGrant
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

# --- Configuration ---
LIVEKIT_URL = "wss://human-in-the-loop-lro67xex.livekit.cloud" 
LIVEKIT_API_KEY = "APIGHhPPPNMXMSC"
LIVEKIT_API_SECRET = "PS8f1KIH5bf5vM75fQ52hVXWyYidV7LUf7o73HTgxftF"
DEEPGRAM_API_KEY = "813a552fadc028c688ad903b497cfa8712a39c2a"
ELEVENLABS_API_KEY = "sk_c82725ca5d8c710b4fe06d33a94fdc4b931ae49bd8e8bd8e"

API_URL = "http://127.0.0.1:8000" 

# --- Firebase Setup ---
cred = credentials.Certificate('service-account-key.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Agent's Initial Knowledge ---
INITIAL_KNOWLEDGE_BASE = {
    "what are your hours?": "We are open from 9 AM to 6 PM, Tuesday to Saturday.",
    "where are you located?": "We are located at 123 Salon Street.",
}

# --- Main Agent Logic ---
class CallAgent:
    def __init__(self):
        self.room = rtc.Room()
        self.deepgram_connection = None
        self.tts_audio_source = rtc.AudioSource(48000, 1) # 48k sample rate, mono
        self.customer_id = None

        # Register event handlers
        self.room.on("track_subscribed", self.handle_track_subscribed)

    async def get_answer(self, question: str) -> str:
        """This is your existing logic to find or escalate an answer."""
        normalized_question = question.lower().strip()
        answer = None

        # 1. Check initial knowledge
        if normalized_question in INITIAL_KNOWLEDGE_BASE:
            answer = INITIAL_KNOWLEDGE_BASE[normalized_question]
        
        # 2. Check learned knowledge
        else:
            kb_ref = db.collection("knowledge_base").stream()
            for item in kb_ref:
                kb_item = item.to_dict()
                if kb_item.get("question", "").lower().strip() == normalized_question:
                    answer = kb_item.get("answer")
                    break
        
        # 3. Escalate if no answer is found
        if not answer:
            print(f" Don't know '{question}'. Escalating...")
            requests.post(f"{API_URL}/help-requests", json={"customer_id": self.customer_id, "question": question})
            answer = "Let me check with my supervisor and get back to you."

        return answer

    async def play_audio_response(self, text: str):
        """Uses ElevenLabs to generate and play audio response."""
        print(f" Synthesizing and playing response: '{text}'")
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio_stream = client.generate(text=text, stream=True)
        
        # Stream audio chunks to the LiveKit audio source
        for chunk in stream(audio_stream):
            frame = rtc.AudioFrame(
                data=chunk,
                sample_rate=48000,
                num_channels=1,
                samples_per_channel=len(chunk) // 2  # 2 bytes per sample
            )
            await self.tts_audio_source.capture_frame(frame)

    def setup_deepgram(self, track: rtc.Track):
        """Sets up a real-time transcription connection with Deepgram."""
        try:
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)
            self.deepgram_connection = deepgram.listen.asynclive.v("1")

            async def on_message(self2, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if result.is_final and transcript:
                    print(f" User said: '{transcript}'")
                    # Get the answer from your logic
                    answer_text = await self.get_answer(transcript)
                    # Play the answer back as audio
                    await self.play_audio_response(answer_text)

            self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            
            options = LiveOptions(
                model="nova-2", language="en-US", encoding="linear16",
                sample_rate=48000, channels=1, smart_format=True
            )
            asyncio.create_task(self.deepgram_connection.start(options))
        except Exception as e:
            print(f" Deepgram Error: {e}")

    async def handle_track_subscribed(self, track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        """Event handler for when a new audio track is received."""
        if track.kind == rtc.TrackKind.AUDIO:
            self.customer_id = participant.identity
            print(f"🎤 Subscribed to audio track from customer: {self.customer_id}")
            self.setup_deepgram(track)
            
            # Pipe audio frames from LiveKit to Deepgram
            async for frame in rtc.AudioStream(track):
                if self.deepgram_connection:
                    await self.deepgram_connection.send(frame.data)

    async def start(self):
        """Connects to the LiveKit room and publishes the agent's audio track."""
        room_name = "salon-voice-call"
        agent_identity = "ai-salon-agent-voice"

        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(agent_identity) \
            .with_grant(VideoGrant(room_join=True, room=room_name)) \
            .to_jwt()
        
        await self.room.connect(LIVEKIT_URL, token)
        print(f" Voice agent connected to room '{self.room.name}'")

        # Publish the agent's audio track (for TTS playback)
        track = rtc.LocalAudioTrack.create_audio_track("agent-tts", self.tts_audio_source)
        await self.room.local_participant.publish_track(track)
        print(" Agent's audio track is published. Waiting for user...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = CallAgent()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(agent.start())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        loop.run_until_complete(agent.room.disconnect())