import msvcrt
import socket
import threading

import protocol


class UserSocket(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.IP = "127.0.0.1"
        self.PORT = 8820
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msg = ""
        self.response = ""
        self.lock = threading.Lock()
        self.event = threading.Event()

    def set_msg(self, msg):
        self.msg = msg

    def get_msg(self):
        return self.msg

    def set_response(self, response):
        self.response = response

    def get_response(self):
        return self.response

    def handler(self, command):
        """makes sure that commands set by the user will be sent to server
        and a response will return to user
        :param command: the full command that user wants to send server
        :return: server response
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
        handles the communication with server
        :return: None
        """
        self.client_sock.connect((self.IP, self.PORT))
        while True:
            if (not self.event.is_set()) and (self.get_msg() != ""):
                vaild_msg, massage = protocol.create_msg(self.get_msg())
                if vaild_msg:
                    self.client_sock.sendall(massage.encode())
                    valid_data, data = protocol.get_msg(self.client_sock)
                    self.set_response(data)
                    if data == "exit":
                        print("exiting")
                        break
                self.event.set()
        self.client_sock.close()


def treat_data(data):
    """
    takes data and removes all parenthesis. then it creates a tuple that consists the treated data
    :param data: a string that reprint a list of tuples
    :return: list of tuples that resemble what server originally sent
    :rtype: list
    """
    new_lst = []
    data = data.strip('][')
    data = data.split("), ")
    for i in data:
        i = i.strip(")(")
        i = i.split(", ")
        i = tuple(i)
        new_lst.append(i)
    return new_lst


def send_command(command, thread):
    """
    sends user commands to server
    :param command: the raw command
    :param thread: a thread that manage  the communication with server
    :return: a nice representation of server response
    """
    # special cases in which we need to a different conduct
    if command == "exit":
        return thread.handler(command)
    if command == "state":
        return protocol.state()
    if command == "help":
        return protocol.help_func()

    valid_split, comm, param, add = protocol.command_split(command)
    if valid_split:
        valid_check, message = protocol.check_command(comm, param, add)
        if valid_check:
            resp = ""
            data = thread.handler(command)
            # processing data so we will display it as better
            if data != "[]":
                # we get from the server a string that is actually a list of tuples,
                # so we need to remove all unnecessary parth
                data = treat_data(data)
                for i in data:
                    # i is a tuple
                    msg = str(i[1])
                    if "\\\\" in msg:
                        msg = msg.replace("\\\\", "\\")
                        if ("\\n" in msg) and (comm == "dir"):
                            msg = msg.replace("\\n", "\n")
                    resp += f"{i[0]}: {msg}\n"
                return resp
            else:
                return "server returned nothing"
        else:
            return valid_check, message
    return False, comm, param, add


def ui(thread):
    """
    in charge of displaying user ui and takes input from user and displays output.
    :param thread: a thread that manage  the communication with server
    :return: None
    """
    # used to track how many chars we have
    letter_counter = 0
    exit_flag = False
    print("""
    __     __            _____   
    \ \   /"/u  ___     |_ " _|  
     \ \ / //  |_"_|      | |    
     /\ V /_,-. | |      /| |\   
    U  \_/-(_/U/| |\\u   u |_|U   
      //   .-,_|___|_,-._// \\_  
     (__)   \_)-' '-(_/(__) (__) 
                                 
    made by Innon Rivkin
    """)

    data_input = ""
    print(f"user: > ", end=" ", flush=True)
    while not exit_flag:
        char = None
        # getting key press
        while msvcrt.kbhit():
            char = msvcrt.getwch()

        if char is not None:
            # if char is "backspace" its removes the last char
            if char == "\b":
                if letter_counter > 0:
                    print("\b ", end="", flush=True)
                    letter_counter -= 1
                    data_input = data_input[:-1]
                else:
                    continue
            else:
                data_input += char

            print(char, end="", flush=True)

            if char not in "\n\t\r\b":
                letter_counter += 1

            if char in "\n\r":
                data_input = data_input[0:letter_counter]
                if '\b' in data_input:
                    # removing all backspaces from data input
                    data_input = data_input.translate({ord('\b'): None})

                print("")
                print(send_command(data_input, thread))

                if data_input == "exit":
                    return False
                # reset data input
                data_input = ""
                print("")
                letter_counter = 0
                print(f"user: > ", end=" ", flush=True)


def main():
    thread_user_socket = UserSocket()
    thread_user_socket.start()
    ui_thread = threading.Thread(target=ui, args=(thread_user_socket,))
    ui_thread.start()
    if not ui_thread:
        thread_user_socket.join()


if __name__ == '__main__':
    main()
