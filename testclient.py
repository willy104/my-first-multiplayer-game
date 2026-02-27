import socket

friend_ip = "25.4.29.65"
port = 5555  # 遊戲伺服器用的 port

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)  # 最多等 5 秒

try:
    sock.connect((friend_ip, port))
    print(f"成功連上 {friend_ip}:{port} 🎉")
except socket.timeout:
    print(f"連線逾時，無法連上 {friend_ip}:{port} ⏰")
except ConnectionRefusedError:
    print(f"連線被拒絕，伺服器可能沒開或防火牆阻擋 ❌")
except Exception as e:
    print(f"其他錯誤：{e}")
finally:
    sock.close()