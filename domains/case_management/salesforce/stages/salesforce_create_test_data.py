import os
import random
from datetime import datetime, timedelta
from simple_salesforce import Salesforce
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
L = logging.getLogger(__name__)

def connect_to_salesforce():
    """
    Connect to Salesforce using environment variables.
    """
    username = os.environ.get('SALESFORCE_USERNAME')
    password = os.environ.get('SALESFORCE_PASSWORD')
    security_token = os.environ.get('SALESFORCE_SECURITY_TOKEN')
    domain = os.environ.get('SALESFORCE_DOMAIN', 'login')
    
    # Strip .salesforce.com if present in the domain
    if domain.endswith('.salesforce.com'):
        domain = domain.replace('.salesforce.com', '')
    
    # Initialize Salesforce connection
    if domain == 'login':
        # For production environment
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token
        )
    else:
        # For sandbox or other environments
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
    
    return sf

def generate_accounts(sf, count=5):
    """
    Generate and insert test accounts.
    """
    L.info(f"Generating {count} test accounts...")
    
    company_types = ["Customer", "Partner", "Prospect", "Vendor", "Other"]
    cities = ["San Francisco", "New York", "Chicago", "Austin", "Seattle", "Boston", "Los Angeles"]
    states = ["CA", "NY", "IL", "TX", "WA", "MA", "CA"]
    
    account_ids = []
    
    for i in range(count):
        company_name = f"Test Company {i+1}"
        account_data = {
            'Name': company_name,
            'Type': random.choice(company_types),
            'BillingStreet': f"{random.randint(100, 999)} Main St",
            'BillingCity': random.choice(cities),
            'BillingState': random.choice(states),
            'BillingPostalCode': f"{random.randint(10000, 99999)}",
            'Phone': f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'Industry': random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing']),
            'Description': f"This is a test account for {company_name}"
        }
        
        try:
            result = sf.Account.create(account_data)
            if result['success']:
                account_id = result['id']
                account_ids.append(account_id)
                L.info(f"Created account: {company_name} (ID: {account_id})")
            else:
                L.error(f"Failed to create account: {result}")
        except Exception as e:
            L.error(f"Exception creating account: {e}")
    
    return account_ids

def generate_contacts(sf, account_ids, count_per_account=2):
    """
    Generate and insert test contacts linked to accounts.
    """
    L.info(f"Generating {count_per_account} contacts per account...")
    
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                  "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]
    titles = ["CEO", "CTO", "CFO", "COO", "VP of Sales", "VP of Marketing", "Director", "Manager", "Consultant", "Analyst"]
    
    contact_ids = []
    
    for account_id in account_ids:
        for i in range(count_per_account):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            contact_data = {
                'AccountId': account_id,
                'FirstName': first_name,
                'LastName': last_name,
                'Title': random.choice(titles),
                'Email': f"{first_name.lower()}.{last_name.lower()}@testcompany.com",
                'Phone': f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                'Department': random.choice(['Sales', 'Marketing', 'Engineering', 'Support', 'Finance']),
            }
            
            try:
                result = sf.Contact.create(contact_data)
                if result['success']:
                    contact_id = result['id']
                    contact_ids.append(contact_id)
                    L.info(f"Created contact: {first_name} {last_name} (ID: {contact_id})")
                else:
                    L.error(f"Failed to create contact: {result}")
            except Exception as e:
                L.error(f"Exception creating contact: {e}")
    
    return contact_ids

