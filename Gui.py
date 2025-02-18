import tkinter as tk
import data_base


# a special button that has "hidden" value
class Button(tk.Button):
    def __init__(self, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)
        self.hidden = 0


def update_scroll_region():
    """
    updates canvas so scrollbar will change
    :return: None
    """
    print("canvas update_scroll_region")
    cvs_buttons.update_idletasks()
    frm_canvas.update_idletasks()
    cvs_buttons.config(scrollregion=cvs_buttons.bbox('all'))


def set_col_name(lst_box):
    """
    this func is used with open_addpopup_click so popup window won't be destroyed until collection is selected
     :param lst_box: tk.ListBox object
     :return: if a collection was selected
     :rtype: bool
     """
    if lst_box.curselection():
        selected_col_name.set(lst_box.get(lst_box.curselection()))
        return True
    return False


def open_addpopup_click(lst_box, top):
    """
    makes sure that popup window will be destroyed when collection has been chosen and submit button is pushed.
    :param lst_box: tk.ListBox object
    :param top: tk.TopLevel object
    :return: None
    """
    if set_col_name(lst_box):
        top.destroy()


def open_addpopup():
    """
    creates a popup window that contains a list box with all additives that exists  and a submit button
    :return:
    """
    top = tk.Toplevel(master=window, width=300, height=300)
    col_names = tk.Variable()
    col_names.set(list(lstbox_dic.keys()))
    lst_box = tk.Listbox(master=top, listvariable=col_names)
    lst_box.pack()
    button = tk.Button(master=top, text="submit", width=20,
                       command=lambda temp_box=lst_box, temp_top=top: open_addpopup_click(lst_box, top))
    button.pack()
    # waits for top to be closed
    window.wait_window(top)


def add_ip_to_col():
    """
    takes a selected ip and lets you add it to  a different collection using open_addpopup
    :return:None
    """
    # gets the current selected button name
    name = selected_btn_name.get()
    lstbox = lstbox_dic.get(name)
    if lstbox.curselection():
        # getting the ip the user selected
        ip = lstbox.get(lstbox.curselection())
        # opening window popup in order for the user to select a collection
        open_addpopup()
        if selected_col_name.get() != "":
            # getting the chosen collection
            col = selected_col_name.get()
            # getting the list box of the chosen collection
            lstbox2 = lstbox_dic.get(col)
            all_ip = lstbox2.get(0, tk.END)
            # checking if ip already exists in collection
            if ip not in all_ip:
                lstbox2.insert(tk.END, ip)
                # adding ip to the collection in the database
                db.add_ip_to_addcol(col, ip)
            selected_col_name.set("")
            # updating the chosen list box
            lstbox2.update_idletasks()


def delete_ip_all_lists(ip):
    """
    used with delete_click(), if the chosen collection is "-free" it deletes it from every collection in the database
    :param ip: string,  the ip we wish to delete
    :return: None
    """
    for lst in lstbox_dic.values():
        item = list(lst.get(0, tk.END))
        if ip in item:
            lst.delete(item.index(ip))


def delete_click():
    """
    deletes a chosen ip from the current collection we in
    :return: None
    """
    # getting the name of the current collection we are viewing
    name = selected_btn_name.get()
    # getting the collection's list box
    lstbox = lstbox_dic.get(name)
    # noting will happen until an ip is selected
    if lstbox.curselection():
        # getting the ip that the user has selected
        ip = lstbox.get(lstbox.curselection())
        # if the current collection is "-free" we go to delete_ip_all_lists()
        # else, we are removing it from the current collection, and we do the same in database
        if name == "-free":
            db.delete_ip_from_data_base(ip)
            delete_ip_all_lists(ip)
        else:
            db.delete_ip_from_addcol(name, str(ip))
            lstbox.delete(lstbox.curselection())


def delete_col_click():
    """
    deletes a chosen collection
    :return: None
    """
    # opening window popup in order for the user to select a collection
    open_addpopup()
    if selected_col_name.get() != "":
        col = selected_col_name.get()
        if col != "-free":
            # removing everything that is related to those collections
            button = button_dic.get(col)
            lstbox_dic.pop(col)
            button_dic.pop(col)
            btn_frame_dic.pop(col)
            button.pack_forget()
            update_scroll_region()
            button.destroy()
            # deletes the collection from database
            db.delete_col(col)
        selected_col_name.set("")


