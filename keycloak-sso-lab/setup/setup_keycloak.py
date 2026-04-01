import requests, time, os, sys

url = os.environ.get('KEYCLOAK_URL', 'http://keycloak:8080')
admin_user = os.environ.get('KEYCLOAK_ADMIN')
admin_pass = os.environ.get('KEYCLOAK_ADMIN_PASSWORD')
demo_secret = os.environ.get('KC_DEMO_APP_SECRET')

def wait_for_keycloak():
    print(f"Waiting for Keycloak at {url}...")
    for _ in range(60):
        try:
            res = requests.get(f"{url}/health/ready")
            if res.status_code == 200:
                print("Keycloak is ready.")
                return
        except Exception:
            pass
        time.sleep(2)
    print("Keycloak not ready. Exiting.")
    sys.exit(1)

def get_admin_token():
    res = requests.post(f"{url}/realms/master/protocol/openid-connect/token", data={
        "client_id": "admin-cli",
        "username": admin_user,
        "password": admin_pass,
        "grant_type": "password"
    })
    res.raise_for_status()
    return res.json()["access_token"]

def api_post(endpoint, json_data, headers):
    res = requests.post(f"{url}{endpoint}", json=json_data, headers=headers)
    if res.status_code not in (201, 204, 409):
        print(f"Failed POST {endpoint}: {res.status_code} {res.text}")
    return res

def setup():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Create realms
    api_post("/admin/realms", {"realm": "corp-internal", "enabled": True}, headers)
    api_post("/admin/realms", {"realm": "partner-external", "enabled": True}, headers)
    
    # Corp Internal: Custom claims scope
    api_post("/admin/realms/corp-internal/client-scopes", {
        "name": "custom-claims", "protocol": "openid-connect"
    }, headers)
    
    scopes = requests.get(f"{url}/admin/realms/corp-internal/client-scopes", headers=headers).json()
    scope_id = next((s['id'] for s in scopes if s['name'] == 'custom-claims'), None)
    
    if scope_id:
        api_post(f"/admin/realms/corp-internal/client-scopes/{scope_id}/protocol-mappers/models", {
            "name": "department",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "config": {
                "user.attribute": "department",
                "claim.name": "department",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true"
            }
        }, headers)

        api_post(f"/admin/realms/corp-internal/client-scopes/{scope_id}/protocol-mappers/models", {
            "name": "cost_center",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "config": {
                "user.attribute": "cost_center",
                "claim.name": "cost_center",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true"
            }
        }, headers)

    # Corp Internal: Demo OIDC App
    api_post("/admin/realms/corp-internal/clients", {
        "clientId": "demo-app",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "secret": demo_secret,
        "redirectUris": ["http://localhost:3000/*", "http://localhost:3000/callback"],
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "defaultClientScopes": ["web-origins", "acr", "roles", "profile", "email", "custom-claims"]
    }, headers)

    # Corp Internal: SAML SP
    api_post("/admin/realms/corp-internal/clients", {
        "clientId": "saml-sp",
        "enabled": True,
        "protocol": "saml",
        "redirectUris": ["http://localhost:8081/saml/acs"],
        "attributes": {
            "saml.authnstatement": "true",
            "saml.server.signature": "false",
            "saml.assertion.signature": "false",
            "saml.client.signature": "false"
        }
    }, headers)

    # Corp Internal: Roles and Users
    api_post("/admin/realms/corp-internal/roles", {"name": "employee"}, headers)

    api_post("/admin/realms/corp-internal/users", {
        "username": "corp-user",
        "enabled": True,
        "emailVerified": True,
        "attributes": {
            "department": ["engineering"],
            "cost_center": ["12345"]
        },
        "credentials": [{"type": "password", "value": "password", "temporary": False}]
    }, headers)

    users = requests.get(f"{url}/admin/realms/corp-internal/users?username=corp-user", headers=headers).json()
    if users:
        user_id = users[0]['id']
        role = requests.get(f"{url}/admin/realms/corp-internal/roles/employee", headers=headers).json()
        requests.post(f"{url}/admin/realms/corp-internal/users/{user_id}/role-mappings/realm", json=[role], headers=headers)

    # Corp Internal: Broker Client for Federation
    api_post("/admin/realms/corp-internal/clients", {
        "clientId": "partner-broker",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "secret": "partner-broker-secret",
        "redirectUris": ["http://localhost:8080/realms/partner-external/broker/corp-oidc/endpoint"],
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "publicClient": False,
        "protocol": "openid-connect"
    }, headers)

    # Partner External: Federation IDP
    api_post("/admin/realms/partner-external/identity-provider/instances", {
        "alias": "corp-oidc",
        "providerId": "keycloak-oidc",
        "enabled": True,
        "config": {
            "authorizationUrl": "http://localhost:8080/realms/corp-internal/protocol/openid-connect/auth",
            "tokenUrl": f"{url}/realms/corp-internal/protocol/openid-connect/token",
            "logoutUrl": "http://localhost:8080/realms/corp-internal/protocol/openid-connect/logout",
            "userInfoUrl": f"{url}/realms/corp-internal/protocol/openid-connect/userinfo",
            "clientId": "partner-broker",
            "clientSecret": "partner-broker-secret",
            "defaultScope": "openid profile email custom-claims",
            "syncMode": "IMPORT",
            "useJwksUrl": "true",
            "jwksUrl": f"{url}/realms/corp-internal/protocol/openid-connect/certs"
        }
    }, headers)

    # Partner External: User
    api_post("/admin/realms/partner-external/users", {
        "username": "partner-user",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "password", "temporary": False}]
    }, headers)

    print("Setup completed successfully.")

if __name__ == '__main__':
    wait_for_keycloak()
    setup()
