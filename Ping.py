#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import sys
import struct
import time
import signal

TIMEOUT = -1 						# Value returned if ping times out. 
TYPE_ECHO_REPLY   = 0 				# ICMP type code for echo reply messages.
CODE_NETWORK_UNREACHABLE = 0 		# ICMP subtype code for network unreachable messages.
TYPE_DESTINATION_UNREACHABLE = 3 	# ICMP type code for destination unreachable messages.
TYPE_ECHO_REQUEST = 8 				# ICMP type code for echo request messages.
CODE_HOST_UNREACHABLE = 11 			# ICMP subtype code for host unreachable messages.

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
def receiveOnePing(ICMP_socket, destinationAddress, ID, timeout):
	
	while True: 
		try:
			reply = ICMP_socket.recv(28)  							 # Block until 28-bytes received (IP header + ICMP header)
		except socket.timeout: 
			print(getHostName(destinationAddress) + " (" + destinationAddress + ")" + " timed out - no response received")	
			return None												 # Return None value to indicate that no response was receved within timeout period.

		end_time = time.time()										 # Save time response was received. 
	
		ICMP_header_packed = reply[20:28]							 # Slice ICMP header from IP header.
		ICMP_header = struct.unpack('bbHHH', ICMP_header_packed)	 # Unpack ICMP header to get contents.
	
		ICMP_type   = ICMP_header[0]							     # Get ICMP type code.
		ICMP_code   = ICMP_header[1]								 # Get ICMP sub-type code.
		received_ID = ICMP_header[3] 					             # Get ID from ICMP header.

		if (ID == received_ID): 									 # If ID matches with sent ICMP packet ID -> Check error type and return appropriate values.
			if ICMP_type == TYPE_DESTINATION_UNREACHABLE:			
				if ICMP_code == CODE_NETWORK_UNREACHABLE:
					print "Destination Unreachable - Network Unreachable."
					return None
			
			elif ICMP_type == CODE_HOST_UNREACHABLE:
				print "Destination Unreachable - Host Unreachable."
				return None
			elif ICMP_type == TYPE_ECHO_REPLY:								# If echo reply was received. Return time of receipt. 
				return end_time											

# Generates ICMP header and sends packet to destination address.
def sendOnePing(ICMP_socket, destinationAddress, ID):
		
	ICMP_header = struct.pack('bbHHH', TYPE_ECHO_REQUEST, 0, 0, ID, 1) 		   # Packing ICMP header with dummy checksum value.								   
	check_sum   = checksum(ICMP_header) 									   # Generating checksum value.
	ICMP_packet = struct.pack('bbHHH', TYPE_ECHO_REQUEST, 0, check_sum, ID, 1) # Repacking ICMP header with actual checksum value.
	ICMP_socket.sendto(ICMP_packet, (destinationAddress, 25))				   # Sending ICMP packet to destination.
	return time.time()														   # Returning send time. 
	
# Completes a single ping cycle and returns the total time elapsed. 
def doOnePing(destinationAddress, timeout, ID): 
	
	try: 
		ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp')) # Creating socket -> Specifying address family, socket type, and protocol.
		ICMP_socket.settimeout(timeout)																# Setting connection timeout period.
	except socket.error:
		print("Couldn't create socket.")
		return 
	
	start_time = sendOnePing(ICMP_socket, destinationAddress, ID) 				 	 # Send packet and return send time.
	time_received = receiveOnePing(ICMP_socket, destinationAddress, ID, timeout) 	 # Attempt to receive packet and return delay.
	
	ICMP_socket.close()															 	 # Closing socket connection.
	if (time_received != None):														 # If didn't time out -> Return elapsed time
		return (time_received-start_time)
	else: 	
		return None

# Pings specified host and displays delay time for each ping.
def ping(host, timeout = 1, ping_num = sys.maxint):	
	
	packets_lost = 0	# Number of packets no response has been received for.
	time_taken   = 0 	# Number of milliseconds the application has been running.
	min_rtt      = 0	# Minimum time recorded for a complete round trip.
	max_rtt      = 0	# Maximum time recorded for a complete round trip.
	count        = 0	# Serves as counter for while loop (number of pings) and ID value for packet header.
	
	try:
		server_ip = socket.gethostbyname(host)		# Resolve host name to IP address. If already an IP address -> Returns itself.
	except socket.gaierror:
		print("Couldn't resolve host name.")	
		return
	
	host = getHostName(host) 						# Resolve IP address to hostname (if IP passed as 'host' instead of a hostname). 
	
	try: 
		while count < ping_num:						# Continue to ping for a specified number of pings or until application closed.
			
			time_elapsed = doOnePing(server_ip, timeout, count)
					
			if time_elapsed != None:
													
				if (time_elapsed < min_rtt or count == 0):														# Update minimum round trip time.
					min_rtt = time_elapsed
			
				if (time_elapsed > max_rtt or count == 0):														# Update maxmimum round trip time.
					max_rtt = time_elapsed
																				
				print '{0} ({1}) time {2} ms'.format(host, server_ip, roundTime(time_elapsed)) 

				time_taken  += time_elapsed
				count       += 1
			
				if (time_elapsed < 1):																			# Artificial 1 second delay between each ping.
					time.sleep(1 - time_elapsed)
			
			else:																																									
				packets_lost += 1																				# Count number of packets lost.	
					
		displayResults(packets_lost, time_taken, count, min_rtt, max_rtt, server_ip)							# Display aggregate results after ping count reached.
		
	except KeyboardInterrupt: 																					# Terminate application upon KeyBoardInterrupt (CTRL+C) and output aggregate results for pings.
		displayResults(packets_lost, time_taken, count, min_rtt, max_rtt, server_ip)

# Displays ping aggregate results to terminal.
def displayResults(packets_lost, time_taken, total_pings, min_rtt, max_rtt, server_ip):
	
	try:
		avg_rtt = time_taken / total_pings						# Calculating average round trip time.
		packets_received = total_pings - packets_lost			# Calculating total number of packets received.
		packet_loss = (packets_lost / total_pings) * 100		# Calculating percentage total of packet loss.
		
		print '\n--- " {0} " ping statistics ---\n'.format(server_ip)
		print '{0} packets transmitted, {1} received, {2}% packet loss, {3} ms'.format(total_pings, packets_received, packet_loss, roundTime(time_taken))
		print 'rtt min/avg/max = {0}/{1}/{2} ms'.format(roundTime(min_rtt), roundTime(avg_rtt), roundTime(max_rtt)) 
		
	except ZeroDivisionError:  									# Don't print anything if no responses received. 
		return

# Returns clock time in milliseconds rounded to the three decimal places in printable string format.
def roundTime(value):
	return round(value * 1000, 3)
	
def getHostName(address):
	try:
		socket.inet_aton(address)				  # If IP passed as hostname instead of an actual hostname -> validate it. 
		return socket.gethostbyaddr(address)[0]   # If its valid -> Get the hostname for the IP address.
	except socket.error:
		return address							  # If IP can't be resolved to a hostname -> returns itself.
	
	
ping("www.google.co.uk") # Passing hostname.
#ping("216.58.211.163")  # Passing IP address in place of hostname.
#ping("10.255.255.1")    # Non-routable IP address -> Use for testing timeout.










