const express = require('express');
const session = require('express-session');
const { Issuer, generators } = require('openid-client');

const app = express();
app.use(session({
    secret: process.env.SECRET || 'secret',
    resave: false,
    saveUninitialized: true
}));

let client;

async function init() {
    const internalUrl = process.env.INTERNAL_ISSUER_URL || 'http://keycloak:8080/realms/corp-internal';
    const externalUrl = process.env.EXTERNAL_ISSUER_URL || 'http://localhost:8080/realms/corp-internal';
    
    // Retry logic in case Keycloak is still starting up
    let keycloakIssuer;
    for(let i=0; i<30; i++) {
        try {
            keycloakIssuer = await Issuer.discover(internalUrl);
            break;
        } catch(e) {
            console.log(`Waiting for Keycloak Discovery at ${internalUrl}...`);
            await new Promise(r => setTimeout(r, 2000));
        }
    }
    
    if(!keycloakIssuer) {
        console.error("Failed to discover Keycloak OIDC configuration.");
        process.exit(1);
    }
    
    // Rewrite endpoints to point to localhost so the browser can reach them
    keycloakIssuer.metadata.authorization_endpoint = keycloakIssuer.metadata.authorization_endpoint.replace(internalUrl, externalUrl);
    keycloakIssuer.metadata.end_session_endpoint = keycloakIssuer.metadata.end_session_endpoint.replace(internalUrl, externalUrl);

    client = new keycloakIssuer.Client({
        client_id: process.env.CLIENT_ID || 'demo-app',
        client_secret: process.env.CLIENT_SECRET,
        redirect_uris: [`${process.env.BASE_URL}/callback`],
        response_types: ['code']
    });
}

init().catch(console.error);

app.get('/', (req, res) => {
    if (req.session.tokenSet) {
        res.send(`
            <h1>Welcome to Corp Internal App</h1>
            <p><strong>Department:</strong> ${req.session.claims.department || 'N/A'}</p>
            <p><strong>Cost Center:</strong> ${req.session.claims.cost_center || 'N/A'}</p>
            <p><a href="/logout">Logout</a></p>
            <h3>All ID Token Claims:</h3>
            <pre>${JSON.stringify(req.session.claims, null, 2)}</pre>
        `);
    } else {
        res.send('<h1>Welcome to Demo App</h1><p><a href="/login">Login with Corp ID</a></p>');
    }
});

app.get('/login', (req, res) => {
    const nonce = generators.nonce();
    const state = generators.state();
    req.session.nonce = nonce;
    req.session.state = state;
    const url = client.authorizationUrl({
        scope: 'openid profile email custom-claims',
        state,
        nonce,
    });
    res.redirect(url);
});

app.get('/callback', async (req, res) => {
    const params = client.callbackParams(req);
    try {
        const tokenSet = await client.callback(`${process.env.BASE_URL}/callback`, params, {
            nonce: req.session.nonce,
            state: req.session.state
        });
        req.session.tokenSet = tokenSet;
        req.session.claims = tokenSet.claims();
        res.redirect('/');
    } catch (err) {
        res.send(`Error: ${err.message}`);
    }
});

app.get('/logout', (req, res) => {
    const id_token = req.session.tokenSet ? req.session.tokenSet.id_token : null;
    req.session.destroy();
    if (id_token) {
        const logoutUrl = client.endSessionUrl({ id_token_hint: id_token, post_logout_redirect_uri: process.env.BASE_URL });
        res.redirect(logoutUrl);
    } else {
        res.redirect('/');
    }
});

app.listen(3000, () => console.log('App listening on port 3000'));
