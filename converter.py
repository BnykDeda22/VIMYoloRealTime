import tkinter as tk
from tkinter import filedialog, messagebox
import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time
import math

bag_file = None
save_dir = None


def select_file():
    global bag_file
    bag_file = filedialog.askopenfilename(filetypes=[("Bag files", "*.bag")])
    if bag_file:
        file_label.config(text=f"Выбран файл: {os.path.basename(bag_file)}")
    else:
        file_label.config(text="Файл не выбран")


def select_directory():
    global save_dir
    save_dir = filedialog.askdirectory()
    if save_dir:
        directory_label.config(text=f"Выбрана директория: {save_dir}")
    else:
        directory_label.config(text="Директория не выбрана")


def bag_to_mp4(input_bag_file, output_mp4_file, spinner_canvas):
    try:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_device_from_file(input_bag_file)
        profile = pipeline.start(config)
        color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
        width = color_stream.width()
        height = color_stream.height()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_mp4_file, fourcc, 30.0, (width, height))

        processed_frames = 0
        # start_time = time.time()

        while True:
            frames = pipeline.wait_for_frames(timeout_ms=1000)

            if not frames:
                break

            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            video_writer.write(rgb_image)

            processed_frames += 1
            update_spinner(spinner_canvas, processed_frames)
            root.update_idletasks()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # elapsed_time = time.time() - start_time
            # if elapsed_time > 30:
            #     break

    finally:
        pipeline.stop()
        video_writer.release()
        cv2.destroyAllWindows()


def update_spinner(canvas, frame_count):
    canvas.delete("all")
    angle = (frame_count % 360) * 2  # Rotate faster
    x0, y0, x1, y1 = 10, 10, 40, 40
    canvas.create_arc(x0, y0, x1, y1, start=angle, extent=90, outline="blue", width=4)


def start_conversion():
    global bag_file, save_dir
    if not bag_file:
        messagebox.showerror("Ошибка", "Пожалуйста, выберите .bag файл!")
        return

    if not save_dir:
        messagebox.showerror("Ошибка", "Пожалуйста, выберите директорию для сохранения!")
        return

    base_filename = os.path.splitext(os.path.basename(bag_file))[0]
    output_mp4 = os.path.join(save_dir, f"{base_filename}.mp4")

    spinner_canvas.delete("all")  # Clear spinner before conversion
    bag_to_mp4(bag_file, output_mp4, spinner_canvas)
    messagebox.showinfo("Успех", f"Видео сохранено как {output_mp4}")


root = tk.Tk()
root.title("Конвертер .bag в .mp4")
root.geometry("400x400")

file_label = tk.Label(root, text="Файл не выбран", fg="black", font=("Helvetica", 12))
file_label.pack(pady=20)

select_button = tk.Button(root, text="Выбрать файл", command=select_file, width=20, height=2)
select_button.pack(pady=10)

directory_label = tk.Label(root, text="Директория не выбрана", fg="black", font=("Helvetica", 12))
directory_label.pack(pady=20)

directory_button = tk.Button(root, text="Выбрать директорию", command=select_directory, width=20, height=2)
directory_button.pack(pady=10)

convert_button = tk.Button(root, text="Начать запись", command=start_conversion, width=20, height=2)
convert_button.pack(pady=10)

spinner_canvas = tk.Canvas(root, width=50, height=50)
spinner_canvas.pack(pady=20)

root.mainloop()