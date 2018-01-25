# Python version: v2.7.9
# GCC 4.2.1 (Apple Inc. build 5666)
# File name: ss.py
# File description: a simple web server
# Create & edited by: Liam Ling
# References: https://docs.python.org/2/howto/sockets.html
#             https://docs.python.org/2/library/socket.html
#             https://wiki.python.org/moin/TcpCommunication
#             http://jmarshall.com/easy/http/#http1.1s1
#             https://docs.python.org/2/library/signal.html
#             https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

import socket # socket interface - low-level networking interface
import signal # for ctrl+c method
import sys # for exiting the program
import time # for request time
import errno # error number handling
import mimetypes # for MIME type checking
import urllib, re # for getting public ip

mimetypes.init() # initialize the internal data structures for mimetypes
#ipdata = re.search('"([0-9.]*)"', urllib.urlopen("http://ip.jsontest.com/").read()).group(1) # public ip ? route forwarding to local ip ?
#print ipdata
s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create an INET, STREAMing (TCP, use SOCK_DGRAM for UDP) server socket (s_socket)
server_name = 'Macintosh HTTP Server'
hostaddress = socket.gethostbyname(socket.gethostname()) # get the local IP address of this machine, if locally testing: using '' or '127.0.0.0' instead
hostport = 4300 # unsigned port, use 0 for system assigning
buffer_size = 1024

def file_handler(file_name):
	data = ''
	if(get_file_type(file_name).split('/')[0] == 'video'): #### more types
		file_name = 'site/assets/film/' + file_name
	elif(get_file_type(file_name).split('/')[0] == 'image'):
		file_name = 'site/assets/img/' + file_name
	elif((get_file_type(file_name).split('/')[1] == 'css')):
		file_name = 'site/css/' + file_name
	elif((get_file_type(file_name).split('/')[0] == 'text')):
		file_name = 'site/' + file_name
	elif((get_file_type(file_name) == 'application/x-font-otf')):
		file_name = 'site/assets/fonts/' + file_name.split('.')[0] + '/' + file_name

	print file_name
	try:
		file = open(file_name, 'rb') # open target file
		data = file.read() # read into data
		file.close()
		flag = 200 # set flag for HTTP response status code
		return flag, data
	except IOError: # if not found or another errors
		flag = 404
		return flag, data

def ctrl_c_shut_down(sig, du):
	shutdown_socket(s_socket)
	print "\n---------------------------------------\nServer shutting down"
	sys.exit(1) # exit the program

def shutdown_socket(sock):  # self-defined socket shutdown function
	try:
		sock.shutdown(socket.SHUT_RDWR) # shutdown a socket, "SHUT_RDWR" means further sends and receives are disallowed
	except socket.error, e:
		if(e.errno != errno.ENOTCONN): # if the socket is already closed
			print("socket is already closed %s" %e)
			raise
	sock.close() # close a socket, all future operations on the socket will fail

def send_msg(c_s, types, data, remain): # try using sendall when sending a larger file
	# print "@@@@@@@Data len: ", len(data, "remain: ", remain, "@@@@@@@@" # used for error checking
	types = types.split('/')[0]
	total = remain
	if(1024 < len(data) < 102400): # larger file
		try:
			check = c_s.sendall(data)
			if(check == None): # in this case sendall() is successful
				remain = 0
				print " --- Sent: ", len(data), "bytes data, remain: ", remain, "bytes data"
		except socket.error, e:
			print "Error sendall(data): %s" %e, ", try using send(data)"
	elif(len(data) >= 102400):
		t = 0.0
		while(data): # try the old way
			try:
				send = c_s.send(data)
				data = data[send:]
				print " --- Sent: ", send, "bytes data, remain: ", len(data), "bytes data"  #### this should be improved if the old socket fails, a new sockets requires new data
				print " -- Pending ...", t, " sec"
				time.sleep(t)
			except socket.error, e:
				print "Error send(data): %s" %e
				break;
	elif(0 <= len(data) <= 1024): # file size in 0-1024 bytes range
		try:
			send = c_s.send(data)
			print " --- sent: ", send, "bytes data, remain: ", len(data) - send, "bytes data"
		except socket.error, e: # when a error occurs
			print "Error send(data): %s" %e

def get_file_type(file): # get the MIME type
	if('.' in file):
		file_type = '.' + file.split('.')[-1]
		file_type = mimetypes.types_map[file_type]
	elif(file == "error"):
		file_type = 'text/html'
	return file_type

def header_generator(code, file, cont_len):
	txt = ''
	file_type = get_file_type(file)
	if(code == 200): # determine response title
		txt = 'HTTP/1.1 200 OK\r\n'
	elif(code == 400):
		txt = 'HTTP/1.1 400 Bad Request\r\n'   #### more error types
	elif(code == 404):
		txt = 'HTTP/1.1 404 Not Found\r\n'
	elif(code == 505):
		txt = 'HTTP/1.1 505 HTTP Version Not Supported\r\n'
	txt += 'Date: ' + time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()) + '\r\n' # get local time
	txt += 'Server: ' + server_name + '\r\n'
	txt += 'Accept-Ranges: bytes\r\n'
	txt += 'Content-Type: ' + file_type + '\r\n'
	txt += 'Content-Language: en\r\n'
	txt += 'Content-Length: ' + str(cont_len) + '\r\n'    #### more contents and decide when to use which of these
	txt += 'Connection: close\r\n'
	txt += '\r\n'
	return txt

