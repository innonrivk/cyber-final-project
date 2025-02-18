import base64
import os
import socket, threading
import protocol

IP = "0.0.0.0"
PORT = 8080
# list contains all the active threads
active_threads = []


class ClientThread(threading.Thread):

    def __init__(self, clientAddress, clientSocket):
        threading.Thread.__init__(self)
        self._client_socket = clientSocket
        # sets name to ip address only.
        self.name = clientAddress[0]
        # adds ip to database
        protocol.add_ip_to_db(self.name)
        self.msg = ""
        self.response = ""
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.photo_path = r""
        print("New connection added: ", clientAddress)

    def get_name(self):
        return self.name

    def set_photo_path(self,photo_path):
        self.photo_path = f"{photo_path}\\{str(self.name)}SC.jpg"

    def get_photo_path(self):
        return self.photo_path

    def set_msg(self, msg):
        self.msg = msg

    def get_msg(self):
        return self.msg

    def set_response(self,response):
        self.response = response

    def get_response(self):
        return self.response

    def send_photo_handler(self):
        """
        used to maintain connection with client until the transfer of the photo finishes.
        :return: confirmation message
        :rtype: str
        """
        try:
            pic_data = ""
            response = f"img was received successfully and has been saved at {self.photo_path}"
            vaild_pick_len, pic_len = protocol.get_msg(self._client_socket)
            if not pic_len.isdigit():
                return f"picture length is not valid. got massage: {pic_len}"

            with open(self.photo_path, "wb") as file:
                while len(pic_data) < int(pic_len):
                    vaild_data, data = protocol.get_msg(self._client_socket)
                    if not vaild_data:
                        response = f"img data wasnt received correctly. {data}"
                    pic_data += data
                # decoding the image to base64 in order to save it
                file.write(base64.b64decode(pic_data.encode()))
            return response
        except FileNotFoundError as ex:
            return ex


    def req_handeler(self, command):
        """
        it makes sure that the client response will be returned fully and correctly.
        :param command: string, the command which is sent to client
        :return:client response
        :rtype: str
        """
        self.lock.acquire()
        resp = ""
        try:
            self.set_msg(command)
            self.event.wait()
            self.set_msg("")
            resp = self.get_response()
            self.set_response("")
            self.event.clear()
        finally:
            self.lock.release()
            return resp



    def run(self):
        """
        manage the direct communication with client
        :return:  None
        """
        while True:
            # checks if everything iss cleared and ready for new message to be sent
            if (not self.event.is_set()) and (self.get_msg() != ""):
                data = ""
                vaild_msg, massage = protocol.create_msg(self.get_msg())
                if vaild_msg:
                    self._client_socket.sendall(massage.encode())
                    # if client is going to transfer an image, self.send_photo_handler() should be used
                    if "send_photo" in self.get_msg():
                        data = self.send_photo_handler()
                    else:
                        valid_data, data = protocol.get_msg(self._client_socket)
                    self.set_response(data)
                # clears the event in order for  self.req_handeler() to continue
                self.event.set()


class user_socket(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.IP = "127.0.0.1"
        self.PORT = 8820
        self.Sphoto_path = r""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind((self.IP, self.PORT))

    def check_thread_group(self, additives, thread):
        """
        checks if a given thread  is a part of a given additive
        :param additives: list, all additives we wish to send the command to
        :param thread: a given thread
        :return: if the thread is located in with in one of the given additive
        :rtype: bool
        """
        for add in additives:
            if thread.get_name() in protocol.ip_list(add):
                return True
        return False

    def user_handler(self, command):
        """
        sends the command to the wanted threads and adds each thread response to response list
        :param command: string, the command contains the command itself, params (file location), and additives
        :return: response list
        :rtype: list
        """
        valid_split, com, param, add = protocol.command_split(command)
        response_lst = []
        for thread in active_threads:
            if self.check_thread_group(add, thread):
                # sets thread's photo_path to the required folder
                if com == "send_photo":
                    thread.set_photo_path(self.Sphoto_path)
                resp = thread.req_handeler(f"{com} {param}")
                response_lst.append((thread.get_name(), resp))
        return response_lst

    def create_sphoto_path(self):
        """
        creates a folder in which  the photos will be saved, the folder
        is created in the same place the current script is located and sets self.Sphoto_path to its path.
        if the folder already exists  its just sets self.Sphoto_path to its path
        :return: None
        """
        current_path = os.getcwd()
        final_directory = os.path.join(current_path, r'saved_photos')
        print(final_directory)
        if not os.path.exists(final_directory):
            os.makedirs(final_directory)
        self.Sphoto_path = f"{final_directory}"

    def run(self):
        """
        it establishes a connection with the user (IT man)
        and its in charge of getting messages from user and sending back responses.
        in case the user closed the connection it waits for the connection to reestablish
        :return: None
        """
        self.create_sphoto_path()
        while True:
            clientsock = None
            self.server_sock.listen(1)
            clientsock, clientAddress = self.server_sock.accept()
            print("ui connect: " + clientAddress[0])
            while clientsock != None:
                valid_data, data = protocol.get_msg(clientsock)
                if valid_data:
                    # in case the user wish to close the connection
                    if data == "exit":
                        # the server sends back confirmation message and exsiting the loop
                        valid_msg, massage = protocol.create_msg(data)
                        if  valid_msg:
                            clientsock.sendall(massage.encode())
                            break
                        else:
                            clientsock.sendall(massage.encode())
                    # sends user data to self.user_handler() for further processing
                    resp = self.user_handler(data)
                    valid_msg, massage = protocol.create_msg(resp)
                    if valid_msg:
                        clientsock.sendall(massage.encode())
                    else:
                        clientsock.sendall(massage.encode())

                else:
                    clientsock.sendall(data.encode())
            print("user closes connection")
            clientsock.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    print("Server started")
    print("Waiting for client request..")
    # creating a thread to manage the connection from user
    thread_user_socket = user_socket()
    thread_user_socket.start()

    while True:
        server.listen(1)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()
        active_threads.append(newthread)


if __name__ == '__main__':
    main()