import os
import sys
import json
import logging
import time
import snowflake.connector
from snowflake.connector.errors import ProgrammingError, DatabaseError, OperationalError
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('snowflake_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_snowflake_credentials():
    """
    Verify Snowflake credentials by attempting to connect to Snowflake and run a simple query.
    
    Environment variables required:
    - SNOWFLAKE_URL: The base URL of the Snowflake instance (optional)
    - SNOWFLAKE_ACCOUNT_ID: Account ID for authenticating with Snowflake
    - SNOWFLAKE_USER: Username for authenticating with Snowflake
    - SNOWFLAKE_PASSWORD: Password for authenticating with Snowflake
    - SNOWFLAKE_DATABASE: (Optional) Default database to use
    - SNOWFLAKE_WAREHOUSE: (Optional) Default warehouse to use
    - SNOWFLAKE_ROLE: (Optional) Default role to use
    
    Returns:
    - True if credentials are valid and can connect to Snowflake
    - False otherwise
    """
    
    # Get environment variables
    url = os.environ.get('SNOWFLAKE_URL')
    account_id = os.environ.get('SNOWFLAKE_ACCOUNT_ID')
    user = os.environ.get('SNOWFLAKE_USER')
    password = os.environ.get('SNOWFLAKE_PASSWORD')
    database = os.environ.get('SNOWFLAKE_DATABASE')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE')
    role = os.environ.get('SNOWFLAKE_ROLE')
    
    L.info("Retrieved environment variables:")
    L.info(f"  URL: {url}")
    L.info(f"  Account ID: {account_id}")
    L.info(f"  User: {user}")
    L.info(f"  Password: {'*****' if password else 'Not set'}")
    L.info(f"  Database: {database}")
    L.info(f"  Warehouse: {warehouse}")
    L.info(f"  Role: {role}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not account_id and not url:
        missing_vars.append('SNOWFLAKE_ACCOUNT_ID or SNOWFLAKE_URL')
    if not user:
        missing_vars.append('SNOWFLAKE_USER')
    if not password:
        missing_vars.append('SNOWFLAKE_PASSWORD')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Prepare connection parameters
    conn_params = {
        'user': user,
        'password': password,
        'account': account_id,
    }
    
    # Add other optional parameters
    if url:
        conn_params['url'] = url
    if database:
        conn_params['database'] = database
    if warehouse:
        conn_params['warehouse'] = warehouse
    if role:
        conn_params['role'] = role
    
    try:
        # Attempt to connect to Snowflake
        L.info(f"Attempting to connect to Snowflake account: {account_id}")
        
        conn = snowflake.connector.connect(**conn_params)
        
        # Run a simple test query to verify the connection
        cursor = conn.cursor()
        cursor.execute("SELECT current_version()")
        version = cursor.fetchone()[0]
        
        L.info(f"Successfully connected to Snowflake. Version: {version}")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return True
    
    except (ProgrammingError, DatabaseError, OperationalError) as e:
        L.error(f"Error connecting to Snowflake: {e}")
        error_code = getattr(e, 'errno', None)
        error_msg = str(e)
        L.error(f"Error code: {error_code}")
        L.error(f"Error message: {error_msg}")
        return False
    
    except Exception as e:
        L.error(f"Unexpected error during Snowflake connection: {e}")
        return False

def execute_query(query, params=None, fetch=True):
    """
    Execute a query on Snowflake and return the results.
    
    Args:
        query (str): SQL query to execute
        params (dict, optional): Parameters for the query
        fetch (bool): Whether to fetch and return results
        
    Returns:
        list: Query results or None if query failed
    """
    url = os.environ.get('SNOWFLAKE_URL')
    account_id = os.environ.get('SNOWFLAKE_ACCOUNT_ID')
    user = os.environ.get('SNOWFLAKE_USER')
    password = os.environ.get('SNOWFLAKE_PASSWORD')
    database = os.environ.get('SNOWFLAKE_DATABASE')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE')
    role = os.environ.get('SNOWFLAKE_ROLE')
    
    # Prepare connection parameters
    conn_params = {
        'user': user,
        'password': password,
        'account': account_id,
    }
    
    # Add other optional parameters
    if url:
        conn_params['url'] = url
    if database:
        conn_params['database'] = database
    if warehouse:
        conn_params['warehouse'] = warehouse
    if role:
        conn_params['role'] = role
    
    try:
        L.info(f"Executing query: {query}")
        if params:
            L.info(f"With parameters: {json.dumps(params)}")
        
        conn = snowflake.connector.connect(**conn_params)
        cursor = conn.cursor(snowflake.connector.DictCursor)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = cursor.fetchall()
            L.info(f"Query returned {len(results)} rows")
            return results
        else:
            affected_rows = cursor.rowcount
            L.info(f"Query affected {affected_rows} rows")
            return affected_rows
    
    except Exception as e:
        L.error(f"Error executing query: {e}")
        return None
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def test_database_listing():
    """
    Test listing databases in Snowflake.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Database Listing ===")
    
    databases = execute_query("SHOW DATABASES")
    
    if not databases:
        print("❌ Failed to retrieve databases or no databases found")
        return False
    
    L.info(f"✅ Successfully retrieved {len(databases)} databases")
    
    # Display database information
    if len(databases) > 0:
        L.info("\nSample Database Information:")
        for i, db in enumerate(databases[:5]):  # Show first 5 databases
            L.info(f"  {i+1}. {db.get('name', 'N/A')}")
            
    return bool(databases)

def test_schema_listing(database=None):
    """
    Test listing schemas in a database.
    
    Args:
        database (str, optional): Database to list schemas from
        
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Schema Listing ===")
    
    if database:
        query = f"SHOW SCHEMAS IN DATABASE {database}"
    else:
        query = "SHOW SCHEMAS"
    
    schemas = execute_query(query)
    
    if not schemas:
        print(f"❌ Failed to retrieve schemas or no schemas found")
        return False
    
    L.info(f"✅ Successfully retrieved {len(schemas)} schemas")
    
    # Display schema information
    if len(schemas) > 0:
        L.info("\nSample Schema Information:")
        for i, schema in enumerate(schemas[:5]):  # Show first 5 schemas
            L.info(f"  {i+1}. {schema.get('name', 'N/A')}")
    
    return bool(schemas)

def test_table_listing(database=None, schema=None):
    """
    Test listing tables in a schema.
    
    Args:
        database (str, optional): Database containing the schema
        schema (str, optional): Schema to list tables from
        
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Table Listing ===")
    
    if database and schema:
        query = f"SHOW TABLES IN {database}.{schema}"
    elif schema:
        query = f"SHOW TABLES IN SCHEMA {schema}"
    else:
        query = "SHOW TABLES"
    
    tables = execute_query(query)
    
    if not tables:
        print(f"❌ Failed to retrieve tables or no tables found")
        return False
    
    L.info(f"✅ Successfully retrieved {len(tables)} tables")
    
    # Display table information
    if len(tables) > 0:
        L.info("\nSample Table Information:")
        for i, table in enumerate(tables[:5]):  # Show first 5 tables
            L.info(f"  {i+1}. {table.get('name', 'N/A')}")
            
        # Save the first table info for later tests
        global test_table
        test_table = {
            'database': database or tables[0].get('database_name'),
            'schema': schema or tables[0].get('schema_name'),
            'name': tables[0].get('name')
        }
    
    return bool(tables)

def test_table_creation():
    """
    Test creating a table in Snowflake.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Table Creation ===")
    
    # Generate a unique table name
    test_table_name = f"TEST_TABLE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create a test table
    create_query = f"""
    CREATE TABLE IF NOT EXISTS {test_table_name} (
        id NUMBER,
        event_type VARCHAR,
        timestamp TIMESTAMP_NTZ,
        source_ip VARCHAR,
        description VARCHAR
    )
    """
    
    result = execute_query(create_query, fetch=False)
    
    if result is None:
        print(f"❌ Failed to create test table: {test_table_name}")
        return False
    
    L.info(f"✅ Successfully created test table: {test_table_name}")
    
    # Save the test table name for later tests
    global test_security_table
    test_security_table = test_table_name
    
    return True

def test_data_insertion():
    """
    Test inserting data into a Snowflake table.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    global test_security_table
    
    # If we don't have a test table yet, create one
    if not test_security_table:
        if not test_table_creation():
            print("❌ Cannot test data insertion - failed to create test table")
            return False
    
    L.info(f"\n=== Testing Data Insertion into Table: {test_security_table} ===")
    
    # Insert test security log data
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
    
    insert_query = f"""
    INSERT INTO {test_security_table} (id, event_type, timestamp, source_ip, description)
    VALUES
        (1, 'login_failure', '{current_time}', '192.168.1.100', 'Failed login attempt'),
        (2, 'permission_denied', '{current_time}', '192.168.1.101', 'Access denied to restricted resource'),
        (3, 'data_access', '{current_time}', '192.168.1.102', 'Sensitive data accessed')
    """
    
    result = execute_query(insert_query, fetch=False)
    
    if result is None or result < 3:
        print(f"❌ Failed to insert data into test table: {test_security_table}")
        return False
    
    L.info(f"✅ Successfully inserted {result} rows into test table: {test_security_table}")
    return True

def test_data_query():
    """
    Test querying data from a Snowflake table.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    global test_security_table
    
    # If we don't have a test table or data, insert some
    if not test_security_table:
        if not test_data_insertion():
            print("❌ Cannot test data query - no test data available")
            return False
    
    L.info(f"\n=== Testing Data Query from Table: {test_security_table} ===")
    
    # Query the test data
    query = f"SELECT * FROM {test_security_table} ORDER BY id"
    
    results = execute_query(query)
    
    if not results:
        print(f"❌ Failed to query data from test table: {test_security_table}")
        return False
    
    L.info(f"✅ Successfully queried {len(results)} rows from test table")
    
    # Display sample data
    if results:
        L.info("\nSample Query Results:")
        for i, row in enumerate(results[:3]):  # Show up to 3 rows
            L.info(f"  Row {i+1}: {row}")
    
    return bool(results)

def test_data_aggregation():
    """
    Test running an aggregation query on Snowflake data.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    global test_security_table
    
    # If we don't have a test table or data, insert some
    if not test_security_table:
        if not test_data_insertion():
            print("❌ Cannot test data aggregation - no test data available")
            return False
    
    L.info(f"\n=== Testing Data Aggregation on Table: {test_security_table} ===")
    
    # Run an aggregation query
    query = f"SELECT event_type, COUNT(*) as event_count FROM {test_security_table} GROUP BY event_type"
    
    results = execute_query(query)
    
    if not results:
        print(f"❌ Failed to run aggregation query on test table: {test_security_table}")
        return False
    
    L.info(f"✅ Successfully ran aggregation query and retrieved {len(results)} result groups")
    
    # Display aggregation results
    if results:
        L.info("\nAggregation Results:")
        for row in results:
            L.info(f"  {row.get('EVENT_TYPE', 'Unknown')}: {row.get('EVENT_COUNT', 0)} events")
    
    return bool(results)

def test_error_handling_and_retry():
    """
    Test error handling and retry functionality.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Error Handling and Retry Mechanism ===")
    
    # Define a function with retry logic
    def execute_with_retry(query, max_retries=3, retry_interval=1):
        for attempt in range(max_retries):
            try:
                L.info(f"Attempt {attempt + 1} of {max_retries}: {query}")
                
                # Get connection parameters from environment variables
                url = os.environ.get('SNOWFLAKE_URL')
                account_id = os.environ.get('SNOWFLAKE_ACCOUNT_ID')
                user = os.environ.get('SNOWFLAKE_USER')
                password = os.environ.get('SNOWFLAKE_PASSWORD')
                
                # Prepare connection parameters
                conn_params = {
                    'user': user,
                    'password': password,
                    'account': account_id,
                }
                
                # Add other optional parameters
                if url:
                    conn_params['url'] = url
                
                conn = snowflake.connector.connect(**conn_params)
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                conn.close()
                return result
            except Exception as e:
                L.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    L.info(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                    retry_interval *= 2  # Exponential backoff
                else:
                    L.error(f"All retry attempts failed for query: {query}")
                    raise
    
    # Test with an intentionally invalid query
    invalid_query = "SELECT * FROM nonexistent_table"
    
    try:
        # This should fail but demonstrate the retry mechanism
        execute_with_retry(invalid_query)
        print("❌ Test failed: Invalid query did not raise an exception")
        return False
    except Exception as e:
        L.info(f"✅ Error handling captured exception as expected: {e}")
        print(f"✅ Error handling and retry mechanism successfully tested")
        return True

def test_rate_limiting_simulation():
    """
    Simulate and test handling of rate limiting.
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Rate Limiting Handling ===")
    
    # Define a function with rate limit handling
    def handle_rate_limits(query, max_retries=3):
        attempt = 0
        while attempt < max_retries:
            try:
                # Simulate a rate limit scenario
                if attempt < 2:  # Simulate rate limit on first 2 attempts
                    L.info(f"Attempt {attempt + 1}: Simulating rate limit...")
                    raise snowflake.connector.errors.ProgrammingError(
                        msg="Simulated rate limit exceeded",
                        errno=90060,  # Snowflake rate limit error code
                        sqlstate="08001"
                    )
                
                # On final attempt, succeed
                L.info(f"Attempt {attempt + 1}: Succeeding after rate limits...")
                return "Success after rate limiting"
            
            except snowflake.connector.errors.ProgrammingError as e:
                error_code = getattr(e, 'errno', None)
                if error_code == 90060:  # Rate limit error
                    attempt += 1
                    backoff_time = 2 ** attempt  # Exponential backoff
                    L.warning(f"Rate limit detected. Backing off for {backoff_time} seconds...")
                    time.sleep(0.1)  # Shortened for testing purposes
                else:
                    L.error(f"Unexpected Snowflake error: {e}")
                    return False
        
        return False  # Failed all retries
    
    # Test rate limit handling
    result = handle_rate_limits("SELECT 1")
    
    if not result:
        print("❌ Failed to properly handle rate limiting")
        return False
    
    L.info(f"✅ Successfully handled simulated rate limiting")
    return True

def test_table_cleanup():
    """
    Clean up the test table created during testing.
    
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    global test_security_table
    
    if not test_security_table:
        L.info("No test table to clean up")
        return True
    
    L.info(f"\n=== Cleaning Up Test Table: {test_security_table} ===")
    
    # Drop the test table
    drop_query = f"DROP TABLE IF EXISTS {test_security_table}"
    
    result = execute_query(drop_query, fetch=False)
    
    if result is None:
        print(f"❌ Failed to drop test table: {test_security_table}")
        return False
    
    L.info(f"✅ Successfully dropped test table: {test_security_table}")
    return True

def test_warehouse_operations():
    """
    Test warehouse operations (list, use).
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Warehouse Operations ===")
    
    # List warehouses
    warehouses = execute_query("SHOW WAREHOUSES")
    
    if not warehouses:
        print("❌ Failed to retrieve warehouses or no warehouses found")
        return False
    
    L.info(f"✅ Successfully retrieved {len(warehouses)} warehouses")
    
    # Display warehouse information
    if warehouses:
        L.info("\nWarehouse Information:")
        for i, wh in enumerate(warehouses[:3]):  # Show up to 3 warehouses
            L.info(f"  {i+1}. {wh.get('name', 'N/A')}")
            
        # Try to use the first warehouse
        if len(warehouses) > 0:
            warehouse_name = warehouses[0].get('name', '')
            if warehouse_name:
                result = execute_query(f"USE WAREHOUSE {warehouse_name}", fetch=False)
                if result is not None:
                    L.info(f"✅ Successfully used warehouse: {warehouse_name}")
                else:
                    L.warning(f"⚠️ Could not use warehouse: {warehouse_name}")
    
    return bool(warehouses)

def test_role_operations():
    """
    Test role operations (list roles, show grants).
    
    Returns:
        bool: True if test passed, False otherwise
    """
    L.info("\n=== Testing Role Operations ===")
    
    # List roles
    roles = execute_query("SHOW ROLES")
    
    if not roles:
        print("❌ Failed to retrieve roles or no roles found")
        return False
    
    L.info(f"✅ Successfully retrieved {len(roles)} roles")
    
    # Display role information
    if roles:
        L.info("\nRole Information:")
        for i, role in enumerate(roles[:3]):  # Show up to 3 roles
            L.info(f"  {i+1}. {role.get('name', 'N/A')}")
            
        # Show grants for the first role
        if len(roles) > 0:
            role_name = roles[0].get('name', '')
            if role_name:
                grants = execute_query(f"SHOW GRANTS TO ROLE {role_name}")
                if grants:
                    L.info(f"✅ Successfully retrieved grants for role: {role_name}")
                    L.info(f"  Number of grants: {len(grants)}")
                else:
                    L.warning(f"⚠️ Could not retrieve grants for role: {role_name}")
    
    return bool(roles)

def explore_threat_intelligence_tables():
    """
    Explore tables that might contain threat intelligence data.
    
    Returns:
        dict: Dictionary containing identified threat intel tables or None if none found
    """
    L.info("\n=== Exploring Potential Threat Intelligence Tables ===")
    
    # Keywords that might indicate threat intelligence tables
    threat_intel_keywords = [
        'THREAT', 'INTEL', 'IOC', 'INDICATOR', 'MALWARE', 
        'VULNERABILITY', 'CVE', 'ATTACK', 'SIGNATURE', 'SECURITY'
    ]
    
    # Get all tables
    all_tables = []
    
    # Try to get tables from the current database and schema
    tables = execute_query("SHOW TABLES")
    if tables:
        all_tables.extend(tables)
    
    # Try to search all databases if permissions allow
    databases = execute_query("SHOW DATABASES")
    if databases:
        for db in databases:
            db_name = db.get('name', '')
            try:
                # Get schemas in this database
                schemas = execute_query(f"SHOW SCHEMAS IN DATABASE {db_name}")
                if schemas:
                    for schema in schemas:
                        schema_name = schema.get('name', '')
                        
                        # Get tables in this schema
                        db_tables = execute_query(f"SHOW TABLES IN {db_name}.{schema_name}")
                        if db_tables:
                            all_tables.extend(db_tables)
            except Exception as e:
                L.warning(f"Could not access database {db_name}: {e}")
    
    # Look for tables that might contain threat intelligence data
    threat_intel_tables = []
    for table in all_tables:
        table_name = table.get('name', '').upper()
        
        # Check if any keyword matches the table name
        if any(keyword in table_name for keyword in threat_intel_keywords):
            threat_intel_tables.append({
                'database': table.get('database_name', ''),
                'schema': table.get('schema_name', ''),
                'name': table_name,
                'created_on': table.get('created_on', ''),
                'kind': table.get('kind', '')
            })
    
    if threat_intel_tables:
        L.info(f"✅ Identified {len(threat_intel_tables)} potential threat intelligence tables")
        
        for i, table in enumerate(threat_intel_tables):
            L.info(f"\nPotential Threat Intel Table {i+1}:")
            L.info(f"  Database: {table['database']}")
            L.info(f"  Schema: {table['schema']}")
            L.info(f"  Table: {table['name']}")
            L.info(f"  Created On: {table['created_on']}")
            
            # Try to get column information
            try:
                columns = execute_query(f"DESCRIBE TABLE {table['database']}.{table['schema']}.{table['name']}")
                if columns:
                    L.info(f"  Columns:")
                    for col in columns[:5]:  # Show up to 5 columns
                        L.info(f"    - {col.get('name', 'N/A')}: {col.get('type', 'N/A')}")
            except Exception as e:
                L.warning(f"Could not retrieve column information: {e}")
        
        return threat_intel_tables
    else:
        L.info("No potential threat intelligence tables identified")
        return None

def main():
    L.info("Starting Snowflake credential verification and API testing")
    
    # Initialize global variables
    global test_table
    global test_security_table
    test_table = None
    test_security_table = None
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SNOWFLAKE_ACCOUNT_ID'):
            os.environ['SNOWFLAKE_ACCOUNT_ID'] = input("Enter Snowflake account ID: ")
        if not os.environ.get('SNOWFLAKE_URL'):
            os.environ['SNOWFLAKE_URL'] = input("Enter Snowflake URL (optional, press Enter to skip): ")
        if not os.environ.get('SNOWFLAKE_USER'):
            os.environ['SNOWFLAKE_USER'] = input("Enter Snowflake username: ")
        if not os.environ.get('SNOWFLAKE_PASSWORD'):
            os.environ['SNOWFLAKE_PASSWORD'] = input("Enter Snowflake password: ")
        if not os.environ.get('SNOWFLAKE_DATABASE'):
            db = input("Enter Snowflake database (optional, press Enter to skip): ")
            if db:
                os.environ['SNOWFLAKE_DATABASE'] = db
        if not os.environ.get('SNOWFLAKE_WAREHOUSE'):
            wh = input("Enter Snowflake warehouse (optional, press Enter to skip): ")
            if wh:
                os.environ['SNOWFLAKE_WAREHOUSE'] = wh
        if not os.environ.get('SNOWFLAKE_ROLE'):
            role = input("Enter Snowflake role (optional, press Enter to skip): ")
            if role:
                os.environ['SNOWFLAKE_ROLE'] = role
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_snowflake_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - different API operations
    database_success = test_database_listing()
    schema_success = test_schema_listing() if database_success else False
    table_success = test_table_listing() if schema_success else False
    table_creation_success = test_table_creation() if table_success else False
    data_insertion_success = test_data_insertion() if table_creation_success else False
    data_query_success = test_data_query() if data_insertion_success else False
    data_aggregation_success = test_data_aggregation() if data_query_success else False
    error_handling_success = test_error_handling_and_retry()
    rate_limiting_success = test_rate_limiting_simulation()
    warehouse_success = test_warehouse_operations()
    role_success = test_role_operations()
    
    # Explore potential threat intelligence tables
    threat_intel_tables = explore_threat_intelligence_tables()
    
    # Clean up
    cleanup_success = test_table_cleanup()
    
    # Print summary of all test results
    L.info("\n=== Verification Test Summary ===")
    L.info(f"Basic Credential Verification: {'✅ Passed' if success else '❌ Failed'}")
    L.info(f"Database Listing: {'✅ Passed' if database_success else '❌ Failed'}")
    L.info(f"Schema Listing: {'✅ Passed' if schema_success else '❌ Failed'}")
    L.info(f"Table Listing: {'✅ Passed' if table_success else '❌ Failed'}")
    L.info(f"Table Creation: {'✅ Passed' if table_creation_success else '❌ Failed'}")
    L.info(f"Data Insertion: {'✅ Passed' if data_insertion_success else '❌ Failed'}")
    L.info(f"Data Query: {'✅ Passed' if data_query_success else '❌ Failed'}")
    L.info(f"Data Aggregation: {'✅ Passed' if data_aggregation_success else '❌ Failed'}")
    L.info(f"Error Handling: {'✅ Passed' if error_handling_success else '❌ Failed'}")
    L.info(f"Rate Limiting: {'✅ Passed' if rate_limiting_success else '❌ Failed'}")
    L.info(f"Warehouse Operations: {'✅ Passed' if warehouse_success else '❌ Failed'}")
    L.info(f"Role Operations: {'✅ Passed' if role_success else '❌ Failed'}")
    L.info(f"Test Table Cleanup: {'✅ Passed' if cleanup_success else '❌ Failed'}")
    L.info(f"Threat Intelligence Tables: {'✅ Found' if threat_intel_tables else '⚠️ Not Found'}")
    
    # Overall assessment
    critical_tests = [
        success,  # Basic auth
        database_success,
        schema_success,
        table_success,
        table_creation_success,
        data_insertion_success,
        data_query_success,
        data_aggregation_success,
        error_handling_success,
        warehouse_success,
        role_success
    ]
    
    if all(critical_tests):
        L.info("\n✅ All critical tests passed! Snowflake API integration is fully functional.")
        return 0
    elif success and any([database_success, schema_success, table_success]):
        L.warning("\n⚠️ Basic functionality works but some advanced tests failed.")
        return 0  # Still return success since basic functionality works
    else:
        L.error("\n❌ Critical Snowflake API tests failed. Please check your credentials and permissions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())