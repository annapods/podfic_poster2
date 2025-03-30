# TODO

## Database

[x] init from spreadsheet
[x] save in spreadsheet
[ ] save data model to spreadsheet
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
        [x] filepath
        [x] length
        [x] date
        [x] ext no options
        [x] ext radio buttons
        [x] ext dropdown
        [ ] ext table
        [ ] ext add new record to foreign table
            [ ] popup?
            [ ] default value on one side of the rel
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
    [ ] tables to select project and section
        [ ] select one
        [ ] aggregated status for whole project?
        [ ] show project sections of selected project
    [ ] button to create a new project
        [ ] what info?
        [ ] new window or below?
    [ ] button to create a new section
    [ ] form to edit project status by stage for selected project section
    [ ] buttons for steps/actions -> new windows? or frames?
        [ ] setup
            [ ] download from ao3
            [ ] extract info from html
        [ ] post
            [ ] automatic file discovery
        [ ] promo
        [ ] archive
            [ ] bsky?
            [ ] save a yaml file?

[ ] user settings
    [ ] secrets
    [ ] database
    [ ] me person?

## Basics

[ ] Gtk app??? how to automate tests pls
[ ] separate GUI and workflow? -> turn GUI bricks into a python library/separate project
[ ] turn db handler into another library? or already separate enough?
[ ] model view controler whatever??
