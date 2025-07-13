import os
import time
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    print("[ERROR] SECRET_KEY is not set in environment")
    raise RuntimeError("SECRET_KEY is not set in environment")
else:
    print("[DEBUG] SECRET_KEY loaded successfully from environment")

def generate_token(user_id: str, company_id: str, expires_in: int = 3600) -> str:
    """
    Generate a JWT token for user authentication

    Args:
        user_id: User identifier
        company_id: Company identifier the user belongs to
        expires_in: Seconds until token expires (default: 1 hour)

    Returns:
        JWT token string
    """
    print(f"[DEBUG] Generating token for user: {user_id}, company: {company_id}")

    # Create payload
    payload = {
        "user_id": user_id,
        "company_id": company_id,
        "exp": time.time() + expires_in
    }

    # Generate token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    print(f"[DEBUG] Token generated successfully. Expires in {expires_in} seconds")

    return token

def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    print(f"[DEBUG] Verifying token...")

    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Check if token contains required fields
        if "user_id" not in payload or "company_id" not in payload:
            print(f"[ACCESS DENIED] Token missing required fields")
            raise HTTPException(status_code=401, detail="Invalid token format")

        print(f"[ACCESS GRANTED] Token decoded successfully")
        print(f"[ACCESS CONTROL] User: {payload['user_id']} is authorized for company: {payload['company_id']}")

        return payload

    except jwt.ExpiredSignatureError:
        print(f"[ACCESS DENIED] Token has expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        print(f"[ACCESS DENIED] Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"[ACCESS DENIED] Error verifying token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")