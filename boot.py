#!/usr/bin/python

import socket
import time
from network import LoRa
import _thread

message_list = []

def message_string_op(method='get', message=None):
    if method == 'get':
        return message_list
    if method == 'add':
        message_list.append(message)
        return message_list
    return None


class Server:
    """ Class describing a simple HTTP server objects."""

    def __init__(self, port=808):
        """ Constructor """
        self.host = ''
        self.port = port
        self.www_dir = 'www'

    def listen_at_all_times(self, conn):
        """This function recieves data at all times."""
        while True:
            data = conn.recv(2056)
            if data:
                message_string_op('add', data.decode())
            time.sleep(0.5)

    def activate_server(self):
        """ Attempts to aquire the socket and launch the server """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Launching HTTP server on ", self.host, ":", self.port)
            self.socket.bind((self.host, self.port))

        except Exception as e:
            print("Warning: Could not aquite port:", self.port, " : ERROR: ", e, "\n")
            print("I will try a higher port")
            user_port = self.port
            self.port = 8080

            try:
                print("Launching HTTP server on ", self.host, ":", self.port)
                self.socket.bind((self.host, self.port))

            except Exception as e:
                print("ERROR: Failed to acquire sockets for ports ",
                      user_port, " and 8080. ")
                print("Try running the Server in a privileged user mode.")
                self.shutdown()
                import sys
                sys.exit(1)

        print("Server successfully acquired the socket with port:", self.port)
        print("Press Ctrl+C to shut down the server and exit.")
        self._wait_for_connections()

    def shutdown(self):
        """ Shut down the server """
        try:
            print("Shutting down the server")
            s.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            print(
                "Warning: could not shut down the socket. Maybe it was already closed?", e)

    def _gen_headers(self,  code):
        """ Generates HTTP response Headers. Ommits the first line! """

        # determine response code
        h = ''
        if (code == 200):
            h = 'HTTP/1.1 200 OK\n'
        elif(code == 404):
            h = 'HTTP/1.1 404 Not Found\n'

        # write further headers
        #  current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        h += 'Date: ' + 'today' + '\n'
        h += 'Server: Simple-Python-HTTP-Server\n'
        # signal that the conection wil be closed after complting the request
        h += 'Connection: close\n\n'

        return h

    def update_again(self, conn, message):
        message_string = ''
        for text in message:
            message_string = message_string + '<br>' + text
        print('+++++++++++++++++++++++++++++++++++++++++++\n\n')
        print(message_string)
        print('\n\n+++++++++++++++++++++++++++++++++++++++++++++++')

        response_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <title>Document</title>
            </head>
            <body>
                <h1>Hello World from LoPy Nigga!</h1>
                <form action="" method="post">
                    <p>%s</p>
                    <input type="text" name="extra_name">
                    <button type="submit">Submit</button>
                </form>
            </body>
            </html>              
            """ % message_string

        response_headers = self._gen_headers(200)
        server_response = response_headers.encode()  # return headers for GET and HEAD
        server_response += response_content  # return additional conten for GET only
        conn.send(server_response)
        conn.close()

    def _wait_for_connections(self):
        """ Main loop awaiting connections """
        
        lora = LoRa(mode=LoRa.LORA)
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        s.setblocking(False)
        _thread.start_new_thread(self.listen_at_all_times, (s,))

        while True:
            print("Awaiting New connection")
            self.socket.listen(3)
            conn, addr = self.socket.accept()
            print("Got connection from:", addr)

            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(message_list)
            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')


            data = conn.recv(1024)
            string = bytes.decode(data)

            request_method = string.split(' ')[0]
            print("Method: ", request_method)
            print("Request body: ", string)

            text_to_send = string.split(' ')[-1]

            if (request_method == 'POST'):
                text_message = []
                print('\n\n\t Trying to send data \n\n')
                s.send(text_to_send)
                print('\n\n\t Sent \n\n')

                text_message.append(text_to_send)
                self.update_again(conn, text_message)

            #  text_message.append(text_to_send)
            #  self.update_again(conn, text_to_send)
            # if string[0:3] == 'GET':

            if (request_method == 'GET') | (request_method == 'HEAD'):
                # file_requested = string[4:]
               #  # split on space "GET /file.html" -into-> ('GET','file.html',...)
               #  file_requested = string.split(' ')
               #  file_requested = file_requested[1] # get 2nd element

               #  # Check for URL arguments. Disregard them
               #  file_requested = file_requested.split('?')[0]  # disregard anything after '?'

               #  if (file_requested == '/'):  # in case no file is specified by the browser
               #      file_requested = '/index.html' # load index.html by default

               #  file_requested = self.www_dir + file_requested
               #  print ("Serving web page [",file_requested,"]")

                # Load file content
                try:
                    response_content = """
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <title>Document</title>
                    </head>
                    <body>
                        <h1>Hello World from LoPy Nigga!</h1>
                        <form action="" method="post">
                            <input type="text" name="extra_name">
                            <button type="submit">Submit</button>
                        </form>
                    </body>
                    </html>              
                 """

                    response_headers = self._gen_headers(200)

                except Exception as e:  # in case file was not found, generate 404 page
                    print("Warning, file not found. Serving response code 404\n", e)
                    response_headers = self._gen_headers(404)

                    if (request_method == 'GET'):
                        response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"

                server_response = response_headers.encode() # return headers for GET and HEAD
                if (request_method == 'GET'):
                    server_response += response_content  # return additional conten for GET only

                conn.send(server_response)
                conn.close()

            else:
                print("Unknown HTTP request method:", request_method)


def graceful_shutdown(sig, dummy):
    """ This function shuts down the server. It's triggered
    by SIGINT signal """
    s.shutdown()  # shut down the server
    import sys
    sys.exit(1)

# shut down on ctrl+c
# signal.signal(signal.SIGINT, graceful_shutdown)


print ("Starting web server")
s = Server(80)  # construct server object
s.activate_server()  # aquire the socket
