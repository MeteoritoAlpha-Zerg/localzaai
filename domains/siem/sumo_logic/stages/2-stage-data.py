import os
import sys
import json
import logging
import requests
import time
import random
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
L = logging.getLogger(__name__)

class SumoLogicAPI:
    """
    Sumo Logic API client for data staging operations.
    """
    
    def __init__(self, url, access_id, access_key, verify_ssl=True, timeout=120):
        self.base_url = url.rstrip('/')
        if not self.base_url.endswith('/api'):
            self.base_url += '/api'
            
        self.access_id = access_id
        self.access_key = access_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Setup authentication
        self.auth = HTTPBasicAuth(access_id, access_key)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.auth = self.auth
        self.session.verify = verify_ssl

    def _make_request(self, method, endpoint, **kwargs):
        """Make an authenticated request to the Sumo Logic API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            return response
        except requests.exceptions.RequestException as e:
            L.error(f"Request failed: {e}")
            raise

    def check_existing_data(self):
        """
        Check existing data in Sumo Logic (collectors, sources, content).
        
        Returns:
            dict: Information about existing data or None if failed
        """
        try:
            L.info("Checking existing data in Sumo Logic...")
            
            # Check collectors
            collectors_response = self._make_request('GET', '/v1/collectors')
            collectors = []
            if collectors_response.status_code == 200:
                collectors_data = collectors_response.json()
                collectors = collectors_data.get('collectors', [])
                L.info(f"Found {len(collectors)} existing collectors")
            
            # Check sources for each collector
            total_sources = 0
            for collector in collectors:
                sources_response = self._make_request('GET', f"/v1/collectors/{collector['id']}/sources")
                if sources_response.status_code == 200:
                    sources_data = sources_response.json()
                    sources = sources_data.get('sources', [])
                    total_sources += len(sources)
            
            L.info(f"Found {total_sources} existing sources across all collectors")
            
            # Check content (folders and searches)
            content_items = 0
            try:
                personal_response = self._make_request('GET', '/v2/content/folders/personal')
                if personal_response.status_code == 200:
                    personal_folder = personal_response.json()
                    
                    # Get children of personal folder
                    children_response = self._make_request('GET', f"/v2/content/{personal_folder['id']}/children")
                    if children_response.status_code == 200:
                        children_data = children_response.json()
                        content_items = len(children_data.get('children', []))
                        L.info(f"Found {content_items} items in personal folder")
            except Exception as e:
                L.warning(f"Could not check content items: {e}")
            
            return {
                'collectors': len(collectors),
                'sources': total_sources,
                'content_items': content_items,
                'collector_details': collectors
            }
            
        except Exception as e:
            L.error(f"Error checking existing data: {e}")
            return None

    def is_data_sufficient(self, existing_data, min_collectors=2, min_sources=3, min_content=1):
        """
        Determine if existing data is sufficient for testing.
        
        Args:
            existing_data (dict): Data from check_existing_data()
            min_collectors (int): Minimum collectors required
            min_sources (int): Minimum sources required
            min_content (int): Minimum content items required
            
        Returns:
            tuple: (is_sufficient, missing_requirements)
        """
        if not existing_data:
            return False, ["Could not retrieve existing data"]
        
        missing_requirements = []
        
        if existing_data['collectors'] < min_collectors:
            missing_requirements.append(f"Need at least {min_collectors} collectors (found {existing_data['collectors']})")
        
        if existing_data['sources'] < min_sources:
            missing_requirements.append(f"Need at least {min_sources} sources (found {existing_data['sources']})")
        
        if existing_data['content_items'] < min_content:
            missing_requirements.append(f"Need at least {min_content} content items (found {existing_data['content_items']})")
        
        is_sufficient = len(missing_requirements) == 0
        
        if is_sufficient:
            L.info("✅ Existing data is sufficient for testing")
        else:
            L.info("❌ Existing data is insufficient:")
            for req in missing_requirements:
                L.info(f"  - {req}")
        
        return is_sufficient, missing_requirements

    def create_hosted_collector(self, name, description="Test hosted collector"):
        """
        Create a hosted collector.
        
        Args:
            name (str): Collector name
            description (str): Collector description
            
        Returns:
            dict: Collector information or None if failed
        """
        try:
            L.info(f"Creating hosted collector: {name}")
            
            collector_config = {
                "collector": {
                    "collectorType": "Hosted",
                    "name": name,
                    "description": description,
                    "category": "test/staging"
                }
            }
            
            response = self._make_request('POST', '/v1/collectors', json=collector_config)
            
            if response.status_code == 201:
                collector_data = response.json()
                collector_id = collector_data['collector']['id']
                L.info(f"✅ Created hosted collector '{name}' with ID: {collector_id}")
                return collector_data['collector']
            else:
                L.error(f"❌ Failed to create collector: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception creating collector: {e}")
            return None

    def create_http_source(self, collector_id, name, description="Test HTTP source", category="test/http"):
        """
        Create an HTTP source for a collector.
        
        Args:
            collector_id (int): Collector ID
            name (str): Source name
            description (str): Source description
            category (str): Source category
            
        Returns:
            dict: Source information or None if failed
        """
        try:
            L.info(f"Creating HTTP source: {name} for collector {collector_id}")
            
            source_config = {
                "source": {
                    "sourceType": "HTTP",
                    "name": name,
                    "description": description,
                    "category": category,
                    "hostName": "",
                    "automaticDateParsing": True,
                    "multilineProcessingEnabled": True,
                    "useAutolineMatching": True,
                    "forceTimeZone": False,
                    "timeZone": "UTC"
                }
            }
            
            response = self._make_request('POST', f'/v1/collectors/{collector_id}/sources', json=source_config)
            
            if response.status_code == 201:
                source_data = response.json()
                source_id = source_data['source']['id']
                url = source_data['source'].get('url', '')
                L.info(f"✅ Created HTTP source '{name}' with ID: {source_id}")
                if url:
                    L.info(f"HTTP endpoint URL: {url}")
                return source_data['source']
            else:
                L.error(f"❌ Failed to create source: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception creating source: {e}")
            return None

    def send_logs_to_http_source(self, http_url, logs, batch_size=100):
        """
        Send log data to an HTTP source endpoint.
        
        Args:
            http_url (str): HTTP source endpoint URL
            logs (list): List of log messages
            batch_size (int): Number of logs to send per request
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            L.info(f"Sending {len(logs)} logs to HTTP source in batches of {batch_size}")
            
            # Send logs in batches
            for i in range(0, len(logs), batch_size):
                batch = logs[i:i+batch_size]
                
                # Format logs as newline-separated text
                log_data = '\n'.join(batch)
                
                # Send to HTTP endpoint (don't use session auth for HTTP sources)
                response = requests.post(
                    http_url,
                    data=log_data,
                    headers={
                        'Content-Type': 'text/plain',
                        'X-Sumo-Name': 'staging-logs',
                        'X-Sumo-Category': 'test/staging'
                    },
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    L.info(f"✅ Sent batch {i//batch_size + 1} ({len(batch)} logs)")
                else:
                    L.error(f"❌ Failed to send batch {i//batch_size + 1}: {response.status_code} - {response.text}")
                    return False
                
                # Small delay between batches to avoid overwhelming the system
                time.sleep(2)
            
            L.info(f"✅ Successfully sent all {len(logs)} logs")
            return True
            
        except Exception as e:
            L.error(f"❌ Exception sending logs: {e}")
            return False

    def create_folder(self, name, description="Test folder", parent_id=None):
        """
        Create a folder in the content library.
        
        Args:
            name (str): Folder name
            description (str): Folder description
            parent_id (str): Parent folder ID (None for personal folder)
            
        Returns:
            dict: Folder information or None if failed
        """
        try:
            L.info(f"Creating folder: {name}")
            
            # If no parent_id specified, use personal folder
            if parent_id is None:
                personal_response = self._make_request('GET', '/v2/content/folders/personal')
                if personal_response.status_code == 200:
                    personal_folder = personal_response.json()
                    parent_id = personal_folder['id']
                else:
                    L.error("Could not get personal folder ID")
                    return None
            
            folder_config = {
                "name": name,
                "description": description,
                "parentId": parent_id
            }
            
            response = self._make_request('POST', '/v2/content/folders', json=folder_config)
            
            if response.status_code == 200:
                folder_data = response.json()
                folder_id = folder_data['id']
                L.info(f"✅ Created folder '{name}' with ID: {folder_id}")
                return folder_data
            else:
                L.error(f"❌ Failed to create folder: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception creating folder: {e}")
            return None

    def create_saved_search(self, name, query, description="Test saved search", parent_id=None):
        """
        Create a saved search.
        
        Args:
            name (str): Search name
            query (str): Search query
            description (str): Search description
            parent_id (str): Parent folder ID
            
        Returns:
            dict: Saved search information or None if failed
        """
        try:
            L.info(f"Creating saved search: {name}")
            
            # If no parent_id specified, use personal folder
            if parent_id is None:
                personal_response = self._make_request('GET', '/v2/content/folders/personal')
                if personal_response.status_code == 200:
                    personal_folder = personal_response.json()
                    parent_id = personal_folder['id']
                else:
                    L.error("Could not get personal folder ID")
                    return None
            
            search_config = {
                "name": name,
                "description": description,
                "query": query,
                "parentId": parent_id
            }
            
            response = self._make_request('POST', '/v2/content/searches', json=search_config)
            
            if response.status_code == 200:
                search_data = response.json()
                search_id = search_data['id']
                L.info(f"✅ Created saved search '{name}' with ID: {search_id}")
                return search_data
            else:
                L.error(f"❌ Failed to create saved search: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception creating saved search: {e}")
            return None

def generate_test_logs(count=1000):
    """
    Generate test log data for staging.
    
    Args:
        count (int): Number of log messages to generate
        
    Returns:
        list: List of log messages
    """
    L.info(f"Generating {count} test log messages...")
    
    # Log templates for different types
    templates = {
        "INFO": [
            "Application started successfully with version {version}",
            "User {user_id} logged in from {ip_address}",
            "Request to {endpoint} completed in {duration}ms with status {status}",
            "Cache hit for key '{cache_key}' - ratio: {ratio}%",
            "Database connection established to {db_name}",
            "Configuration loaded from {config_source}",
            "Service {service_name} health check passed",
            "File {filename} processed successfully ({file_size} bytes)",
            "API call to {external_service} completed successfully",
            "Session {session_id} created for user {user_id}"
        ],
        "WARN": [
            "High memory usage detected: {memory_usage}% - consider scaling",
            "Slow query detected: {query_time}ms for query '{query_hash}'",
            "Rate limiting applied to IP {ip_address} - threshold exceeded",
            "Connection pool running low: {available_connections} connections available",
            "Deprecated API endpoint {endpoint} called by {user_agent}",
            "Certificate {cert_name} expires in {days_until_expiry} days",
            "Disk space on {mount_point} is {disk_usage}% full",
            "Service {service_name} response time degraded: {response_time}ms",
            "Failed retry attempt {retry_count} for operation {operation_id}",
            "Queue {queue_name} depth is {queue_depth} - potential backlog"
        ],
        "ERROR": [
            "Failed to connect to database {db_name}: {error_message}",
            "Exception in service {service_name}: {exception_type} - {error_details}",
            "Authentication failed for user {user_id}: {failure_reason}",
            "Request to {endpoint} failed with status {error_status}: {error_message}",
            "File operation failed: cannot {operation} file {filename} - {error_reason}",
            "External API {api_name} returned error: {api_error_code} - {api_error_message}",
            "Payment processing failed for transaction {transaction_id}: {payment_error}",
            "Email delivery failed to {email_address}: {smtp_error}",
            "Backup operation failed for {backup_target}: {backup_error}",
            "Security violation detected from IP {ip_address}: {violation_type}"
        ],
        "DEBUG": [
            "Function {function_name} called with parameters: {parameters}",
            "SQL query executed: {query} (execution_time: {exec_time}ms)",
            "Cache operation: {cache_operation} for key '{cache_key}'",
            "Thread {thread_id} state changed to {thread_state}",
            "Environment variable {env_var} loaded with value '{env_value}'",
            "HTTP request headers: {request_headers}",
            "Response body size: {response_size} bytes",
            "Garbage collection triggered: {gc_type} (duration: {gc_duration}ms)",
            "Lock acquired for resource {resource_id} by thread {thread_id}",
            "Configuration parameter {param_name} set to {param_value}"
        ]
    }
    
    # Services and systems for more realistic logs
    services = ["auth-service", "payment-service", "user-service", "notification-service", "api-gateway", "web-frontend"]
    endpoints = ["/api/v1/users", "/api/v1/orders", "/api/v1/products", "/api/v1/auth/login", "/api/v1/payments", "/health"]
    environments = ["production", "staging", "development"]
    
    logs = []
    
    for i in range(count):
        # Select log level with weighted distribution
        level_weights = [0.6, 0.2, 0.15, 0.05]  # INFO, WARN, ERROR, DEBUG
        level = random.choices(["INFO", "WARN", "ERROR", "DEBUG"], weights=level_weights)[0]
        
        # Select a template
        template = random.choice(templates[level])
        
        # Generate timestamp (within last 24 hours)
        timestamp = datetime.now() - timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # Fill in template variables with realistic data
        message = template
        
        # Replace common placeholders
        replacements = {
            "{version}": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "{user_id}": f"user-{random.randint(1000, 9999)}",
            "{ip_address}": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
            "{endpoint}": random.choice(endpoints),
            "{duration}": str(random.randint(1, 500)),
            "{status}": str(random.choice([200, 201, 204, 400, 401, 403, 404, 500])),
            "{cache_key}": f"cache-{random.randint(1000, 9999)}",
            "{ratio}": str(random.randint(60, 95)),
            "{service_name}": random.choice(services),
            "{db_name}": random.choice(["users_db", "orders_db", "products_db", "analytics_db"]),
            "{error_message}": random.choice(["Connection timeout", "Access denied", "Resource not found", "Invalid input", "Service unavailable"]),
            "{memory_usage}": str(random.randint(75, 95)),
            "{query_time}": str(random.randint(100, 5000)),
            "{session_id}": f"sess-{random.randint(100000, 999999)}",
            "{filename}": random.choice(["config.json", "data.csv", "backup.sql", "app.log", "image.jpg"]),
            "{file_size}": str(random.randint(1024, 1048576)),
            "{transaction_id}": f"txn-{random.randint(100000, 999999)}",
        }
        
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)
        
        # Handle remaining placeholders with generic values
        import re
        remaining_placeholders = re.findall(r'\{[^}]+\}', message)
        for placeholder in remaining_placeholders:
            message = message.replace(placeholder, f"value-{random.randint(100, 999)}")
        
        # Create log entry in standard format
        log_entry = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} [{level:5}] [{random.choice(services):15}] [{random.choice(environments):10}] {message}"
        logs.append(log_entry)
    
    L.info(f"Generated {len(logs)} test log messages")
    return logs

