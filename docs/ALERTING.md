# FireWatch AI Alerting Modes

FireWatch AI supports demo-safe alerting by default. This keeps the project usable even when Twilio trial access is unavailable or when you do not want accidental calls during testing.

## Recommended Demo Setup

```env
ALERT_MODE=demo
AUTO_ALERTS_ENABLED=false
ALERT_CONFIRMATION_FRAMES=3
ALERT_COOLDOWN_SECONDS=300
```

In this mode the backend prepares and records email/voice alert payloads, but it does not contact real people.

## Live Gmail Alerts

```env
ALERT_MODE=email
AUTO_ALERTS_ENABLED=true
REMINDER_EMAIL_SENDER=your_email@gmail.com
REMINDER_EMAIL_RECEIVERS=stakeholder1@email.com,stakeholder2@email.com
```

You also need `credentials.json` and `token.json` for the Gmail API. Keep both files local and out of git.

## Live Gmail + Twilio Voice

```env
ALERT_MODE=email_and_call
AUTO_ALERTS_ENABLED=true
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
EMERGENCY_RECIPIENT_PHONE=+1987654321
```

Twilio trials are not guaranteed for every region, phone number, or account. Trial accounts can also restrict calls to verified numbers and may block some custom behavior. If Twilio does not allow a free trial for you, keep `ALERT_MODE=demo` or use `ALERT_MODE=email`.

## Safety Guards

- `ALERT_CONFIRMATION_FRAMES` requires multiple positive sampled frames before alert dispatch.
- `ALERT_COOLDOWN_SECONDS` prevents repeated alerts for the same zone.
- `AUTO_ALERTS_ENABLED=false` is the safest setting for development and demos.
- Do not configure this project to call real emergency services.
