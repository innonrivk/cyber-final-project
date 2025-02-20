import pymongo


class DataBase:

    def __init__(self):
        self._myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        # creating database
        self._mydb = self._myclient["mydatabase"]
        # the dictionary is created in order to have easy access to all collections
        self._addcol_dic = {}
        # getting all collections from database and storing it in dictionary
        for i in self._mydb.list_collection_names():
            self._addcol_dic[i] = self._mydb.get_collection(i)

    def check_addcol(self, add):
        """
        Checking if additive collection exist in the database
        :param add: additive, a name of a collection
        :return: if additive (collection) exist in database
        :rtype: bool
        """
        if add in list(self._addcol_dic.keys()):
            return True
        return False

    def add_addcol(self, add):
        """
         Adding an additive collection to the database
        :param add: additive, a name of a collection
        :return: if a new  additive (collection) was added to database
        :rtype: bool
        """
        if not self.check_addcol(add):
            # create new collection
            new_col = self._mydb[str(add)]
            # adds it to the dictionary
            self._addcol_dic[new_col.name] = new_col
            return True
        return False

    def get_all_addcol(self):
        """
        Saves all collections from database to self._addcol_dic again ("refreshing it")
        :return: all keys in  self._addcol_dic
        :rtype: dict.keys
        """
        # recreating self._addcol_dic
        self._addcol_dic = {}
        for i in self._mydb.list_collection_names():
            self._addcol_dic[i] = self._mydb.get_collection(i)
        return self._addcol_dic.keys()

    def delete_col(self, add):
        """
        deletes a collection from the database.
        :param add: additive, name of a collection
        :return: True. collection was deleted
        :rtype: bool
        """
        self._mydb.drop_collection(add)
        self._addcol_dic.pop(add)
        return True

    def add_ip_to_addcol(self, add, ip):
        """
        Adding an ip to additive collection
        :param add: additive, name of a collection
        :param ip: ip address of a computer.
        :return: confirmation message (used for debug)
        :rtype: str
        """
        query = {"ip": ip}
        if self.check_addcol(add):
            col = self._addcol_dic.get(add)
            # checking if ip exists in the collection
            if col.find_one(query) is None:
                # adding ip to collection
                col.insert_one(query)
                return "ip added"
            else:
                return "ip already exist"
        else:
            return "add_ip_to_addcol, additive wasn't found or was'nt put correctly"

    def get_all_ip_from_addcol(self, add):
        """
        finds all queries (ip addresses) which are stored in a given additive collection, and adds each ip address to
        a list
        :param add: string, name of an additive collection
        :return: list containing ip addresses.
        :rtype: list
        """
        ip_lst = []
        if self.check_addcol(add):
            col = self._addcol_dic.get(add)
            # col.find({},{"_id":0}) = getting all queries without their id value
            for i in col.find({}, {"_id": 0}):
                ip_lst.append(i.get("ip"))
            return ip_lst
        else:
            # error message in case "add" wasn't put correctly (for debug)
            return "get_all_ip_from_addcol, additive wasn't found or wasn't put correctly"

    def delete_ip_from_data_base(self, ip):
        """
        deletes all occurrences of the ip from the database
        :param ip: string, ip address
        :return:  confirmation message (used for debug)
        :rtype: str
        """
        # Goes through each collection and deletes the given ip from it.
        for i in self.get_all_addcol():
            self.delete_ip_from_addcol(i, ip)
        free_col = self._addcol_dic.get("-free")
        # deletes the ip from -free collection
        free_col.find_one_and_delete({"ip": ip})
        return f"deleted all occurrences of {ip} from data base"

    def add_ip_to_freecol(self, ip):
        """used when a new client connects to server. Adds to -free additive collection
        :param ip: string, ip address
        :return: confirmation message (used for debug)
        :rtype: str
        """
        self.add_addcol("-free")
        self.add_ip_to_addcol("-free", ip)
        return "ip added to -free collection"

    def delete_ip_from_addcol(self, add, ip):
        """
        deletes a given ip address from a given additive collection
        :param add: string, name of additive collection
        :param ip: string, ip address
        :return: confirmation message (used for debug)
        :rtype: str
        """
        
        if self.check_addcol(add):
            col = self._addcol_dic.get(add)
            resp = col.find_one_and_delete({"ip": ip})
            # checks if ip was found
            if resp is None:
                return f"ip wasn't found in {add}"
            # used to make sure it will still exist in the database
            resp = self.add_ip_to_freecol(ip)
            return f"ip has been deleted from: {add} and {resp}"
        else:
            # error message in case "add" wasn't put correctly (for debug)
            return "delete_ip_from_addcol, additive wasn't found or was'nt put correctly"
