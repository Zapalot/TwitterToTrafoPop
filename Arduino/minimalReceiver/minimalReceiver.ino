#define DEBUG 1
#include "debugTrace.h"

#define nTotalLeds 100          //total number of leds in the chain.
#define totalCurrentLimit 2000  //maximum total LED current in mA
#include "SPI.h"
#include "LedInterface.h"
LedInterface leds;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  leds.setup();
}

void loop() {
  receiveCommands();
  leds.sendToLeds();
}
void receiveCommands(){
  // put your main code here, to run repeatedly:
  char command;
  Serial.setTimeout(1); // wait up to 1 ms for garbage
  while(Serial.readBytes(&command,1)>0){} // flush incoming data that is left from before
  Serial.write('t');                        // signal "ready for transmission"
  Serial.setTimeout(5); // wait up to 5 ms for commands
  if(!Serial.readBytes(&command,1))return; //read the command, if none came, return.
  TRACELN("got potential command!");
  TRACELN(command);
  switch (command){
    case 'p': //pixel data!
      readPixelData(10,(char*)leds.colorBuffer,nTotalLeds*3);
      break;
    default:
      Serial.println("go away.. weirdo!");
  }
  // after the command, we expect a 
  unsigned int dataLength;
  Serial.read();
}
void readPixelData(unsigned long timeout, char* pixelBuffer,unsigned long bufferLength){
  TRACELN("waiting for pixel data...");
  //this little trick helps us to glue together 4 single bytes to an unsigned long with no pain.
  union u_tag {
    char b[4];
    unsigned long ulval;
  } bytesExpected;
  int bytesRead=Serial.readBytes(bytesExpected.b,4);
  if(bytesRead<4) return; // got no data length marker
  TRACE(bytesExpected.ulval);
  TRACELN(" bytes expected...");
  // now.. lets read that data!
  unsigned long pixelBytesRead= Serial.readBytes(pixelBuffer,min(bufferLength,bytesExpected.ulval));

  TRACE(pixelBytesRead);
  TRACELN(" bytes received...");
}