def main(): # main program
	signal.signal(signal.SIGINT, ctrl_c_shut_down) # close socket when there is a ctrl+c keyboard interruption

	try:
		s_socket.bind((hostaddress, hostport)) # bind the socket to a host and a port
	except socket.error as msg:
		print "In-used binding between address:", hostaddress, "and port number:", hostport
		print "Try other ports."
		print "socket.error message: ", msg
		shutdown_socket(s_socket)
		sys.exit(1)

	s_socket.listen(5) # listen for connections made to the socket, minimum 0, maximum depends on the system, use 5 as the requirement
	print "Servering at: ", s_socket.getsockname(), "\n---------------------------------------" # get the socket's binded address and port number

	while 1: # Server main loop
		c_socket, c_address = s_socket.accept() # accpect connections, get client socket (c_socket) and client address (c_address)
		c_socket.settimeout(7200.0) # set time out for client socket 2hr
		print " -- Connected to address: ", c_address # show client ip and port number
		print " -- Client socket: ", c_socket # show client socket which used to send and recieve data

		try:
			recv_data = c_socket.recv(buffer_size) # receive client data
		except socket.error, e: # error on receiving client data
			print "Error receiving data: %s" %e
		decd_recv_data = bytes.decode(recv_data) # decode received data to string
		print "*******************\n", decd_recv_data, "*******************"
		print " --- Received: ", len(decd_recv_data), "bytes data" # show received client data

		if(decd_recv_data == ''): # if client refresh the page, resend the data
			send_msg(c_socket,  get_file_type(request_file), resp_data, len(resp_data)) # self-defined send response through socket
			shutdown_socket(c_socket)
			print " -- Close connection with client: ", c_address
		else:
			request_line = decd_recv_data.splitlines()[0] # split the first request line
			request_msg = request_line.split(' ')[0] # split the client requst message
			request_file = request_line.split(' ')[1] # split the request file name
			HTTP_version = request_line.split(' ')[2] # split the HTTP version of the client

			if(HTTP_version != 'HTTP/1.1'): # if the client requests HTTP 1.0 version
				print " --- Client HTTP version is non-compatible: '", HTTP_version, "'"
				resp_cont = b"<html><head></head><body><h1>505 HTTP Version Not Supported</h1></body></html>"
				request_file = "error"
				resp_header = header_generator(505, request_file, len(resp_cont))
				resp_data = resp_header.encode()
				resp_data += resp_cont

				print "======== msg: \n", resp_data

				send_msg(c_socket,  get_file_type(request_file), resp_data, len(resp_data))
				shutdown_socket(c_socket) # close connection to client
				print " -- Close connection with client: ", c_address

			elif(HTTP_version == 'HTTP/1.1'): # if the client requests HTTP 1.1 version
				if(request_msg == 'GET' or 'HEAD'): # GET request from client
					resp_cont = ''
					if(request_file == '/'): # empty request file name
						request_file = 'index.html' # the default web page to display
						print "No specific file requested, sending file: '", request_file, "'"
						file_flag, resp_cont = file_handler(request_file) # a flag to indicate which response header need to generated
						if(file_flag == 200):
							resp_header = header_generator(200, request_file, len(resp_cont)) # response header
						elif(file_flag == 404):
							print " --- File: '", request_file, "' cannot be opened"
							resp_cont = b"<html><head></head><body><h1>404 Not Found</h1></body></html>"
							request_file = "error"
							resp_header = header_generator(404, request_file, len(resp_cont))
						resp_data = resp_header.encode()
						resp_data += resp_cont # combinded data need to be responsed to client

					elif(len(request_file) > 1): # non-empty request file name
						request_file = request_file.split('/')[1] # splite the file name
						print "File requested, sending file: '", request_file, "'" 
						file_flag, resp_cont = file_handler(request_file)
						if(file_flag == 200):
							resp_header = header_generator(200, request_file, len(resp_cont))
						elif(file_flag == 404):
							print " --- File: '", request_file, "' cannot be opened"
							resp_cont = b"<html><head></head><body><h1>404 Not Found</h1></body></html>"
							request_file = "error"
							resp_header = header_generator(404, request_file, len(resp_cont))
						resp_data = resp_header.encode()
						resp_data += resp_cont

					send_msg(c_socket, get_file_type(request_file), resp_data, len(resp_data))
					shutdown_socket(c_socket) # close connection to client
					print " -- Close connection with client: ", c_address

				elif(request_msg == 'POST'): # HEAD request from client
					resp_cont = ''

				else:
					print "Unsupported HTTP request: ", request_msg # other request like 'HEAD', 'POST', etc are currently not programmed
					resp_cont = b"<html><head></head><body><h1>400 Bad Request</h1></body></html>"
					request_file = "error"
					resp_header = header_generator(400, request_file, len(resp_cont))
					resp_data = resp_header.encode()
					resp_data += resp_cont
					send_msg(c_socket,  get_file_type(request_file), resp_data, len(resp_data))   ### need to implement "HEAD", "POST", etc
					shutdown_socket(c_socket)
					print " -- Close connection with client: ", c_address

main() # main function
