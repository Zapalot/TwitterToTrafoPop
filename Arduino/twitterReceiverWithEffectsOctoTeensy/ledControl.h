#pragma once
#include "Arduino.h"
#include "debugTrace.h"


// the Buffers for Data-Transfer to the Leds are declared globally:
DMAMEM int octoWS2811DisplayMemory[maxLedsPerStrip *6];
int  octoWS2811DrawingMemory[maxLedsPerStrip*6];
const int octoWS2811Config = WS2811_GBR | WS2811_800kHz;


//we'll use this to define colors
struct Color{
  byte r;
  byte g;
  byte b;
};

// wrapper to the OctoLed-Library that uses the same interface as our other led-pixel interfaces.
class OctoLedInterface{
public:
  OctoLedInterface():
  leds(OctoWS2811(maxLedsPerStrip, octoWS2811DisplayMemory, octoWS2811DrawingMemory, octoWS2811Config))
  {
    brightnessMultiplier=0;
    useDynamicCurrentLimit=true;
  }
  Color colorBuffer[nTotalLeds];   //here we store the LED colors
  void setup();       //initialize SPI connection and calculate current limiting
  void sendToLeds();  // send Data from Buffer to leds
  int calculateDynamicCurrentLimiter(); // calculate a brighness multiplier that will keep the current image just below the max Current
  void setUseDynamicLimit(bool newValue){useDynamicCurrentLimit=newValue;}
  bool getUseDynamicLimit(bool newValue){return useDynamicCurrentLimit;}
protected:
  OctoWS2811 leds; // the hardware interface
  bool useDynamicCurrentLimit; // shall we use the brightnessMultiplier calculated for a white frame or an adaptive multiplier?
  int brightnessMultiplier; // this is initialized in 'setupOctoLedInterface' to a safe value for current limitig.
};



void OctoLedInterface::setup()
{
    leds.begin();
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
void OctoLedInterface::sendToLeds(){
  // copy internal buffer to drawing memory:
  unsigned int sourceOffset=0; // where to start copying
  unsigned int destOffset=0;  // where to put the dat
  //select current limit multiplier depending on selected mode
  int currentLimiter=useDynamicCurrentLimit?calculateDynamicCurrentLimiter():brightnessMultiplier;

  //the octows2811 lib does some black magic to the data that I have no clue of... so let's just use their 'setPixel' method...
  //nasty hack to correct the flipped stripes in the 10 row display we built.
 /*
  int rowOffsets[10]={
  60,
  0,
  180,
  120,
  240,
  300,
  360,
  420,
  480,
  540
  };
  int ledsPerRow=60;
  for(int row=0;row<10;row++){
    destOffset=rowOffsets[row];
    for(int col=0;col<ledsPerRow;col++){
      Color curColor=colorBuffer[sourceOffset];
      unsigned int pixelColor=
      ((((unsigned int)curColor.r*currentLimiter)>>8)&0x000000FF)|
      ((((unsigned int)curColor.g*currentLimiter))&0x0000FF00)|
      ((((unsigned int)curColor.b*currentLimiter)<<8)&0x00FF0000);
      
      leds.setPixel(destOffset,pixelColor);
      sourceOffset++;
      destOffset++;
    }
  }
  */
  //this how you would normally do it:
  
  for(int stripIndex=0;stripIndex<8;stripIndex++){
    for(int ledIndex=0;ledIndex<ledsPerStrip[stripIndex];ledIndex++){
      Color curColor=colorBuffer[sourceOffset];
 
      unsigned int pixelColor=
      ((((unsigned int)curColor.r*currentLimiter)>>8)&0x000000FF)|
      ((((unsigned int)curColor.g*currentLimiter))&0x0000FF00)|
      ((((unsigned int)curColor.b*currentLimiter)<<8)&0x00FF0000);
      
      leds.setPixel(destOffset,pixelColor);
      sourceOffset++;
      destOffset++;
    }
    destOffset+=(maxLedsPerStrip-ledsPerStrip[stripIndex]);
  }
  
  leds.show(); // let the library to it's work..
};

// calculate a brighness multiplier that will keep the current image just below the max Current
int OctoLedInterface::calculateDynamicCurrentLimiter(){
  long brightnessSum=0;
  for(int i=0;i<nTotalLeds;i++){
    brightnessSum+=colorBuffer[i].r+colorBuffer[i].g+colorBuffer[i].b;
  }
  float currentForThisImage=((float)brightnessSum*20.0)/255.0;
  float safeMultiplier=(float)totalCurrentLimit/(float)currentForThisImage;
  /*
  Serial.print(safeMultiplier);
  Serial.print("\t-\t");  
  Serial.println(min(floor(safeMultiplier*255),255));
  Serial.println(brightnessMultiplier);
  */
  return(min(floor(safeMultiplier*255),255));
}
