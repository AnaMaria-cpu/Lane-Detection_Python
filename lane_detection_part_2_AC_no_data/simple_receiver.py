import socket

ip = '127.0.0.1'
port = 5001

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

conn.connect((ip, port))
print('Connected.')

msg = conn.recv(128)
received_message = msg.decode('utf-8')
print(f'Received message [{received_message}]')

response_text = f'Hello! Your message was {received_message}.'
response = response_text.encode('utf-8')
conn.send(response)

print(f'Sent response [{response_text}]')
conn.close()
