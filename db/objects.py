""" Database objects and auxiliary functions
A DataModel object, instanciated from an excel datamodel file, contains Table objects
which contain Field objects
Records are not saved in the DataModel or Table objects but have a link back to their parent Table """

from typing import Any, Dict, List, Optional, Union
from numpy import nan
from pandas import DataFrame, ExcelFile


from src.base_object import BaseObject


def display_name_concat(to_concat:List[str]) -> str:
    """ Concatenate display name parts """
    print("DEBUG", " - ".join(to_concat))
    return " - ".join(to_concat)


def clean_df(df:DataFrame) -> DataFrame:
    """ Clean dataframe """
    df.dropna(how="all", inplace=True)
    df.fillna(nan, inplace=True)
    df.replace([nan], [None], inplace=True)
    return df


class BaseDataObject(BaseObject):
    """ Data or data model base object class to be inherited from """
    def __init__(self, display_name:str, verbose:Optional[bool]=True) -> None:
        super().__init__(verbose)
        self.display_name = display_name
    def __str__(self) -> str:
        return self.display_name.replace("_"," ")
    def __repr__(self) -> str:
        return f"{type(self).__name__.lower()}: {self.display_name.replace('_',' ')}"


class Field(BaseDataObject):
    """ Field in a Table """
    def __init__(
            self, parent_table:BaseDataObject, field_name:str,
            foreign_key_table:Optional[BaseDataObject]=None,
            part_of_display_name:Optional[bool]=False, mandatory:Optional[bool]=False,
            editable:Optional[bool]=True, default_value:Optional[str]="",
            display_order:Optional[int]=1000000, verbose:Optional[bool]=True):
        """ NOTE parent_table and foreign_key_table are Table objects
        Order of declaration in the file doesn't allow for more specific type hinting """
        display_name = display_name_concat([parent_table.table_name, field_name])
        super().__init__(display_name, verbose)
        self.parent_table = parent_table
        self.field_name = field_name
        self.foreign_key_table = foreign_key_table
        self.part_of_display_name = part_of_display_name
        self.mandatory = mandatory
        self.editable = editable
        self.default_value = default_value
        self.display_order = display_order

    def __str__(self) -> str:
        return self.display_name.replace("_"," ")
    
    def __repr__(self) -> str:
        return f"Field in {self.parent_table}: {self}"
    
    def validate(self, value:Any) -> bool:
        """ Validate the value in type/format and mandatory/not """
        raise NotImplementedError

class IntField(Field):
    def validate(self, value:Any) -> bool:
        if type(value) is not int: return False
        if self.mandatory and value is None: return False
        return True
    
class TextField(Field):
    def validate(self, value:Any) -> bool:
        if (type(value)) is not str: return False
        if self.mandatory and value == "": return False
        return True
    
class BoolField(Field):
    def validate(self, value:Any) -> bool:
        if (type(value)) is not bool: return False
        return True
    
class DateField(Field):
    def validate(self, value:Any) -> bool:
        if (type(value)) is not str: return False
        if self.mandatory and value == "": return False
        # TODO format checks
        return True
    
class FilepathField(Field):
    def validate(self, value:Any) -> bool:
        if (type(value)) is not str: return False
        if self.mandatory and value == "": return False
        # TODO format checks
        return True
    
class LengthField(Field):
    def validate(self, value:Any) -> bool:
        if (type(value)) is not str: return False
        if self.mandatory and value == "": return False
        # TODO format checks
        return True


py_to_spreadsheet_type_mapping = {
    TextField: "TEXT", IntField: "INTEGER",
    BoolField: "BOOLEAN", DateField:"DATE",
    FilepathField:"FILEPATH", LengthField:"TEXT"
}

spreadsheet_to_py_type_mapping = {
    "TEXT": TextField, "INTEGER": IntField,
    "BOOLEAN": BoolField, "DATE":DateField,
    "FILEPATH": FilepathField, "LENGTH": LengthField
}


class Table(BaseDataObject):
    """ Table in a DataModel, contains Fields """
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
    Records are not loaded in the DataModel or the Table
    ID and display_name can be empty if the record doesn't exist in the database yet """
    def __init__(
            self, parent_table:Table,
            values:Dict[Field, Any],
            verbose:Optional[bool]=True) -> None:
        super().__init__("", verbose)
        self.parent_table = parent_table
        # ID and creation date fields
        # Values are automatically generated by the database
        ID_field = parent_table.get_field("ID")
        if ID_field not in values:
            self.ID = None
            values[ID_field] = None
        else:
            self.ID = values[ID_field]
        creation_date_field = parent_table.get_field("creation_date")
        if creation_date_field not in values:
            self.creation_date = None
            values[creation_date_field] = None
        else:
            self.creation_date = values[creation_date_field]
        # All values are kept
        self.values = values
        # Display name is also managed by the database but can change
        # and needs to be known by the python program
        self.recalculate_display_name()
    
    def __repr__(self) -> str:
        return f"{self.parent_table}: {self}"
    
    def save_to_db(self, new:bool=False):
        from db.handler import SQLiteHandler
        if new:
            SQLiteHandler().create_record_or_fail(self)
        else:
            SQLiteHandler().update_record_or_fail(self)
    
    def recalculate_display_name(self):
        """ """
        self.display_name = display_name_concat([self.values[field] for field in self.values if field.part_of_display_name])
        self.values[self.parent_table.get_field("display_name")] = self.display_name



class DataModel(BaseObject):
    """ Data model, contains Tables, which contain Fields """
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
            "field_name", "foreign_key_table", "part_of_display_name", "mandatory",
            "editable", "default_value", "display_order"]
        
        # Load fields in tables in model
        for table in self.tables:
            table.fields = []
            # All field info from the spreadsheet
            table_field_df = data_field_df[data_field_df["table_name"] == table.table_name]
            types = table_field_df["type"]
            infos = zip(*[table_field_df[column] for column in field_info])
            table.fields = [spreadsheet_to_py_type_mapping[type](table, *info_list) for type, info_list in zip(types, infos)]
        # NOTE foreign_key_table is supposed to be a Table object but is a string for now
            
        # Add ID, display_name and creation_date fields to tables
        for table in self.tables:
            table.fields = [
                    IntField(table, "ID", mandatory=False, editable=False,
                        display_order=-2),
                    TextField(table, "display_name", mandatory=True, editable=False,
                        display_order=-1),
                ] + table.fields + [
                    DateField(table, "creation_date", mandatory=True, editable=False)
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
