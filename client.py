import socket
import threading
import pyautogui
import client_protocol
import glob
import os.path
import shutil
import subprocess
import base64

# set manually server computer ip
SERVER_IP = "10.0.0.13"


class Client:

    def __init__(self):
        self.IP = SERVER_IP
        self.PORT = 8080
        self.photo_path = r""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def check_server_request(command):
        """ takes a command  and splits it into comm (the command itself) and params (file locations)
        :param: command: string value, command and file location together
        :return: if params is None or if file location exist, comm, file location
        :rtype: bool, str, tuple """

        # split command
        comm, param = str(command).split(maxsplit=1)

        # check if param is None (in case no file location is needed)
        if param == "None":
            return True, comm, param
        else:
            # split file location in case there are two file locations
            file_location = tuple(str(param).split())
            # check if first location exist
            if os.path.exists(file_location[0]):
                return True, comm, file_location

            return False, comm, file_location

    def handle_server_request(self, command, params):

        """Create the response to the client, given the command is legal and params are OK
    :param command: String, the command to execute
    :param params:  tuple or None , the file locations (depends on the command)
    :return: the result of command or a confirmation message
    :rtype: str
    """

        response = "no client response"
        if command == "find_path":
            response = os.getcwd()
        # DIR command show all files in a given directory
        elif command == "dir":

            try:
                data = glob.glob(f"{params[0]}\\*.*")
                if len(data) != 0:
                    response = ""
                    for item in data:
                        response += item + "\n "
                else:
                    response = "there are no files in the directory, or path is wrong"
            except FileNotFoundError as ex:
                response = ex

        # DELETE command deletes a given file
        elif command == "delete":
            try:
                os.remove(params[0])
                response = f"{params[0]} was deleted"
            except FileNotFoundError as ex:
                response = ex

        # COPY command copies data from  the first file to second file
        elif command == "copy":
            try:
                shutil.copy(params[0], params[1])
                response = f"{params[0]} was copied to {params[1]}"
            except FileNotFoundError as ex1:
                response = ex1
            except IndexError as ex2:
                response = ex2

        # EXECUTE command execute a given file
        elif command == "execute":
            try:
                # starts a thread so client could still receive commands
                exe_thread = threading.Thread(target=subprocess.call, args=(params[0],))
                exe_thread.start()
                response = f"{params[0]} was executed"
            except FileNotFoundError as ex:
                response = ex

        #  TAKE_SCREENSHOT command takes a screenshot and saves it in PHOTO_PATH
        elif command == "take_screenshot":
            try:
                my_screenshot = pyautogui.screenshot()
                my_screenshot.save(self.photo_path)
                response = f"screen shot have been taken and been saved at {self.photo_path}"
            except FileNotFoundError as exf:
                response = f"client's PHOTO_PATH is not valid, please put a new path, error message: {exf}"

        # preparing the photo in order to send to server
        elif command == "send_photo":
            try:
                with open(self.photo_path, "rb") as file:
                    # translating img data to base64.
                    file_data = base64.b64encode(file.read()).decode()
                is_valid_response, img_length = client_protocol.create_msg(len(file_data))
                img_data = ""

                if not is_valid_response:
                    response = "img length data is not according to protocol"
                    return response

                while len(file_data) > 0:
                    # splitting  img data into chunks
                    chunk_data = file_data[:9999]
                    is_valid_response, data = client_protocol.create_msg(chunk_data)

                    if not is_valid_response:
                        response = "img  data is not according to protocol"
                        return response

                    img_data += data
                    file_data = file_data[9999:]
                response = f"{img_length}{img_data}"

            except FileNotFoundError as exs:
                response = f"server's PHOTO_PATH is not valid, please put a new path, error message: {exs}"

        return response

    def create_dir(self):
        """ Creates a folder in which screenshots will be saved at and sets self.photo_path as its path.
            if a folder already exists it just sets self.photo_path as its path
        """
        # get the path of the folder in which the script is located (aka ...\big_project\src\)
        current_path = os.getcwd()
        # adding to the path the screenshot folder
        final_directory = os.path.join(current_path, r'Screenshots')
        # checking if folder exist
        if not os.path.exists(final_directory):
            # creating the folder "screenshots"
            os.makedirs(final_directory)
        self.photo_path = f"{final_directory}\\screenShot.jpg"

    def main(self):
        self.create_dir()
        # connecting to server. NOTE: server ip need to be specified manually
        self.client_socket.connect((self.IP, self.PORT))
        while True:
            # receiving  msg from server
            valid_data, command = client_protocol.get_msg(self.client_socket)
            if valid_data:
                # checking command and params are valid
                valid_command, comm, params = self.check_server_request(command)
                if valid_command:
                    if comm == 'send_photo':
                        # the data that returned from "send_photo" already went through "client_protocol.create_msg()"
                        data = self.handle_server_request(comm, params)
                        self.client_socket.sendall(data.encode())
                        continue
                    # send command and param to handler where it will be executed
                    msg = self.handle_server_request(comm, params)
                    # creating and sending response to server
                    valid_msg, msg = client_protocol.create_msg(msg)
                    self.client_socket.sendall(msg.encode())
                else:
                    # sends error msg to server
                    valid_msg, msg = client_protocol.create_msg("file path wasn't found")
                    self.client_socket.sendall(msg.encode())
            else:
                # sends error msg to server
                valid_msg, msg = client_protocol.create_msg(f"{valid_data} {command}")
                self.client_socket.sendall(msg.encode())

        self.client_socket.close()


if __name__ == '__main__':
    my_client = Client()
    my_client.main()
