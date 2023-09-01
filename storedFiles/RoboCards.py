import os
import random
import sys
import threading
import tkinter as tk

import serial

from PIL import Image, ImageTk

CARD_CODES = 'LRFU2'

CARDS_DRAW = 6
NUM_SLOTS = 4

ROUND_TIME = 30

BG_COLOR = '#FFE1B7'
ARCADE_FONT = ("Press Start 2P", 20)  # Adjust the size as needed
GAME_OVER_FONT = ("Press Start 2P", 50)  # Adjust the size as needed

CARD_WIDTH = 400
CARD_HEIGHT = 400

SCALE = 1.0

MAX_PLAYS = 3

USB_PORT = 'COM5'

# Iterate through command-line arguments to find an override for USB_PORT
for i in range(1, len(sys.argv)):
    if sys.argv[i] == '--usb_port':
        try:
            USB_PORT = sys.argv[i + 1]
        except IndexError:
            print("Error: --usb_port argument provided but no value given.")
            sys.exit(1)

    if sys.argv[i] == '--scale':
        try:
            SCALE = float(sys.argv[i + 1])
            CARD_WIDTH = round(CARD_WIDTH * SCALE)
            CARD_HEIGHT = round(CARD_HEIGHT * SCALE)
            ARCADE_FONT = ("Press Start 2P", round(20 * SCALE))
            GAME_OVER_FONT = ("Press Start 2P", round(50 * SCALE))
        except IndexError:
            print("Error: --scale argument provided but no value given.")
            sys.exit(1)

print(f'Using USB Port: {USB_PORT}')


class Nexus():
    xPosition = ""
    yPosition = ""
    points = 0

    def __init__(self, x, y, points):
        self.xPosition = x
        self.yPosition = y
        self.points = points


gameboard = {
    1944688892: Nexus("A", 1, 1),
    2214546422: Nexus("A", 2, 2),
    3287137276: Nexus("A", 3, 3),
    871609077: Nexus("A", 4, 0),
    4081897461: Nexus("A", 5, 1),
    3004060668: Nexus("B", 1, 2),
    1944446709: Nexus("B", 2, 1),
    1676494582: Nexus("B", 3, -2),
    329147126: Nexus("B", 4, 1),
    3543034358: Nexus("B", 5, 2),
    601800188: Nexus("C", 1, -3),
    864110588: Nexus("C", 2, 2),
    3010023420: Nexus("C", 3, 1),
    2481922550: Nexus("C", 4, 2),
    2735262972: Nexus("C", 5, 1),
    3813451004: Nexus("D", 1, 1),
    3019725814: Nexus("D", 2, 1),
    1667070454: Nexus("D", 3, 1),
    868100604: Nexus("D", 4, 2),
    3278031868: Nexus("D", 5, -1),
    869677308: Nexus("E", 1, 6),
    3279192572: Nexus("E", 2, 2),
    2212260348: Nexus("E", 3, 1),
    1945225468: Nexus("E", 4, 1),
    1664226294: Nexus("E", 5, 1)
}

card_image_cache = {}


def load_card_image(label):
    cardimage = tk.PhotoImage(file=f"roborally {label}.png")
    x_factor = cardimage.width() // round(CARD_WIDTH / 1.5)
    y_factor = cardimage.height() // round(CARD_HEIGHT / 1.5)
    card_image_cache[label] = cardimage.subsample(x_factor, y_factor)


class Card(tk.Label):
    def __init__(self, parent, index, **kwargs):

        self.code = random.choice(CARD_CODES)
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
        global card_image_cache
        if not label in card_image_cache:
            load_card_image(label)

        self.display_image = card_image_cache[label]

        # Calculate the subsample factors based on the image size and card size

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
        # If the card is not placed over any slot, reset its previous slot (if any)
        if self.slot:
            self.slot.card = None
            self.slot = None
        self.place(x=self.original_x, y=self.original_y)

    def reset(self, label):
        self.code = label
        self.load_image(label)
        self.config(image=self.display_image)
        self.place(x=self.original_x, y=self.original_y)
        self.slot = None
        self.lift()


class Slot(tk.Label):
    def __init__(self, parent, **kwargs):
        self.bg_image = tk.PhotoImage(file="roborally background.png")
        x_factor = self.bg_image.width() // round(CARD_WIDTH / 1.5)
        y_factor = self.bg_image.height() // round(CARD_HEIGHT / 1.5)
        self.display_image = self.bg_image.subsample(x_factor, y_factor)

        super().__init__(parent, image=self.display_image)
        self.card = None

    def is_over(self, card):
        card_center_x = card.winfo_x() + card.winfo_width() // 2
        card_center_y = card.winfo_y() + card.winfo_height() // 2
        return self.winfo_x() < card_center_x < self.winfo_x() + self.winfo_width() and \
            self.winfo_y() < card_center_y < self.winfo_y() + self.winfo_height()


