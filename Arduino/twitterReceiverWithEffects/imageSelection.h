#pragma once
#include "Arduino.h"
#include "images.h"
#include "commands.h"
#include "debugTrace.h"

#define nImages 4
prog_char imageName0[] PROGMEM = "#trafo";
prog_char imageName1[] PROGMEM = "#smily";
prog_char imageName2[] PROGMEM = "#stawberry";
prog_char imageName3[] PROGMEM = "#wear";


prog_char * const imageNames[] = {imageName0, imageName1, imageName2, imageName3};
const prog_uchar* const images[]={image0,image1,image2,image3};
class LedImageSelector:public AbstractCommandReceiver{
  public:
  LedImageSelector();
  void receiveCommand(char* inBuffer, int length); ///< looks for image names in the message
  void applyOnLeds();
  int selectedImageIndex;
  unsigned long lastSetTime;
};
LedImageSelector::LedImageSelector(){
  selectedImageIndex=-1; //no Image selected
  lastSetTime=millis();
}
void LedImageSelector::receiveCommand(char*inBuffer, int length){
     TRACELN(F("imageSelector looks at command..."));
     //TRACELN((const char PROGMEM *)imageName0);
     
 for (int i=0;i<nImages;i++){
     //TRACELN(imageNames[i]);
   if(strstr_P(inBuffer,(const char PROGMEM *)imageNames[i])!=0){
     TRACE(F("selected Image "));
     TRACELN(i);
     selectedImageIndex=i;
     lastSetTime=millis();
   }
 }
}
// you MUST have images that are at least as long as the leds...
void LedImageSelector::applyOnLeds(){
  if(millis()-lastSetTime>15000)selectedImageIndex=-1;
  if(selectedImageIndex<0)return; //-1 means nothing selected
 int arrayIndex=0;
 for (int i=0;i<nTotalLeds;i++){
   colorBuffer[i].r=pgm_read_byte(&images[selectedImageIndex][i*3]);
   colorBuffer[i].g=pgm_read_byte(&images[selectedImageIndex][i*3+1]);
   colorBuffer[i].b=pgm_read_byte(&images[selectedImageIndex][i*3+2]);
 }
 
}
