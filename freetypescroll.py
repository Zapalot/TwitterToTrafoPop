#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Needs freetype-py>=1.0

# For more info see:
# http://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python

# The MIT License (MIT)
#
# Copyright (c) 2013 Daniel Bader (http://dbader.org)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import freetype
import time
import math
import os
import re  # regular expressions used to parse led positions from file
import array

class GrayBitmap(object):
	"""
	A 2D bitmap image represented as a list of byte values. Each byte indicates the state
	of a single pixel in the bitmap. A value of 0 indicates that the pixel is `off`
	and any other value indicates that it is `on`.
	"""
	def __init__(self, width, height, pixels=None):
		self.width = int(width)
		self.height = int(height)
		self.pixels = pixels or bytearray(int(width * height))

	def __repr__(self):
		"""Return a string representation of the bitmap's pixels."""
		rows = ''
		for y in range(self.height):
			for x in range(self.width):
				rows += '#' if self.pixels[y * self.width + x] else '.'
			rows += '\n'
		return rows

	def bitblt(self, src, x, y):
		"""Copy all pixels from `src` into this bitmap"""
		#Limit the source buffer to fit into the destination buffer
		sourceStartX=int(max(x,0)-x)
		sourceEndX=int(min(x+src.width,self.width)-x)
		sourceStartY=int(max(y,0)-y)
		sourceEndY=int(min(y+src.height,self.height)-y)
				
		dstpixel = int(max(y,0) * self.width + max(x,0)) #pixel of destination where we start
		# pixels skip to end up in the same column of the destination buffer after completing one row of the source
		row_offset = int(self.width - (sourceEndX-sourceStartX))
		
		for sy in range(sourceStartY,sourceEndY):
			srcpixel=int(src.width*sy+sourceStartX)
			for sx in range(sourceStartX,sourceEndX):
				# Perform an OR operation on the destination pixel and the source pixel
				# because glyph bitmaps may overlap if character kerning is applied, e.g.
				# in the string "AVA", the "A" and "V" glyphs must be rendered with
				# overlapping bounding boxes.
				self.pixels[dstpixel] = self.pixels[dstpixel] or src.pixels[srcpixel]
				srcpixel += 1
				dstpixel += 1
			dstpixel += row_offset
	def clear(self):
		for index in range(self.height*self.width):
			self.pixels[index]=0
	#get R,G,B values for given pixel position
	def get_at(self,x,y):
		index=(int(x)+int(y)*self.width)*int(3)
		return( self.pixels[index])
	def convert_to_RGB(self):
		return ColorBitmap.make_from_mono(self)

class ColorBitmap(object):
	def __init__(self, width, height, pixels=None):
		self.width = int(width)
		self.height = int(height)
		self.pixels = pixels or bytearray(int(width * height)*3)
	def clear(self):
		for index in range(len(self.pixels)):
			self.pixels[index]=0
			
	#get R,G,B values for given pixel position
	def get_at(self,x,y):
		index=(int(x)+int(y)*self.width)*int(3)
		return( self.pixels[index:index+3])
		
	# create from a monochrome bitmap
	@staticmethod
	def make_from_mono(mono_bitmap):
		rgb_bytes=bytearray(len(mono_bitmap.pixels)*3)
		dstindex=0
		for mono in mono_bitmap.pixels:
			rgb_bytes[dstindex]=mono
			rgb_bytes[dstindex+1]=mono
			rgb_bytes[dstindex+2]=mono
			dstindex+=3
		return ColorBitmap(mono_bitmap.width, mono_bitmap.height,rgb_bytes)

