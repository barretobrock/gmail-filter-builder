# Gmail Filter Builder
Builds a Gmail-supported xml file of email filters for overengineering your filtering in Gmail

## Background
I built this because I found managing my somewhat complex mail filters in Gmail to be quite unwieldy. By leveraging a JSON file, I'm able to manage multiple filters at once and I'm able to keep really large filters in one area (Gmail seems to have some kind of limit to manually entering emails in a filter.) 

## Installation
This package uses only the native Python3 libraries. You'll really just need to download the script and run locally.

## Example Use
```bash
python3 gfb.py ~/path/to/my/json_file.json
```
`mailFilters.xml` is then created in the same directory as the file. Use that to import in your Gmail Settings / Filters section.

## Example JSON Structure

### `data` section syntax
Filter
```
{number}-{joiner}-{section}[-not]
```
Joiner (joins filters in logic)
 ```
{number}-join
```
Breakdown:
 - number: Any number can go here, so long as it helps the key stay unique
 - joiner: This joins items in the list. Ideally, should be either `or` or `and`
 - section: This is the part of the email data you want to filter on. Supported sections:
    - `from`, `to`, `cc`, `bcc`, `subject`, `text`
 - not: This is an optional part, typically used when some criteria needs to be excluded

### Other sections outside of `data`
These key value pairs should match exactly what's accepted by Gmail when importing an XML file.
Examples:
 - `shouldArchive`: Takes the email out of your inbox (value set to `true`)
 - `shouldNeverMarkAsImportant`: Never marks the email as important (value set to `true`)
 - `shouldStar`: Automatically stars the email (value set to `true`)
 - `forwardTo`: Forward the emails to the address (value set to the email to send)

### Example
```json
{
  "Reading": { 
        "data": [  
            {
                "0-or-from": ["*.wired.com", "*.aeon.co", "*@nautil.us"],
                "1-join": "or",
                "2-or-text": ["this", "that"],
                "3-join": "and",
                "4-or-text": ["something else", "another thing"]
            }
        ],
        "shouldArchive": "true",
        "shouldNeverMarkAsImportant": "true"
    }
}
``` 

## Future Plans
 - Find a better way to 1) make the data keys easier to enter. Maybe leave out the numbering in the JSON file, but add it after reading in the file.
 - An easier way of adding the Archive, MarkAsImportant, etc flags at each entry.
