from livekit_api import AccessToken, VideoGrant

LIVEKIT_API_KEY = "APIGHhPPPNMXMSC"
LIVEKIT_API_SECRET = "PS8f1KIH5bf5vM75fQ52hVXWyYidV7LUf7o73HTgxftF"

room_name = "salon-voice-call"
user_identity = "customer-sravan"

token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
    .with_identity(user_identity) \
    .with_grant(VideoGrant(room_join=True, room=room_name)) \
    .to_jwt()

print("✅ User Token Generated:")
print(token)