class Glyph(object):
	def __init__(self, pixels, width, height, top, advance_width):
		self.bitmap = GrayBitmap(width, height, pixels)

		# The glyph bitmap's top-side bearing, i.e. the vertical distance from the
		# baseline to the bitmap's top-most scanline.
		self.top = top

		# Ascent and descent determine how many pixels the glyph extends
		# above or below the baseline.
		self.descent = max(0, self.height - self.top)
		self.ascent = max(0, max(self.top, self.height) - self.descent) # this should be self.top

		# The advance width determines where to place the next character horizontally,
		# that is, how many pixels we move to the right to draw the next glyph.
		self.advance_width = advance_width

	@property
	def width(self):
		return self.bitmap.width

	@property
	def height(self):
		return self.bitmap.height

	@staticmethod
	def from_glyphslot(slot):
		"""Construct and return a Glyph object from a FreeType GlyphSlot."""
		pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
		width, height = slot.bitmap.width, slot.bitmap.rows
		top = slot.bitmap_top

		# The advance width is given in FreeType's 26.6 fixed point format,
		# which means that the pixel values are multiples of 64.
		advance_width = slot.advance.x / 64

		return Glyph(pixels, width, height, top, advance_width)

	@staticmethod
	def unpack_mono_bitmap(bitmap):
		"""
		Unpack a freetype FT_LOAD_TARGET_MONO glyph bitmap into a bytearray where each
		pixel is represented by a single byte.
		"""
		# Allocate a bytearray of sufficient size to hold the glyph bitmap.
		data = bytearray(bitmap.rows * bitmap.width)

		# Iterate over every byte in the glyph bitmap. Note that we're not
		# iterating over every pixel in the resulting unpacked bitmap --
		# we're iterating over the packed bytes in the input bitmap.
		for y in range(bitmap.rows):
			for byte_index in range(bitmap.pitch):

				# Read the byte that contains the packed pixel data.
				byte_value = bitmap.buffer[y * bitmap.pitch + byte_index]

				# We've processed this many bits (=pixels) so far. This determines
				# where we'll read the next batch of pixels from.
				num_bits_done = byte_index * 8

				# Pre-compute where to write the pixels that we're going
				# to unpack from the current byte in the glyph bitmap.
				rowstart = y * bitmap.width + byte_index * 8

				# Iterate over every bit (=pixel) that's still a part of the
				# output bitmap. Sometimes we're only unpacking a fraction of a byte
				# because glyphs may not always fit on a byte boundary. So we make sure
				# to stop if we unpack past the current row of pixels.
				for bit_index in range(min(8, bitmap.width - num_bits_done)):

					# Unpack the next pixel from the current glyph byte.
					bit = byte_value & (1 << (7 - bit_index))

					# Write the pixel to the output bytearray. We ensure that `off`
					# pixels have a value of 0 and `on` pixels have a value of 1.
					data[rowstart + bit_index] = 255 if bit else 0

		return data


