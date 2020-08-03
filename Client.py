
import socket

# Sends a HTTP GET request to a specified IP address / port.
def sendRequest(request, serverAddress, serverPort = 8000):
	
	mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)					# Create TCP socket.
	mySocket.connect((serverAddress, serverPort))									# Bind socket to remote address
	mySocket.sendall(request)														# Send HTTP request.
	
	while True: 
		serverResponse = mySocket.recv(4096)										# Wait for response.
		saveFile("file", serverResponse)											# Write server response to local storage.
		if not serverResponse:
			break
			
	mySocket.close()																# Close connection.

# Write server response to local storage. 
def saveFile(fileName, fileContents): 
	print("Storing file locally.")
	try: 														 					
		returned_file = open(fileName, "a+")					 					# Open / create file for writing. 
		returned_file.write(fileContents)						 					# Write response to file.	
		returned_file.close()									 					# Close file handle.
	except IOError:
		returned_file.close()	
	 
sendRequest("GET /index.html HTTP:1.1\r\nConnection: Keep-Alive\r\n\r\n", "127.0.0.1") 


