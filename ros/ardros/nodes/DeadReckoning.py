#!/usr/bin/env python
'''
Created February, 2011

@author: Dr. Rainer Hessmer

  DeadReckoning.py - A Python implementation of the tutorial
  http://www.ros.org/wiki/pr2_controllers/Tutorials/Using%20the%20base%20controller%20with%20odometry%20and%20transform%20information
  Copyright (c) 2011 Dr. Rainer Hessmer.  All right reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:
      * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
      * Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
      * Neither the name of the Vanadium Labs LLC nor the names of its 
        contributors may be used to endorse or promote products derived 
        from this software without specific prior written permission.
  
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  DISCLAIMED. IN NO EVENT SHALL VANADIUM LABS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
  OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import roslib; roslib.load_manifest('ardros')
import rospy
import tf
from tf import transformations
import time
#import numpy
import math

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class Driver(object):
	'''
	Implements the logic for driving a given distance by monitoring the transform
	messages that contain the odometry information class for communicating with an Arduino board over serial port.
	'''

	def __init__(self):
		'''
		Initializes the receiver class. 
		port: The serial port to listen to.
		baudrate: Baud rate for the serial communication
		'''

		rospy.init_node('DeadReckoning')
		
		self._VelocityCommandPublisher = rospy.Publisher("cmd_vel", Twist)

	def DriveForward(self, distance, speed):
		'''
		Drive forward a specified distance based on odometry information
		distance [m]: the distance to travel in the x direction (>0: forward, <0: backwards)
		speed [m/s]: the speed with which to travel; must be positive
		'''

		forward = (distance >= 0)
		listener = tf.TransformListener()
		# wait for the listener to get the first message
		listener.waitForTransform("/base_link", "/odom", rospy.Time(), rospy.Duration(1.0))
		
		# record the starting transform from the odometry to the base frame
		(startTranslation, startRotation) = listener.lookupTransform("/base_link", "/odom", rospy.Time(0))
		# startTranslation is a tuple holding the x,y,z components of the translation vector
		# startRotation is a tuple holding the four components of the quaternion
		
		#transformer = tf.TransformerROS(True, rospy.Duration(1.0))
		# for details related to the TransformerROS class see http://www.ros.org/wiki/tf/TfUsingPython
		#startTransform = transformer.fromTranslationRotation(startTranslation, startRotation)
		
		done = False

		velocityCommand = Twist()
		if forward:
			velocityCommand.linear.x = speed # going forward m/s
		else:
			velocityCommand.linear.x = -speed # going forward m/s
			
		velocityCommand.angular.z = 0.0 # no angular velocity
		#rate = rospy.Rate(10.0) # update rate in Hz

		while True:
			try:
				(currentTranslation, currentRotation) = listener.lookupTransform("/base_link", "/odom", rospy.Time(0))
				#currentTransform = transformer.fromTranslationRotation(currentTranslation, currentRotation)
				
				#invertedStartTransform = numpy.linalg.inv(startTransform)
				#relativeTransform = numpy.dot(invertedStartTransform, currentTransform);
				#print relativeTransform
				
				dx = currentTranslation[0] - startTranslation[0]
				dy = currentTranslation[1] - startTranslation[1]
				#dy = currentTranslation[2] - startTranslation[2]
				
				distanceMoved = math.sqrt(dx * dx + dy * dy)
				print distanceMoved
				if (forward):
					arrived = distanceMoved >= distance
				else:
					arrived = distanceMoved >= -distance
				
				if (arrived):
					break
				else:
					# send the drive command
					#print("sending vel command" + str(velocityCommand))
					self._VelocityCommandPublisher.publish(velocityCommand)
				
			except (tf.LookupException, tf.ConnectivityException):
				continue

			time.sleep(0.1)

		#stop
		velocityCommand.linear.x = 0.0
		velocityCommand.angular.z = 0.0
		self._VelocityCommandPublisher.publish(velocityCommand)
		
		return done


if __name__ == '__main__':
	try:
		driver = Driver()
		driver.DriveForward(distance = -0.5, speed = 0.1);
	except rospy.ROSInterruptException: pass