class Font(object):
	def __init__(self, filename, size, min_kern=0):
		self.face = freetype.Face(filename)
		self.face.set_pixel_sizes(0, size)
		self.min_kern =min_kern # a minimum kerning distance (in pixels) useful for fonts which are not optimized for small sizes
		self.determine_font_dimensions();

	# find out the maximum scent and descent of some common characters and save them.
	def determine_font_dimensions(self):
		testString='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnoprstuvwxyz!?,.#1234567890Î'
		width, self.max_ascent,self.max_descent = self.text_dimensions(testString)
		
	def glyph_for_character(self, char):
		# Let FreeType load the glyph for the given character and tell it to render
		# a monochromatic bitmap representation.
		self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
		return Glyph.from_glyphslot(self.face.glyph)

	def render_character(self, char):
		glyph = self.glyph_for_character(char)
		return glyph.bitmap

	def kerning_offset(self, previous_char, char):
		"""
		Return the horizontal kerning offset in pixels when rendering `char`
		after `previous_char`.

		Use the resulting offset to adjust the glyph's drawing position to
		reduces extra diagonal whitespace, for example in the string "AV" the
		bitmaps for "A" and "V" may overlap slightly with some fonts. In this
		case the glyph for "V" has a negative horizontal kerning offset as it is
		moved slightly towards the "A".
		"""
		kerning = self.face.get_kerning(previous_char, char)

		# The kerning offset is given in FreeType's 26.6 fixed point format,
		# which means that the pixel values are multiples of 64.
		# we also use a minimum kerning if it is 0 to prevent small types from sticking together
		return max(math.ceil(float(kerning.x) / float(64)),self.min_kern)

	def text_dimensions(self, text):
		"""Return (width, max_ascent,max_descent) of `text` rendered in the current font."""
		width = 0
		max_ascent = 0
		max_descent = 0
		previous_char = None

		# For each character in the text string we get the glyph
		# and update the overall dimensions of the resulting bitmap.
		for char in text:
			glyph = self.glyph_for_character(char)
			max_ascent = max(max_ascent, glyph.ascent)
			max_descent = max(max_descent, glyph.descent)
			kerning_x = self.kerning_offset(previous_char, char)
			width += glyph.advance_width + kerning_x
			previous_char = char
		# With kerning, the advance width may be less than the width of the glyph's bitmap.
		# For the last character, we use the total width so that all of the glyph's pixels
		# fit into the returned dimensions.
		width += glyph.width-glyph.advance_width
		return (width, max_ascent, max_descent)
	#render a text to a buffer.
	def render_to_buffer(self, text, x_offset, y_offset,buffer):
		x = x_offset
		previous_char = None
		for char in text:
			glyph = self.glyph_for_character(char)

			# Take kerning information into account before we render the
			# glyph to the output bitmap.
			x +=( self.kerning_offset(previous_char, char))

			# The vertical drawing position should place the glyph
			# on the baseline as intended.
			y = y_offset+self.max_ascent-glyph.top
			buffer.bitblt(glyph.bitmap, x, y)
			x += glyph.advance_width
			previous_char = char
	def render_text(self, text, width=None, height=None, x_offset=0,y_offset=0):
		"""
		Render the given `text` into a GrayBitmap and return it.

		If `width`, `height`, and `baseline` are not specified they are computed using
		the `text_dimensions' method.
		"""
		text_width,text_ascend, text_descend=self.text_dimensions(text)
		if width==None:
			width = text_width
		if height==None:
			height=self.max_ascent+self.max_descent

		outbuffer = GrayBitmap(width, height)
		self.render_to_buffer(text,x_offset,y_offset,outbuffer)
		return outbuffer

		
