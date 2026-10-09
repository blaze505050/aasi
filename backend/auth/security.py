"""
AASI Phase 27: Cryptographic Security & Session Management.
PBKDF2-HMAC-SHA256 password hashing and signed tamper-proof session tokens.
"""

import os
import hmac
import hashlib
import base64
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path

from backend.auth.models import User, UserRole, SessionToken, ApiKey
from backend.deployment.config import get_deployment_config


class HashResult(str):
    salt: str = ""

    def __new__(cls, val: str, salt: str):
        s = super().__new__(cls, val)
        s.salt = salt
        return s

    def __iter__(self):
        return iter([str(self), self.salt])


class SecurityManager:
    """Manages password hashing, token verification, and user credential lifecycle."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.config = get_deployment_config()
        self.secret_key = self.config.secret_key.encode("utf-8")
        self.data_dir = data_dir or Path("data/auth")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.api_keys_file = self.data_dir / "api_keys.json"
        self.revocations_file = self.data_dir / "revoked_tokens.json"
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, ApiKey] = {}
        self._revoked_tokens: set[str] = set()
        self._load_users()
        self._load_api_keys()
        self._load_revocations()
        self._ensure_default_user()

    def _load_users(self):
        if self.users_file.exists():
            try:
                data = json.loads(self.users_file.read_text(encoding="utf-8"))
                for uid, udata in data.items():
                    self._users[uid] = User.model_validate(udata)
            except Exception:
                self._users = {}

    def _save_users(self):
        data = {uid: u.model_dump() for uid, u in self._users.items()}
        self.users_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_api_keys(self):
        if self.api_keys_file.exists():
            try:
                data = json.loads(self.api_keys_file.read_text(encoding="utf-8"))
                for khash, kdata in data.items():
                    self._api_keys[khash] = ApiKey.model_validate(kdata)
            except Exception:
                self._api_keys = {}

    def _save_api_keys(self):
        data = {khash: k.model_dump() for khash, k in self._api_keys.items()}
        self.api_keys_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_revocations(self):
        if self.revocations_file.exists():
            try:
                tokens = json.loads(self.revocations_file.read_text(encoding="utf-8"))
                self._revoked_tokens = set(tokens)
            except Exception:
                self._revoked_tokens = set()

    def _save_revocations(self):
        self.revocations_file.write_text(json.dumps(list(self._revoked_tokens), indent=2), encoding="utf-8")

    def _ensure_default_user(self):
        """Create a default researcher user for instant local/dev usage if empty.
        SECURITY: Only creates the default user when AASI_DEV_MODE is explicitly enabled.
        In production, users must be created through the registration API.
        """
        import os
        is_dev = os.getenv("AASI_DEV_MODE", "false").lower() in ("true", "1", "yes")
        if not self._users and is_dev:
            self.create_user(
                username="researcher",
                email="researcher@aasi.aero",
                password="aerospace-secure-password-2026",
                role=UserRole.RESEARCHER
            )
            logger.info("DEV MODE: Created default researcher user. Do NOT use in production.")

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> HashResult:
        """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
        if not salt:
            salt = secrets.token_hex(16)
        salt_bytes = salt.encode("utf-8")
        pwd_bytes = password.encode("utf-8")
        key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000)
        formatted = f"pbkdf2_sha256$100000${salt}${key.hex()}"
        return HashResult(formatted, salt)

    def verify_password(self, password: str, password_hash: str, salt: Optional[str] = None) -> bool:
        """Verify password against stored hash using constant-time comparison."""
        if not password_hash:
            return False
        if salt is None and "$" in password_hash:
            parts = password_hash.split("$")
            if len(parts) >= 4:
                salt = parts[2]
                target_hash = parts[3]
                computed = self.hash_password(password, salt)
                computed_hex = str(computed).split("$")[3]
                return hmac.compare_digest(computed_hex, target_hash)
        computed = self.hash_password(password, salt or "")
        computed_hex = str(computed).split("$")[3] if "$" in str(computed) else str(computed)
        target_hex = password_hash.split("$")[3] if "$" in password_hash else password_hash
        return hmac.compare_digest(computed_hex, target_hex)

    def issue_session_token(self, user_id: str, username: str, role: UserRole) -> SessionToken:
        mock_user = User(
            user_id=user_id,
            username=username,
            email=f"{username}@aasi.internal",
            password_hash="",
            salt="",
            role=role,
        )
        return self.create_session_token(mock_user)


    def create_user(
        self, username: str, email: str, password: str, role: UserRole = UserRole.RESEARCHER
    ) -> User:
        """Register a new user account."""
        # Check existing
        for u in self._users.values():
            if u.username.lower() == username.lower():
                raise ValueError(f"Username '{username}' already exists.")
            if u.email.lower() == email.lower():
                raise ValueError(f"Email '{email}' already exists.")

        user_id = f"USR-{secrets.token_hex(6).upper()}"
        pwd_hash, salt = self.hash_password(password)
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=pwd_hash,
            salt=salt,
            role=role,
            is_active=True,
        )
        self._users[user_id] = user
        self._save_users()
        return user

    def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        target_user = None
        for u in self._users.values():
            if u.username.lower() == username_or_email.lower() or u.email.lower() == username_or_email.lower():
                target_user = u
                break
        if not target_user or not target_user.is_active:
            return None
        if self.verify_password(password, target_user.password_hash, target_user.salt):
            target_user.last_login = datetime.now(timezone.utc).isoformat()
            self._save_users()
            return target_user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        for u in self._users.values():
            if u.username.lower() == username.lower():
                return u
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        for u in self._users.values():
            if u.email.lower() == email.lower():
                return u
        return None

    def create_session_token(self, user: User) -> SessionToken:
        """Generate a signed, tamper-proof session token."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.config.token_expiry_hours)
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "exp": expires_at.timestamp(),
            "iat": now.timestamp(),
            "nonce": secrets.token_hex(8),
        }
        raw_json = json.dumps(payload, separators=(",", ":"))
        encoded_payload = base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("utf-8").rstrip("=")
        signature = hmac.new(self.secret_key, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        full_token = f"aasi_tok_{encoded_payload}.{signature}"

        return SessionToken(
            token=full_token,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            expires_at=expires_at.isoformat(),
            created_at=now.isoformat(),
        )

    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify session token signature, expiration, and revocation status."""
        try:
            if token.startswith("aasi_tok_"):
                raw_sig_part = token[len("aasi_tok_"):]
            else:
                raw_sig_part = token

            if self.is_token_revoked(token) or self.is_token_revoked(raw_sig_part):
                return None

            if "." not in raw_sig_part:
                return None
            encoded_payload, signature = raw_sig_part.split(".", 1)
            expected_sig = hmac.new(self.secret_key, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return None

            padding = "=" * (-len(encoded_payload) % 4)
            raw_json = base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
            payload = json.loads(raw_json)

            now_ts = datetime.now(timezone.utc).timestamp()
            if payload.get("exp", 0) < now_ts:
                return None  # Expired
            return payload
        except Exception:
            return None

    def revoke_token(self, token: str) -> bool:
        """Add session token to revocation list."""
        if token.startswith("aasi_tok_"):
            token = token[len("aasi_tok_"):]
        self._revoked_tokens.add(token)
        self._save_revocations()
        return True

    def is_token_revoked(self, token: str) -> bool:
        """Check if a session token has been revoked."""
        if token.startswith("aasi_tok_"):
            token = token[len("aasi_tok_"):]
        return token in self._revoked_tokens

    def create_api_key(
        self,
        user_id: str,
        name: str,
        org_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> Tuple[str, ApiKey]:
        """Generate a cryptographically secure API key.
        Returns the plaintext raw key (displayed only once) and the ApiKey metadata model.
        """
        raw_secret = secrets.token_hex(24)
        raw_key = f"aasi_sk_{raw_secret}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_id = f"KEY-{secrets.token_hex(6).upper()}"
        prefix = f"{raw_key[:12]}..."

        api_key = ApiKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            org_id=org_id,
            prefix=prefix,
            scopes=scopes or ["read", "write", "investigate"],
            is_active=True,
        )
        self._api_keys[key_hash] = api_key
        self._save_api_keys()
        return raw_key, api_key

    def verify_api_key(self, raw_key: str) -> Optional[Tuple[User, ApiKey]]:
        """Verify an API key by hash and return associated User and ApiKey."""
        if not raw_key or not raw_key.startswith("aasi_sk_"):
            return None
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        api_key = self._api_keys.get(key_hash)
        if not api_key or not api_key.is_active:
            return None
        user = self.get_user_by_id(api_key.user_id)
        if not user or not user.is_active:
            return None
        api_key.last_used_at = datetime.now(timezone.utc).isoformat()
        self._save_api_keys()
        return user, api_key

    def list_api_keys(self, user_id: str) -> List[ApiKey]:
        """List active API keys for a user."""
        return [k for k in self._api_keys.values() if k.user_id == user_id and k.is_active]

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Deactivate an API key."""
        for k in self._api_keys.values():
            if k.key_id == key_id and k.user_id == user_id:
                k.is_active = False
                self._save_api_keys()
                return True
        return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """Enforce enterprise password complexity requirements (X8)."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit."
        return True, "Password meets complexity requirements."


# Global singleton security manager
security_manager = SecurityManager()

