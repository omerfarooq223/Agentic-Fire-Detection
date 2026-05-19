import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
EMERGENCY_RECIPIENT_PHONE = os.getenv("EMERGENCY_RECIPIENT_PHONE")

def test_call():
    print("Testing Twilio Emergency Call...")
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, EMERGENCY_RECIPIENT_PHONE]):
        print("❌ Error: Missing Twilio configuration in .env")
        print(f"TWILIO_ACCOUNT_SID: {'Set' if TWILIO_ACCOUNT_SID else 'MISSING'}")
        print(f"TWILIO_AUTH_TOKEN: {'Set' if TWILIO_AUTH_TOKEN else 'MISSING'}")
        print(f"TWILIO_PHONE_NUMBER: {'Set' if TWILIO_PHONE_NUMBER else 'MISSING'}")
        print(f"EMERGENCY_RECIPIENT_PHONE: {'Set' if EMERGENCY_RECIPIENT_PHONE else 'MISSING'}")
        return

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        script = "This is an automated emergency test from FireWatch AI. A fire has been detected at the Warehouse. Please respond immediately."
        
        # Example menu navigation: wait 2 seconds then press 1
        press_digits = "wwww1" 
        
        twiml_content = f"""
        <Response>
            <Pause length="1"/>
            <Say loop="3" voice="Polly.Joey">{script}</Say>
            <Say>Goodbye.</Say>
        </Response>
        """
        
        print(f"Initiating call to {EMERGENCY_RECIPIENT_PHONE}...")
        call = client.calls.create(
            to=EMERGENCY_RECIPIENT_PHONE,
            from_=TWILIO_PHONE_NUMBER,
            twiml=twiml_content.strip(),
            send_digits=press_digits
        )
        
        print(f"✅ Call initiated successfully!")
        print(f"Call SID: {call.sid}")
        
    except Exception as e:
        print(f"❌ Failed to initiate call: {str(e)}")

if __name__ == "__main__":
    test_call()