#this class is used to map leds to pixels in the bitmap buffer.
class PixelMapper(object):
	def __init__(self,x_positions,y_positions):
		self.x_positions=x_positions
		self.y_positions=y_positions
	# pick the colors from the defined led-positions and put them in an array...
	def get_colors_from_bitmap(self,bitmap,x_offset=0,y_offset=0):
		#define a clamping function for convenient limiting of positions
		def get_clamped_pixel(bitmap,x,y):
			if(x>=0 and x<=bitmap.width-1 and y>=0 and y<=bitmap.height-1):
				return bitmap.get_at(x,y)
			else:
				return [0,0,0]
		n_leds=len(self.x_positions)
		output= bytearray(n_leds*3)
		outpos=0 #position in the output buffer
		for i in range(n_leds):
			output[outpos:outpos+3]=get_clamped_pixel(bitmap,self.x_positions[i]+x_offset,self.y_positions[i]+y_offset)
			outpos+=3
		return output
	# a fast way to extract colors from a bitmap for grid aligned leds
	def get_colors_from_grid(self,bitmap,x_offset=0,y_offset=0,led_width=60,led_height=10):
		x_offset=int(x_offset)
		led_width=int(led_width)
		led_height=int(led_height)
		output= bytearray(led_width*led_height*3)

		n_empty_start=max(-x_offset,0)
		n_empty_end=max((x_offset+led_width)-bitmap.width,0)
		n_to_show=max(led_width-n_empty_start-n_empty_end,0)
		
		output_start=n_empty_start*3
		input_start=max(x_offset*3,0)
			
		for row in range(bitmap.height):
			output[output_start:(output_start+n_to_show*3)]=bitmap.pixels[input_start:(input_start+n_to_show*3)]
			output_start+=led_width*3
			input_start+=bitmap.width*3
		return (output)
		
	def get_antialiased_from_bitmap(self,bitmap, x_offsets=[-0.25,0,0.25],y_offsets=[-0.25,0,0.25],x_offset=0,y_offset=0):
		#define a clamping function for convenient limiting of positions
		def get_clamped_pixel(bitmap,x,y):
			if(x>=0 and x<=bitmap.width-1 and y>=0 and y<=bitmap.height-1):
				return bitmap.get_at(x,y)
			else:
				return [0,0,0]
		n_leds=len(self.x_positions)
		output= bytearray(n_leds*3)
		outpos=0 #position in the output buffer
		n_samples=float(len(x_offsets)*len(y_offsets))
		for i in range(n_leds):
			out_val=[0.0,0.0,0.0]
			for x_o in x_offsets:
				for y_o in y_offsets:
					pixel=get_clamped_pixel(bitmap,self.x_positions[i]+x_o+x_offset,self.y_positions[i]+y_o+y_offset)
					out_val[0]+=pixel[0]
					out_val[1]+=pixel[1]
					out_val[2]+=pixel[2]
			output[outpos]=int(out_val[0]/n_samples)
			output[outpos+1]=int(out_val[1]/n_samples)
			output[outpos+2]=int(out_val[2]/n_samples)
			outpos+=3
		return output
	# scale the coordinates (can be useful to fit them to a given buffer size)
	def scale(self,x_scale,y_scale):
		for i in range(len(self.x_positions)):
			self.x_positions[i]*=x_scale
			self.y_positions[i]*=y_scale
	# add an offset to the coordinates (can be useful to fit them to a given buffer size)
	def add_offset(self,x_offset,y_offset):
		for i in range(len(self.x_positions)):
			self.x_positions[i]+=x_offset
			self.y_positions[i]+=y_offset
	
	# build a pixelmapper with a rectangulat grid of pixel positions
	@staticmethod
	def create_from_grid(width, height):
		x_pos=array.array('f',[])
		y_pos=array.array('f',[])
		for y in range (height):
			for x in range(width):
				x_pos.append(float(x))
				y_pos.append(float(y))
		return PixelMapper(x_pos,y_pos)
	
	# read pixel positions from a file generated by the TrafoPop Editor and return a PixelMapper instance with these coordiantes.
	@staticmethod
	def create_from_file(filename):
		if (not os.path.exists(filename)):
			print ('Led position definition file not found!')
			return
		file=open(filename,'r')	#open position file
		content=file.read()		#put the content into a string
		
		#now we extract the part of the file that interests us: the 'positions' array.
		#find the definition of the 'positions' array
		start_matcher=re.compile(r'Point\s*points\s*\[.*\]\s=\s\{') 
		match_result=start_matcher.search(content)
		if(match_result== None):
			print ('couldn\'t find beginning of points array in file!')
			return
		content=content[match_result.end():] #strip all the uninteresting part at the beginning...
		#find the closing bracket of the array definition
		end_matcher=re.compile(r'\}') 
		match_result=end_matcher.search(content)
		if(match_result== None):
			print ('couldn\'t find end of points array in file!')
			return
		content=content[:match_result.start()] #strip everything that comes after the bracket
		
		#at this point, we should have the content of the array in a string.
		
		# now we split it at all comma's
		string_parts=content.split(',')
		
		#and finally put the content into the right lists...
		isX=True # the first part is an x-coordinate
		x_pos=array.array('f',[])
		y_pos=array.array('f',[])
		for part in string_parts:
			#if we cannot convert it, we just skip it...
			try: 
				if (isX):
					x_pos.append(float(part))
				else:
					y_pos.append(float(part))
				isX= not isX
			except ValueError: 
				pass
		if(len(x_pos)!=len(y_pos)):
			print ('LED coordinate list contains contains an odd number of numbers!')
			return
		return PixelMapper(x_pos,y_pos)
