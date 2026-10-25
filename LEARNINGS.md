* Project Decisions and Lessons

** Stage One

*** Initial Text Parsing
- Decided on using a literal for determining who the turn belongs to for the sake simplicity
- TurnIDs are 1 based allowing for a 0 ID to be caught as an error and keeping the numerical convention more consistent with human logic
- interview turns get IDs as well, this can lead to consistently placing responses in context
- speaker labels normalized as the name is what's important, not case and whitespace sensitivity
- edge cases have not yet been handled as I wanted to get a working parser up and running and determine what edge cases were relevant before handling


