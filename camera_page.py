import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from camera import Camera
from detection import ODModel


def calculate_image_size(image):
    scale_factor = 0.72
    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    return new_width, new_height


class CameraPage:
    def __init__(self, page, ser):
        self.camera_label = None
        self.page = page
        self.ser = ser

        self.apple_list = []

        self.my_model = ODModel(path_to_weights=r"last_apples.pt")

        self.conf_threshold = tk.DoubleVar(value=0.5)
        self.conf_slider = tk.Scale(self.page, from_=0.0, to=1.0, resolution=0.01, orient='horizontal',
                                    variable=self.conf_threshold, font=("Arial", 12))
        self.conf_slider.place(relx=.65, rely=.02)

        self.image_type = 'color'

        self.camera_frame = ttk.Frame(self.page)
        self.camera_frame.place(relx=.40, rely=.1)

        self.switch_button = tk.Button(self.page, text="Переключить изображение", command=self.switch_image,
                                       font=("Arial", 12, "bold"))
        self.switch_button.place(relx=.6, rely=.7)

        self.sent_data_label = ttk.Label(self.page, text="Sent: None", font=("Arial", 14, "bold"))
        self.sent_data_label.place(relx=.05, rely=.9, anchor="sw")

        self.received_data_label = ttk.Label(self.page, text="Received: None", font=("Arial", 14, "bold"))
        self.received_data_label.place(relx=.05, rely=.95, anchor="sw")

        self.create_point_widgets()
        self.create_block_widgets("position", placeX=.05, placeY=.7)

        self.cap = Camera()
        self.update_camera_image()

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

    def update_camera_image(self):
        self.apple_list = []
        color_image, depth_image = self.cap.get_frame_stream()
        image_to_display = color_image if self.image_type == 'color' else depth_image
        processed_image = self.process_image(color_image, image_to_display)
        self.display_image(processed_image)
        self.apple_list = sorted(self.apple_list, key=lambda x: x[1][1])
        self.page.after(100, self.update_camera_image)

    def display_image(self, image_array):
        image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
        new_width, new_height = calculate_image_size(image)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.update_or_create_label(photo)

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
            distance, coordinates = self.cap.get_distance_and_coordinate_point(cx, cy)
            x, y, z = coordinates
            x, y, z = int(x), int(y), int(z)
            self.apple_list.append((number, (x, y, z)))
            cv2.rectangle(display_image, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(display_image, f"Apple {number} {score:.2}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return display_image

    def switch_image(self):
        self.image_type = 'depth' if self.image_type == 'color' else 'color'

    def create_point_widgets(self):
        self.apple_list = self.apple_list
        listbox = tk.Listbox(self.page, height=15, selectmode=tk.SINGLE, width=27, font=('Times', 14))
        listbox.place(relx=0.1, rely=0.1, anchor='nw')

        scrollbar = ttk.Scrollbar(self.page, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.place(relx=0.295, rely=0.1, relheight=0.48, anchor='nw')

        listbox.config(yscrollcommand=scrollbar.set)
        listbox.delete(0, tk.END)

        for i in range(len(self.apple_list)):
            listbox.insert(tk.END,
                           f"Apple {self.apple_list[i][0]}: x:{self.apple_list[i][1][0]}, y:{self.apple_list[i][1][1]}, z:{self.apple_list[i][1][2]}")
        self.page.after(1000, self.create_point_widgets)

