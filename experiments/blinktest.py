from blinkstick import blinkstick
import time

# Display bstick info
for bstick in blinkstick.find_all():
    print("Found device:")
    print("    Manufacturer:  " + bstick.get_manufacturer())
    print("    Description:   " + bstick.get_description())
    print("    Serial:        " + bstick.get_serial())
    print("    Current Color: " + bstick.get_color(color_format="hex"))
    print("    Info Block 1:  " + bstick.get_info_block1())
    print("    Info Block 2:  " + bstick.get_info_block2())

# Set bstick to a random color
for bstick in blinkstick.find_all():
    bstick.set_random_color()
    print(bstick.get_serial() + " " + bstick.get_color(color_format="hex"))
time.sleep(3)

myColors = ['red', 'green', 'blue']

# Rainbow time
for bstick in blinkstick.find_all():
    for currentColor in myColors:
        for currentLED in range (0,32):
            bstick.set_color(channel=0, index=currentLED, name=currentColor)
            time.sleep(0.1)

# Turn bstick off
for bstick in blinkstick.find_all():
    bstick.turn_off()
    print(bstick.get_serial() + " turned off")
