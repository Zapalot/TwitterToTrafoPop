//stuff you might have to change:
#define DEBUG 0
#define DEBUG 1  //uncomment to get debug messages between these two to enable/disable debug
#define totalCurrentLimit 3500 // maximum current we allow the leds to draw when they are all white
#define nTotalLeds 600  //the number of LEDs on your jacket. Used for current limiting and data transfer

// inn addition to the above, the OctoWS2811 LED-Interface needs the following data:
const int  maxLedsPerStrip =120; // the amount of LEDs in the longest Strip. used to reserve memory for OctoWs2811
const int ledsPerStrip[8] ={120,120,60,60,60,60,60,60}; // the number of LEds in each strip - used to map colorbuffers to transfer - memory of OctoWs2811

// the functionality is split into a few modules:
#include "SPI.h"          // SPI is used to push data to the LEDs on a hardware level
#include "debugTrace.h"   // Debug output on Serial that can be easily switched off 
#include "commands.h"     // a general framework for text based commands on Arduino
#include "vec2d.h"        // some useful functions and structures for calculation in 2D-space
#include "ledPositions.h" // the positions of the LEDs on the jacket
#include <OctoWS2811.h>
#include "ledControl.h"   // initialization and hardware access to the LEDs
OctoLedInterface leds;            // keeps a buffer of pixel colors and talks with the leds
Color* colorBuffer=leds.colorBuffer; // keep a global copy to bypass overhead when drawing effects
#include "ledEffects.h"   // the LED animations effects
#include "streamFun.h"    // some convenience functions for receiving data from streams

#include "images.h" // images you might want to show
#include "imageSelection.h" // reception of image show commands

//this buffer is used to store the last incoming text message
#define messageBufferLength 100          //maximum length of a message:
char messageBuffer[messageBufferLength]; //messages are stored here
long serialReadTimeout = 10; // wait at most 50 ms for the next character of a message. increase if you loose data, decrease for smoother operation
unsigned long lastReceiveTime=0; // Used to check if the connection to the host computer is alive
unsigned long heartbeatTimeOut=10000; // after receiving nothing for this time, an  error mode will be displayed

//these objects do most of our work:
CommandParser smsParser;      // takes care of parsing incoming messages for commands
LedEffectEngine effectEngine; // does the actual graphics
LedImageSelector ledImageEngine; //receives image commands and shows images
LedEffectEngine::EffectMode lastEffect=LedEffectEngine::flash;  // used to revert to the last effect if no new pictures are sent

//all Commands are handled by so called callback Functions. To reduce clutter, we have put them in a separate file
#include "callbackFunctions.h"


void setup(){
  Serial.begin(115200);

  /*while (!Serial) {
   ; // wait for serial port to connect. Needed for Leonardo only
   }*/
  Serial.setTimeout(5);

  //you can easily add your own commands by writing a function and adding a callback like I do below for all the modes and colors.
  //the functions used here are declared in "callbackFunctions.h"
  smsParser.addCallback(F("#flash"),startFlash);
  smsParser.addCallback(F("#fade"),startFade);
  smsParser.addCallback(F("#glitter"),startGlitter);
  smsParser.addCallback(F("#fill"),startFill);
  smsParser.addCallback(F("#move"),startMove);
  smsParser.addCallback(F("#rainbow"),startRainbow);

  smsParser.addCallback(F("#green"),startGreen);
  smsParser.addCallback(F("#cyan"),startCyan);
  smsParser.addCallback(F("#blue"),startBlue);
  smsParser.addCallback(F("#mauve"),startMauve);
  smsParser.addCallback(F("#pink"),startPink);
  smsParser.addCallback(F("#red"),startRed);
  smsParser.addCallback(F("#orange"),startOrange);
  smsParser.addCallback(F("#yellow"),startYellow);
  smsParser.addCallback(F("#white"),startWhite);
  smsParser.addCallback(F("#black"),startBlack);

  smsParser.addReceiver(&ledImageEngine); // allow reception of image load commands

  leds.setup();        // setup the SPI communication with the LEDs;

}

void loop(){
  // get new commands from Serial for test purposes
  unsigned long lastMillis=millis();
  receiveCommands();// receive commands from the RasPi
  //check if the connection is broken:
  if((millis()-lastReceiveTime)>heartbeatTimeOut){
    if(effectEngine.getEffect()!=LedEffectEngine::idle&&effectEngine.getEffect()!=LedEffectEngine::showErrorMessage){
      lastEffect=effectEngine.getEffect(); // save last effect so we can use it later when no more images arrive
    }
    effectEngine.setEffect(LedEffectEngine::showErrorMessage);
  }
  //TRACELN(millis()-lastMillis);
  effectEngine.updateColors(); // update LED colors according to current effect
  leds.sendToLeds();           // push the updated colors to the LEDs
  delay(2); // we need this for letting the led chain update its colors
};

//get commands from the rasPi
void receiveCommands(){
  // put your main code here, to run repeatedly:
  char command;
  Serial.setTimeout(1); // wait up to 1 ms for garbage
  while(Serial.readBytes(&command,1)>0){
  } // flush incoming data that is left from before
  Serial.write('t');// signal "ready for transmission"
  Serial.send_now();
  Serial.setTimeout(10); // wait up to 5 ms for commands
  if(!Serial.readBytes(&command,1))return; //read the command, if none came, return.
  lastReceiveTime=millis(); // Used to check if the connection to the host computer is alive

  TRACELN("got potential command!");
  TRACELN(command);
  switch (command){
  case 'p': //pixel data!
    if(effectEngine.getEffect()!=LedEffectEngine::idle&&effectEngine.getEffect()!=LedEffectEngine::showErrorMessage){
      lastEffect=effectEngine.getEffect(); // save last effect so we can use it later when no more images arrive
    }
    effectEngine.setEffect(LedEffectEngine::idle);
    readPixelData(10,(char*)leds.colorBuffer,nTotalLeds*3);
    break; 
  case 'c': // iteffect commands
    receiveEffectCommand();
  case 'a': // it's a keep alive ping.
    if(effectEngine.getEffect()==LedEffectEngine::idle)effectEngine.setEffect(lastEffect);//start last effect again if nothing is going on.
    break;
  default:
    Serial.println(F("Got an unexpected command!"));
  }
  // after the command, we expect a 
  unsigned int dataLength;
  Serial.read();
}
void readPixelData(unsigned long timeout, char* pixelBuffer,unsigned long bufferLength){
  TRACELN("waiting for pixel data...");
  Serial.setTimeout(300); // wait up to 5 ms for commands
  //this little trick helps us to glue together 4 single bytes to an unsigned long with no pain.
  union u_tag {
    char b[4];
    unsigned long ulval;
  } 
  bytesExpected;
  int bytesRead=Serial.readBytes(bytesExpected.b,4);
  if(bytesRead<4) return; // got no data length marker
  TRACE(bytesExpected.ulval);
  TRACELN(" bytes expected...");
  // now.. lets read that data!
  unsigned long pixelBytesRead= Serial.readBytes(pixelBuffer,min(bufferLength,bytesExpected.ulval));

  TRACE(pixelBytesRead);
  TRACELN(" bytes received...");
}

// 
void receiveEffectCommand(){
  Serial.setTimeout(serialReadTimeout);
  int bytesRead= Serial.readBytes(messageBuffer,messageBufferLength-1);
  messageBuffer[bytesRead]=0; // add zero-termination at the end of the message
  smsParser.parseString(messageBuffer,bytesRead);
}















