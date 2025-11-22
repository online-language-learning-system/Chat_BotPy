# app/auth/jwt_auth.py
from functools import wraps
from flask import request, jsonify, g
from jwt import PyJWKClient, InvalidTokenError, ExpiredSignatureError
import jwt as pyjwt

from app.config import settings

# lazy init jwks client
_jwks_client = None
def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        if not settings.JWKS_URL:
            raise RuntimeError("JWKS_URL is not configured")
        _jwks_client = PyJWKClient(settings.JWKS_URL)
    return _jwks_client

def get_token_from_header():
    auth = request.headers.get("Authorization", "")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

def verify_jwt(token: str):
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    key = signing_key.key
    options = {
        "verify_signature": True,
        "verify_aud": bool(settings.KEYCLOAK_CLIENT_ID),
        "verify_exp": True,
        "verify_iss": bool(settings.KEYCLOAK_ISSUER_URI)
    }
    decoded = pyjwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=settings.KEYCLOAK_CLIENT_ID if settings.KEYCLOAK_CLIENT_ID else None,
        issuer=settings.KEYCLOAK_ISSUER_URI if settings.KEYCLOAK_ISSUER_URI else None,
        options=options
    )
    return decoded

def extract_roles_from_claims(claims: dict):
    roles = set()
    realm = claims.get("realm_access", {})
    if isinstance(realm, dict):
        r = realm.get("roles", [])
        if isinstance(r, (list, tuple)):
            for role in r:
                roles.add("ROLE_" + str(role))
    # Optionally extract client roles from resource_access if you use client roles
    resource_access = claims.get("resource_access", {})
    if isinstance(resource_access, dict):
        for client, info in resource_access.items():
            client_roles = info.get("roles", [])
            for cr in client_roles:
                roles.add("ROLE_" + str(cr))
    return roles

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # permitlist check
        token = get_token_from_header()
        if not token:
            return jsonify({"msg": "Missing Authorization Bearer token"}), 401
        try:
            claims = verify_jwt(token)
        except ExpiredSignatureError:
            return jsonify({"msg": "Token expired"}), 401
        except InvalidTokenError as e:
            return jsonify({"msg": "Invalid token", "error": str(e)}), 401
        except Exception as e:
            return jsonify({"msg": "Token verification error", "error": str(e)}), 401

        g.jwt_claims = claims
        g.roles = extract_roles_from_claims(claims)
        # helper username
        g.username = claims.get("preferred_username") or claims.get("sub")
        return func(*args, **kwargs)
    return wrapper

def require_roles(*required_roles):
    required = set()
    for r in required_roles:
        if r.startswith("ROLE_"):
            required.add(r)
        else:
            required.add("ROLE_" + r)
    def decorator(func):
        @wraps(func)
        @require_auth
        def wrapped(*args, **kwargs):
            current = getattr(g, "roles", set())
            if current & required:
                return func(*args, **kwargs)
            return jsonify({"msg": "Forbidden: missing role"}), 403
        return wrapped
    return decorator
