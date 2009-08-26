# Copyright (c) 2009 John (Jack) Angers, jacktasia@gmail.com
# Licensed under the terms of the MIT License (see LICENSE.txt)

import os

## TODO
def runit(cmd):
	#a = subprocess.Popen(cmd,shell=True)
	os.system(cmd)
	print "ran: " + cmd



if __name__ == '__main__':
	runit('del yay.jar')
        runit('rmdir /s /q cachedir')
	
	runit("javac -classpath jythonlib.jar *.java")
	runit("copy jythonlib.jar yay.jar")
	runit("jar ufm yay.jar manifest.txt *.class *.py *.gif *.conf")

	runit('del *.class')

        runit('move yay.jar ../../')
	runit('java -jar c:/yay.jar')
	#maybe use API to upload directly to "Downloads" section
