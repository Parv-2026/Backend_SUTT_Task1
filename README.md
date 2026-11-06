# Backend_SUTT_Task1

# Models.py
This file describes two data models used by the application:
1.)Ride Request
2.)Cab
### 1.)Ride Request
This file stores student information, including name, destination, preferred time slot, and academic year.
It also records when a student submits a ride request.
### 2.)Cab
This file stores driver information, destination, time slot, and seating capacity.
It maintains the list of assigned passengers and lastly, it
tracks whether the cab has been dispatched.

# Data JSON FILE CAB
This file was used to accept the information from our original Ride Request class in Models.py in the form of a dictonary.
We first create an object using our Models.py then send it to the Cab JSON file in the form of a dictionary; this makes sure our data doesn't get lost 
When we close the Python program as it is stored in the JSON File.When we later upload those file contents back from_dict() reconstructs
the student information when the application restarts.
