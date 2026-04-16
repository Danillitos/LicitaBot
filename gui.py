import customtkinter as ctk

#Pegando o tamanho do monitor
app = ctk.CTk()

monitor_width, monitor_height = app.winfo_screenwidth(), app.winfo_screenheight()
Reference_Monitor_Width = 1920
Reference_Monitor_Height = 1080
Reference_App_Width = 1440
Reference_App_Height = 900

width = (Reference_App_Width * monitor_width) // Reference_Monitor_Width
height = (Reference_App_Height * monitor_height) // Reference_Monitor_Height


app.title("LicitaBot")
app.geometry(f"{width}x{height}")
app.resizable(False, False)

button = ctk.CTkButton(app, text="my button")
button.grid(row=0, column=0, padx=20, pady=20)

ctk.set_default_color_theme("green")


app.mainloop()