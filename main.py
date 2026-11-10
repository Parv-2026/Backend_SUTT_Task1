from pathlib import Path
from matcher import CabPoolMatcher
from models import DESTINATIONS, SLOTS

BASE = Path(__file__).resolve().parent
CAB_FILE = BASE / 'data' / 'cabs.json'
SAVE_FILE = BASE / 'data' / 'state.json'


def choose(label, choices):
    while True:
        print(f'\n{label}:')
        for i, value in enumerate(choices, 1):
            print(f'  {i}. {value}')
        raw = input('Choose a number: ').strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print(f'Invalid choice. Enter a number from 1 to {len(choices)}.')


def show_waiting(app):
    print('\n=== WAITING STUDENTS (priority order within each trip) ===')
    count = 0
    for d in DESTINATIONS:
        for s in SLOTS:
            students = app.waiting(d, s)
            if students:
                print(f'\n{d} / {s}:')
                for r in students:
                    print(f'  {r.name} | Year {r.year} | {r.submitted_at} | #{r.sequence}')
                count += len(students)
    if count == 0:
        print('Nobody is waiting.')
    print(f'Total waiting: {count}')


def show_cabs(app):
    print('\n=== ALL CABS ===')
    for i, cab in enumerate(app.cabs, 1):
        print(f'{i}. {cab.driver} | {cab.destination} / {cab.slot} | '
              f'{len(cab.passengers)}/{cab.capacity} seats | '
              f'{"DEPARTED" if cab.departed else "OPEN"}')
        for r in cab.passengers:
            print(f'     - {r.name} (Year {r.year})')
    if not app.cabs:
        print('No cabs configured.')


def main():
    try:
        app = CabPoolMatcher.from_cab_file(CAB_FILE, SAVE_FILE)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Cannot start: invalid cab configuration: {exc}')
        return
    print('=== SUTT CAB POOL MATCHER ===')
    print(app.load())
    try:
        while True:
            print('\n1. Add ride request\n2. View waiting students and all cabs'
                  '\n3. Find matches (preview only)\n4. Dispatch cab\n5. Quit')
            choice = input('Select an option (1-5): ').strip()
            if choice == '1':
                name = input('Student name: ').strip()
                destination = choose('Destination', DESTINATIONS)
                slot = choose('Time slot', SLOTS)
                year_raw = input('Year (1-5): ').strip()
                try:
                    year = int(year_raw)
                    r = app.add_request(name, destination, slot, year)
                    print(f'Request added for {r.name}. Waiting for dispatch.')
                    if app.open_cab_index(destination, slot) is None:
                        print('Note: No open cab for this trip. Request remains in the queue.')
                except ValueError as exc:
                    print(f'Invalid request: {exc}')
            elif choice == '2':
                show_waiting(app)
                show_cabs(app)
            elif choice == '3':
                print('\n=== MATCH PREVIEW (no seats assigned) ===')
                results = app.preview()
                if not results:
                    print('No open cabs.')
                for index, cab, passengers in results:
                    print(f'Cab #{index + 1}: {cab.driver} | {cab.destination} / {cab.slot} '
                          f'| {len(passengers)}/{cab.capacity} potential seats')
                    if passengers:
                        for r in passengers:
                            print(f'  - {r.name} (Year {r.year})')
                    else:
                        print('  No matching waiting students.')
            elif choice == '4':
                destination = choose('Destination', DESTINATIONS)
                slot = choose('Time slot', SLOTS)
                cab, message = app.dispatch(destination, slot)
                print(message)
                if cab:
                    for r in cab.passengers:
                        print(f'  - {r.name} (Year {r.year})')
            elif choice == '5':
                try:
                    app.save()
                    print('State saved. Goodbye!')
                except OSError as exc:
                    print(f'WARNING: Could not save: {exc}')
                break
            else:
                print('Invalid menu option. Choose 1, 2, 3, 4, or 5.')
    except (KeyboardInterrupt, EOFError):
        print('\nExiting safely...')
        try:
            app.save()
            print('State saved.')
        except OSError as exc:
            print(f'WARNING: Could not save: {exc}')


if __name__ == '__main__':
    main()
