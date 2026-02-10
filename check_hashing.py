try:
    from app.services.auth import get_password_hash
    print(f"Hash check: {get_password_hash('test')}")
    print("HASH_SUCCESS")
except Exception as e:
    print(f"HASH_ERROR: {e}")