def refresh_freecol():
    """
    refreshes  -free collection each time it is chosen so new ips will appear
    :return: None
    """
    ip_list = tk.Variable()
    # getting all ips of -free collection from database
    ip_list.set(db.get_all_ip_from_addcol("-free"))
    lstbox = lstbox_dic["-free"]
    lstbox.delete(0,tk.END)
    # reinserting everything back to -free list box
    for ip in ip_list.get():
        lstbox.insert(tk.END,ip)
    lstbox_dic["-free"] = lstbox
    btn_frm = btn_frame_dic["-free"]
    btn_frm.update()


def on_click(btn):
    """
    this makes that when you click on a collection button, the button you chose
    will  be sunken and al its related frames will be shown. Also, it makes sure
    the other buttons will be raised, so you'll know in which collection you currently at
    :param btn: tk.Button object of the button you pressed
    :return: None
    """
    name = btn["text"]
    selected_btn_name.set(name)
    button_frame = btn_frame_dic.get(name)
    # raising all others buttons
    for f in btn_frame_dic.keys():
        if f != name:
            btn_frame_dic.get(f).pack_forget()
            button = button_dic.get(f)
            button.config(relief="raised")
            button.hidden = 0
    # if the chosen button is raised it will be sunk, and it's frame will be shown
    if btn.hidden == 0:
        button_frame.pack(fill=tk.BOTH, expand=True)
        # if the button is "-free" it will refresh its list
        if "-free" in name:
            refresh_freecol()
        btn.config(relief="sunken")
        btn.hidden = 1
        addcol_frm.grid_forget()
        opt_frm.grid(column=0, row=0, rowspan=3, sticky="nsew")
    else:
        # if the button is sunk  it will raised it and  its related frames will disappear
        button_frame.pack_forget()
        btn.config(relief="raised")
        btn.hidden = 0
        opt_frm.grid_forget()
        addcol_frm.grid(column=0, row=0, rowspan=3, sticky="nsew")


def add_name_button():
    """
    this lets you add a news collection which can be used to store ip addresses.
    NOTE, if the new collection is empty the database will not save it.
    :return: None
    """
    # gets new collection name from entry
    name = ent_addname.get()
    name = name.strip()

    if "-" == str(name)[0] and len(name.split()) == 1:
        # checks if name already exists
        if name not in button_dic.keys():
            # creates all the needed things like lis box and ect....
            new_btn = Button(master=frm_canvas, text=name, pady=2, padx=5, width=10)
            new_btn.config(command=lambda temp_name=new_btn: on_click(temp_name))
            btn_frm = tk.Frame(master=frm_downleft, width=400, height=300)
            btn_frame_dic[name] = btn_frm
            button_dic[name] = new_btn
            lstbox = tk.Listbox(master=btn_frm, width=50, height=20)
            lstbox_dic[name] = lstbox
            db.add_addcol(name)
            lstbox.pack()
            new_btn.pack(fill=tk.BOTH, side=tk.LEFT, padx=10, pady=5)
            update_scroll_region()
    # clears the entry
    ent_addname.delete(0, tk.END)


def add_col_from_db():
    """
    gets all collection from database and the ip addresses they have,
    then creates all needed frames and a list box for the addresses to be stored at
     :return: None
    """
    # gets all collections from database
    names = list(db.get_all_addcol())
    if names == list(button_dic.keys()):
        return

    if names:
        # sets it so -free wil always be easily accessible
        free_place = names.index("-free")
        names[0], names[free_place] = names[int(free_place)], names[0]
        # for each collection it creates a button, frames and a list box
        for name in names:
            # button is created
            new_btn = Button(master=frm_canvas, text=name, pady=2, padx=5, width=10)
            new_btn.config(command=lambda temp_name=new_btn: on_click(temp_name))
            button_dic[name] = new_btn
            # button frames is created
            btn_frm = tk.Frame(master=frm_downleft, width=400, height=300)
            btn_frame_dic[name] = btn_frm
            # getting all ip addresses from database and saving it in a list box
            ip_list = tk.Variable()
            ip_list.set(db.get_all_ip_from_addcol(name))
            lstbox = tk.Listbox(master=btn_frm, listvariable=ip_list, width=50, height=20)
            lstbox_dic[name] = lstbox
            # packing everything
            lstbox.pack()
            new_btn.pack(fill=tk.BOTH, side=tk.LEFT, padx=10, pady=5, expand=True)
            update_scroll_region()


