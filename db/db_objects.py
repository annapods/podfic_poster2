
from typing import Any, Dict, List, Optional, Union
from numpy import nan

from pandas import DataFrame, ExcelFile

from src.base_object import BaseObject


def display_name_concat(to_concat:List[str]) -> str:
    """ Concatenate display name parts """
    return " - ".join(to_concat)


def clean_df(df:DataFrame) -> DataFrame:
    """ Clean dataframe """
    df.dropna(how="all", inplace=True)
    df.fillna(nan, inplace=True)
    df.replace([nan], [None], inplace=True)
    return df


class BaseDataObject(BaseObject):
    """ Data or data model base object class """
    def __init__(self, ID:str, verbose:Optional[bool]=True) -> None:
        super().__init__(verbose)
        self.ID = ID

    def __str__(self) -> str:
        return self.ID
    
    def __repr__(self) -> str:
        return f"{type(self).__name__.lower()}:{self.ID}"


class Field(BaseDataObject):
    """ Field in data model """
    def __init__(
            self, parent_table:BaseDataObject, field_name:str, type:str,
            foreign_key_table:Optional[BaseDataObject]=None,
            part_of_display_name:Optional[bool]=False, mandatory:Optional[bool]=False,
            default_value:Optional[str]="", display_in_table:Optional[bool]=True,
            display_order:Optional[int]=1000000, verbose:Optional[bool]=True):
        """ NOTE parent_table and foreign_key_table are Table objects
        Order of declaration in the file doesn't allow for more specific type hinting """
        ID = display_name_concat([parent_table.table_name, field_name])
        super().__init__(ID, verbose)
        self.parent_table = parent_table
        self.field_name = field_name
        self.type = type
        self.foreign_key_table = foreign_key_table
        self.part_of_display_name = part_of_display_name
        self.mandatory = mandatory
        self.default_value = default_value
        self.display_in_table = display_in_table
        self.display_order = display_order


class Table(BaseDataObject):
    """ Table in data model """
    def __init__(
            self, table_name:str, fields:Optional[List[Field]] = [],
            sort_rows_by:Optional[Field]=None, verbose:Optional[bool]=True):
        super().__init__(table_name, verbose)
        self.table_name = table_name
        self.sort_rows_by = sort_rows_by
        self.fields = fields

    def get_field(self, field_name:str) -> Field:
        """ Fetch one field based on field name """
        found_fields = [field for field in self.fields if field.field_name==field_name]
        if len(found_fields) == 0: raise NameError(
            f"Coudln't find field {field_name} in table {self} in data model")
        if len(found_fields) > 1: raise NameError(
            f"Found several field {field_name} in table {self} in data model")
        return found_fields[0]
    
    def get_fields(self, field_names:List[str]) -> List[Field]:
        """ Fetch several fields based on field names """
        fields = [self.get_field(field_name) for field_name in field_names]
        return fields


class Record(BaseDataObject):
    """ Record in a table
    Records are not loaded in the DataModel """
    def __init__(
            self, ID:str, parent_table:Table, values:Dict[Field, Any],
            verbose:Optional[bool]=True) -> None:
        super().__init__(ID, verbose)
        self.parent_table = parent_table
        self.values = values


class DataModel(BaseObject):
    """ Data model """
    def __init__(self, spreadsheet_path:str="db/datamodel.ods", verbose:Optional[bool]=True):
        super().__init__(verbose)
        self.spreadsheet_path = spreadsheet_path
        self.load_db_model_from_spreadsheet()
    

    def load_db_model_from_spreadsheet(self) -> None:
        """ Load tables and fields based on spreadsheet """

        # Load model in dataframes
        excel_file = ExcelFile(self.spreadsheet_path)
        data_table_df = clean_df(excel_file.parse("data_table"))
        data_field_df = clean_df(excel_file.parse("data_field"))

        # Load tables in model
        self.tables = [
            Table(table_name, sort_rows_by=sort_rows_by) for table_name, sort_rows_by \
            in zip(data_table_df["table_name"], data_table_df["sort_rows_by"])]
        # NOTE sort_rows_by is supposed to be a Field object but is a string for now
        
        field_info = [
            "field_name", "type", "foreign_key_table", "part_of_display_name", "mandatory",
            "default_value", "display_in_table", "display_order"]
        
        # Load fields in tables in model
        for table in self.tables:
            table_field_df = data_field_df[data_field_df["table_name"] == table.ID]
            table.fields = [
                Field(table, *info_list) for info_list \
                in zip(*[table_field_df[column] for column in field_info])]
        # NOTE foreign_key_table is supposed to be a Table object but is a string for now
            
        # Add ID, display_name and creation_date fields to tables
        for table in self.tables:
            table.fields = [
                    Field(table, "ID", "INTEGER", mandatory=True, display_in_table=False,
                        display_order=-2),
                    Field(table, "display_name", "TEXT", mandatory=True, display_in_table=False,
                        display_order=-1),
                ] + table.fields + [
                    Field(table, "creation_date", "DATE", mandatory=True)
                ]
            
        # Crosslink sort_rows_by and foreign_key_table with the actual objects
        for table in self.tables:
            table.sort_rows_by = table.get_field(table.sort_rows_by) if table.sort_rows_by else None
            for field in table.fields:
                field.foreign_key_table = self.get_table(field.foreign_key_table) \
                    if field.foreign_key_table else None

    
    def get_table(self, table_name:str) -> Table:
        """ Fetch table based on table name """
        found_tables = [table for table in self.tables if table.table_name==table_name]
        if len(found_tables) == 0: raise NameError(f"Coudln't find table {table_name} in data model")
        if len(found_tables) > 1: raise NameError(f"Found several {table_name} in data model")
        return found_tables[0]
