import os
import requests
import zlib
import base64
import urllib.parse
import re
import json

KEYCLOAK_URL = "http://localhost:8080"
OIDC_REALM = "corp-internal"
CLIENT_ID = "demo-app"
CLIENT_SECRET = os.environ.get("KC_DEMO_APP_SECRET", "demo-app-client-secret-123")
USERNAME = "corp-user"
PASSWORD = "password"

def test_oidc_password_grant():
    print("\n==============================================")
    print("--- 1. OIDC Password Grant Flow ---")
    print("==============================================\n")
    token_endpoint = f"{KEYCLOAK_URL}/realms/{OIDC_REALM}/protocol/openid-connect/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
        "scope": "openid custom-claims"
    }
    
    print(f"Requesting token from {token_endpoint}...")
    response = requests.post(token_endpoint, data=data)
    response.raise_for_status()
    tokens = response.json()
    
    access_token = tokens["access_token"]
    id_token = tokens["id_token"]
    
    print("✅ Successfully retrieved tokens!\n")
    print("--- Decoded ID Token ---")
    
    # decode without verification just to inspect contents
    def decode_jwt(token):
        parts = token.split('.')
        padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
        return json.loads(base64.b64decode(padded).decode('utf-8'))
    
    decoded = decode_jwt(id_token)
    print(json.dumps(decoded, indent=2))
    
    if "department" in decoded and "cost_center" in decoded:
        print("\n✅ Custom claims (department, cost_center) verified in token.")
    else:
        print("\n❌ Custom claims missing!")

def test_saml_flow():
    print("\n==============================================")
    print("--- 2. SAML AuthnRequest & Login Flow ---")
    print("==============================================\n")
    
    # 1. Generate SAML AuthnRequest
    xml = f"""<?xml version="1.0"?>
    <samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" 
        xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" 
        ID="test-request-123" 
        Version="2.0" 
        IssueInstant="2024-01-01T00:00:00Z" 
        Destination="{KEYCLOAK_URL}/realms/{OIDC_REALM}/protocol/saml" 
        ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" 
        AssertionConsumerServiceURL="http://localhost:8081/saml/acs">
        <saml:Issuer>saml-sp</saml:Issuer>
    </samlp:AuthnRequest>"""
    
    deflated = zlib.compress(xml.encode())[2:-4]
    saml_request = base64.b64encode(deflated).decode()
    
    url = f"{KEYCLOAK_URL}/realms/{OIDC_REALM}/protocol/saml?SAMLRequest={urllib.parse.quote(saml_request)}"
    print("✅ Generated SAML AuthnRequest URL:")
    print(url + "\n")
    
    # 2. Simulate Browser Flow
    print("Simulating browser login...")
    session = requests.Session()
    
    # Get the login page
    resp = session.get(url)
    resp.raise_for_status()
    
    # Parse login form action
    match = re.search(r'action="([^"]+)"', resp.text)
    if not match:
        raise Exception("Login form not found in response!")
        
    action_url = match.group(1).replace("&amp;", "&")
    
    # Submit login form
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "credentialId": ""
    }
    resp2 = session.post(action_url, data=login_data)
    resp2.raise_for_status()
    
    # Keycloak returns a form that auto-submits SAMLResponse via JS
    match_saml = re.search(r'name="SAMLResponse"\s+value="([^"]+)"', resp2.text)
    if not match_saml:
        raise Exception("SAMLResponse not found. Login might have failed.")
        
    saml_response_b64 = match_saml.group(1)
    print("✅ Successfully logged in and received SAML Assertion!\n")
    
    print("--- Decoded SAML Assertion XML ---")
    saml_xml = base64.b64decode(saml_response_b64).decode('utf-8')
    
    try:
        import xml.dom.minidom
        dom = xml.dom.minidom.parseString(saml_xml)
        pretty_xml = dom.toprettyxml(indent="  ")
        print(pretty_xml[:1500] + "\n... [TRUNCATED FOR BREVITY]")
    except Exception:
        print(saml_xml[:1500] + "\n... [TRUNCATED FOR BREVITY]")

if __name__ == "__main__":
    try:
        test_oidc_password_grant()
        test_saml_flow()
    except Exception as e:
        print(f"❌ Error during test execution: {e}")
