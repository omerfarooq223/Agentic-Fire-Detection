# Security Policy

## Supported Use

This repository is intended for research, prototyping, and controlled demonstrations. It is not certified life-safety software.

## Secrets

Never commit:

- `.env`
- `credentials.json`
- `token.json`
- API keys
- Gmail OAuth tokens
- local databases
- generated detection images
- model weights

If a secret is exposed, revoke and rotate it immediately.

## Alerting Safety

The safe default is:

```env
ALERT_MODE=demo
AUTO_ALERTS_ENABLED=false
```

Do not configure this project to contact real emergency services. Test only with verified, consenting recipients.

## Reporting Issues

Please open a private security advisory on GitHub if available. If not, contact the repository owner privately before filing a public issue.
