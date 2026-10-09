
import customtkinter as ctk


def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("AuraPlan")
    app.geometry("800x500")

    title = ctk.CTkLabel(
        app,
        text="AuraPlan",
        font=("Arial", 28, "bold"),
    )
    title.pack(pady=30)

    subtitle = ctk.CTkLabel(
        app,
        text="Your offline academic assistant",
        font=("Arial", 16),
    )
    subtitle.pack(pady=10)

    app.mainloop()


if __name__ == "__main__":
    main()