def generate_leads(sf, count=10):
    """
    Generate and insert test leads.
    """
    L.info(f"Generating {count} test leads...")
    
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                  "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]
    companies = ["Acme Corp", "Globex", "Initech", "Umbrella Corp", "Stark Industries", "Wayne Enterprises",
                 "Cyberdyne Systems", "Massive Dynamic", "Hooli", "Pied Piper"]
    
    lead_ids = []
    
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        
        lead_data = {
            'FirstName': first_name,
            'LastName': last_name,
            'Company': f"{company} {random.randint(1, 100)}",
            'Title': random.choice(['CEO', 'CTO', 'CFO', 'VP', 'Director', 'Manager']),
            'Email': f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com",
            'Phone': f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'LeadSource': random.choice(['Web', 'Phone Inquiry', 'Partner Referral', 'Trade Show', 'Other']),
            'Status': random.choice(['Open - Not Contacted', 'Working - Contacted', 'Closed - Converted', 'Closed - Not Converted']),
        }
        
        try:
            result = sf.Lead.create(lead_data)
            if result['success']:
                lead_id = result['id']
                lead_ids.append(lead_id)
                L.info(f"Created lead: {first_name} {last_name} at {company} (ID: {lead_id})")
            else:
                L.error(f"Failed to create lead: {result}")
        except Exception as e:
            L.error(f"Exception creating lead: {e}")
    
    return lead_ids

def generate_opportunities(sf, account_ids, count_per_account=1):
    """
    Generate and insert test opportunities linked to accounts.
    """
    L.info(f"Generating {count_per_account} opportunities per account...")
    
    opportunity_names = ["New Deal", "Expansion", "Renewal", "Product Purchase", "Service Contract"]
    stages = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Decision Makers", "Perception Analysis", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
    
    opportunity_ids = []
    
    today = datetime.now()
    
    for account_id in account_ids:
        for i in range(count_per_account):
            opportunity_name = f"{random.choice(opportunity_names)} - {random.randint(1000, 9999)}"
            stage = random.choice(stages)
            
            # Random close date between now and 90 days in future
            close_date = today + timedelta(days=random.randint(30, 90))
            close_date_str = close_date.strftime('%Y-%m-%d')
            
            # Amount based on stage (earlier stages have less certainty)
            if stage in ["Closed Won", "Closed Lost"]:
                amount = random.randint(10000, 100000)
                probability = 100 if stage == "Closed Won" else 0
            elif stage in ["Proposal/Price Quote", "Negotiation/Review"]:
                amount = random.randint(8000, 80000)
                probability = random.randint(60, 90)
            else:
                amount = random.randint(5000, 50000)
                probability = random.randint(10, 60)
            
            opportunity_data = {
                'AccountId': account_id,
                'Name': opportunity_name,
                'StageName': stage,
                'CloseDate': close_date_str,
                'Amount': amount,
                'Probability': probability,
                'Type': random.choice(['New Business', 'Existing Business']),
            }
            
            try:
                result = sf.Opportunity.create(opportunity_data)
                if result['success']:
                    opportunity_id = result['id']
                    opportunity_ids.append(opportunity_id)
                    L.info(f"Created opportunity: {opportunity_name} (ID: {opportunity_id})")
                else:
                    L.error(f"Failed to create opportunity: {result}")
            except Exception as e:
                L.error(f"Exception creating opportunity: {e}")
    
    return opportunity_ids

def create_test_data():
    """
    Create test data in Salesforce.
    """
    L.info("Starting test data generation...")
    
    try:
        # Connect to Salesforce
        sf = connect_to_salesforce()
        L.info("Connected to Salesforce successfully")
        
        # Generate accounts
        account_ids = generate_accounts(sf, count=5)
        
        if account_ids:
            # Generate contacts linked to accounts
            contact_ids = generate_contacts(sf, account_ids, count_per_account=2)
            
            # Generate opportunities linked to accounts
            opportunity_ids = generate_opportunities(sf, account_ids, count_per_account=1)
        
        # Generate leads (not linked to accounts)
        lead_ids = generate_leads(sf, count=10)
        
        L.info("Test data generation completed successfully!")
        
        summary = {
            'accounts': len(account_ids),
            'contacts': len(contact_ids) if 'contact_ids' in locals() else 0,
            'opportunities': len(opportunity_ids) if 'opportunity_ids' in locals() else 0,
            'leads': len(lead_ids)
        }
        
        L.info(f"Summary of created records: {summary}")
        return True
        
    except Exception as e:
        L.error(f"Exception during test data generation: {e}")
        return False

if __name__ == "__main__":
    create_test_data()