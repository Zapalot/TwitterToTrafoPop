import array
width=60
height=10
fo = open("position.h", "wb")
fo.write( ("Point points["+str(height*width)+"] = {\n").encode('ascii'));

x_pos=array.array('f',[])
y_pos=array.array('f',[])
for y in range (height):
	for x in range(width):
		fo.write(str(x).encode('ascii'))
		fo.write(",".encode('ascii'))
		fo.write(str(y).encode('ascii'))
		fo.write(",\n".encode('ascii'))
fo.write( "\n};\n".encode('ascii'));
fo.close()