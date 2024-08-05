import tkinter as tk
from tkinter import ttk
import time


class ManagementPage:
    def __init__(self, page, ser, camera):
        self.camera = camera

        self.apple_list = []
        self.auto_flag = False

        self.page = page
        self.ser = ser

        self.sent_data_label = ttk.Label(self.page, text="Sent: None", font=("Arial", 14, "bold"))
        self.sent_data_label.place(relx=.05, rely=.85, anchor="sw")

        self.received_data_label = ttk.Label(self.page, text="Received: None", font=("Arial", 14, "bold"))
        self.received_data_label.place(relx=.05, rely=.9, anchor="sw")

        self.create_port_widgets()
        self.create_home_widgets()
        self.create_other_input()
        self.create_get_position_button()
        self.create_catch_button()
        self.create_point_buttons()
        self.create_point_widgets()

        self.create_block_widgets("speed", placeX=.05, placeY=.3)
        self.create_block_widgets("position", placeX=.05, placeY=.5)

    def create_port_widgets(self):
        connection_frame = ttk.Frame(self.page, padding="20")
        connection_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        ttk.Label(connection_frame, text="Port:").grid(column=0, row=0, sticky=tk.W)
        port_combobox = ttk.Combobox(connection_frame, values=self.ser.ports)
        port_combobox.grid(column=1, row=0)

        ttk.Label(connection_frame, text="Baud Rate:").grid(column=0, row=1, sticky=tk.W)
        baudrate_combobox = ttk.Combobox(connection_frame, values=[9600, 19200, 38400, 57600, 115200], state="readonly")
        baudrate_combobox.grid(column=1, row=1)
        baudrate_combobox.current(4)

        self.create_port_button(connection_frame, port_combobox, baudrate_combobox)

    def create_port_button(self, frame, port_box, baudrate_box):
        connect_status_label = ttk.Label(frame, text="Not connected", font=("Arial", 14, "bold"))
        connect_status_label.grid(column=3, row=0, sticky=tk.W)

        ttk.Button(frame,
                   text="Open Port",
                   command=lambda: self.ser.connect_port(port_box.get(),
                                                         baudrate_box.get(),
                                                         connect_status_label,
                                                         self.page,
                                                         self.received_data_label)
                   ).grid(column=2, row=0)

        ttk.Button(frame,
                   text="Close Port",
                   command=lambda: self.ser.close_port(connect_status_label)
                   ).grid(column=2, row=1)

    def create_entry(self, frame, axis, type):
        coords = ["X", "Y", "Z"]
        var = tk.StringVar()
        ttk.Entry(frame, textvariable=var).grid(row=int(axis), column=0, sticky=(tk.W, tk.E))
        ttk.Button(frame,
                   text=f"Send {type.capitalize()} {coords[int(axis) - 1]}",
                   command=lambda: self.ser.send_command(f"${axis},{type},mm/s,set,{var.get()}*"
                                                         if type == "speed" else
                                                         f"${axis},goto,mm,{var.get()}*",
                                                         self.sent_data_label)
                   ).grid(row=int(axis), column=2)
        return var

    def create_block_widgets(self, type, placeX, placeY):
        frame = ttk.Frame(self.page, padding="10")
        frame.place(relx=placeX, rely=placeY, anchor="w")
        frame_label = ttk.Label(frame, text=type.capitalize(), font=("Arial", 16, "bold"))
        frame_label.grid(column=0, row=0, sticky=tk.W)

        pos_x = self.create_entry(frame, "1", type)
        pos_y = self.create_entry(frame, "2", type)
        pos_z = self.create_entry(frame, "3", type)

        if type == "position":
            ttk.Button(self.page,
                       text=f"Send All",
                       command=lambda: self.ser.send_command(f"$all,1,{pos_x.get()},2,{pos_y.get()},3,{pos_z.get()}*",
                                                             self.sent_data_label)
                       ).place(relx=placeX + 0.06, rely=placeY + 0.09)

    def create_home_widgets(self):
        home_combobox = ttk.Combobox(self.page, values=['ALL', 'X', 'Y', 'Z'], font=("Arial", 13, "bold"))
        home_combobox.place(relx=.8, rely=.875, anchor="sw")
        home_combobox.current(0)

        tk.Button(self.page,
                  text="Send Home",
                  command=lambda: self.send_home_command(home_combobox.get()),
                  font=("Arial", 12, "bold")
                  ).place(relx=.715, rely=.88, anchor="sw")

    def send_home_command(self, type):
        if type == "X" or type == "ALL":
            command = f"$1,home,find*"
            self.ser.send_command(command, self.sent_data_label)
            time.sleep(0.002)
        if type == "Y" or type == "ALL":
            command = f"$2,home,find*"
            self.ser.send_command(command, self.sent_data_label)
            time.sleep(0.002)
        if type == "Z" or type == "ALL":
            command = f"$3,home,find*"
            self.ser.send_command(command, self.sent_data_label)
            time.sleep(0.002)
        if type == "ALL" and self.ser.ser:
            self.sent_data_label.config(text="Go Home")

    def create_other_input(self):
        other_command_label = ttk.Label(self.page, text="Other command", font=("Arial", 16, "bold"))
        other_command_label.place(relx=.055, rely=.67, anchor="w")
        other_var = tk.StringVar()
        ttk.Entry(self.page, textvariable=other_var).place(relx=.057, rely=.71, anchor="w")
        ttk.Button(self.page,
                   text=f"Send command",
                   command=lambda: self.ser.send_command(other_var.get(), self.sent_data_label)
                   ).place(relx=.16, rely=.71, anchor="w")

    def get_position(self):
        commands = [f"$1,position,get,mm*", f"$2,position,get,mm*", f"$3,position,get,mm*"]
        for command in commands:
            self.ser.send_command(command, self.sent_data_label)
        self.sent_data_label.config(text="Get position command")

    def create_get_position_button(self):
        tk.Button(self.page,
                  text="Get Position MM",
                  command=self.get_position,
                  font=("Arial", 12, "bold")
                  ).place(relx=.555, rely=.88, anchor="sw")

    def create_catch_button(self):
        tk.Button(self.page,
                  text="Catch",
                  command=lambda: self.ser.send_command("open*", self.sent_data_label),
                  font=("Arial", 12, "bold")
                  ).place(relx=.665, rely=.88, anchor="sw")

    def auto_loop(self):
        if self.auto_flag:
            print(self.ser.received_data)
            if self.ser.received_data == "Next":
                print(123)
                self.ser.send_command(
                    f"$1,{self.apple_list[0][1][0]},2,{self.apple_list[0][1][1]},3,{self.apple_list[0][1][2]}*",
                    self.sent_data_label)
                print(f"$1,{self.apple_list[0][1][0]},2,{self.apple_list[0][1][1]},3,{self.apple_list[0][1][2]}*",
                      self.sent_data_label)
                self.ser.received_data = None
            self.page.after(1, self.auto_loop)

    def auto_assembly(self, button):
        if not self.auto_flag:
            button.config(text="Stop")
            self.auto_flag = True
            self.ser.send_command(
                f"$1,{self.apple_list[0][1][0]},2,{self.apple_list[0][1][1]},3,{self.apple_list[0][1][2]}*",
                self.sent_data_label)
            self.auto_loop()
        else:
            button.config(text="Auto")
            self.auto_flag = False

    def create_point_buttons(self):
        b1 = tk.Button(self.page,
                       text="Auto",
                       command=lambda: self.auto_assembly(b1),
                       font=("Arial", 12, "bold")
                       )
        b1.place(relx=0.72, rely=0.15)

        tk.Button(self.page,
                  text="Next",
                  command=lambda: self.ser.send_command(
                      f"$1,{self.apple_list[0][1][0]},2,{self.apple_list[0][1][1]},3,{self.apple_list[0][1][2]}*",
                      self.sent_data_label),
                  font=("Arial", 12, "bold")
                  ).place(relx=0.68, rely=0.15)

    def create_point_widgets(self):
        self.apple_list = self.camera.apple_list
        listbox = tk.Listbox(self.page, height=15, selectmode=tk.SINGLE, width=27, font=('Times', 14))
        listbox.place(relx=0.63, rely=0.22, anchor='nw')

        scrollbar = ttk.Scrollbar(self.page, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.place(relx=0.825, rely=0.22, relheight=0.48, anchor='nw')

        listbox.config(yscrollcommand=scrollbar.set)
        listbox.delete(0, tk.END)

        for i in range(len(self.apple_list)):
            listbox.insert(tk.END,
                           f"Apple {self.apple_list[i][0]}: x:{self.apple_list[i][1][0]}, y:{self.apple_list[i][1][1]}, z:{self.apple_list[i][1][2]}")
        self.page.after(1000, self.create_point_widgets)
