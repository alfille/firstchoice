# Global args
# python3
# part of firstchoice -- web interface to first choice database
# {C} Paul H Alfille 2021
# http://github.com/alfille/firstchoice

# A single value so far -- set by command line args
args = None

# Errors
# class MyError is extended from super class Exception
class User_Error(Exception):
   # Constructor method
   def __init__(self, value):
      self.value = value
   # __str__ display function
   def __str__(self):
      return(repr(self.value))
