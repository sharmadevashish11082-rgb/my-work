import turtle
import time

# -----------------------
# Window
# -----------------------
wn = turtle.Screen()
wn.title("Mini Mario")
wn.bgcolor("skyblue")
wn.setup(width=800, height=600)
wn.tracer(0)

# -----------------------
# Ground
# -----------------------
ground = turtle.Turtle()
ground.speed(0)
ground.shape("square")
ground.color("green")
ground.shapesize(stretch_wid=2, stretch_len=40)
ground.penup()
ground.goto(0, -250)

# -----------------------
# Player (Mario)
# -----------------------
player = turtle.Turtle()
player.speed(0)
player.shape("square")
player.color("red")
player.shapesize(stretch_wid=1.5, stretch_len=1)
player.penup()
player.goto(-300, -200)

x_velocity = 0
y_velocity = 0
gravity = -0.5
jumping = False

# -----------------------
# Coins
# -----------------------
coins = []

for x in [-150, 0, 150, 300]:
    coin = turtle.Turtle()
    coin.shape("circle")
    coin.color("gold")
    coin.penup()
    coin.goto(x, -170)
    coins.append(coin)

score = 0

pen = turtle.Turtle()
pen.hideturtle()
pen.penup()
pen.goto(-380, 250)
pen.write("Score: 0", font=("Arial", 18, "bold"))

# -----------------------
# Controls
# -----------------------
def move_left():
    global x_velocity
    x_velocity = -6

def move_right():
    global x_velocity
    x_velocity = 6

def stop():
    global x_velocity
    x_velocity = 0

def jump():
    global y_velocity, jumping
    if not jumping:
        y_velocity = 12
        jumping = True

wn.listen()
wn.onkeypress(move_left, "Left")
wn.onkeypress(move_right, "Right")
wn.onkeyrelease(stop, "Left")
wn.onkeyrelease(stop, "Right")
wn.onkeypress(jump, "space")

# -----------------------
# Game Loop
# -----------------------
while True:
    wn.update()

    # Horizontal movement
    player.setx(player.xcor() + x_velocity)

    # Gravity
    y_velocity += gravity
    player.sety(player.ycor() + y_velocity)

    # Ground collision
    if player.ycor() <= -200:
        player.sety(-200)
        y_velocity = 0
        jumping = False

    # Screen boundaries
    if player.xcor() > 390:
        player.setx(390)
    if player.xcor() < -390:
        player.setx(-390)

    # Collect coins
    for coin in coins:
        if coin.isvisible():
            if player.distance(coin) < 25:
                coin.hideturtle()
                score += 1
                pen.clear()
                pen.write(
                    f"Score: {score}",
                    font=("Arial", 18, "bold")
                )

    time.sleep(0.02)

















    
