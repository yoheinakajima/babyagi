from functionz import func

# Initialize the Airtable Table instance
@func.register_function(
    metadata={"description": "Initialize Airtable table instance with access token, base ID, and table name."},
    key_dependencies=["airtable_access_token"],
    imports=["pyairtable"]
)
def init_airtable(base_id, table_name):
    """
    Initialize the Airtable Table instance.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :return: Airtable Table instance
    """
    api_token = globals()["airtable_access_token"]
    from pyairtable import Table
    return Table(api_token, base_id, table_name)


# Create a single record in a given Airtable table
@func.register_function(
    metadata={"description": "Create a new record in a specific Airtable table."},
    dependencies=["init_airtable"]
)
def create_record(base_id, table_name, record_data):
    """
    Create a new record in the specified Airtable table.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param record_data: Dictionary containing record fields and values
    :return: The newly created record
    """
    table = init_airtable(base_id, table_name)
    return table.create(record_data)


# Retrieve a single record by its ID
@func.register_function(
    metadata={"description": "Retrieve a specific record from Airtable using its record ID."},
    dependencies=["init_airtable"]
)
def get_record_by_id(base_id, table_name, record_id):
    """
    Retrieve a record by its unique ID from the specified Airtable table.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param record_id: Unique record ID in Airtable
    :return: The record data as a dictionary
    """
    table = init_airtable(base_id, table_name)
    return table.get(record_id)


# Update an existing record by its ID
@func.register_function(
    metadata={"description": "Update a record in Airtable using its ID and new field values."},
    dependencies=["init_airtable"]
)
def update_record(base_id, table_name, record_id, updated_fields):
    """
    Update a record in Airtable with new values for specified fields.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param record_id: Unique record ID in Airtable
    :param updated_fields: Dictionary with updated field values
    :return: The updated record data as a dictionary
    """
    table = init_airtable(base_id, table_name)
    return table.update(record_id, updated_fields)


# Delete a record by its ID
@func.register_function(
    metadata={"description": "Delete a specific record from an Airtable table."},
    dependencies=["init_airtable"]
)
def delete_record(base_id, table_name, record_id):
    """
    Delete a record from Airtable using its unique ID.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param record_id: Unique record ID in Airtable
    :return: Deletion confirmation message
    """
    table = init_airtable(base_id, table_name)
    return table.delete(record_id)


# Retrieve all records from a table
@func.register_function(
    metadata={"description": "Retrieve all records from a specific Airtable table."},
    dependencies=["init_airtable"]
)
def get_all_records(base_id, table_name, max_records=100, sort_by=None):
    """
    Get all records from the specified table, with optional sorting.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param max_records: Maximum number of records to retrieve
    :param sort_by: Optional list of fields to sort the records by
    :return: List of all records
    """
    table = init_airtable(base_id, table_name)
    return table.all(max_records=max_records, sort=sort_by)


# Upsert multiple records into a table based on unique fields
@func.register_function(
    metadata={"description": "Upsert (create or update) multiple records into a table using unique field identifiers."},
    dependencies=["init_airtable"]
)
def batch_upsert_records(base_id, table_name, records, key_fields):
    """
    Upsert multiple records into the specified table.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param records: List of records to be upserted
    :param key_fields: List of fields to use as unique keys
    :return: List of created or updated records
    """
    table = init_airtable(base_id, table_name)
    return table.batch_upsert(records, key_fields=key_fields)


# Batch create multiple records in a table
@func.register_function(
    metadata={"description": "Create multiple records in a table using batch operations."},
    dependencies=["init_airtable"]
)
def batch_create_records(base_id, table_name, records):
    """
    Create multiple records in the specified table.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param records: List of records to be created
    :return: List of created records
    """
    table = init_airtable(base_id, table_name)
    return table.batch_create(records)


# Batch delete multiple records from a table
@func.register_function(
    metadata={"description": "Delete multiple records in a table using batch operations."},
    dependencies=["init_airtable"]
)
def batch_delete_records(base_id, table_name, record_ids):
    """
    Batch delete records using their unique IDs.
    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param record_ids: List of record IDs to be deleted
    :return: Confirmation messages for deleted records
    """
    table = init_airtable(base_id, table_name)
    return table.batch_delete(record_ids)



from functionz import func

@func.register_function(
    metadata={"description": "Fetch a dynamic number of rows from Airtable based on a flexible search query."},
    dependencies=["init_airtable"],
    imports=["pyairtable"]
)
def get_dynamic_records(base_id, table_name, max_records=100, search_query=None, sort_by=None, fields=None, view=None, page_size=100):
    """
    Fetch a dynamic number of records from an Airtable table based on a custom query.

    :param base_id: ID of the Airtable base
    :param table_name: Name of the table within the base
    :param max_records: Maximum number of records to retrieve
    :param search_query: Dictionary of field-value pairs to match (e.g., {"Name": "Alice", "Age": 30})
    :param sort_by: List of fields to sort the records by (e.g., ["Name", "-Age"])
    :param fields: List of specific fields to retrieve (e.g., ["Name", "Age"])
    :param view: View ID or name to filter the records by
    :param page_size: Number of records per page request
    :return: List of matching records
    """
    from pyairtable.formulas import match
    table = init_airtable(base_id, table_name)

    # Construct a formula using the match function if search_query is provided
    formula = None
    if search_query:
        from pyairtable.formulas import match
        formula = match(search_query)

    # Use iterate to handle large datasets if max_records is set higher than page_size
    records = table.iterate(
        formula=formula,
        sort=sort_by,
        fields=fields,
        view=view,
        page_size=page_size,
        max_records=max_records
    )

    # Collect results from the generator into a list
    return list(records)

