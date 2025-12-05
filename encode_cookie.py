import base64

# Dán nội dung file gemini_cookie.txt của bạn vào giữa hai dấu nháy đơn
my_cookie = '__Secure-1PSID=g.a0003wh0-G95yXy0j7PTbJmKFozfT3s7cO3o-Lo0_Y86hLqUFMZBmY3hD0FPDftzzC43XTp68gACgYKATkSARASFQHGX2MiZfWE3WkLavGguYa7p73EIRoVAUF8yKqvahzaccRVHGMWBLYhGr4C0076; __Secure-3PSID=g.a0003wh0-G95yXy0j7PTbJmKFozfT3s7cO3o-Lo0_Y86hLqUFMZB2bQfy4eh3cuYdKjpvDz0PgACgYKAf4SARASFQHGX2MiYOrttDilOVQHCQsmOaSxqRoVAUF8yKo0Cb_SEi5Xmtv5f_hEqxD80076'

# Mã hóa
encoded_bytes = base64.b64encode(my_cookie.encode("utf-8"))
encoded_str = encoded_bytes.decode("utf-8")

print("--- COPY CHUỖI DƯỚI ĐÂY VÀO CODE CHÍNH ---")
print(encoded_str)