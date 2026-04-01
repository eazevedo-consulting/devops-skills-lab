# Keycloak SSO Lab

This project provisions a fully functional Keycloak environment simulating a Corporate and Partner architecture using Docker Compose.

## Architecture
- **Keycloak 24+** backed by **PostgreSQL 15**.
- **Realms:**
  - `corp-internal`: Central identity provider.
  - `partner-external`: Uses OIDC identity brokering to federate logins to `corp-internal`.
- **Clients:**
  - `demo-app`: OIDC Confidential Client using authorization code flow.
  - `saml-sp`: SAML Client simulating an enterprise service provider.
  - `partner-broker`: Client mapped to identity federation logic.
- **Node.js Demo App:** Express web application demonstrating OIDC integration with custom claim mapping.

## Setup Instructions

1. Start the lab environment (all secrets are loaded automatically from `.env`):
   ```bash
   docker-compose up -d --build
   ```

2. Wait a few moments. A temporary `setup` container will use the Keycloak Admin REST API to automatically provision the realms, clients, scopes, mappers, roles, IDP federation, and users. You can check its progress with:
   ```bash
   docker-compose logs -f setup
   ```

## Demo & Testing

### 1. Web UI (Node.js Express App)
Navigate to http://localhost:3000
- Click "Login with Corp ID"
- Use credentials: `corp-user` / `password`
- You will see the injected custom claims (`department: engineering`, `cost_center: 12345`) retrieved via OIDC.

### 2. Identity Brokering (Federation)
To test the Partner external realm federating to Corp:
- Open http://localhost:8080/realms/partner-external/account
- Click "Sign In"
- Click "corp-oidc" on the right side.
- Login with `corp-user` / `password`.
- You are seamlessly authenticated into the partner realm using the corporate identity.

### 3. Programmatic API Testing (Python)
We have included a Python script to demonstrate backend OIDC and SAML integration flows:

```bash
# Install requests library (or use a virtual environment)
pip install -r requirements.txt

# Run the test flows
python test_flows.py
```

### 4. Direct cURL commands
You can reproduce the OIDC Password Grant flow directly via your terminal:

**Get Token & Parse JWT (Requires `jq`):**
```bash
curl -s -X POST http://localhost:8080/realms/corp-internal/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=demo-app" \
  -d "client_secret=demo-app-client-secret-123" \
  -d "grant_type=password" \
  -d "username=corp-user" \
  -d "password=password" \
  -d "scope=openid custom-claims" \
  | jq -R 'fromjson? | .id_token | split(".") | .[1] | @base64d | fromjson?'
```

## Default Credentials
- **Admin Console:** `admin` / `admin` (http://localhost:8080)
- **Corp User:** `corp-user` / `password`
- **Partner User:** `partner-user` / `password`