def stage_test_data(min_collectors=2, min_sources=3, min_content=2):
    """
    Stage test data in Sumo Logic if insufficient data exists.
    
    Args:
        min_collectors (int): Minimum collectors required
        min_sources (int): Minimum sources required
        min_content (int): Minimum content items required
        
    Returns:
        bool: True if staging was successful
    """
    L.info("Starting Sumo Logic test data staging...")
    
    try:
        # Get environment variables
        url = os.environ.get('SUMOLOGIC_URL')
        access_id = os.environ.get('SUMOLOGIC_ACCESS_ID')
        access_key = os.environ.get('SUMOLOGIC_ACCESS_KEY')
        verify_ssl = os.environ.get('SUMOLOGIC_VERIFY_SSL', 'true').lower() == 'true'
        timeout = int(os.environ.get('SUMOLOGIC_API_REQUEST_TIMEOUT', '120'))
        
        # Check required environment variables
        missing_vars = []
        if not url:
            missing_vars.append('SUMOLOGIC_URL')
        if not access_id:
            missing_vars.append('SUMOLOGIC_ACCESS_ID')
        if not access_key:
            missing_vars.append('SUMOLOGIC_ACCESS_KEY')
        
        if missing_vars:
            L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Create Sumo Logic API client
        sumo = SumoLogicAPI(url, access_id, access_key, verify_ssl, timeout)
        L.info("Connected to Sumo Logic API")
        
        # Check existing data
        existing_data = sumo.check_existing_data()
        if not existing_data:
            L.error("Failed to check existing data")
            return False
        
        # Determine if data is sufficient
        is_sufficient, missing_requirements = sumo.is_data_sufficient(
            existing_data, min_collectors, min_sources, min_content
        )
        
        if is_sufficient:
            L.info("✅ Existing data is sufficient for testing")
            L.info("No additional data staging required")
            return True
        
        L.info("📝 Data staging required. Creating test data...")
        
        # Create collectors and sources if needed
        collectors_to_create = max(0, min_collectors - existing_data['collectors'])
        sources_created = []
        
        if collectors_to_create > 0:
            L.info(f"\n=== Creating {collectors_to_create} Collectors and Sources ===")
            
            collector_configs = [
                {"name": f"test-app-collector-{i+1}", "description": f"Test application collector #{i+1}"}
                for i in range(collectors_to_create)
            ]
            
            for config in collector_configs:
                collector = sumo.create_hosted_collector(config["name"], config["description"])
                if collector:
                    # Create HTTP sources for each collector
                    source_configs = [
                        {"name": f"{config['name']}-app-logs", "category": "test/application"},
                        {"name": f"{config['name']}-access-logs", "category": "test/access"}
                    ]
                    
                    for source_config in source_configs:
                        source = sumo.create_http_source(
                            collector['id'], 
                            source_config["name"], 
                            f"Test source for {source_config['name']}", 
                            source_config["category"]
                        )
                        if source:
                            sources_created.append(source)
                        
                        # Small delay between source creations
                        time.sleep(1)
                
                # Small delay between collector creations
                time.sleep(2)
        
        # Generate and send test logs if we have HTTP sources
        if sources_created:
            L.info(f"\n=== Generating and Sending Test Logs to {len(sources_created)} Sources ===")
            
            for source in sources_created:
                if 'url' in source and source['url']:
                    logs = generate_test_logs(count=200)  # 200 logs per source
                    success = sumo.send_logs_to_http_source(source['url'], logs, batch_size=25)
                    if success:
                        L.info(f"✅ Successfully sent logs to source: {source['name']}")
                    else:
                        L.warning(f"⚠️  Failed to send logs to source: {source['name']}")
                else:
                    L.warning(f"⚠️  No HTTP URL available for source: {source.get('name', 'Unknown')}")
        
        # Create content items if needed
        content_to_create = max(0, min_content - existing_data['content_items'])
        
        if content_to_create > 0:
            L.info(f"\n=== Creating {content_to_create} Content Items ===")
            
            # Create a test folder
            test_folder = sumo.create_folder("Test Staging Folder", "Folder created by staging script")
            
            if test_folder:
                folder_id = test_folder['id']
                
                # Create saved searches
                search_configs = [
                    {
                        "name": "Error Logs",
                        "query": '_sourceCategory=test/* "ERROR"',
                        "description": "Find all error logs in test data"
                    },
                    {
                        "name": "High Memory Usage",
                        "query": '_sourceCategory=test/* "High memory usage"',
                        "description": "Find high memory usage warnings"
                    },
                    {
                        "name": "Authentication Failures",
                        "query": '_sourceCategory=test/* "Authentication failed"',
                        "description": "Find authentication failure events"
                    },
                    {
                        "name": "API Response Times",
                        "query": '_sourceCategory=test/* "completed in" | parse "completed in *ms" as response_time | where response_time > 100',
                        "description": "Find API calls with response time > 100ms"
                    }
                ]
                
                searches_created = []
                for search_config in search_configs[:content_to_create]:
                    search = sumo.create_saved_search(
                        search_config["name"],
                        search_config["query"],
                        search_config["description"],
                        folder_id
                    )
                    if search:
                        searches_created.append(search)
                    
                    # Small delay between creations
                    time.sleep(1)
                
                L.info(f"Created {len(searches_created)} saved searches in folder")
        
        # Wait a bit for data to be processed
        L.info("\nWaiting 60 seconds for data to be indexed...")
        time.sleep(60)
        
        # Final verification
        L.info("Verifying staged data...")
        final_data = sumo.check_existing_data()
        
        if final_data:
            final_sufficient, final_missing = sumo.is_data_sufficient(
                final_data, min_collectors, min_sources, min_content
            )
            
            if final_sufficient:
                L.info("✅ Data staging completed successfully!")
                L.info(f"Final state: {final_data['collectors']} collectors, {final_data['sources']} sources, {final_data['content_items']} content items")
                return True
            else:
                L.warning("⚠️  Data staging partially successful but requirements still not fully met")
                L.info(f"Final state: {final_data['collectors']} collectors, {final_data['sources']} sources, {final_data['content_items']} content items")
                for req in final_missing:
                    L.info(f"  Still missing: {req}")
                # Return True anyway as we made progress
                return True
        else:
            L.error("Failed to verify final data state")
            return False
            
    except Exception as e:
        L.error(f"Exception during data staging: {e}")
        return False

