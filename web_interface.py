#!/usr/bin/env python3
 
from http.server import SimpleHTTPRequestHandler, HTTPServer
import exfiltrate
import urllib
import threading
import signal
import sys

threads = {}

def exit_handler(signal=None, b=None):
    print("Shutting down web interface")
    for t in threads:
        threads[t].cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(SimpleHTTPRequestHandler):
    # GET
    def do_GET(self):
        try:   
            if self.path == "/":
                msg = open("index.html", "r").read()
            else:
                basepath = urllib.parse.urlparse(self.path).path
                if basepath == "/exfiltrate_query":
                    qs = urllib.parse.urlparse(self.path).query
                    url = urllib.parse.parse_qs(qs).get('url')
                    if url is not None:
                        url = url[0]

                    prev_thread = threads.get(url)
                    if prev_thread:
                        prev_thread.join()
                    exfilt = exfiltrate.ExfiltrateThread(url)
                    exfilt.daemon = True
                    exfilt.start()
                    threads[url] = exfilt

                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    first = int(qs['first'][0].rsplit("_",1)[1])
                    last = int(qs['last'][0].rsplit("_",1)[1])
                    folder = qs['first'][0].rsplit("_", 1)[0].replace("/","_",1)
                    msg = "title: " + qs['title'][0] + "<br>"
                    msg += "dossier: " + qs['dossier'][0] + "<br>"
                    msg += "pages: " + str(first) + "-" + str(last) + "<br>"
                    msg += "<br>"
                    msg += "Your files are being downloaded to: "
                    msg += "<a href=\"/" + folder + "\">" + folder + "</a>\n"
                    msg += "<br><br>This process can take a while.<br>"
                    msg += "If the images aren't all there yet, just refresh the page."
                    msg = exfiltrate.Templates.html.replace("%%BODY%%", msg)
                else:
                    SimpleHTTPRequestHandler.do_GET(self)
                    return
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            msg = "Internal Server Error: " + type(e).__name__ + " " + str(e)
            self.wfile.write(bytes(msg, "utf8"))
            return

        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(bytes(msg, "utf8"))
        return

def run():
    # Server settings
    # Choose port 8080 or 8000, for port 80, which is normally used for a http server, you need root access
    server_address = ('127.0.0.1', 8000)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('Visit http://localhost:8000 in your web browser')
    try:
        httpd.serve_forever()
    finally:
        print("Good bye")

run()
