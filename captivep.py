#!/usr/bin/python

import os
import BaseHTTPServer
import subprocess
from BaseHTTPServer import BaseHTTPRequestHandler
import sys
import thread 
import ssl

 
PORTN1 = 80
IP_ADDRESS = "192.168.1.1" #subprocess.check_output("hostname -I | awk 'NR==1 {printf $2}'", shell=True)
BASE_DIR = None	 
LOAD_PERFIX = "/load?file="
LOAD_PERFIX_LEN = len(LOAD_PERFIX)
MARK_PERFIX = "/mark?file="
MARK_PERFIX_LEN = len(MARK_PERFIX)

MAIN_HTML = """
<html>
<style>
h1 {text-align:center;}
p {text-align:center;}
table, th, td {
border: 5px solid grey; padding: 15px; text-align: left;
}
</style>
<head>
</head>
<body>
<table style="width:100%%">
<tr><td><h1>For today</h1></td><td><h1>All files</h1></td></tr>
<tr><td>%s</td><td>%s</td></tr>
</table>
</body>
</html>
"""

REDIRECT_HTML = """
<html>
<head>
	<meta http-equiv="refresh" content="0; url=http://%s:%s/login" />
</head>
<body>
	<b>Redirecting to login page</b>
</body>
</html>
""" % (IP_ADDRESS, PORTN1)

FILE_HTML = """
<html>
<style>
iframe { 
   position: absolute; 
   top: 3%%; 
   left:3%%; 
   width: 95%%; 
   height: 95%%;
} 
</style>
<head>
</head>
<body>
<iframe id="myFrame" src="%s"></iframe>

<script>
var frame = document.getElementById('myFrame');
	frame.onload = function () {
		var body = frame.contentWindow.document.querySelector('body');
		body.style.color = 'black';
		body.style.fontSize = '2vw';
	 };
</script>

</body>
</html>
"""
	
	
def getIpTablesCommands(ipAddr, portN1):
	lst1 = []
	#allow fwd 
	#lst1.append("sysctl -w net.ipv4.ip_forward=1")
	# clean iptables
	#lst1.append("iptables -t filter -F")
	#lst1.append("iptables -t nat	-F")
	# Block all other traffic
	#lst1.append("iptables -A FORWARD -j REJECT")
 	#Redirecting HTTP traffic to captive portal
	#lst1.append("iptables -t nat -A PREROUTING	   -p tcp --dport 443 ! -d  %s -j DNAT --to-destination %s:%s" % (ipAddr, ipAddr, portN1))
  	#lst1.append("iptables -t nat -A PREROUTING -p tcp --dport 80 ! -d  %s -j DNAT --to-destination %s:%s" % (ipAddr, ipAddr, portN1))
 	#lst1.append("iptables -L -vn  -t nat -t filter")
	return lst1


def recursiveFiles(mydir):
	matches = {}
	for root, _, filenames in os.walk(mydir):
		for fn in filenames:
			if fn.endswith("1.txt"):
				relDir = os.path.relpath(root, mydir)
				relFile = os.path.join(relDir, fn)
				matches[relFile] = fn
	return matches


class FileSelector(object):

	def __init__(self, dirname):   
		self.dirNm = dirname
		self.allFiles = recursiveFiles(dirname)
		self.selectedFiles = {}

	def decorate(self, keyValPair, linkStart):
		 strTag = "<a href=%s%s>%s</a><br>" % (linkStart, keyValPair[0], keyValPair[1]) 
		 return strTag
		
	def getSelected(self, linkStart):
		strTag = ""
		for x in self.selectedFiles.items():
			strTag += self.decorate(x, linkStart)
		return strTag  
			
	def getAll(self, linkStart):
		strTag = ""
		for x in self.allFiles.items():
			strTag += self.decorate(x, linkStart)
		return strTag  
		
	
 
class CaptiveHandler(BaseHTTPRequestHandler):
	def getFs(self):
		return self.server.fileSelector
	
	def getAdminAddr(self):
	 	return self.server.adminAddr

	def setAdminAddr(self, value):
	 	self.server.adminAddr = value

	def send_Load(self):
		self.send_Head()
		filename = self.path[LOAD_PERFIX_LEN:]
		str1 = "./" + filename
		str2 = FILE_HTML % (str1)
		self.wfile.write(str2)
		
	def change_Mark(self):
		filename = self.path[MARK_PERFIX_LEN:]
		dic1 = self.getFs().selectedFiles
		dic2 = self.getFs().allFiles
		
		if filename in dic1:
			value = dic1[filename]
			dic2[filename] = value
			del dic1[filename]
		elif filename in dic2:
			value = dic2[filename]
			dic1[filename] = value
			del dic2[filename]
		self.send_Main()
			
	def send_Main(self):
		self.send_Head()
		pref = LOAD_PERFIX
		if self.isAdmin():
			pref = MARK_PERFIX
		str1 = MAIN_HTML % (self.getFs().getSelected(pref), self.getFs().getAll(pref))
		self.wfile.write(str1)
	
	
	def send_Binary(self, filename):
		f = open(filename, "rb")
		str1 = f.read()
		f.close()		
		self.wfile.write(str1)
	
	def send_Redir(self):
		self.send_Head()
		self.wfile.write(REDIRECT_HTML)

	def isAdmin(self):
		return self.getAdminAddr() == self.client_address[0]
	
	def send_Head(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):	
		#kind of password put into address bar
		#print "connect to: " + self.path
		if "222" in self.path:
			if self.isAdmin():
				self.setAdminAddr(None)
			else:
				self.setAdminAddr(self.client_address[0])
			
		isLoad = self.path.startswith(LOAD_PERFIX)
		if isLoad:
			return self.send_Load()
	
		isMark = self.path.startswith(MARK_PERFIX)
		if isMark:
			return self.change_Mark()

		isLogin = self.path.startswith("/login")
		if isLogin:
			return self.send_Main()
		

		isLocal = self.path.startswith("/")
		fileExists = os.path.isfile("." + self.path)
		if isLocal and fileExists:
			return self.send_Binary("." + self.path)
		
		return self.send_Redir()
		
def main():

	IP_TABLES_COMMANDS = getIpTablesCommands(IP_ADDRESS, PORTN1)
	BASE_DIR = os.path.expanduser("~/Dropbox/mypi/music")
	if not os.path.isdir(BASE_DIR):
		BASE_DIR = os.path.expanduser("~/mypi/music")
		if not os.path.isdir(BASE_DIR):
			sys.exit("Root directory not found: " + BASE_DIR)
	

	FNAME_END = "1.txt"
	SAVEPATH = os.getcwd()
	os.chdir(BASE_DIR)
	print os.getcwd(), SAVEPATH

 	my_serv1 = BaseHTTPServer.HTTPServer(('', PORTN1), CaptiveHandler)
 	my_serv1.fileSelector = FileSelector(BASE_DIR)
 	my_serv1.adminAddr = None

 	 
 	
	print "Now start redirecting HTTP traffic to captive portal"
	for str1 in IP_TABLES_COMMANDS:
		ret = os.system("sudo " + str1)
		print str1
		if ret != 0:
			sys.exit("Error setting IP table command: " + str1)

	try:
		my_serv1.serve_forever()
	except KeyboardInterrupt:
		print "closed"
		
	my_serv1.server_close()
	#my_serv2.server_close()
	os.chdir(SAVEPATH)


if __name__ == '__main__':
   main()
