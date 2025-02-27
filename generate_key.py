import secrets

# Printing new secure secret key
secure_key = secrets.token_hex(32)
print("Copy this key and put to config file.")
print(secure_key)