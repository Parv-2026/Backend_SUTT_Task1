import heapq
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from models import Cab, RideRequest, DESTINATIONS, SLOTS


def validate_trip(destination, slot):
    if destination not in DESTINATIONS:
        raise ValueError('Destination must be Delhi or Jaipur.')
    if slot not in SLOTS:
        raise ValueError('Slot must be Morning, Afternoon, Evening, or Night.')


def validate_request(r):
    if not isinstance(r.name, str) or not r.name.strip():
        raise ValueError('Student name cannot be empty.')
    validate_trip(r.destination, r.slot)
    if type(r.year) is not int or not 1 <= r.year <= 5:
        raise ValueError('Year must be an integer from 1 to 5.')
    if type(r.sequence) is not int or r.sequence < 0:
        raise ValueError('Invalid submission sequence.')
    if not isinstance(r.submitted_at, str) or not r.submitted_at:
        raise ValueError('Missing submission time.')


def validate_cab(cab):
    if not isinstance(cab.driver, str) or not cab.driver.strip():
        raise ValueError('Driver name cannot be empty.')
    validate_trip(cab.destination, cab.slot)
    if type(cab.capacity) is not int or not 1 <= cab.capacity <= 4:
        raise ValueError('Cab capacity must be between 1 and 4.')
    if type(cab.departed) is not bool:
        raise ValueError('Invalid departure status.')
    if len(cab.passengers) > cab.capacity:
        raise ValueError('Cab has too many passengers.')
    if not cab.departed and cab.passengers:
        raise ValueError('An open cab cannot already contain passengers.')
    for r in cab.passengers:
        validate_request(r)
        if (r.destination, r.slot) != (cab.destination, cab.slot):
            raise ValueError('Passenger trip does not match cab.')


class CabPoolMatcher:
    def __init__(self, cabs, save_path=None, autosave=True):
        self.cabs = list(cabs)
        for cab in self.cabs:
            validate_cab(cab)
        self.queues = {(d, s): [] for d in DESTINATIONS for s in SLOTS}
        self.next_sequence = 0
        self.save_path = Path(save_path) if save_path else None
        self.autosave = autosave

    @classmethod
    def from_cab_file(cls, path, save_path=None, autosave=True):
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError('Cab configuration must be a JSON list.')
        return cls([Cab.from_dict(c) for c in raw], save_path, autosave)

    def _push(self, request):
        heapq.heappush(self.queues[(request.destination, request.slot)],
                       (-request.year, request.sequence, request))

    def add_request(self, name, destination, slot, year):
        request = RideRequest(name.strip(), destination, slot, year,
                              datetime.now(timezone.utc).isoformat(), self.next_sequence)
        validate_request(request)
        self._push(request)
        self.next_sequence += 1
        self._save_after_change()
        return request

    def waiting(self, destination=None, slot=None):
        if destination is not None or slot is not None:
            if destination is None or slot is None:
                raise ValueError('Provide both destination and slot.')
            validate_trip(destination, slot)
            return [item[2] for item in sorted(self.queues[(destination, slot)])]
        return [r for d in DESTINATIONS for s in SLOTS for r in self.waiting(d, s)]

    def open_cab_index(self, destination, slot):
        validate_trip(destination, slot)
        return next((i for i, c in enumerate(self.cabs)
                     if not c.departed and (c.destination, c.slot) == (destination, slot)), None)

    def preview(self):
        """Preview each open cab in file order, without modifying any queue."""
        simulated = {trip: list(heap) for trip, heap in self.queues.items()}
        for heap in simulated.values():
            heapq.heapify(heap)
        results = []
        for index, cab in enumerate(self.cabs):
            if cab.departed:
                continue
            heap = simulated[(cab.destination, cab.slot)]
            passengers = [heapq.heappop(heap)[2] for _ in range(min(cab.capacity, len(heap)))]
            results.append((index, cab, passengers))
        return results

    def dispatch(self, destination, slot):
        index = self.open_cab_index(destination, slot)
        if index is None:
            return None, 'No open cab is available for that trip.'
        heap = self.queues[(destination, slot)]
        if not heap:
            return None, 'No students are waiting for that trip; no cab was dispatched.'
        cab = self.cabs[index]
        cab.passengers.extend(heapq.heappop(heap)[2] for _ in range(min(cab.capacity, len(heap))))
        cab.departed = True
        self._save_after_change()
        return cab, f'Cab driven by {cab.driver} dispatched with {len(cab.passengers)} passenger(s).'

    def _save_after_change(self):
        if self.autosave and self.save_path:
            try:
                self.save()
            except OSError as exc:
                print(f'WARNING: Could not save state: {exc}')

    def save(self):
        if self.save_path is None:
            return
        state = {'version': 1, 'next_sequence': self.next_sequence,
                 'waiting': [r.to_dict() for r in self.waiting()],
                 'cabs': [c.to_dict() for c in self.cabs]}
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                    dir=self.save_path.parent, prefix='.cabpool-', suffix='.tmp',
                    delete=False) as f:
                temp_name = f.name
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_name, self.save_path)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)

    def load(self):
        """Return a status message; leave fresh config untouched on invalid save."""
        if self.save_path is None or not self.save_path.exists():
            return 'No saved state found. Starting fresh with sample cabs.'
        try:
            with self.save_path.open(encoding='utf-8') as f:
                data = json.load(f)
            if type(data) is not dict or data.get('version') != 1:
                raise ValueError('Unsupported save format.')
            cabs = [Cab.from_dict(c) for c in data['cabs']]
            for cab in cabs:
                validate_cab(cab)
            waiting = [RideRequest.from_dict(r) for r in data['waiting']]
            all_requests = waiting + [r for c in cabs for r in c.passengers]
            for r in all_requests:
                validate_request(r)
            sequences = [r.sequence for r in all_requests]
            if len(set(sequences)) != len(sequences):
                raise ValueError('Duplicate submission sequence.')
            next_sequence = data['next_sequence']
            if type(next_sequence) is not int or next_sequence < 0 or (sequences and next_sequence <= max(sequences)):
                raise ValueError('Invalid sequence counter.')
            # Validate everything before mutating the running app.
            new_queues = {(d, s): [] for d in DESTINATIONS for s in SLOTS}
            for r in waiting:
                heapq.heappush(new_queues[(r.destination, r.slot)], (-r.year, r.sequence, r))
            self.cabs, self.queues, self.next_sequence = cabs, new_queues, next_sequence
            return 'Saved state restored successfully.'
        except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
            return f'Saved state could not be loaded ({exc}). Starting fresh with sample cabs.'
