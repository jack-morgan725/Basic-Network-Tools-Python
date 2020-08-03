
import socket
import signal
import sys

cached_files = []

STATUS_OK = 200

# Returns file from proxy to client. If file isn't cached -> get from server, cache it, and return it to client.
def manageRequest(clientSocket): 
	
	cachedFile = None 
	
	while True: 
		
		clientRequest = clientSocket.recv(4096)									# Receive client request. 
		
		if not clientRequest:													# If client has finished sending HTTP requests -> return.
			proxySocket.close()													# Close the connection between the proxy and server.
			return
			
		proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)		# Create TCP socket to transfer request from proxy to server
		request_line, headers_alone = clientRequest.split('\r\n', 1)			# Parse request into request line and headers.
		path = clientRequest.split()[1].split('/', 1)[1]						# Get URI path for file from request line.
		file_name = path.split()[-1].split('/')[1]								# Get file name.
		
		for fileName in cached_files:											# Check if proxy holds a copy of the requested file.
			if file_name == fileName:
				cachedFile = file_name
	
		if cachedFile == None:														# If a copy isn't found: 
											
			hostName = request_line.split()[1].split('//', 1)[1].split('/')[0]		# Get hostname from request line.
			proxySocket.connect((socket.gethostbyname(hostName), 80)) 				# Resolve hostname to IP address and create a connection between the socket and server.
			proxySocket.sendall(clientRequest)										# Forward the clients request to the server.
			
			while True:														
				serverResponse = proxySocket.recv(4096)								# Get servers response to request. 
				
				try:
					status_code = serverResponse.split()[1]			# Parse request into status line and headers.
				except: 
					pass
			
				clientSocket.sendall(serverResponse)								# Send response back to client.
				
				if status_code == str(STATUS_OK):
					cacheFile(file_name, serverResponse)							# Write file contents to disk if server response is successful.
					cached_files.append(file_name)

				if not serverResponse:												# If server has finished responsing -> save record of cached file.
					break
		else:
			clientSocket.sendall(getCachedFile(file_name))					 # Return file to client. # Replace with file_name.
			break 
					
	proxySocket.close()														# Close the connection between the proxy and server.
	return

# Saves a file locally.
def cacheFile(file_name, fileContents): 
	print("Storing file locally: " + file_name)
	try: 														 # Should probably check for a 200 OK here with if statement.
		returned_file = open(file_name, "a+")					 # Open / create file for writing. 
		returned_file.write(fileContents)						 # Write response to file.	
		returned_file.close()									 # Close file handle.
	except IOError:
		pass	

# Retrieves a locally saved file.
def getCachedFile(file_name):
	print("Retrieving local file: " + file_name)
	try: 
		fileHandle = open(file_name, "r")					 # Attempt to load file from URI in request line.
		return fileHandle.read()					 		 # Store file in buffer.
	except IOError: 	
		pass 

# Starts proxy server.
def startProxy(serverAddress, serverPort = 8000):

	mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 
	mySocket.bind((serverAddress, serverPort))						# Bind socket to server address and server 

	while True:
		mySocket.listen(5)											# Listen for connections to socket.
		conn, addr = mySocket.accept()								# Accept connection -> Returns new socket to send / receive data on the established connection. Connection established between client and proxy.
		manageRequest(conn)											# Forward client request to server or retrieve file locally if possible.

	mySocket.close()												# Close socket connection between the client and server.

# Exit application on keyboard interrupt (CTRL+C) without stacktrace.
def signal_handler(signal, frame):									
		print("Proxy Server Shutting Down...")
		sys.exit(0)
 
signal.signal(signal.SIGINT, signal_handler)
	
startProxy("127.0.0.1")
