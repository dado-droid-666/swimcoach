"""Generate a VAPID keypair for Web Push (run ONCE, keep private key secret).

Usage (local venv):
    .\\venv\\Scripts\\python.exe tools/gen_vapid.py

Then set (Render dashboard -> Environment + local .env, NEVER in git):
    VAPID_PUBLIC_KEY=<public line>
    VAPID_PRIVATE_KEY=<private line>

Requires: cryptography (already via python-jose). No new dependency.
"""
from base64 import urlsafe_b64encode

from cryptography.hazmat.primitives.asymmetric import ec


def b64url(data: bytes) -> str:
    return urlsafe_b64encode(data).decode().rstrip("=")


def main() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    private = key.private_numbers().private_value.to_bytes(32, "big")
    pub = key.public_key().public_numbers()
    public = b"\x04" + pub.x.to_bytes(32, "big") + pub.y.to_bytes(32, "big")
    print("VAPID_PUBLIC_KEY=" + b64url(public))
    print("VAPID_PRIVATE_KEY=" + b64url(private))
    print("\nPut both in Render env vars + local .env. Never commit them.")


if __name__ == "__main__":
    main()
