# Imports go at the top
import microbit
from microbit import i2c, display, Image
import time
import radio
import machine
import random

radio.config(channel=11, address=0xDEADBEEF, length=100, power=5)
my_id = hash(machine.unique_id())
who_starts = None

microbit.i2c.init(freq=100_000)
microbit.set_volume(10)

CONNECTING_START = 0
CONNECTING_HELLO1 = 1
CONNECTING_ACK = 2

def find_partner() -> int:
    global who_starts
    connecting_state = CONNECTING_START
    their_id = -1
    last_msg_time = time.ticks_ms()
    wait = random.randint(900,1100)
    while True:
        for index, img in enumerate(Image.ALL_CLOCKS):
            display.show(img)
            msg = radio.receive()
            if msg:
                if connecting_state == CONNECTING_START and msg.startswith("hello1"):
                    _, their_id = msg.split(";")
                    last_msg_time = time.ticks_ms()
                    if int(their_id) > int(my_id):
                        #display.scroll(their_id, delay=10)
                        who_starts = bool(random.getrandbits(1))
                        radio.send("hello2;{};{};{}".format(their_id,my_id,int(who_starts)))
                        connecting_state = CONNECTING_ACK
                    else:
                        #display.scroll(my_id, delay=10)
                        connecting_state = CONNECTING_HELLO1
                if connecting_state == CONNECTING_HELLO1 and msg.startswith("hello2"):
                    _, my_id2, their_id2, who_starts2 = msg.split(";")
                    if their_id2 == their_id and int(my_id2) == my_id:
                        who_starts = not bool(int(who_starts2))
                        radio.send("ACK;{}".format(my_id))
                        return int(their_id)
                if connecting_state == CONNECTING_ACK and msg.startswith("ACK"):
                    _, their_id2 = msg.split(";")
                    if their_id2 == their_id:
                        return int(my_id)
                if connecting_state != CONNECTING_START and time.ticks_diff(time.ticks_ms(), last_msg_time) > wait:
                    connecting_state = CONNECTING_START
                    wait = random.randint(500,1500)

            microbit.sleep(random.randint(40,60))
            if index % 3 == 0:
                radio.send("hello1;{}".format(my_id))

def i2c_write_data(data):
    i2c.write(0x3C, bytearray([0x40]) + data)

def i2c_write_cmd(cmd):
    i2c.write(0x3C, bytearray([0, cmd]))

def set_pos(col=0, page=0):
    i2c_write_cmd(0xB0 | page)
    i2c_write_cmd(0x00 | (col % 16))
    i2c_write_cmd(0x10 | (col >> 4))

def clear_display():
    for page in range(8):
        set_pos(0, page)
        i2c_write_data(bytearray(128))


# cast the magic spell
cmds = [
  0xAE, 0xA4, 0xD5, 0xF0, 0xA8, 0x3F, 0xD3, 0x00, 0x00, 0x8D, 0x14,
  0x20, 0x00, 0x21, 0, 127, 0x22, 0, 63, 0xA0 | 0x1, 0xC8, 0xDA, 0x12,
  0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA6, 0xD6, 0x00, 0xAF
]
for cmd in cmds:
    i2c_write_cmd(cmd)

clear_display()

row_pos = [
    0b0100_0001,
    0b0001_0000,
    0b0000_0100,
    0b0100_0001,
    
    0b0001_0000,
    0b0000_0100,
    0b0100_0001,
    0b0001_0000,
]

blankBuf = bytearray(128*8)
for row in range(8):
    for col in range(121):
        num = 0
        num = num | row_pos[row]
        if col % 12 == 0:
            if row != 7:
                num = 0b1111_1111
            else:
                num = 0b0001_1111
        blankBuf[col+128*row] = num

# y is on 10x10
# x is on real grid
def blit_virt(buf,x,y, bits):
    bits <<= (y*6)
    for i in range(0,8):
        inc = 8*i
        a = (bits & (0b1111_1111<<inc)) >> inc
        buf[i*128+(x)] |= a

# y and x are on 10x10
def blit_square(buf, x, y, bit_array):
    x = x*12
    for index, arr in enumerate(bit_array):
        blit_virt(buf, x+index, y, arr)

