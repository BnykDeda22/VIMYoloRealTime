from tkinter import Tk
from tkinter import ttk
from server import Server
from management_page import ManagementPage
from camera_page import CameraPage


class Application(Tk):
    def __init__(self):
        super().__init__()
        self.title("Манипулятор")

        self.tk.call('tk', 'scaling', 1.5)

        self.state('zoomed')

        self.ser = Server()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill='both')

        self.tab2 = ttk.Frame(self.notebook)
        cam = CameraPage(self.tab2, self.ser)

        self.tab1 = ttk.Frame(self.notebook)
        ManagementPage(self.tab1, self.ser, cam)

        self.notebook.add(self.tab1, text="Управление")
        self.notebook.add(self.tab2, text="Камера")


app = Application()
app.mainloop()
