# Gmail Filter Builder
Builds a filter in GMail via a YAML file organized by desired labels, filters for these labels and what actions to perform on emails matching these filters.

Two options to use GFB:
 1. GMail API:
    Pros: Less involved (everything is automated)
    Cons: GMail API authentication required - if your GMail is managed by another entity, this may not be possible.
 2. XML file generation:
    Pros: More control, more flexibility in application, can be used with any GMail account (i.e., managed or personal)
    Cons: More manual (removal of old filters, upload of new) 

A previous version of this script built a simple XML file to manually upload in the "Import Filters" section of the [GMail filter settings page](https://mail.google.com/mail/u/0/#settings/filters). In future iterations, this functionality will be brought back as a fall-back.

## Background
I built this because I found managing my somewhat complex mail filters in Gmail to be quite unwieldy. By leveraging a YAML file, I'm able to manage multiple filters at once and I'm able to keep really large filters in one area (Gmail seems to have some kind of limit to manually entering emails in a filter.) 

## Installation
To install, make sure you have all the package requirements installed. You can install them to your virtual environment of choice with this command:
```bash
pip3 install -r requirements.txt
```  
From this point, you'll have two options regarding how you'd like to use GFB

## Option 1: GFB with GMail API
This section covers the unique steps needed to set up using GFB leveraging the GMail API

### Authentication (required only for GMail API)
 1. Follow step 1 on [this page](https://developers.google.com/gmail/api/quickstart/python) to enable the GMail API for your account
 2. Rename the `credentials.json` file you just made and put it in the `creds` folder in this repo.
 3. Run the `auth.py` script. This will attempt a connection to the GMail API and subsequently try to pull a list of all the labels and filters under the account.
    _NOTE: A google auth window will pop up in your browser to grant access to the scopes needed to read/write labels and filters._
    ```bash
    python3 auth.py
    ```
 4. If the script above ran without error, you're good to go and a pickle file has been created in the `creds` folder to indicate that the credentials have been successfully authenticated. 
    _NOTE: Should you ever decide to change the scope in `gmail.py`, you'll need to delete the `token.pickle` file and re-run auth to regenerate the pickle file._

### Example Use 
```bash
python3 gfb_api_method.py ~/path/to/my/yaml_file.yaml
```

## Option 2: GFB with XML generation
This section covers the unique steps needed to run GFB using only the XML building aspect

### Example Use
```bash
python3 gfb_xml_method.py ~/path/to/my/yaml_file.yaml
```

## Example YAML Structure
```yaml
MyLabel/Sublabel:
    data:
        - or-from: ["this@domain.com", "another@sites.domain.com"]
        - join: or
        - section:
            - or-text: ["this", "that"]
            - join: and
            - or-text: ["hello", "everyone"]
    # yields this:
    # from:(this@domain.com OR another@sites.domain.com) OR (("this" OR "that") AND ("hello" OR "everyone"))
    actions: [archive, never-important]
    # Archives (remove from inbox, but don't delete) & never marks important
```
### `data` section syntax
Filter structure
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
 - not: This is an optional part, typically used when criteria needs to be negated
    example: `or-from-not: [email list]` yields `... NOT from:(email1 OR email2 OR email 3)`

### `action` section
This section is just a list of actions you want performed on any email that gets this label.
Actions:
 - `mark-read`: Marks email as read
 - `never-spam`: Never marks the email as spam
 - `archive`: Takes the email out of your inbox (but doesn't delete)
 - `never-important`: Never marks the email as important
 - `always-important`: Always marks the email as important
 - `delete-email`: Delete the email (move to trash)
 - `mark-starred`: Stars the email

## Future Plans
 - Verbose logging!