def draw_ship(buf, x, y, ship):
    SHIP_VIRT_TOP = 0
    SHIP_VIRT_MIDDLE = 1
    SHIP_VIRT_END = 2
    SHIP_HORIZ_LEFT = 3
    SHIP_HORIZ_MIDDLE = 4
    SHIP_HORIZ_END = 5
    image = None
    if ship == SHIP_VIRT_TOP:
        image = ImageShipVirtTop
    elif ship == SHIP_VIRT_MIDDLE:
        image = ImageShipVirtMiddle
    elif ship == SHIP_VIRT_END:
        image = ImageShipVirtEnd
    elif ship == SHIP_HORIZ_LEFT:
        image = ImageShipHorizLeft
    elif ship == SHIP_HORIZ_MIDDLE:
        image = ImageShipHorizMiddle
    elif ship == SHIP_HORIZ_END:
        image = ImageShipHorizRight
    elif ship == SHIP_DEAD:
        image = ImageShipDead
    
    blit_square(buf, x, y, image)


arr = [[False]*10]*10
pos = (0,0)

ImageCursorA = [
    0b000000,0b000000,0b011100,0b011100,
    0b011100,0b011100,0b011100,0b011100,
    0b011100,0b011100,0b011100
]

ImageCursorB = [
    0b000000,0b000000,0b011100,0b010100,
    0b010100,0b010100,0b010100,0b010100,
    0b010100,0b010100,0b011100
]

ImageShipVirtTop = [
    0b000000,0b000000,0b000000,0b111100,
    0b111100,0b111100,0b111100,0b111100,
    0b111100,0b111100
]

ImageShipVirtMiddle = [
    0b000000,0b000000,0b000000,0b111110,
    0b111110,0b111110,0b111110,0b111110,
    0b111110,0b111110
]

ImageShipVirtEnd = [
    0b000000,0b000000,0b000000,0b011110,
    0b011110,0b011110,0b011110,0b011110,
    0b011110,0b011110
]

ImageShipHorizLeft = [
    0b000000,0b000000,0b000000,0b011100,
    0b011100,0b011100,0b011100,0b011100,
    0b011100,0b011100,0b011100,0b011100
]

ImageShipHorizMiddle = [
    0b000000,0b011100,0b011100,0b011100,
    0b011100,0b011100,0b011100,0b011100,
    0b011100,0b011100,0b011100,0b011100
]

ImageShipHorizRight = [
    0b000000,0b011100,0b011100,0b011100,
    0b011100,0b011100,0b011100,0b011100,
    0b011100,0b011100
]

ImageShipDead = [
    0b000000,0b000000,0b010100,0b000000,
    0b010100,0b000000,0b010100,0b000000,
    0b010100,0b000000,0b010100
]



alt = 0

availableShips = [
    5,
    4,4,
    3,3,3,
    2,2,2,2
]

SHIP_VIRT_TOP = 0
SHIP_VIRT_MIDDLE = 1
SHIP_VIRT_END = 2
SHIP_HORIZ_LEFT = 3
SHIP_HORIZ_MIDDLE = 4
SHIP_HORIZ_END = 5
SHIP_DEAD = 6

ships: "list[list[int | None]]" = []
for i in range(10):
    ships.append([None]*10)

def draw_shoot():
    buf = blankBuf[:]
    blit_square(buf, pos[0], pos[1], ImageCursorB)
    for x, row in enumerate(guesses):
        for y, guess in enumerate(row):
            if guess == True:
                blit_square(buf, x, y, ImageCursorA)
            elif guess == False:
                blit_square(buf, x, y, ImageCursorB)
    i2c_write_data(buf)

def draw_get_shot():
    buf = blankBuf[:]
    for y, row in enumerate(ships):
        for x, ship in enumerate(row):
            if ship != None:
                draw_ship(buf, x, y, ship)
    i2c_write_data(buf)

def draw_placement(shipLength):
    buf = blankBuf[:]
    for y, row in enumerate(ships):
        for x, ship in enumerate(row):
            if ship != None:
                draw_ship(buf, x, y, ship)
    for offset in range(shipLength):
        if isVirt:
            blit_square(buf, pos[0], pos[1]+offset, ImageCursorA)
        else:
            blit_square(buf, pos[0]+offset, pos[1], ImageCursorA)
    i2c_write_data(buf)

