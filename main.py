"""缝纫机导针及紧线机构运动仿真 —— 程序入口"""
import tkinter as tk
from gui import SewingMachineApp


def main():
    root = tk.Tk()
    root.title("缝纫机导针及紧线机构运动仿真")
    root.geometry("1280x720")
    root.configure(bg="#f0f0f0")
    app = SewingMachineApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
