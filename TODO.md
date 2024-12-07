# TODO

## Database

[x] init from spreadsheet
[x] save in spreadsheet
[-] save data model to spreadsheet
[x] debug_schema
[x] fill static tables
[?] debug display name concatenation
[x] delete_record_or_fail
[x] delete_record_or_ignore

[ ] parameter table and secrets
[ ] DBHandler() returns the singleton object -> no need to pass the reference in calls
[ ] test save then init from spreadsheet
    [ ] data controls: types, mandatory, ...
    [ ] examples


## Graphic interface

[ ] Database Manager
    [x] pick database
    [x] pick table
        [x] column order
    [x] pick record
    [x] reload dynamically
    [ ] show record
        [x] text
        [x] boolean
        [x] int
        [x] ext no options
        [x] ext radio buttons
        [ ] ext dropdown
        [?] ext table
        [ ] ext add new record to foreign table
            [ ] popup?
            [ ] default value on one side of the rel)
        [ ] filepath
        [ ] length
        [ ] date
    [x] create record
        [ ] autoselect the newly created record
    [x] modify record
        [x] keep modified record selected
    [x] delete record
        [x] sql handler functions
        [ ] if record selected, confirmation popup
        [ ] if no record selected, reset to default values
    [ ] cancel
        [x] if record selected, reset to current record
        [ ] if no record selected, reset to default values
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
            [ ] setup
            [ ] post
            [ ] promo
            [ ] archive
    [ ] automatic steps
        [ ] files discovery
        [ ] html extraction and auto-fill
        [ ] etc 

[ ] user settings
    [ ] secrets
    [ ] database
    [ ] me person?

## Basics

[ ] separate GUI and workflow?
[ ] model view whatever
