#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import sys 
import email
import io
import random
import thread
import time

# Handles a request sent to the server.
def handleRequest(tcpSocket):
	
	message = tcpSocket.recv(4096)					 # Receive HTTP request from client.

	request_line, headers = message.split('\r\n', 1) # Split HTTP message into request line and headers.
	path = message.split()[1].split('/', 1)[1]		 # Get URI path for file from request line.
	
	try: 
		text_file = open(path, "r")					 # Attempt to load file from URI in request line.
		responseBody = text_file.read()				 # Store file in buffer.
	except IOError: 
		print "Couldn't locate / read file."
		tcpSocket.sendall("HTTP/1.1 404:NOT FOUND\r\n Host: 127.0.0.1\r\n Content-Type: text/html; charset=utf-8\r\n\r\n") 		# If file could not be found -> Return 404 error message to client.
		tcpSocket.close()																										# Close the socket connection.
		text_file.close()																										# Close the file.
		return
	
	text_file.close()
	responseMessage = "HTTP/1.1 200:OK\r\n Host: 127.0.0.1\r\n Content-Type: text/html; charset=utf-8\r\n\r\n" + responseBody	# Generate response containing requestsed file.
	tcpSocket.sendall(responseMessage)																							# Send response.
	tcpSocket.close()																											# Close connection.
	return

# Creates a socket and binds it to a local address and port. Listens for connections.
def startServer(serverAddress, serverPort = 8000):
	
	try: 
		mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# Creating socket for using TCP protocol.
		mySocket.bind((serverAddress, serverPort)) 							# Bind socket to local address and port.
	
		while True:	
			mySocket.listen(5)												# Listen for connections made to the socket.
			conn, addr = mySocket.accept() 									# Accept connection -> Returns new socket to send / receive data on the established connection.
			thread.start_new_thread(handleRequest, (conn, ))				# Start new thread to handle request.
	
	except KeyboardInterrupt:												# CTRL+C -> Clean exit. No stacktrace.
			print "Server shutting down..."
			mySocket.close()												# Close socket connection.
										
	
startServer("127.0.0.1")









