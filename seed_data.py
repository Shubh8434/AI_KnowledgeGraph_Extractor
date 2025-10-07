#!/usr/bin/env python3
"""
Seed script for AI-Powered Knowledge Graph Builder
Creates sample data for testing and demonstration purposes.
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import Document, Version, Node, Edge
from config import settings


def create_sample_documents():
    """Create sample documents with knowledge graphs"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Document).count() > 0:
            print("Sample data already exists. Skipping seed.")
            return
        
        print("Creating sample documents and knowledge graphs...")
        
        # Sample Document 1: Tech Company Overview
        doc1 = Document(
            filename="tech_company_overview.txt",
            file_type="txt",
            file_path="uploads/tech_company_overview.txt",
            upload_date=datetime.utcnow(),
            text_content="""Acme Corporation is a leading technology company founded in 2010 by John Smith and Jane Doe. 
            The company is headquartered in San Francisco, California. John Smith serves as the CEO while Jane Doe is the CTO.
            Acme Corporation specializes in artificial intelligence and machine learning solutions. 
            The company has developed several innovative products including the AcmeAI platform and the SmartBot assistant.
            In 2024, Acme Corporation acquired TechStart, a smaller AI startup founded by Alice Johnson in 2018.
            The acquisition was completed for $50 million. Alice Johnson now serves as the Head of Innovation at Acme Corporation.
            The company employs over 500 people across offices in San Francisco, New York, and London.
            Acme Corporation's main competitors include DataCorp and AI Solutions Inc."""
        )
        db.add(doc1)
        db.commit()
        db.refresh(doc1)
        
        # Create version 1 for doc1
        version1 = Version(
            document_id=doc1.id,
            version_number=1,
            created_at=datetime.utcnow()
        )
        db.add(version1)
        db.commit()
        db.refresh(version1)
        
        # Create nodes for doc1
        nodes1 = [
            Node(document_id=doc1.id, version_id=version1.id, node_id="n1", label="Acme Corporation", node_type="Organization"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n2", label="John Smith", node_type="Person"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n3", label="Jane Doe", node_type="Person"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n4", label="San Francisco", node_type="Location"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n5", label="California", node_type="Location"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n6", label="AcmeAI platform", node_type="Product"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n7", label="SmartBot assistant", node_type="Product"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n8", label="TechStart", node_type="Organization"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n9", label="Alice Johnson", node_type="Person"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n10", label="New York", node_type="Location"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n11", label="London", node_type="Location"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n12", label="DataCorp", node_type="Organization"),
            Node(document_id=doc1.id, version_id=version1.id, node_id="n13", label="AI Solutions Inc", node_type="Organization"),
        ]
        
        for node in nodes1:
            db.add(node)
        db.commit()
        
        # Create edges for doc1
        edges1 = [
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n2", target_node_id="n1", relationship_type="founded"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n3", target_node_id="n1", relationship_type="founded"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n4", relationship_type="located_in"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n4", target_node_id="n5", relationship_type="located_in"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n2", target_node_id="n1", relationship_type="ceo_of"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n3", target_node_id="n1", relationship_type="cto_of"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n6", relationship_type="developed"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n7", relationship_type="developed"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n8", relationship_type="acquired"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n9", target_node_id="n8", relationship_type="founded"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n9", target_node_id="n1", relationship_type="member_of"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n10", relationship_type="located_in"),
            Edge(document_id=doc1.id, version_id=version1.id, source_node_id="n1", target_node_id="n11", relationship_type="located_in"),
        ]
        
        for edge in edges1:
            db.add(edge)
        db.commit()
        
        # Sample Document 2: Research Paper Abstract
        doc2 = Document(
            filename="ai_research_paper.pdf",
            file_type="pdf",
            file_path="uploads/ai_research_paper.pdf",
            upload_date=datetime.utcnow(),
            text_content="""Machine Learning in Healthcare: A Comprehensive Review

            Dr. Sarah Wilson from Stanford University and Dr. Michael Chen from MIT have published a groundbreaking research paper on machine learning applications in healthcare.
            The study was conducted in collaboration with the National Institute of Health (NIH) and the World Health Organization (WHO).
            The research focuses on three main areas: diagnostic imaging, drug discovery, and patient monitoring.
            The team developed a new algorithm called HealthAI that can predict disease progression with 95% accuracy.
            The algorithm was trained on a dataset of over 1 million patient records from hospitals across the United States.
            The research was funded by the National Science Foundation (NSF) and the Bill & Melinda Gates Foundation.
            The paper was published in the Journal of Medical AI in March 2024.
            Future work will focus on implementing the algorithm in clinical settings and expanding the dataset to include international patient data."""
        )
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        
        # Create version 1 for doc2
        version2 = Version(
            document_id=doc2.id,
            version_number=1,
            created_at=datetime.utcnow()
        )
        db.add(version2)
        db.commit()
        db.refresh(version2)
        
        # Create nodes for doc2
        nodes2 = [
            Node(document_id=doc2.id, version_id=version2.id, node_id="n1", label="Dr. Sarah Wilson", node_type="Person"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n2", label="Stanford University", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n3", label="Dr. Michael Chen", node_type="Person"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n4", label="MIT", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n5", label="National Institute of Health", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n6", label="World Health Organization", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n7", label="HealthAI", node_type="Technology"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n8", label="National Science Foundation", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n9", label="Bill & Melinda Gates Foundation", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n10", label="Journal of Medical AI", node_type="Organization"),
            Node(document_id=doc2.id, version_id=version2.id, node_id="n11", label="United States", node_type="Location"),
        ]
        
        for node in nodes2:
            db.add(node)
        db.commit()
        
        # Create edges for doc2
        edges2 = [
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n2", relationship_type="affiliated_with"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n3", target_node_id="n4", relationship_type="affiliated_with"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n3", relationship_type="collaborated_with"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n5", relationship_type="collaborated_with"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n6", relationship_type="collaborated_with"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n7", relationship_type="developed"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n8", target_node_id="n1", relationship_type="funded"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n9", target_node_id="n1", relationship_type="funded"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n1", target_node_id="n10", relationship_type="published_in"),
            Edge(document_id=doc2.id, version_id=version2.id, source_node_id="n7", target_node_id="n11", relationship_type="trained_on"),
        ]
        
        for edge in edges2:
            db.add(edge)
        db.commit()
        
        # Sample Document 3: Company Financial Report
        doc3 = Document(
            filename="financial_report_2024.csv",
            file_type="csv",
            file_path="uploads/financial_report_2024.csv",
            upload_date=datetime.utcnow(),
            text_content="""Company,Revenue,Profit,Employees,CEO,Headquarters
            TechCorp,500000000,75000000,2500,David Kim,Seattle
            DataFlow Inc,300000000,45000000,1200,Lisa Wang,Boston
            CloudTech Solutions,800000000,120000000,4000,Robert Johnson,Austin
            AI Innovations,150000000,20000000,800,Emily Davis,San Francisco
            Quantum Systems,900000000,135000000,3500,James Wilson,New York"""
        )
        db.add(doc3)
        db.commit()
        db.refresh(doc3)
        
        # Create version 1 for doc3
        version3 = Version(
            document_id=doc3.id,
            version_number=1,
            created_at=datetime.utcnow()
        )
        db.add(version3)
        db.commit()
        db.refresh(version3)
        
        # Create nodes for doc3
        nodes3 = [
            Node(document_id=doc3.id, version_id=version3.id, node_id="n1", label="TechCorp", node_type="Organization"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n2", label="David Kim", node_type="Person"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n3", label="Seattle", node_type="Location"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n4", label="DataFlow Inc", node_type="Organization"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n5", label="Lisa Wang", node_type="Person"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n6", label="Boston", node_type="Location"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n7", label="CloudTech Solutions", node_type="Organization"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n8", label="Robert Johnson", node_type="Person"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n9", label="Austin", node_type="Location"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n10", label="AI Innovations", node_type="Organization"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n11", label="Emily Davis", node_type="Person"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n12", label="San Francisco", node_type="Location"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n13", label="Quantum Systems", node_type="Organization"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n14", label="James Wilson", node_type="Person"),
            Node(document_id=doc3.id, version_id=version3.id, node_id="n15", label="New York", node_type="Location"),
        ]
        
        for node in nodes3:
            db.add(node)
        db.commit()
        
        # Create edges for doc3
        edges3 = [
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n2", target_node_id="n1", relationship_type="ceo_of"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n1", target_node_id="n3", relationship_type="headquartered_in"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n5", target_node_id="n4", relationship_type="ceo_of"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n4", target_node_id="n6", relationship_type="headquartered_in"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n8", target_node_id="n7", relationship_type="ceo_of"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n7", target_node_id="n9", relationship_type="headquartered_in"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n11", target_node_id="n10", relationship_type="ceo_of"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n10", target_node_id="n12", relationship_type="headquartered_in"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n14", target_node_id="n13", relationship_type="ceo_of"),
            Edge(document_id=doc3.id, version_id=version3.id, source_node_id="n13", target_node_id="n15", relationship_type="headquartered_in"),
        ]
        
        for edge in edges3:
            db.add(edge)
        db.commit()
        
        print(f"✅ Created {db.query(Document).count()} sample documents")
        print(f"✅ Created {db.query(Version).count()} versions")
        print(f"✅ Created {db.query(Node).count()} nodes")
        print(f"✅ Created {db.query(Edge).count()} edges")
        print("\nSample data created successfully!")
        print("\nYou can now test the API endpoints:")
        print("- GET /documents - List all documents")
        print("- GET /documents/1/graph - Get knowledge graph for document 1")
        print("- GET /documents/1/versions - List versions for document 1")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        db.close()


def create_sample_files():
    """Create sample text files for testing"""
    
    # Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Create sample text files
    sample_files = {
        "tech_company_overview.txt": """Acme Corporation is a leading technology company founded in 2010 by John Smith and Jane Doe. 
The company is headquartered in San Francisco, California. John Smith serves as the CEO while Jane Doe is the CTO.
Acme Corporation specializes in artificial intelligence and machine learning solutions. 
The company has developed several innovative products including the AcmeAI platform and the SmartBot assistant.
In 2024, Acme Corporation acquired TechStart, a smaller AI startup founded by Alice Johnson in 2018.
The acquisition was completed for $50 million. Alice Johnson now serves as the Head of Innovation at Acme Corporation.
The company employs over 500 people across offices in San Francisco, New York, and London.
Acme Corporation's main competitors include DataCorp and AI Solutions Inc.""",
        
        "ai_research_paper.txt": """Machine Learning in Healthcare: A Comprehensive Review

Dr. Sarah Wilson from Stanford University and Dr. Michael Chen from MIT have published a groundbreaking research paper on machine learning applications in healthcare.
The study was conducted in collaboration with the National Institute of Health (NIH) and the World Health Organization (WHO).
The research focuses on three main areas: diagnostic imaging, drug discovery, and patient monitoring.
The team developed a new algorithm called HealthAI that can predict disease progression with 95% accuracy.
The algorithm was trained on a dataset of over 1 million patient records from hospitals across the United States.
The research was funded by the National Science Foundation (NSF) and the Bill & Melinda Gates Foundation.
The paper was published in the Journal of Medical AI in March 2024.
Future work will focus on implementing the algorithm in clinical settings and expanding the dataset to include international patient data.""",
        
        "financial_report_2024.txt": """Company,Revenue,Profit,Employees,CEO,Headquarters
TechCorp,500000000,75000000,2500,David Kim,Seattle
DataFlow Inc,300000000,45000000,1200,Lisa Wang,Boston
CloudTech Solutions,800000000,120000000,4000,Robert Johnson,Austin
AI Innovations,150000000,20000000,800,Emily Davis,San Francisco
Quantum Systems,900000000,135000000,3500,James Wilson,New York"""
    }
    
    for filename, content in sample_files.items():
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created sample file: {filename}")


if __name__ == "__main__":
    print("🌱 Seeding AI-Powered Knowledge Graph Builder...")
    print("=" * 50)
    
    # Create sample files first
    print("\n📁 Creating sample files...")
    create_sample_files()
    
    # Create sample data
    print("\n🗄️  Creating sample database records...")
    create_sample_documents()
    
    print("\n🎉 Seed completed successfully!")
    print("\nTo start the API server, run:")
    print("python main.py")
    print("\nThen visit http://localhost:8000/docs for the API documentation.")