# Gmail Filter Builder
Builds a Gmail-supported xml file of email filters for overengineering your filtering in Gmail

## Background
I built this because I found managing my somewhat complex mail filters in Gmail to be quite unwieldy. By leveraging a YAML file, I'm able to manage multiple filters at once and I'm able to keep really large filters in one area (Gmail seems to have some kind of limit to manually entering emails in a filter.) 

## Installation
This package uses only the native Python3 libraries. You'll really just need to download the script and run locally.

## Example Use
```bash
python3 gfb.py ~/path/to/my/yaml_file.yaml
```
`mailFilters.xml` is then created in the same directory as the source file. Use that to import in your Gmail Settings / Filters section.

## Example YAML Structure
```yaml
# Filters
MyFilter/Subfilter:
    data:
        - or-from: ["this@domain.com", "another@sites.domain.com"]
        - join: or
        - or-text: ["this", "that"]
        - join: and
        - or-text: ["hello", "everyone"]
    shouldArchive: true
    shouldNeverMarkAsImportant: true
```
### `data` section syntax
Filters
```
{joiner}-{section}[-not]
```
Joiners (joins filters in logic)
 ```yaml
join: and
join: or
```
Breakdown:
 - joiner: This joins sections in the list. Ideally, should be either `or` or `and`
 - section: This is the part of the email data you want to filter on. Supported sections:
    - `from`, `to`, `cc`, `bcc`, `subject`, `text`
 - not: This is an optional part, typically used when some criteria needs to be excluded

### Other sections outside of `data`
These key value pairs should match exactly what's accepted by Gmail when importing an XML file.
Examples:
 - `shouldArchive`: Takes the email out of your inbox (value set to `true`)
 - `shouldNeverMarkAsImportant`: Never marks the email as important (value set to `true`)
 - `shouldAlwaysMarkAsImportant`: Always marks the email as important (value set to `true`)
 - `shouldStar`: Automatically stars the email (value set to `true`)
 - `forwardTo`: Forward the emails to the address (value set to the email to send)

## Importing the finished XML file
1. Go to your gmail settings page, click on Filters and Blocked Addresses
2. Scroll down to the bottom, click Import Filters.
3. Select the XML file that was just made
4. Click Open File.
5. Select the filters you want, import them!

## Future Plans
 - An easier way of adding the Archive, MarkAsImportant, etc flags at each entry.
