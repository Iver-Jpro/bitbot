import tkinter as tk
import tkinter.messagebox as messagebox
import random
import serial

from PIL import Image, ImageTk

BG_COLOR = '#FFE1B7'

CARD_WIDTH = 400
CARD_HEIGHT = 400

class Card(tk.Label):
    def __init__(self, parent, index, **kwargs):

        self.code= random.choice('LRFU')
        self.load_image(self.code)
        super().__init__(parent, image=self.display_image, borderwidth=2, relief="ridge")

        self.index = index
        self.original_x = self.master.cards_x + index * CARD_WIDTH
        self.original_y = self.master.cards_y
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.slot = None

    def load_image(self, label):
        self.image = tk.PhotoImage(file=f"C:\\dev\\linerider\\storedFiles\\roborally {label}.png")
        # Calculate the subsample factors based on the image size and card size
        x_factor = self.image.width() // round(CARD_WIDTH/1.5)
        y_factor = self.image.height() // round(CARD_HEIGHT/1.5)
        self.display_image = self.image.subsample(x_factor, y_factor)


    def on_press(self, event):
        self.x = event.x
        self.y = event.y

    def on_drag(self, event):
        x = self.winfo_x() + event.x - self.x
        y = self.winfo_y() + event.y - self.y
        self.place(x=x, y=y)
        self.lift()  # Bring the card to the top of the stacking order

    def on_release(self, event):
        for slot in self.master.slots:
            if slot.is_over(self):
                if slot.card:
                    # If the slot already has a card, return it to its original position
                    slot.card.place(x=slot.card.original_x, y=slot.card.original_y)
                    slot.card.slot = None
                    slot.card.lift()
                if self.slot:
                    # If the dragged card was previously in a slot, clear that slot
                    self.slot.card = None
                self.slot = slot
                slot.card = self
                self.place(x=slot.winfo_x(), y=slot.winfo_y())
                self.lift()
                return
        self.place(x=self.original_x, y=self.original_y)

    def reset(self, label):
        self.load_image(label)
        self.config(image=self.display_image)
        self.place(x=self.original_x, y=self.original_y)
        self.slot = None
        self.lift()



class Slot(tk.Label):
    def __init__(self, parent, **kwargs):
        self.bg_image = tk.PhotoImage(file="C:\\dev\\linerider\\storedFiles\\roborally background.png")
        x_factor = self.bg_image.width() // round(CARD_WIDTH/1.5)
        y_factor = self.bg_image.height() // round(CARD_HEIGHT/1.5)
        self.display_image = self.bg_image.subsample(x_factor, y_factor)

        super().__init__(parent, image=self.display_image)
        self.card = None

    def is_over(self, card):
        card_center_x = card.winfo_x() + card.winfo_width() // 2
        card_center_y = card.winfo_y() + card.winfo_height() // 2
        return self.winfo_x() < card_center_x < self.winfo_x() + self.winfo_width() and \
            self.winfo_y() < card_center_y < self.winfo_y() + self.winfo_height()

class App(tk.Tk):

    ser = serial.Serial('COM5', 115200)  # Change 'COM3' to the appropriate COM port
    ser.timeout = 1

    def __init__(self):
        super().__init__()
        self.title("JRobotics Racing")
        self.geometry(f"{5 * CARD_WIDTH + 100}x{2 * CARD_HEIGHT + 100}")
        self.configure(bg=BG_COLOR)  # Set the window background color

        self.cards_x = 10
        self.cards_y = 10
        self.slots_x = 10
        self.slots_y = CARD_HEIGHT + 20
        self.cards = [Card(self, index=i, borderwidth=2, relief="ridge") for i in range(5)]
        self.slots = [Slot(self, borderwidth=2, relief="sunken") for _ in range(5)]

        for i, card in enumerate(self.cards):
            card.place(x=self.cards_x + i * CARD_WIDTH, y=self.cards_y)

        for i, slot in enumerate(self.slots):
            slot.place(x=self.slots_x + i * CARD_WIDTH, y=self.slots_y)

        button_font = ("Arial", 20)  # Adjust the font size as needed
        button_width = 20  # Adjust the width as needed
        button_height = 2  # Adjust the height as needed

        self.redraw_button = tk.Button(self, text="Redraw", command=self.redraw, bg=BG_COLOR, font=button_font, width=button_width, height=button_height)
        self.redraw_button.place(x=2 * CARD_WIDTH, y=2 * CARD_HEIGHT)

        self.execute_button = tk.Button(self, text="Execute", command=self.execute, bg=BG_COLOR, font=button_font, width=button_width, height=button_height)
        self.execute_button.place(x=3 * CARD_WIDTH, y=2 * CARD_HEIGHT)

        self.redraw()
    def redraw(self):
        labels = ["U"] + [random.choice("LRF") for _ in range(4)]
        random.shuffle(labels)
        for card, label in zip(self.cards, labels):
            card.reset(label)


    def execute(self):
        # Generate the command using only filled slots
        command = "".join([slot.card.code for slot in self.slots if slot.card is not None])

        print("Command:", command)
        self.ser.write(command.encode('utf-8'))

if __name__ == "__main__":
    app = App()
    app.mainloop()