def main():
    L.info("Sumo Logic Data Staging - Ensuring sufficient test data exists")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SUMOLOGIC_URL'):
            print("\nCommon Sumo Logic API endpoints:")
            print("- US1: https://api.sumologic.com/api")
            print("- US2: https://api.us2.sumologic.com/api")
            print("- EU: https://api.eu.sumologic.com/api")
            print("- AU: https://api.au.sumologic.com/api")
            print("- CA: https://api.ca.sumologic.com/api")
            print("- DE: https://api.de.sumologic.com/api")
            print("- JP: https://api.jp.sumologic.com/api")
            os.environ['SUMOLOGIC_URL'] = input("\nEnter Sumo Logic API URL: ")
            
        if not os.environ.get('SUMOLOGIC_ACCESS_ID'):
            os.environ['SUMOLOGIC_ACCESS_ID'] = input("Enter Access ID: ")
            
        if not os.environ.get('SUMOLOGIC_ACCESS_KEY'):
            os.environ['SUMOLOGIC_ACCESS_KEY'] = input("Enter Access Key: ")
            
        # Set optional environment variables with defaults
        os.environ.setdefault('SUMOLOGIC_VERIFY_SSL', 'true')
        os.environ.setdefault('SUMOLOGIC_API_REQUEST_TIMEOUT', '120')
    else:
        L.info("Using environment variables for credentials")
    
    # Parse command line arguments for requirements
    min_collectors = 2
    min_sources = 3
    min_content = 2
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--min-collectors='):
                min_collectors = int(arg.split('=')[1])
            elif arg.startswith('--min-sources='):
                min_sources = int(arg.split('=')[1])
            elif arg.startswith('--min-content='):
                min_content = int(arg.split('=')[1])
    
    L.info(f"Data requirements: {min_collectors} collectors, {min_sources} sources, {min_content} content items")
    
    success = stage_test_data(min_collectors, min_sources, min_content)
    
    if success:
        L.info("✅ Sumo Logic data staging completed successfully!")
        L.info("Target instance has sufficient data for connector testing")
        return 0
    else:
        L.error("❌ Sumo Logic data staging failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())