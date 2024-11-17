# TODO

## Database

[x] init from spreadsheet
[x] save in spreadsheet
[-] save data model to spreadsheet
[x] debug_schema
[x] fill static tables
[!] debug display name concatenation
[ ] delete_record_or_fail
[ ] delete_record_or_ignore
[ ] data control
    [ ] data types (file, handler, doc)
        [ ] document field types in doc
        [ ] any data type control on import?
        [ ] ...?
    [ ] mandatory fields
[ ] parameter table and secrets
[ ] DBHandler() returns the singleton object -> no need to pass the reference in calls
[ ] test save then init from spreadsheet -> types, etc

## Graphic interface

[ ] Database Manager
    [x] pick database
    [x] pick table
        [ ] column order
    [x] pick record
    [x] reload dynamically
    [ ] show record
        [x] text
        [x] boolean
        [ ] int
            [ ] doesn't show values not 0
        [x] ext no options
        [ ] ext radio buttons
            [ ] default or lack thereof
        [ ] ext dropdown
        [?] ext table
        [ ] filepath
        [ ] length
        [ ] date
    [ ] save record (create)
    [~] save record (edit)
    [ ] delete record
        [ ] if edit, popup
        [ ] if new, cancel
    [ ] cancel
        [x] edit -> reset to current record
        [ ] create -> reset to default values
    [ ] fix horizontal stretch when showing record form

[ ] Projects Handler
    [ ] show projects
    [ ] edit state and status
        [ ] sort to show?
        [ ] status of whole project?
            [ ] one or none?
            [ ] when and how to calculate?
    [ ] create a new project
        [ ] what info?
        [ ] new window or below?
    [ ] select project to work on
        [ ] how to select a step/action?
        [ ] process definition
    [ ] automatic steps
        [ ] files discovery
        [ ] html extraction and auto-fill
        [ ] etc 

[ ] user settings
    [ ] secrets
    [ ] database
    [ ] me person?

## Workflow

[ ] separate GUI and workflow?
