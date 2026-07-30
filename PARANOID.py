import turtle
import random

# Screen
wn = turtle.Screen()
wn.title("Arkanoid")
wn.bgcolor("black")
wn.setup(width=800, height=600)
wn.tracer(0)

# Score
score = 0

# Paddle
paddle = turtle.Turtle()
paddle.shape("square")
paddle.color("white")
paddle.shapesize(stretch_wid=1, stretch_len=6)
paddle.penup()
paddle.goto(0, -250)

# Ball
ball = turtle.Turtle()
ball.shape("circle")
ball.color("red")
ball.penup()
ball.goto(0, -100)

ball.dx = 3
ball.dy = 3

# Bricks
bricks = []

colors = ["red", "orange", "yellow", "green", "blue"]

for row in range(5):
    for col in range(10):
        brick = turtle.Turtle()
        brick.shape("square")
        brick.color(colors[row])
        brick.shapesize(stretch_wid=1, stretch_len=2)
        brick.penup()
        brick.goto(-360 + col * 80, 220 - row * 30)
        bricks.append(brick)

# Score display
pen = turtle.Turtle()
pen.hideturtle()
pen.color("white")
pen.penup()
pen.goto(0, 260)
pen.write("Score: 0", align="center",
          font=("Arial", 16, "normal"))

# Controls
def move_left():
    x = paddle.xcor() - 40
    if x < -340:
        x = -340
    paddle.setx(x)

def move_right():
    x = paddle.xcor() + 40
    if x > 340:
        x = 340
    paddle.setx(x)

wn.listen()
wn.onkeypress(move_left, "Left")
wn.onkeypress(move_right, "Right")

# Main loop
running = True

while running:
    wn.update()

    ball.setx(ball.xcor() + ball.dx)
    ball.sety(ball.ycor() + ball.dy)

    # Wall collision
    if ball.xcor() > 390:
        ball.setx(390)
        ball.dx *= -1

    if ball.xcor() < -390:
        ball.setx(-390)
        ball.dx *= -1

    if ball.ycor() > 290:
        ball.sety(290)
        ball.dy *= -1

    # Lose condition
    if ball.ycor() < -290:
        pen.clear()
        pen.goto(0, 0)
        pen.write("GAME OVER",
                  align="center",
                  font=("Arial", 28, "bold"))
        running = False

    # Paddle collision
    if (ball.ycor() < -235 and
        ball.ycor() > -255 and
        abs(ball.xcor() - paddle.xcor()) < 65):
        ball.sety(-235)
        ball.dy *= -1

    # Brick collisions
    for brick in bricks[:]:
        if ball.distance(brick) < 30:
            brick.hideturtle()
            bricks.remove(brick)

            ball.dy *= -1

            score += 10

            pen.clear()
            pen.goto(0, 260)
            pen.write(f"Score: {score}",
                      align="center",
                      font=("Arial", 16, "normal"))
            break

    # Win condition
    if len(bricks) == 0:
        pen.clear()
        pen.goto(0, 0)
        pen.write("YOU WIN!",
                  align="center",
                  font=("Arial", 28, "bold"))
        running = False

wn.mainloop()
