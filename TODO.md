# TODO

## Database

[x] init from spreadsheet
[x] save in spreadsheet
[-] save data model to spreadsheet
[x] debug_schema
[x] fill static tables
[ ] data types (file, handler, doc)
    [ ] document field types in doc
    [ ] any data type control on import?
    [ ] ...?
[ ] records in GUI
[ ] delete_record_or_fail, delete_record_or_ignore
[ ] test save then init from spreadsheet -> types, etc

## Graphic interface

[ ] Database Manager
    [ ] pick database
    [ ] show tables, fields, records
    [ ] reload
    [ ] run command
    [ ] insert button -> open new window
        [ ] text fields from data model
        [ ] integer fields from data model
        [ ] date and datetime fields from data model
        [ ] foreign key dropdowns from data model
    [ ] update record button -> pre-fill form with values

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