### Setup loop
### KNOWN BUG: ROTATING NEAR BORDER IS FUNKY!
for count, shipLength in enumerate(availableShips):
    pos = (0,0)
    isVirt = True
    draw_placement(shipLength)
    lastA, lastB, lastLogo = None, None, None
    display.show(len(availableShips)-count-1)

    while True:
        now = time.ticks_ms()
        if microbit.button_a.was_pressed():
            lastA = now
        if microbit.button_b.was_pressed():
            lastB = now
        if microbit.pin_logo.is_touched():
            lastLogo = now

        if lastA != None and lastB != None:
            if isVirt:
                ships[pos[1]][pos[0]] = SHIP_VIRT_TOP
                for offset in range(1,shipLength-1):
                    ships[pos[1]+offset][pos[0]] = SHIP_VIRT_MIDDLE
                ships[pos[1]+shipLength-1][pos[0]] = SHIP_VIRT_END
            else:
                ships[pos[1]][pos[0]] = SHIP_HORIZ_LEFT
                for offset in range(1,shipLength-1):
                    ships[pos[1]][pos[0]+offset] = SHIP_HORIZ_MIDDLE
                ships[pos[1]][pos[0]+shipLength-1] = SHIP_HORIZ_END
            break
        
        if lastA != None and time.ticks_diff(now, lastA) > 50:
            lastA = None
            if isVirt:
                pos = ((pos[0] + 1) % 10, pos[1])
            else:
                pos = ((pos[0] + 1) % (11-shipLength), pos[1])
            draw_placement(shipLength)
        if lastB != None and time.ticks_diff(now, lastB) > 50:
            lastB = None
            if isVirt:
                pos = (pos[0], (pos[1] + 1) % (11-shipLength))
            else:
                pos = (pos[0], (pos[1] + 1) % 10)
            draw_placement(shipLength)
        if lastLogo != None and time.ticks_diff(now, lastLogo) > 50:
            lastLogo = None
            isVirt = not isVirt
            draw_placement(shipLength)

### Find a partner
radio.on()
group_id = find_partner()
radio.config(channel=15, address=0xDEADBEEF, group=group_id%255, length=40, queue=10, power=7)

### Gameplay loop
ship_count = len(availableShips)
guesses: "list[list[bool | None]]" = []
for i in range(10):
    guesses.append([None]*10)

MODE_SHOOT = 0
MODE_GET_SHOT = 1
if who_starts:
    mode = MODE_SHOOT
    draw_shoot()
    display.show(Image.SWORD)
else:
    mode = MODE_GET_SHOT
    draw_get_shot()
    display.show(Image.SKULL)

lastA, lastB = None, None

def shoot_loop():
    global lastA, lastB, mode, pos, ship_count
    now = time.ticks_ms()
    if microbit.button_a.is_pressed():
        lastA = now
    if microbit.button_b.is_pressed():
        lastB = now

    if lastA != None and lastB != None:
        lastA, lastB = None, None
        if guesses[pos[0]][pos[1]] == None:
            display.show(Image.PACMAN)
            radio.send("shoot;{};{}".format(pos[0],pos[1]))
            while True:
                msg = radio.receive()
                if msg:
                    if msg == "hit":
                        guesses[pos[0]][pos[1]] = True
                        display.show(Image.YES)
                        ship_count -= 1
                    elif msg == "miss":
                        guesses[pos[0]][pos[1]] = False
                        display.show(Image.NO)
                    elif msg == "game_over":
                        display.scroll("YOU WIN!")
                        draw_shoot()
                        microbit.sleep(600)
                        clear_display()
                        microbit.reset()
                        return

                    if msg == "hit" or msg == "miss":
                        draw_shoot()
                        microbit.sleep(700)
                        display.clear()
                        draw_get_shot()
                        mode = MODE_GET_SHOT
                        return

    elif lastA != None and time.ticks_diff(now, lastA) > 50:
        lastA = None
        pos = (pos[0], (pos[1]+1)%10)
        draw_shoot()
        
    
    elif lastB != None and time.ticks_diff(now, lastB) > 50:
        lastB = None
        pos = ((pos[0]+1)%10, pos[1])
        draw_shoot()

        

# game over logic is non-sensical
def get_shot_loop():
    global mode, ship_count, pos
    msg = radio.receive()
    display.show(Image.ARROW_E)
    if msg and msg.startswith("shoot"):
        _, x, y = msg.split(";")
        microbit.sleep(50)
        if ships[int(y)][int(x)] != None:
            radio.send("hit")
            ships[int(y)][int(x)] = SHIP_DEAD
            display.show(Image.SAD)
            ship_count -= 1
            if False:
                radio.send("game_over")
                display.scroll("YOU LOSE!")
                draw_get_shot()
                clear_display()
                microbit.sleep(600)
                microbit.reset()
                return
        else:
            radio.send("miss")
            display.show(Image.HAPPY)
        draw_get_shot()
        microbit.sleep(600)
        microbit.display.clear()
        pos = (4,4)
        draw_shoot()
        mode = MODE_SHOOT

while True:
    if mode == MODE_SHOOT:
        shoot_loop()
    else:
        get_shot_loop()
    
