"""Data models for the Cab Pool Matcher."""
from dataclasses import dataclass, field

DESTINATIONS = ('Delhi', 'Jaipur')
SLOTS = ('Morning', 'Afternoon', 'Evening', 'Night')


@dataclass
class RideRequest:
    name: str
    destination: str
    slot: str
    year: int
    submitted_at: str
    sequence: int

    def to_dict(self):
        return vars(self).copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Cab:
    driver: str
    capacity: int
    destination: str
    slot: str
    departed: bool = False
    passengers: list[RideRequest] = field(default_factory=list)

    def to_dict(self):
        return {'driver': self.driver, 'capacity': self.capacity,
                'destination': self.destination, 'slot': self.slot,
                'departed': self.departed,
                'passengers': [r.to_dict() for r in self.passengers]}

    @classmethod
    def from_dict(cls, data):
        return cls(driver=data['driver'], capacity=data['capacity'],
                   destination=data['destination'], slot=data['slot'],
                   departed=data.get('departed', False),
                   passengers=[RideRequest.from_dict(r) for r in data.get('passengers', [])])
