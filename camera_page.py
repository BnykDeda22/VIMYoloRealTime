import cv2
import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk

from camera import Camera
from detection import ODModel


class CameraPage:
    def __init__(self, page, ser):
        self.rotation_angle = 0
        self.new_height = 600
        self.new_width = 800
        self.camera_label = None
        self.page = page
        self.ser = ser
        self.cap = None
        self.camera_running = False

        self.apple_list = []

        self.my_model = ODModel(path_to_weights=r"last_apples.pt")

        self.conf_threshold = tk.DoubleVar(value=0.5)
        self.conf_slider = tk.Scale(self.page, from_=0.0, to=1.0, resolution=0.01, orient='horizontal',
                                    variable=self.conf_threshold, font=("Arial", 12))
        self.conf_slider.place(relx=.64, rely=.02)

        self.image_type = 'color'

        self.camera_frame = ttk.Frame(self.page)
        self.camera_frame.place(relx=.40, rely=.1)

        self.switch_button = tk.Button(self.page, text="Переключить изображение", command=self.switch_image,
                                       font=("Arial", 12, "bold"), takefocus=False)
        self.switch_button.place(relx=.748, rely=.04)
        self.rotation_button = tk.Button(self.page, text="Поворот на 90°", command=self.turn_image,
                                         font=("Arial", 12, "bold"), takefocus=False)
        self.rotation_button.place(relx=.407, rely=.04)
        self.start_button = tk.Button(self.page, text="Запустить", command=self.start_camera,
                                      font=("Arial", 12, "bold"), takefocus=False)
        self.start_button.place(relx=.278, rely=.8, anchor="w")

        self.pause_button = tk.Button(self.page, text="Пауза", command=self.pause_camera,
                                      font=("Arial", 12, "bold"), takefocus=False)
        self.pause_button.place(relx=.278, rely=.85, anchor="w")

        self.stop_button = tk.Button(self.page, text="Остановить", command=self.stop_camera,
                                     font=("Arial", 12, "bold"), takefocus=False)
        self.stop_button.place(relx=.278, rely=.90, anchor="w")

        self.sent_data_label = ttk.Label(self.page, text="Sent: None", font=("Arial", 14, "bold"))
        self.sent_data_label.place(relx=.05, rely=.9, anchor="sw")

        self.received_data_label = ttk.Label(self.page, text="Received: None", font=("Arial", 14, "bold"))
        self.received_data_label.place(relx=.05, rely=.95, anchor="sw")

        self.create_points_widgets()
        self.create_point_buttons()
        self.create_block_widgets("position", placeX=.05, placeY=.7)
        self.create_other_input()

        self.placeholder_image = Image.open("VIM.png")
        self.display_placeholder_image()

    def turn_image(self):
        self.rotation_angle = (self.rotation_angle + 90) % 360
        if self.rotation_angle in [90, 270]:
            self.new_width, self.new_height = self.new_height, self.new_width
        else:
            self.new_width, self.new_height = 800, 600

    def start_camera(self):
        if not self.camera_running:
            self.cap = Camera()
            self.camera_running = True
            self.update_camera_image()

    def pause_camera(self):
        if self.camera_running:
            self.camera_running = False
            self.pause_button.config(text="Возобновить")
        else:
            self.camera_running = True
            self.pause_button.config(text="Пауза")
            self.update_camera_image()

    def stop_camera(self):
        self.camera_running = False
        if self.cap:
            self.cap.release()
        self.cap = None
        self.display_placeholder_image()

    def create_other_input(self):
        other_command_label = ttk.Label(self.page, text="Other command", font=("Arial", 16, "bold"))
        other_command_label.place(relx=.25, rely=.63, anchor="w")
        other_var = tk.StringVar()
        ttk.Entry(self.page, textvariable=other_var).place(relx=.263, rely=.67, anchor="w")
        ttk.Button(self.page,
                   text=f"Send command",
                   command=lambda: self.ser.send_command(other_var.get(), self.sent_data_label)
                   ).place(relx=.278, rely=.71, anchor="w")

    def create_block_widgets(self, type, placeX, placeY):
        frame = ttk.Frame(self.page, padding="10")
        frame.place(relx=placeX, rely=placeY, anchor="w")
        frame_label = ttk.Label(frame, text=type.capitalize(), font=("Arial", 16, "bold"))
        frame_label.grid(column=0, row=0, sticky=tk.W)

        pos_x = self.create_entry(frame, "1", type)
        pos_y = self.create_entry(frame, "2", type)
        pos_z = self.create_entry(frame, "3", type)
        pos_l = self.create_entry(frame, "4", type)

        if type == "position":
            ttk.Button(self.page,
                       text=f"Send All",
                       command=lambda: self.ser.send_command(
                           f"$a,goto,mm,{pos_x.get()},{pos_y.get()},{pos_z.get()},{pos_l.get()}*",
                           self.sent_data_label)
                       ).place(relx=placeX + 0.03, rely=placeY + 0.1)
            ttk.Button(self.page,
                       text=f"Send xyl",
                       command=lambda: self.ser.send_command(
                           f"$xyl,goto,mm,{pos_x.get()},{pos_y.get()},{pos_l.get()}*",
                           self.sent_data_label)
                       ).place(relx=placeX + 0.09, rely=placeY + 0.1)

    def create_entry(self, frame, axis, type):
        coords = ["x", "y", "z", "l"]
        var = tk.StringVar()
        ttk.Entry(frame, textvariable=var).grid(row=int(axis), column=0, sticky=(tk.W, tk.E))
        ttk.Button(frame,
                   text=f"Send {type.capitalize()} {coords[int(axis) - 1].upper()}",
                   command=lambda: self.ser.send_command(f"${axis},{type},mm/s,set,{var.get()}*"
                                                         if type == "speed" else
                                                         f"${coords[int(axis) - 1]},goto,mm,{var.get()}*",
                                                         self.sent_data_label)
                   ).grid(row=int(axis), column=2)
        return var

    def create_point_buttons(self):
        b1 = tk.Button(self.page,
                       text="Auto",
                       command=lambda: self.auto_assembly(b1),
                       font=("Arial", 12, "bold")
                       )
        b1.place(relx=0.15, rely=0.04)

        tk.Button(self.page,
                  text="Next",
                  command=lambda: self.ser.send_command(
                      f"$yolo,x,{self.apple_list[0][1][0]},y,{self.apple_list[0][1][1]},z,{self.apple_list[0][1][2]}*",
                      self.sent_data_label),
                  font=("Arial", 12, "bold")
                  ).place(relx=0.11, rely=0.04)

    def auto_loop(self):
        if self.auto_flag:
            if self.ser.received_data == "next":
                self.ser.send_command(f"$yolo,x,{self.apple_list[0][1][0]},y,{self.apple_list[0][1][1]},z,{self.apple_list[0][1][2]}*", self.sent_data_label)
                self.ser.received_data = None
            self.page.after(1, self.auto_loop)

    def auto_assembly(self, button):
        if not self.auto_flag:
            button.config(text="Stop")
            self.auto_flag = True
            self.ser.send_command(
                f"$yolo,x,{self.apple_list[0][1][0]},y,{self.apple_list[0][1][1]},z,{self.apple_list[0][1][2]}*",
                self.sent_data_label)
            self.auto_loop()
        else:
            button.config(text="Auto")
            self.auto_flag = False

    def display_placeholder_image(self):
        resized_image = self.placeholder_image.resize((self.new_width, self.new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        self.update_or_create_label(photo)

    def display_image(self, image_array):
        image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
        image = image.resize((self.new_width, self.new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.update_or_create_label(photo)

    def update_camera_image(self):
        if not self.camera_running:
            return

        self.apple_list = []
        color_image, depth_image = self.cap.get_frame_stream()
        image_to_display = color_image if self.image_type == 'color' else depth_image

        # Rotate the image using PIL and adjust dimensions
        image_pil = Image.fromarray(cv2.cvtColor(image_to_display, cv2.COLOR_BGR2RGB))
        image_pil = image_pil.rotate(self.rotation_angle, expand=True)
        image_to_display = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

        # Also rotate the color_image for processing
        color_image_pil = Image.fromarray(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
        color_image_pil = color_image_pil.rotate(self.rotation_angle, expand=True)
        color_image_rotated = cv2.cvtColor(np.array(color_image_pil), cv2.COLOR_RGB2BGR)

        # Process the rotated image
        processed_image = self.process_image(color_image_rotated, image_to_display)

        # Display the processed image
        self.display_image(processed_image)

        self.apple_list = sorted(self.apple_list, key=lambda item: (-item[1][1], item[1][0]))
        self.page.after(100, self.update_camera_image)

    def update_or_create_label(self, photo):
        if self.camera_label is None:
            self.camera_label = tk.Label(self.camera_frame, image=photo)
            self.camera_label.pack()
        else:
            self.camera_label.configure(image=photo)
        self.camera_label.image = photo

    def process_image(self, image_array, display_image):
        bboxes, class_ids, scores = self.my_model.predict(image_array, conf=self.conf_threshold.get())
        for number, (bbox, class_id, score) in enumerate(zip(bboxes, class_ids, scores), start=1):
            x1, y1, x2, y2 = bbox

            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            if self.rotation_angle == 90:
                cx, cy = 640 - cy, cx
            elif self.rotation_angle == 180:
                cx, cy = 640 - cx, 480 - cy
            elif self.rotation_angle == 270:
                cx, cy = cy, 480 - cx

            distance, coordinates = self.cap.get_distance_and_coordinate_point(cx, cy)
            x, y, z = coordinates
            x, y, z = int(x), int(y), int(z)
            if 0 <= x <= 1000 and 0 <= y <= 1600 and 0 <= z <= 750:
                self.apple_list.append((number, (x, y, z)))
                color = (255, 255, 255)
            else:
                color = (0, 0, 255)
            cv2.rectangle(display_image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display_image, f"Apple {number} {score:.2}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return display_image

    def switch_image(self):
        self.image_type = 'depth' if self.image_type == 'color' else 'color'

    def create_points_widgets(self):
        self.apple_list = self.apple_list
        listbox = tk.Listbox(self.page, height=15, selectmode=tk.SINGLE, width=27, font=('Times', 14))
        listbox.place(relx=0.05, rely=0.1, anchor='nw')

        for i in range(len(self.apple_list)):
            listbox.insert(tk.END,
                           f"Apple {self.apple_list[i][0]}: x:{self.apple_list[i][1][0]}, y:{self.apple_list[i][1][1]}, z:{self.apple_list[i][1][2]}")
        self.page.after(1000, self.create_points_widgets)

