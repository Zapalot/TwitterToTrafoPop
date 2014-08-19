#pragma once
#include "Arduino.h"
#include "SPI.h"
#include "debugTrace.h"
//we'll use this to define colors
struct Color{
  byte r;
  byte g;
  byte b;
};

class LedInterface{
public:
LedInterface(){brightnessMultiplier=0;}
  Color colorBuffer[nTotalLeds];   //here we store the LED colors
  void setup();       //initialize SPI connection and calculate current limiting
  void sendToLeds();  // send Data from Buffer to leds
protected:
  int brightnessMultiplier; // this is initialized in 'setupLedInterface' to a safe value for current limitig.

};



void LedInterface::setup(){
  //we use SPI to send data to the LEDs:
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  // SPI.setClockDivider(SPI_CLOCK_DIV16); // 1 MHz
  SPI.setClockDivider(SPI_CLOCK_DIV8); // 2 MHz
  // SPI.setClockDivider(SPI_CLOCK_DIV4); // 4 MHz
  //calculate a brightness scaling factor that honors the current limit:
  float totalMaxCurrent=nTotalLeds*3*20; //each color draws 20mA max per Pixel
  float safeMultiplier=totalCurrentLimit/totalMaxCurrent;
  brightnessMultiplier=floor(safeMultiplier*255);
  // we use bitshifting to modify the brightness values because it is faster than dividing
  // but this means we can only 'divide' by powers of two.
  //&brightnessBitShift= (int)ceil(log(1.0/safeMultiplier)/log(2.0)); // this calculates the bitshift that is always on the safe side.
  TRACE(F("brightness multiplier:"));
  TRACELN(brightnessMultiplier); 
};

//this function sends the data stored in colorBuffer to the LEDs
void LedInterface::sendToLeds(){
  byte* rawData = (byte*)colorBuffer; // we treat the color array as raw bytes to speed up the next step.
  int dataLength=nTotalLeds*3;
  for (int i=0;i<dataLength;i++){
    unsigned int limitedColorPixelData=((unsigned int)rawData[i]*brightnessMultiplier)>>8;
    //byte limitedColorPixelData=rawData[i]>>brightnessBitShift; // reduce the brightness value to limit power consumption
    //load the data into the SPI DATA register (SPDR) and wait for the transmission to be finished (SPSR & _BV(SPIF)).
    for (SPDR = (byte)limitedColorPixelData; !(SPSR & _BV(SPIF)););
  }
};
