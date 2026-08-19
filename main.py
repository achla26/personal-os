from datetime import datetime, timedelta, timezone
import secrets
import uuid


token_id = uuid.uuid4() 

secret = secrets.token_urlsafe(32)
 

# cookie_value = f"{token_id}.{secret}"

# token_id_str, secret = cookie_value.split(".", 1)

# print("="*20)
# print(token_id_str , secret)
# print("="*20)

# print(cookie_value.split(".", 0))
# print("="*20)

# print(cookie_value.split(".", 1))

# print("="*20)
# print(cookie_value.split(".", 2))

# print("="*20)
# print(cookie_value.split(".", 3))



cookie_value = "1.2.3.4"

token_id_str, secret = cookie_value.split(".", 1)

print("="*20)
print(token_id_str , secret)
print("="*20)

print(cookie_value.split(".", 0))
print("="*20)

print(cookie_value.split(".", 1))

print("="*20)
print(cookie_value.split(".", 2))

print("="*20)
print(cookie_value.split(".", 3))