# creating the root window
window = tk.Tk()
# dictonarys for accessing needed objects
btn_frame_dic = {}
lstbox_dic = {}
button_dic = {}
# db is needed in order to access the database
db = data_base.DataBase()

# those Vars hold the the button that was selected
# and collection that was selected (from the popup window)
selected_btn_name = tk.StringVar()
selected_col_name = tk.StringVar()
selected_col_name.set("")
# creating the main frames that divide the window to constant parts and will host other frames
frm_upleft = tk.Frame(window, width=400, height=150, borderwidth=5)
frm_downleft = tk.Frame(window, relief="sunken", width=400, height=300, borderwidth=5)
frm_right = tk.Frame(master=window, relief="ridge", width=750, height=300, borderwidth=5)

# the canvas hosts the collection buttons and displays them
cvs_buttons = tk.Canvas(frm_upleft, width=400, height=50)
horibar = tk.Scrollbar(frm_upleft)
frm_canvas = tk.Frame(cvs_buttons, width=400, height=50)

# addcol_frm is hosted in the "right frame" and contain the widgets for adding and deleting collections
addcol_frm = tk.Frame(frm_right, width=750, height=300)
del_col_btn = tk.Button(master=frm_right, text="delete collection", width=20, command=delete_col_click)
lbl_addname = tk.Label(master=addcol_frm, text="add collection")
ent_addname = tk.Entry(master=addcol_frm)
btn_add = Button(master=addcol_frm, text="Add", command=add_name_button)


# the opt_frm is hosted in the "right frame" and holds the widgets needed to delete and add an ip
# it appears when a collection button is pressed
opt_frm = tk.Frame(frm_right, width=750, height=300)
btn_addip = tk.Button(master=opt_frm, text="Add ip", command=add_ip_to_col)
btn_del = tk.Button(master=opt_frm, text="delete ip", command=delete_click)

# main frames griding
frm_upleft.grid(column=0, row=0, columnspan=2, sticky="sewn")
frm_downleft.grid(column=0, row=1, columnspan=2, rowspan=2, sticky="nsew")
frm_right.grid(column=2, row=0, rowspan=3, sticky="nsew")
addcol_frm.grid(column=0, row=0, rowspan=3, sticky="nsew")

# setting the size and setting for the collection button's canvas and scrollbar
cvs_buttons.config(width=400, height=50)
cvs_buttons.config(xscrollcommand=horibar.set)
horibar.config(orient=tk.HORIZONTAL, command=cvs_buttons.xview)
cvs_buttons.grid(column=0, row=0, columnspan=2, sticky="sewn")
horibar.grid(column=0, row=1, columnspan=2, sticky="ew")
cvs_buttons.create_window(0, 0, window=frm_canvas, anchor=tk.NW)

# once the canvas is ready it adds all collection from database to gui
add_col_from_db()

# griding all addcol_frm's widgets
del_col_btn.grid(column=0, row=0, sticky="new")
lbl_addname.grid(column=0, row=1, sticky="s")
ent_addname.grid(column=0, row=2, sticky="new", pady=10)
btn_add.grid(column=0, row=3, sticky="nesw")

# griding all opt_frm widgets
btn_addip.grid(column=0, row=1, sticky="nesw")
btn_del.grid(column=0, row=2, sticky="nesw")


# configuring all row and columns of frames
frm_right.columnconfigure(0, weight=1)
frm_right.rowconfigure(0, weight=1)
frm_right.rowconfigure(1, weight=1)
frm_right.rowconfigure(2, weight=1)

addcol_frm.columnconfigure(0, weight=1)
addcol_frm.rowconfigure(0, weight=1)
addcol_frm.rowconfigure(1, weight=1)
addcol_frm.rowconfigure(2, weight=1)

opt_frm.columnconfigure(0, weight=1)
opt_frm.rowconfigure(0, weight=1)
opt_frm.rowconfigure(1, weight=1)
opt_frm.rowconfigure(2, weight=1)

frm_upleft.columnconfigure(0, weight=1)
frm_upleft.columnconfigure(1, weight=1)
frm_upleft.rowconfigure(0, weight=1)
frm_upleft.rowconfigure(1, weight=1)

frm_downleft.columnconfigure(0, weight=1)
frm_downleft.columnconfigure(1, weight=1)
frm_downleft.rowconfigure(0, weight=1)
frm_downleft.rowconfigure(1, weight=1)

window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)

frm_canvas.update()
cvs_buttons.update()
window.mainloop()