class GridWithPoint():
    def __init__(self, parent, x_position, y_position, grid_image_path, point_image_path):
        self.grid_height = CARD_HEIGHT * 2
        self.grid_width = CARD_WIDTH * 2

        self.canvas = tk.Canvas(parent, width=self.grid_width, height=self.grid_height, bg="orange")
        self.bg_image = tk.PhotoImage(file="circuit-bg.png")
        self.canvas.create_image(0, 0, image=self.bg_image, anchor=tk.NW)

        self.canvas.place(x=x_position, y=y_position)

        # Load and scale the grid image
        grid_image = Image.open(grid_image_path)
        grid_image = grid_image.resize((CARD_WIDTH * 2, CARD_HEIGHT * 2))
        self.grid_photo = ImageTk.PhotoImage(grid_image)

        # Load the robot image
        robo_image = Image.open("clownbot.png")
        robo_image = robo_image.resize((CARD_WIDTH // 3, CARD_HEIGHT // 3))

        self.robot_photo = ImageTk.PhotoImage(robo_image)

        # load the point images
        point_values = {n.points for n in gameboard.values()}
        self.point_images = {}
        for point in point_values:
            pngFilename = "point" + str(point) + ".png"
            if not os.path.exists(pngFilename):
                continue
            point_image = Image.open(pngFilename)
            point_image = point_image.resize((CARD_WIDTH // 10, CARD_HEIGHT // 10))
            self.point_images[point] = ImageTk.PhotoImage(point_image)

        # Create a label for the grid image

        self.canvas.create_image(0, 0, image=self.grid_photo, anchor=tk.NW)

        self.draw_robot("A", 4)

    def draw_robot(self, x, y):
        point_x, point_y = self.calculate_grid_pos(x, y, size=3)
        self.canvas.delete("robot")
        self.canvas.create_image(point_x, point_y, image=self.robot_photo, anchor=tk.NW, tags="robot")

    def draw_point(self, x, y, id):
        points = gameboard[id].points

        if points == 0:
            return

        point_x, point_y = self.calculate_grid_pos(x, y)

        # Encode the tag
        tag = "point" + str(x) + str(y)

        # Update the red point position
        self.canvas.create_image(point_x, point_y, image=self.point_images[points], anchor=tk.NW, tags=tag)

    def calculate_grid_pos(self, x, y, size=1):
        # Convert A-E to numerical coordinates
        xPos = 6 - (ord(x.upper()) - ord('A') + 1)
        yPos = y + 1
        # Calculate the pixel position based on the grid size
        point_x = (self.grid_width // 6) * xPos - CARD_WIDTH // 20 * size
        point_y = (self.grid_height // 6) * (yPos - 1) - CARD_HEIGHT // 20 * size
        return point_x, point_y

    def remove_point(self, x, y):
        tag = "point" + str(x) + str(y)
        self.canvas.delete(tag)


def loadAllCardFiles():
    global card_image_cache
    for code in CARD_CODES:
        load_card_image(code)


class App(tk.Tk):
    ser = serial.Serial(USB_PORT, 115200)  # Change 'COM3' to the appropriate COM port
    ser.timeout = 1

    def __init__(self):
        super().__init__()

        self.seen_cards = []
        self.play_count = 0
        self.title("JRobotics Racing")
        self.geometry(f"{7 * CARD_WIDTH + 100}x{5 * CARD_HEIGHT}")
        self.configure(bg=BG_COLOR)  # Set the window background color

        loadAllCardFiles()

        # Load the background image
        self.bg_image = tk.PhotoImage(file="roborally BG2.png")

        # Create a canvas for the background
        self.canvas = tk.Canvas(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ensure the canvas covers the entire window

        # Tile the image on the canvas
        for x in range(0, self.winfo_screenwidth(), self.bg_image.width()):
            for y in range(0, self.winfo_screenheight(), self.bg_image.height()):
                self.canvas.create_image(x, y, image=self.bg_image, anchor=tk.NW)

        self.cards_x = 10
        self.cards_y = 10
        self.slots_x = 10
        self.slots_y = CARD_HEIGHT + 20
        self.cards = [Card(self, index=i, borderwidth=2, relief="ridge") for i in range(7)]

        self.slots = [Slot(self, borderwidth=2, relief="sunken") for _ in range(NUM_SLOTS)]

        for i, slot in enumerate(self.slots):
            slot.place(x=self.slots_x + i * CARD_WIDTH + CARD_WIDTH, y=self.slots_y)

        button_font = ARCADE_FONT  # Adjust the font size as needed
        button_width = 15  # Adjust the width as needed
        button_height = 2  # Adjust the height as needed

        self.draw_button = tk.Button(self, text="Draw", command=self.draw, bg=BG_COLOR, font=button_font, width=button_width, height=button_height)
        drawbuttonY = 2 * CARD_HEIGHT
        self.draw_button.place(x=1.3 * CARD_WIDTH + CARD_WIDTH, y=drawbuttonY)

        self.execute_button = tk.Button(self, text="Execute", command=self.execute, bg=BG_COLOR, font=button_font, width=button_width, height=button_height)
        self.execute_button.place(x=2.7 * CARD_WIDTH + CARD_WIDTH, y=2 * CARD_HEIGHT)

        # Disable the "Execute" button when the app starts up
        self.execute_button.config(state=tk.DISABLED)

        # Timer label
        self.remaining_time = tk.IntVar(value=ROUND_TIME)
        self.timer_text = tk.StringVar(value=f"Time left: {ROUND_TIME}")
        self.timer_label = tk.Label(self, textvariable=self.timer_text, font=ARCADE_FONT, bg=BG_COLOR)
        self.timer_label.place(x=CARD_WIDTH / 4 + CARD_WIDTH, y=2 * CARD_HEIGHT)

        # Timer state
        self.timer_running = False

        # Initialize the score
        self.score = 0

        # Create a StringVar to hold the score text
        self.score_text = tk.StringVar()
        self.update_score_display()

        # Create a Label to display the score
        self.score_label = tk.Label(self, textvariable=self.score_text, font=ARCADE_FONT, bg=BG_COLOR)
        self.score_label.place(x=4 * CARD_WIDTH + CARD_WIDTH, y=2 * CARD_HEIGHT)

        # Create a label for the "GAME OVER" text
        self.game_over_label = tk.Label(self, text="GAME OVER\n\nFinal Score: X", font=GAME_OVER_FONT, fg="red", bg='blue')
        self.game_over_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.game_over_label.lower()  # Send it to the back initially

        # Set up the high score functionality
        self.cursor_visible = False
        self.is_high_score = False
        self.name = ""
        self.bind("<Key>", self.capture_key)

        # Initially, don't allow the click event to hide the text
        self.allow_hide = False

        # Create an instance of GridWithPoint and place it below the Draw button
        self.grid_with_point = GridWithPoint(self, CARD_WIDTH, drawbuttonY + 100, "6x6-grid3.png", "point1.png")

        self.place_points_markers()

    def update_score_display(self):
        """Update the score display."""
        self.score_text.set(f"Score: {self.score}")

    def draw_cards(self):
        """Return a list of card labels for a new draw."""
        # Possible card types
        card_types = ["L", "R", "F"]

        # Decide if we should draw a "2" or "3" card
        special_cards = [None, "2", "3"]
        drawn_special_card = random.choice(special_cards)
        drawn_cards = [drawn_special_card] if drawn_special_card else []

        # Decide if we should draw a "U" card
        if random.choice([True, False]):
            drawn_cards.append("U")

        # Fill the rest of the slots with the other card types
        for _ in range(CARDS_DRAW - len(drawn_cards)):
            drawn_cards.append(random.choice(card_types))

        # Shuffle the list to randomize the order
        random.shuffle(drawn_cards)

        return drawn_cards

    def draw(self):
        """Draw new cards."""
        labels = self.draw_cards()
        for card, label in zip(self.cards, labels):
            card.reset(label)
        for card, label in zip(self.cards, labels):
            card.reset(label)
            # Place the card if it hasn't been placed yet
            if not card.winfo_ismapped():
                card.place(x=self.cards_x + card.index * CARD_WIDTH, y=self.cards_y)

        for slot in self.slots:
            slot.card = None

        self.execute_button.config(state=tk.NORMAL)

        self.remaining_time.set(ROUND_TIME)
        self.timer_running = True
        self.update_timer()

        self.draw_button.config(state=tk.DISABLED)

    def update_timer(self):
        if self.timer_running:
            current_time = self.remaining_time.get()
            if current_time > 0:
                self.remaining_time.set(current_time - 1)
                self.timer_text.set(f"Time left: {current_time - 1}")
                # Call this function again after 1000ms (1 second)
                self.after(1000, self.update_timer)
            else:
                self.execute()

    def execute(self):
        # Don't do anything if no cards have been placed

        if all(x.card is None for x in self.slots):
            self.play_count += 1
            self.execute_button.config(state=tk.DISABLED)
            self.timer_running = False

            if self.play_count >= MAX_PLAYS:
                self.game_over(high_score=self.score > 0)
            else:
                self.draw_button.config(state=tk.NORMAL)

            return

        self.execute_button.config(state=tk.DISABLED)

        # Generate the command using only filled slots
        cardlabels = "".join([slot.card.code for slot in self.slots if slot.card is not None])
        if self.play_count == 0:
            command = "S"
        else:
            command = ""
        command = command + cardlabels.replace("2", "FF").replace("3", "FFF")
        self.timer_running = False
        print("Command:", command)
        self.ser.write(command.encode('utf-8'))
        # self.draw_button.config(state=tk.NORMAL)

        thread = threading.Thread(target=self.listenToTheRadio)
        thread.start()

    def game_over(self, high_score=True):
        """Display the 'GAME OVER' text."""
        self.name = ""
        if not high_score:
            self.game_over_label.config(text=f"GAME OVER\n\nFinal Score: {self.score}")
            self.bind("<Button-1>", self.hide_game_over)  # Bind the click event
            self.after(300, self.enable_hide)  # After 0.3 seconds, allow the click event to hide the text
        else:
            self.game_over_label.config(text=f"GAME OVER\n\nFinal Score: {self.score}\n\nYou have a high score!\nEnter your name:")
            self.is_high_score = True
            self.toggle_cursor()
        self.game_over_label.lift()  # Bring the canvas to the front

        self.play_count = 0
        self.seen_cards = []
        self.draw_button.config(state=tk.DISABLED)

    def update_game_over_label(self):
        cursor = "|" if self.cursor_visible else " "
        self.game_over_label.config(text=f"GAME OVER\n\nFinal Score: {self.score}\n\nYou have a high score!\n\nEnter your name:\n {self.name}{cursor}")
        # self.game_over_label.config(text=f"GAME OVER\n\nName: {self.name}{cursor}")

    def toggle_cursor(self):
        if not self.is_high_score:
            return
        self.cursor_visible = not self.cursor_visible
        self.update_game_over_label()
        self.after(500, self.toggle_cursor)

    def capture_key(self, event):
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ"
        if len(self.name) < 5 or event.keysym == "BackSpace":
            if event.keysym == "BackSpace":
                self.name = self.name[:-1]
            elif (event.keysym == "Return"):
                if len(self.name) > 0:
                    self.submit_high_score()
                    return
            elif len(event.char) == 1 and event.char.upper() in allowed_chars:
                self.name += event.char.upper()

            self.update_game_over_label()

    def submit_high_score(self):
        name = self.name
        self.name = ""

        if len(name) > 5:
            name = name[:5]
        print(f"High score submitted with name: {name}")
        self.allow_hide = True
        self.is_high_score = False
        self.hide_game_over(None)

    def enable_hide(self):
        """Allow the 'GAME OVER' text to be hidden."""
        self.allow_hide = True

    def hide_game_over(self, event):
        """Hide the 'GAME OVER' text."""
        if self.allow_hide:
            tk.Misc.lower(self.game_over_label, self.canvas)  # Send the canvas to the back
            self.draw_button.config(state=tk.NORMAL)
            self.score = 0
            self.update_score_display()
            self.place_points_markers()

    def listenToTheRadio(self):
        global gameboard

        while not self.timer_running:

            if self.ser.in_waiting > 1:

                usbMessage = self.ser.read(64).decode('utf-8').rstrip()

                print(usbMessage)
                messages = usbMessage.split("\n")
                messages.sort()

                for message in messages:
                    print(message)

                    find = message.find("RUN_END")
                    if find >= 0:

                        self.play_count += 1
                        if (self.play_count >= MAX_PLAYS):
                            self.after(0, self.game_over())
                        else:
                            # sjekk OFF_TAG
                            if (message.find("OFF_TAG")) >= 0:
                                print("CAR IS OFF TAG")

                        self.after(0, self.draw_button.config(state=tk.NORMAL))
                        return  # break out of the loop

                    else:
                        try:
                            rfid = int(message)
                            if gameboard.get(rfid) != None:
                                self.addPoints(rfid)
                        except ValueError:
                            print("Not a number" + message)

    def addPoints(self, rfid):
        global gameboard

        ps = gameboard.get(rfid)

        self.grid_with_point.draw_robot(ps.xPosition, ps.yPosition)

        if rfid not in self.seen_cards:
            self.grid_with_point.remove_point(ps.xPosition, ps.yPosition)

            self.seen_cards.append(rfid)
            self.score += gameboard.get(rfid).points
            self.after(0, self.update_score_display)

    def place_points_markers(self):
        global gameboard

        for rfid, ps in gameboard.items():
            self.grid_with_point.draw_point(ps.xPosition, ps.yPosition, rfid)


if __name__ == "__main__":
    app = App()
    app.mainloop()
