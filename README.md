# BBCMicrobitBattleship
Simple 2 player battleship game for 2 BBC Microbits &amp; 2 Kitronik Air Quality and Environmental Boards. Sadly unfinished as I lost access to the boards before I added support for games ending.

Has custom handshake protocol which randomly picks which of the two players should start. No idea if the way I'm controlling the display is sensible, as it was mostly just reverse-engineered from some example code that was displaying text on the display.

Code quality is slightly poor as this was just sort of thrown together.

![image](https://github.com/user-attachments/assets/5fcff166-23ce-4417-8545-c18e0e26c6f4)

### Gameplay
![clip of gameplay loop](docs/gameplay.mp4)

### Game setup
![clip of game setup](docs/boardsetup.mp4)

### Handshake
Repeatedly randomly deciding between the pair which is player A and which is player B

![clip of repeated handshake](docs/repeated_negotiation.mp4)
