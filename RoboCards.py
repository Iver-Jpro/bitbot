import tkinter as tk
import tkinter.messagebox as messagebox
import random
import serial



class Card(tk.Label):
    def __init__(self, parent, index, **kwargs):
        super().__init__(parent, text=random.choice("LRFU"), **kwargs)
        self.index = index
        self.original_x = self.master.cards_x + index * 60
        self.original_y = self.master.cards_y
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.slot = None

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
        self.place(x=self.original_x, y=self.original_y)
        self.slot = None
        self.config(text=label)
        self.lift()



class Slot(tk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
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
        self.title("Drag and Drop Cards")
        self.geometry("1400x1200")
        self.cards_x = 10
        self.cards_y = 10
        self.slots_x = 10
        self.slots_y = 100
        self.cards = [Card(self, index=i, borderwidth=2, relief="ridge", width=5, height=2) for i in range(5)]
        self.slots = [Slot(self, borderwidth=2, relief="sunken", width=5, height=2) for _ in range(5)]
        self.redraw_button = tk.Button(self, text="Redraw", command=self.redraw)
        self.redraw_button.place(x=180, y=150)

        for i, slot in enumerate(self.slots):
            slot.place(x=self.slots_x + i * 60, y=self.slots_y)

        self.execute_button = tk.Button(self, text="Execute", command=self.execute)
        self.execute_button.place(x=250, y=150)

        self.redraw()

    def redraw(self):
        labels = ["U"] + [random.choice("LRF") for _ in range(4)]
        random.shuffle(labels)
        for card, label in zip(self.cards, labels):
            card.reset(label)


    def execute(self):
        if any(slot.card is None for slot in self.slots):
            messagebox.showerror("Error", "All slots must be filled to execute.")
        else:
            command = "".join([slot.card.cget("text") for slot in self.slots])
            print("Command:", command)
            self.ser.write((command).encode('utf-8'))

if __name__ == "__main__":
    app = App()
    app.mainloop()
