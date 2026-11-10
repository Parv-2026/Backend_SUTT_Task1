# Cab Pool Matcher 

A Python-based terminal application built for SUTT Backend Recruitment Task 1.

The project helps students find shared cabs travelling to Delhi or Jaipur. Students can choose a time slot (Morning, Afternoon, Evening, or Night), and the system matches them based on priority.

Senior students get higher priority, while students from the same year are matched on a first-come-first-served basis.

Features

Add ride requests with student details, destination, and time slot.

Priority-based matching using Python's heapq.

Preview matches before dispatching a cab.

Dispatch cabs even when they aren't completely full.

View waiting students and cab availability.

Save and restore data using JSON.

Handle invalid inputs and missing or corrupted save files.

Unit tests for the matching logic.

How to Run

### python main.py
To run the tests:
python -m unittest discover -s tests -v

How Matching Works
Each destination and time slot has its own priority queue.
I used Python's heapq module to manage requests. Since it is a min-heap, I store the negative of the student's year so that senior students come first.
Each request also gets a unique sequence number to maintain first-come-first-served ordering among students in the same year.
(-request.year, request.sequence, request)
The program also supports match previews. These use copies of the queues, so checking possible matches doesn't change the actual waiting list.
When a cab is dispatched, the highest-priority students are assigned up to the cab's capacity.

Saving Data

I used JSON to save the application's state so that requests and cab details aren't lost when the program closes.

data/cabs.json stores the initial cab configuration.

data/state.json stores waiting requests, assigned passengers, and cab departure status.

The program saves changes automatically and restores the previous state when restarted.

Edge Cases Handled

Partially filled cabs: A cab can depart without filling every seat.

No available cabs: New requests can still be added to the waiting list.

Same-year students: Requests are handled in submission order.

Large queues: Heap operations keep matching efficient even with 1,000 requests.



