kris-kringle
---
Kris Kringle is a tradition similar to Secret Santa. This project will generate a randomized assignment between families

# TODO:
- Validate input file schema
- Remove preferred senders from regular senders list before assignment (avoid duplicates)
- Get the "historical" checking working correctly.
- 


# Notes
## Input Excel Schema
The "KK Pick 2021.xlsx" Excel file is the input to the program. It has the following sheets and columns:
`Family`: 
  - Name: Text
  - Group: int [1-7]
  - Group2: int [4]

`Preferred Assign`:
  (Preferred Assignments)
  - KK Giver: Text
  - KK Receiver: int [1-7]

`Historical`: 
  (Previous assignments throughout the years)
  - KK Giver: Text
  - VLookup: Text  # TAKE OUT
  - 2020: Text
  - 2019: Text


## Logic Flow
0. Optionally start with GUI for user input
1. Read input Excel workbook file and find expected sheets
2. Determine weights for each assignee based on:
    a. preference
    b. historical data (avoid recent repeats)
    c. assignments (avoid cycles)
3. Generate random assignments for preferred assignments
4. Generate random "regular" assignments for the remainder
5. Write out assignments and weights file.

## Constraints
Each sender and receiver pair are unique and mutually exclusive.
  - A sender may have only one assignment.
  - A receiver may have only one sender.

Quirks:
Pre-Assign must have at least two potentials (can be duplicated to force a single option)

## Dependencies
MacOS: may require:

```
> brew install python-tk
```
