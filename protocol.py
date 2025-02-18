import data_base
import ipaddress

mydb = data_base.DataBase()
command_list = ["state", "delete", "execute", "copy", "dir", "help", "take_screenshot", "send_photo", "find_path"]


def add_ip_to_db(ip):
    """
    it is used to add the ip of a new client
    :param ip: string, an ip address
    :return: True
    :rtype:bool
    """
    mydb.add_ip_to_freecol(ip)
    return True


def additive_list():
    """
    gets all additives collections from the database
    :return: all additives collections
    :rtype: list
    """
    add_list = mydb.get_all_addcol()
    return add_list


def ip_list(col):
    """
    gets all ip addresses from a given additive collection
    :param col:
    :return: list containing all ips
    :rtype: list
    """
    ip_lst = []
    # checks if col is an additive or an ip (all additives have "-")
    if "-" in col:
        ip_lst = mydb.get_all_ip_from_addcol(col)
    else:
        ip_lst = [col]
    return ip_lst


def state():
    """
    gets all additive collections and the ips they contain
    :return: a string that contains the name of an additive and all ips it contains
    :rtype: str
    """
    resp = ""
    for a in additive_list():
        resp += f"{a}: {len(ip_list(a))}, {ip_list(a)}\n"
    return resp


def validate_ip_address(address):
    """
    checks if an ip address exist in the database
    :param address: string,  ip address
    :return: if address exist in database
    :rtype: bool
    """
    return address in ip_list("-free")


def is_additive(additives):
    """
    checks if each item in additives can be an additive
    :param additives: list of additives
    :return: if  each item in additives can be an additive
    :rtype: bool
    """

    def is_add_an_ip(address):
        """
        takes an address and checks if it in the right formation of an ip address
        :param address: an ip address
        :return: if it in the right formation of an ip address
        """
        try:
            ip = ipaddress.ip_address(address)
            return True
        except ValueError:
            return False

    for item in additives:
        if ("-" not in item[0] and (not is_add_an_ip(item))) or ("-" in item[0] and is_add_an_ip(item)):
            return False
    return True


def command_split(command):
    """
    takes a command and splits it to the command itself, params (file location mostly) and additives
    :param command: string, the raw command
    :return: if the raw command is right, the command itself, params and additives
    :rtype: tuple
    """
    additive = []
    com = ""
    param = ""
    # splits command into comm (the command itself) and everything else
    if len(command.split(maxsplit=1)) == 2:
        com, param = command.split(maxsplit=1)
        # checks if params are additives only
        if is_additive(param.split()):
            additive = param.split()
            return True, com, "None", additive

        if len(param.split(maxsplit=1)) == 2:
            param, add = param.split(maxsplit=1)
            additive = add.split()
            # checks if each element in additive has the formation of an additive
            for i in additive:
                if not is_additive([i]):
                    # if it doesn't it adds i to params
                    param += " " + i
                    additive.remove(i)
        return True, com, param, additive
    else:
        return False, com, param, additive


def help_func():
    """
    :return: string, all commands available and al additives available
    :rtype: str
    """
    return f"""commands: {command_list} \n additive: {list(additive_list())}."""


def check_param_is_additive(params):
    """
    checks each item in param exists in database
    :param params: list, contains additives
    :return: if an item is not a valid additive
    """
    for item in params:
        is_not_in_additive_list = str(item) not in additive_list()
        is_valid_ip = validate_ip_address(str(item))
        # checks if an item is ether an additive that is not  in database and is not a valid ip
        # or an additive that is in database and a valid ip
        if (is_not_in_additive_list and (not is_valid_ip)) or ((not is_not_in_additive_list) and is_valid_ip):
            return False
    return True


def check_additive(add):
    """
    checks if the additives list that is given is correct and according to our needs
    :param add: list , contains additive groups we wish to send our command to
    :return: if  everything is ok and a message if needed
    :rtype: bool, str
    """
    add_flag = True
    massage = ""
    if len(add) == 0:
        return False, "there are no additives"
    for item in add:
        if not check_param_is_additive([item]):
            add_flag = False
            massage = "additive is not in additive list"
            print("additive is not in additive list")
            break
    return add_flag, massage


def check_command(command, param, add):
    """
    checks if command is right and consist everything that is needed
    :param command: string, the command itself
    :param param: string, file location
    :param add: list, all additives groups we wish to send the command to
    :return: if every element is right and a message
    :rtype: bool, str
    """
    message = ""
    if command in command_list:
        if command == "help":
            return help_func()
        if param == "None":
            add_flag, message = check_additive(add)
            return (command in command_list) and add_flag, message
        else:
            add_flag, message = check_additive(add)

            return (command in command_list) and (param is not None) and add_flag, message
    else:
        return False, "command is not in command list"


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
