# invaders.py
#
# ESP8266 (node MCU D1 mini)  micropython
# by Billy Cheung  2019 08 31
#
# SPI OLED
# GND
# VCC
# D0/Sck - D5 (=GPIO14=HSCLK)
# D1/MOSI- D7 (=GPIO13=HMOSI)
# RES    - D0 (=GPIO16)
# DC     - D4 (=GPIO2)
# CS     - D3 (=GPIO0)
# Speaker
# GPIO15   D8  Speaker
# n.c.   - D6  (=GPIO13=HMOSI)
#
# GPIO5    D1——   On to read ADC for Btn
# GPIO4    D2——   On to read ADC for Paddle
#
# buttons   A0
# A0 VCC-9K-U-9K-L-12K-R-9K-D-9K-A-12K-B-9K-GND
import gc
import sys
gc.collect()
print (gc.mem_free())
import network
import utime
from utime import sleep_ms,ticks_ms, ticks_us, ticks_diff
from machine import Pin, SPI, PWM, ADC
from math import sqrt
import ssd1306
from random import getrandbits, seed

# configure oled display SPI SSD1306
hspi = SPI(1, baudrate=8000000, polarity=0, phase=0)
#DC, RES, CS
display = ssd1306.SSD1306_SPI(128, 64, hspi, Pin(2), Pin(16), Pin(0))


#---buttons

btnU = const (1 << 1)
btnL = const (1 << 2)
btnR = const (1 << 3)
btnD = const (1 << 4)
btnA = const (1 << 5)
btnB = const (1 << 6)

Btns = 0
lastBtns = 0

pinBtn = Pin(5, Pin.OUT)
pinPaddle = Pin(4, Pin.OUT)


buzzer = Pin(15, Pin.OUT)

adc = ADC(0)

def getPaddle () :
  pinPaddle.on()
  pinBtn.off()
  sleep_ms(20)
  return adc.read()

def pressed (btn, waitRelease=False) :
  global Btns
  if waitRelease and Btns :
    pinPaddle.off()
    pinBtn.on()
    while ADC(0).read() > 70 :
       sleep_ms (20)
  return (Btns & btn)

def lastpressed (btn) :
  global lastBtns
  return (lastBtns & btn)


def getBtn () :
  global Btns
  global lastBtns
  pinPaddle.off()
  pinBtn.on()
  lastBtns = Btns
  Btns = 0
  a0=ADC(0).read()
  if a0  < 564 :
    if a0 < 361 :
      if a0 > 192 :
        if a0 > 278 :
          Btns |= btnU | btnA
        else :
          Btns |= btnL
      else:
        if a0 > 70 :
          Btns |= btnU
    else :
      if a0 > 482 :
        if a0 > 527 :
          Btns |= btnD
        else :
          Btns |= btnU | btnB
      else:
        if a0 > 440 :
          Btns |= btnL | btnA
        else :
          Btns |= btnR
  else:
      if a0 < 728 :
        if a0 < 653 :
          if a0 > 609 :
            Btns |= btnD | btnA
          else :
            Btns |= btnR | btnA
        elif a0 > 675 :
          Btns |= btnA
        else :
          Btns |= btnL | btnB
      elif a0 < 829 :
        if a0 > 794 :
          Btns |= btnD | btnB
        else :
          Btns |= btnR | btnB
      elif a0 > 857 :
        Btns |= btnB
      else :
        Btns |= btnA | btnB



tones = {
    'c4': 262,
    'd4': 294,
    'e4': 330,
    'f4': 349,
    'f#4': 370,
    'g4': 392,
    'g#4': 415,
    'a4': 440,
    "a#4": 466,
    'b4': 494,
    'c5': 523,
    'c#5': 554,
    'd5': 587,
    'd#5': 622,
    'e5': 659,
    'f5': 698,
    'f#5': 740,
    'g5': 784,
    'g#5': 831,
    'a5': 880,
    'b5': 988,
    'c6': 1047,
    'c#6': 1109,
    'd6': 1175,
    ' ': 0
}


def playTone(tone, tone_duration, total_duration):
            beeper = PWM(buzzer, freq=tones[tone], duty=512)
            utime.sleep_ms(tone_duration)
            beeper.deinit()
            utime.sleep_ms(int(total_duration * 1000)-tone_duration)

def playSound(freq, tone_duration, total_duration):
            beeper = PWM(buzzer, freq, duty=512)
            utime.sleep_ms(tone_duration)
            beeper.deinit()
            utime.sleep_ms(int(total_duration * 1000)-tone_duration)
            
