#!/usr/bin/env python3
"""
Demo script to test the Knowledge Graph Builder API
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def create_sample_document():
    """Create a sample text document for testing"""
    sample_text = """
    John Doe is the CEO of Acme Corporation, headquartered in New York City.
    Jane Smith founded TechStart in San Francisco in 2020.
    In 2024, Acme Corporation acquired TechStart for $50 million.
    John Doe manages the Engineering Department at Acme.
    Sarah Johnson works as a Senior Engineer at Acme Corporation.
    TechStart developed an AI platform called SmartBot.
    SmartBot is used by companies worldwide.
    Jane Smith now serves as CTO of Acme Corporation.
    The Engineering Department is located in the New York office.
    """
    
    with open("sample_document.txt", "w") as f:
        f.write(sample_text.strip())
    
    print("✓ Created sample_document.txt")
    return "sample_document.txt"


def upload_document(filename):
    """Upload a document to the API"""
    print_section("1. Uploading Document")
    
    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'text/plain')}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Document uploaded successfully!")
        print(f"  Document ID: {data['id']}")
        print(f"  Filename: {data['filename']}")
        print(f"  Status: {data['status']}")
        return data['id']
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def list_documents():
    """List all documents"""
    print_section("2. Listing All Documents")
    
    response = requests.get(f"{BASE_URL}/documents")
    
    if response.status_code == 200:
        documents = response.json()
        print(f"✓ Found {len(documents)} document(s):\n")
        for doc in documents:
            print(f"  ID: {doc['id']}")
            print(f"  Filename: {doc['filename']}")
            print(f"  Type: {doc['file_type']}")
            print(f"  Uploaded: {doc['upload_date']}")
            print()
    else:
        print(f"✗ Failed to list documents: {response.status_code}")


def get_knowledge_graph(document_id):
    """Get the knowledge graph for a document"""
    print_section("3. Retrieving Knowledge Graph")
    
    response = requests.get(f"{BASE_URL}/documents/{document_id}/graph")
    
    if response.status_code == 200:
        graph = response.json()
        print(f"✓ Knowledge Graph Retrieved!")
        print(f"  Document ID: {graph['document_id']}")
        print(f"  Version: {graph['version']}")
        print(f"\n  Nodes ({len(graph['nodes'])}):")
        for node in graph['nodes']:
            print(f"    - [{node['type']}] {node['label']} (ID: {node['id']})")
        
        print(f"\n  Edges ({len(graph['edges'])}):")
        for edge in graph['edges']:
            print(f"    - {edge['source']} --[{edge['relationship']}]--> {edge['target']}")
        
        print("\n  Full JSON Output:")
        print(json.dumps(graph, indent=2))
        
        return graph
    else:
        print(f"✗ Failed to get graph: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def list_versions(document_id):
    """List all versions of a document's graph"""
    print_section("4. Listing Graph Versions")
    
    response = requests.get(f"{BASE_URL}/documents/{document_id}/versions")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data['versions'])} version(s):\n")
        for version in data['versions']:
            print(f"  Version: {version['version_number']}")
            print(f"  Created: {version['created_at']}")
            print()
    else:
        print(f"✗ Failed to list versions: {response.status_code}")


def get_specific_version(document_id, version_number):
    """Get a specific version of the graph"""
    print_section(f"5. Retrieving Version {version_number}")
    
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/versions/{version_number}"
    )
    
    if response.status_code == 200:
        graph = response.json()
        print(f"✓ Version {version_number} Retrieved!")
        print(f"  Nodes: {len(graph['nodes'])}")
        print(f"  Edges: {len(graph['edges'])}")
    else:
        print(f"✗ Failed to get version: {response.status_code}")


def check_api_health():
    """Check if the API is running"""
    print_section("Checking API Health")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✓ API is running!")
            data = response.json()
            print(f"  {data['message']}")
            return True
        else:
            print(f"✗ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the server is running!")
        print("  Run: python main.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run the complete demo"""
    print("\n" + "🚀 " * 20)
    print("  KNOWLEDGE GRAPH BUILDER - API DEMO")
    print("🚀 " * 20)
    
    # Check API health
    if not check_api_health():
        print("\n⚠️  Please start the API server first: python main.py")
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Create sample document
    print_section("Preparation")
    sample_file = create_sample_document()
    
    # Wait for user
    input("\nPress Enter to continue with the demo...")
    
    # Upload document
    doc_id = upload_document(sample_file)
    if not doc_id:
        return
    
    time.sleep(1)
    
    # List documents
    list_documents()
    time.sleep(1)
    
    # Get knowledge graph
    graph = get_knowledge_graph(doc_id)
    if not graph:
        return
    
    time.sleep(1)
    
    # List versions
    list_versions(doc_id)
    time.sleep(1)
    
    # Get specific version
    get_specific_version(doc_id, 1)
    
    # Summary
    print_section("Demo Complete!")
    print("✓ Successfully demonstrated all API endpoints")
    print("\nNext steps:")
    print("  1. Check the API documentation at http://localhost:8000/docs")
    print("  2. Try uploading your own documents")
    print("  3. Explore the knowledge graphs generated")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()