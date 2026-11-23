# §12 Security

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `12.01` **[P0]** Authentication vs authorization; sessions, JWT, OAuth 2.0, OIDC
- [ ] `12.02` **[P0]** OWASP Top 10: injection, XSS, CSRF, SSRF, broken access control
- [ ] `12.03` **[P1]** Encryption in transit and at rest; hashing vs encryption; password storage
- [ ] `12.04` **[P1]** Secrets management, least privilege, key rotation
- [ ] `12.05` **[P1]** Multi-tenant isolation and data access boundaries
- [ ] `12.06` **[P2]** Threat modeling a design
- [ ] `12.07` **[P2]** Supply chain security and dependency risk
- [ ] `12.08` **[P1]** LLM-specific risks: prompt injection, data exfiltration through tools, sandbox escape

## Layout

```
12-security/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