frameRate = 30
screenW = const(128)
screenH = const(64)
xMargin = const (5)
yMargin = const(10)
screenL = const (5)
screenR = const(117)
screenT = const (10)
screenB = const (58)
dx = 5
vc = 3
gunW= const(7)
gunH = const (5)
invaderSize = const(5)
invaders_rows = const(4)
invaders_per_row = const(11)


gameOver = False

class Rect (object):
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x2 = x + w -1
        self.y2 = y + h - 1 
    def move_ip (self, vx, vy) :
        self.x = self.x + vx
        self.y = self.y + vy
    def colliderect (self, rect1) :
      if (self.x2 >= rect1.x and
         self.x <= rect1.x2 and
         self.y2 >= rect1.y and
         self.y <= rect1.y2) :
        return True
      else :
        return False
          
        
  
def setUpInvaders ():
    invaderList = []
    y = yMargin
    while y < yMargin + (invaderSize+2) * invaders_rows :
      x = xMargin
      while x < xMargin + (invaderSize+2) * invaders_per_row :
        invaderList.append(Rect(x,y,invaderSize, invaderSize))
        # print (str(x) + ":" + str(y))
        x = x + invaderSize + 2
      y = y + invaderSize + 2  
    return invaderList
  
def drawInvaders (invaderList, postureA) :
  if postureA :
    for i in invaderList :
        display.fill_rect(i.x, i.y, i.w, i.h, 1)
        display.fill_rect(i.x+2, i.y+2, i.w-4, i.h-2, 0)
  else :
      for i in invaderList :
        display.fill_rect(i.x, i.y, i.w, i.h, 1)
        display.fill_rect(i.x+2, i.y, i.w-4, i.h-2, 0)
def drawGun () :
  display.fill_rect(gun.x, gun.y+3, gunW, 3,1)
  display.fill_rect(gun.x+3, gun.y, 1, 3,1)
def drawBullets () :
  for b in bullets:
    display.fill_rect(b.x, b.y, 1,3,1)



frameCount = 0
postureA = False
usePaddle = False
demo = False

display.fill(0)
display.text('Invaders', 5, 0, 1)
display.text('A = Button', 5, 20, 1)
display.text('B = Paddle', 5,30,  1)
display.text('D = Demo', 5, 40,  1)
display.text('L = Exit', 5, 50,  1)
display.show()

#menu screen
while True:
  getBtn()
  if pressed(btnL,True) :
    gameOver = True
    exitGame = True
    break
  elif pressed(btnA,True) :
    usePaddle = False
    break
  elif pressed(btnB,True) :
    usePaddle = True
    break
  elif pressed(btnD,True) :
    demo = True
    usePddle = False
    wait_for_keys=False
    display.fill(0)
    display.text('DEMO', 5, 0, 1)
    display.text('A or B to Stop', 5, 30, 1)
    display.show()
    sleep_ms(2000)  
    break
    
#reset the game 

bullets = []
invaderList = setUpInvaders()
gun = Rect(screenL+int((screenR-screenL)/2), screenB, gunW, gunH)

while not gameOver:
  timer = ticks_ms()
  display.fill(0)
  display.text ("Score:", 0,0, 1)
  frameCount += 1
  if frameCount > 15 :
      
    for i in invaderList:
        if i.x > screenR or i.x < screenL :
            dx = -dx
            for alien in invaderList :
              alien.move_ip (0, invaderSize + 2)
              if alien.y > screenB :
                gameOver = True
            break
    for i in invaderList :
        i.move_ip (dx, 0)
    frameCount = 0
    postureA = not postureA
    
     
  # move gun
  getBtn()
  if Btns & btnA and len(bullets) < 2:
    bullets.append(Rect(gun.x+3, gun.y-1, 1, 3))
  if usePaddle :
    gun.x = int(getPaddle() / (1024/(screenR-screenL)))
  else :
    if Btns & btnL and gun.x - 3 > 0 :
      vc = -3
    elif Btns & btnR and (gun.x + 3 + gunW ) < screenW :
      vc = 3
    else :
      vc = 0
    gun.move_ip (vc, 0)
      

  
  # move bullets
  
  for b in bullets:
    b.move_ip(0,-3)
    if b.y < 0 : 
      bullets.remove(b)
      for i in invaderList:
        if i.colliderect(b) :
          invaderList.remove(i)
          bullets.remove(b)
  
  drawInvaders (invaderList, postureA)
  drawGun()
  drawBullets()
  
  timer_dif = int(1000/frameRate) - ticks_diff(ticks_ms(), timer)

  if timer_dif > 0 :
      sleep_ms(timer_dif)  
      display.show()


 





