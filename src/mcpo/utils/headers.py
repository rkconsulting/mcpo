import json
import logging
import re
from typing import Dict, List, Optional, Any, Union
from fastapi import Request
import jwt
from jwt.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


def validate_header_forwarding_config(server_name: str, config: Dict[str, Any]) -> None:
    """Validate header forwarding configuration for a server."""
    if not isinstance(config, dict):
        raise ValueError(f"Server '{server_name}' header_forwarding must be a dictionary")
    
    enabled = config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError(f"Server '{server_name}' header_forwarding.enabled must be a boolean")
    
    if not enabled:
        return  # No further validation needed if disabled
    
    whitelist = config.get("whitelist", [])
    blacklist = config.get("blacklist", [])
    
    if whitelist and not isinstance(whitelist, list):
        raise ValueError(f"Server '{server_name}' header_forwarding.whitelist must be a list")
    
    if blacklist and not isinstance(blacklist, list):
        raise ValueError(f"Server '{server_name}' header_forwarding.blacklist must be a list")
    
    # Validate JWT configuration if present
    jwt_config = config.get("jwt_validation", {})
    if jwt_config and not isinstance(jwt_config, dict):
        raise ValueError(f"Server '{server_name}' header_forwarding.jwt_validation must be a dictionary")
    
    if jwt_config.get("enabled", False):
        issuer = jwt_config.get("issuer")
        if issuer and not isinstance(issuer, str):
            raise ValueError(f"Server '{server_name}' jwt_validation.issuer must be a string")


def match_header_pattern(header_name: str, patterns: List[str]) -> bool:
    """Check if header name matches any of the given patterns."""
    for pattern in patterns:
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            # Wildcard pattern like "X-User-*"
            prefix = pattern[:-1]
            if header_name.startswith(prefix):
                return True
        elif pattern == header_name:
            return True
    return False


def filter_headers(
    request_headers: Dict[str, str], 
    whitelist: List[str],
    blacklist: List[str],
    debug_headers: bool = False
) -> Dict[str, str]:
    """Filter request headers based on whitelist and blacklist."""
    filtered_headers = {}
    
    for header_name, header_value in request_headers.items():
        # Skip if in blacklist
        if blacklist and match_header_pattern(header_name, blacklist):
            if debug_headers:
                logger.debug(f"Header '{header_name}' blocked by blacklist")
            continue
        
        # Include if in whitelist (or no whitelist specified)
        if not whitelist or match_header_pattern(header_name, whitelist):
            filtered_headers[header_name] = header_value
            if debug_headers:
                logger.debug(f"Header '{header_name}' forwarded")
        elif debug_headers:
            logger.debug(f"Header '{header_name}' not in whitelist")
    
    return filtered_headers


def validate_jwt_token(
    token: str, 
    jwt_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Validate JWT token according to configuration."""
    if not jwt_config.get("enabled", False):
        return None
    
    try:
        # For now, decode without verification to extract claims
        # In production, you'd want to verify against the issuer's public key
        decoded = jwt.decode(
            token, 
            options={"verify_signature": False, "verify_exp": jwt_config.get("check_expiration", True)}
        )
        
        # Validate issuer if specified
        issuer = jwt_config.get("issuer")
        if issuer and decoded.get("iss") != issuer:
            logger.warning(f"JWT issuer mismatch: expected {issuer}, got {decoded.get('iss')}")
            return None
        
        # Validate audience if specified
        audience = jwt_config.get("audience")
        if audience:
            token_aud = decoded.get("aud")
            if isinstance(token_aud, list):
                if audience not in token_aud:
                    logger.warning(f"JWT audience mismatch: {audience} not in {token_aud}")
                    return None
            elif token_aud != audience:
                logger.warning(f"JWT audience mismatch: expected {audience}, got {token_aud}")
                return None
        
        # Validate required claims
        required_claims = jwt_config.get("required_claims", {})
        for claim_path, expected_value in required_claims.items():
            actual_value = get_nested_claim(decoded, claim_path)
            if not validate_claim_value(actual_value, expected_value):
                logger.warning(f"JWT claim validation failed: {claim_path}")
                return None
        
        return decoded
    
    except InvalidTokenError as e:
        logger.warning(f"JWT validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT validation: {e}")
        return None


def get_nested_claim(claims: Dict[str, Any], path: str) -> Any:
    """Get nested claim value using dot notation (e.g., 'realm_access.roles')."""
    keys = path.split('.')
    value = claims
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def validate_claim_value(actual: Any, expected: Union[str, List[str], Any]) -> bool:
    """Validate that actual claim value matches expected value(s)."""
    if isinstance(expected, list):
        # Check if actual value contains any of the expected values
        if isinstance(actual, list):
            return any(item in actual for item in expected)
        else:
            return actual in expected
    else:
        return actual == expected


def extract_user_headers_from_jwt(claims: Dict[str, Any]) -> Dict[str, str]:
    """Extract user context headers from JWT claims."""
    user_headers = {}
    
    # Standard claims
    if "sub" in claims:
        user_headers["X-User-ID"] = claims["sub"]
    
    if "email" in claims:
        user_headers["X-User-Email"] = claims["email"]
    
    if "preferred_username" in claims:
        user_headers["X-User-Username"] = claims["preferred_username"]
    
    # Roles from realm_access
    realm_roles = get_nested_claim(claims, "realm_access.roles")
    if realm_roles and isinstance(realm_roles, list):
        user_headers["X-User-Roles"] = ",".join(realm_roles)
    
    # Session information
    if "session_state" in claims:
        user_headers["X-Session-ID"] = claims["session_state"]
    
    return user_headers


def process_headers_for_server(
    request: Request,
    header_config: Dict[str, Any]
) -> Dict[str, str]:
    """Process and filter headers for a specific MCP server."""
    if not header_config.get("enabled", False):
        return {}
    
    # Convert FastAPI headers to dict
    request_headers = dict(request.headers)
    
    # Get configuration values
    whitelist = header_config.get("whitelist", [])
    blacklist = header_config.get("blacklist", [])
    debug_headers = header_config.get("debug_headers", False)
    jwt_config = header_config.get("jwt_validation", {})
    
    # Filter headers based on whitelist/blacklist
    filtered_headers = filter_headers(request_headers, whitelist, blacklist, debug_headers)
    
    # Validate JWT if present and configured
    auth_header = filtered_headers.get("authorization") or filtered_headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer ") and jwt_config:
        token = auth_header[7:]  # Remove "Bearer " prefix
        jwt_claims = validate_jwt_token(token, jwt_config)
        
        if jwt_claims is None and jwt_config.get("required", False):
            # JWT validation failed and is required
            logger.warning("JWT validation failed for required token")
            # Remove authorization header to prevent forwarding invalid token
            filtered_headers.pop("authorization", None)
            filtered_headers.pop("Authorization", None)
        elif jwt_claims:
            # Add user context headers based on JWT claims
            user_headers = extract_user_headers_from_jwt(jwt_claims)
            filtered_headers.update(user_headers)
    
    if debug_headers:
        logger.debug(f"Final forwarded headers: {list(filtered_headers.keys())}")
    
    return filtered_headers
