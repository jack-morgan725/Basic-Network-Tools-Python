
import socket
import sys
import struct
import time
import signal

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages.
ICMP_ECHO_REPLY   = 0  # ICMP type code for echo reply messages.
ICMP_TTL_EXCEEDED = 11 # ICMP type code for TTL exceeded messages.

# Generates and returns checksum value for a packet.
def checksum(string): 
	
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	
	if sys.platform == 'darwin':
		answer = socket.htons(answer) & 0xffff		
	else:
		answer = socket.htons(answer)

	return answer 

# Waits until ping response received or timeout reached -> Returns time of receipt.
def receiveOnePing(ID, timeout, ttl):
	
	trace_receive = get_socket(timeout, ttl, 'icmp')
	
	try:
		reply = trace_receive.recv(4096)  						# Wait for reply from node.
	except socket.timeout: 
		trace_receive.close()
		return (time.time(), '*')								# If response times out -> Return timeout time and asterisk for the host.
			
	end_time = time.time()										# Store time of receipt. 
	ICMP_header_packed = reply[20:28]							# Slice ICMP head from packet. First 20-bytes is IP.
	ICMP_header = struct.unpack('bbHHH', ICMP_header_packed)	# Unpack ICMP head to get contents.	
	ICMP_type = ICMP_header[0]									# Get response type. 
	received_ID = ICMP_header[3] 					            # Get ID from ICMP header.
		
	try:
		source_IP = socket.inet_ntoa(reply[12:16])				# Convert packed IP address to dotted quad string representation.
	except socket.error:
		print("Source IP could not be obtained. ")
		
	trace_receive.close()
	return (end_time, source_IP)	
		
# Generates ICMP header and sends packet to destination address.
def sendOnePing(sender, destinationAddress, ID):
		
	ICMP_header = struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, 0, ID, 1)  		# Packing ICMP header with dummy checksum value.																   
	check_sum   = checksum(ICMP_header) 										# Generating checksum value.	
	ICMP_packet = struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, check_sum, ID, 1) 	# Repacking ICMP header with actual checksum value.	
	sender.sendto(ICMP_packet, (destinationAddress, 10000))						# Sending ICMP packet to destination.				
	return time.time()															# Returning send time. 

# Completes a single ping cycle and returns the total time elapsed, source IP, and response type.
def doOnePing(destinationAddress, timeout, ID, ttl, protocol): 
	
	trace_send = get_socket(timeout, ttl, protocol)
	start_time = sendOnePing(trace_send, destinationAddress, ID) 			# Send packet and return send time.
	received_inf = receiveOnePing(ID, timeout, ttl) 						# Attempt to receive packet and packet info -> tuple containing time response was received (or timeout), source address of response, and response type.
	trace_send.close()														# Closing socket connection.
							
	return (received_inf[0] - start_time, received_inf[1]) 				# Returning rtt delay time and source IP.

# Returns a ICMP socket with the specified timeout and ttl.
def get_socket(timeout, ttl, protocol):
	
	try: 
		mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname(protocol))    # Creating socket -> Specifying address family, socket type, and protocol.
		mySocket.settimeout(timeout)																  # Setting connection timeout period.														
		mySocket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)									  	  # Setting packet time-to-live.																												
	except socket.error:
		print("Couldn't create socket. Are you running as super user?")
		return 
	
	return mySocket
	

# Pings host continously -> each time increasing TTL by one until destination reached. Outputs 
# hostname and IP for each node traversed by the packet to reach the specified destination to the
# terminal.
def trace(host, timeout = 1, ping = 3, protocol = 'icmp'):
	
	ttl = 1		  									 							# Time-to-live. Incremented every loop until destination reached. 	
																				
	try:
		server_ip = socket.gethostbyname(host)			 						# Attempt to resolve hostname to IP address.
	except socket.gaierror:
		print("Couldn't resolve host name.")	
		return
	
	try: 	
		while True:
			
			ping_time = []														# Stores ping times for each node. Reset each time TTL is incremented.
			source_ip = '*'														# Stores source IP for current pings. Reset each time TTL is incremented. Default value of asterisk if no response received. 
			
			for i in range(ping): 												# Ping node 'ping' times for each node. 
			
				ping_inf = doOnePing(server_ip, timeout, 1, ttl, protocol) 		# Completes a single ping sequence. Returns tuple containing time delay, node source address, and ICMP response code.
				
				if (ping_inf[0] < timeout):										# If request didn't timeout -> save the time and source ip.
					source_ip = ping_inf[1]
					ping_time.append(roundTime(ping_inf[0])) 
				else: 															# If timeout -> Set time to asterisk. 
					ping_time.append('*') 										
			
			try: 																# Attempt to resolve IP address to hostname and output results.
				host_name = socket.gethostbyaddr(source_ip)[0]				
				print '---------------------------------------------------------------------------------------------------------->'
				print '| {0:4} | {1:40} | {2:25} | {3:6} | {4:6} | {5:6} |'.format(ttl, host_name, source_ip, ping_time[0], ping_time[1], ping_time[2])
			
			except socket.error:
				print '---------------------------------------------------------------------------------------------------------->'
				print '| {0:4} | {1:40} | {2:25} | {3:6} | {4:6} | {5:6} |'.format(ttl, source_ip, source_ip, ping_time[0], ping_time[1], ping_time[2])
			
			if (server_ip == ping_inf[1]):										# Destination reached -> trace complete.
				print '---------------------------------------------------------------------------------------------------------->'
				print"\n Trace complete."
	
				return
	
			ping_time = []
			ttl += 1
			
	except KeyboardInterrupt:													# CTRL+C -> Clean exit. No stacktrace.
		print "\n Trace aborted."

# Returns clock time in milliseconds rounded to the three decimal places in printable string format.
def roundTime(value):
	return round(value * 1000, 3)
	
trace('www.lancaster.ac.uk', 1, 3, 'icmp')
