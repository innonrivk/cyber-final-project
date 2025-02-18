# client_protocol is a file that contains purely what the client needs

def create_msg(data):
    """
    Create a valid protocol message, with length field
    :param data: string value
    :return: the data with length header
    :rtype: bool, str
    """
    data_len = len(str(data))
    if data_len > 9999 or data_len == 0:
        data = f"data len is bigger then 9999 or is 0"
        return False, f"{str(len(data)).zfill(4)}{data}"
    len_field = str(data_len).zfill(4)

    return True, f"{len_field}{data}"


def get_msg(my_socket):
    """
    Extract message from protocol, without the length field
    If length field does not include a number, returns False, "Error"
    :param my_socket: socket, it can be ether the  server socket or client socket
    :return: decoded data recived from socket
    :rtype: bool, str
    """
    lenght_field = ""
    data = ""
    try:
        while len(lenght_field) < 4:
            lenght_field += my_socket.recv(4 - len(lenght_field)).decode()

    except RuntimeError as exc_run:
        return False, "header wasnt sent properly"

    if not lenght_field.isdigit():
        return False, "error, length header is not valid"

    lenght_field = lenght_field.lstrip("0")
    try:
        while len(data) < int(lenght_field):
            data += my_socket.recv(int(lenght_field) - len(data)).decode()
    except UnicodeDecodeError as ex:
        print(ex)
        # cleaning socket
        my_socket.recv(int(lenght_field) - len(data))
        return True, "this error happens when there is a file that its  name is not in english. try other directory"

    return True, data

