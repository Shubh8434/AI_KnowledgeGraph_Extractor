import os
import json
import re
import logging
from typing import Dict, List, Optional
import PyPDF2
import docx
import csv
import requests
from config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Handles document text extraction
    """
    
    def extract_text(self, file_path: str, file_ext: str) -> str:
        """
        Extract text content from different file types
        """
        if file_ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_ext == '.docx':
            return self._extract_from_docx(file_path)
        elif file_ext == '.txt':
            return self._extract_from_txt(file_path)
        elif file_ext == '.csv':
            return self._extract_from_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    
    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from CSV"""
        text_lines = []
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text_lines.append(", ".join(row))
        return "\n".join(text_lines)


class KnowledgeGraphExtractor:
    """
    Extracts entities and relationships using LLM
    """
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.use_openai = getattr(settings, 'USE_OPENAI', False)
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    def extract_graph(self, text: str) -> Dict:
        """
        Extract knowledge graph from text using LLM with robust error handling
        """
        # Validate input text
        if not text or not text.strip():
            logger.warning("Empty text provided for extraction")
            return {"nodes": [], "edges": []}
        
        # Try OpenAI first if configured
        if self.use_openai and self.openai_key:
            try:
                logger.info("Using OpenAI for extraction")
                result = self._extract_with_openai(text)
                if self._validate_extraction_result(result):
                    return result
                else:
                    logger.warning("OpenAI result validation failed, trying fallback")
            except Exception as e:
                logger.error(f"OpenAI extraction failed: {e}")
        
        # Check if we should try Ollama
        if not settings.USE_OLLAMA:
            logger.info("Using rule-based extraction (USE_OLLAMA=False)")
            return self._extract_with_rules(text)
        
        # Try Ollama
        try:
            logger.info("Using Ollama for extraction")
            result = self._extract_with_ollama(text)
            if self._validate_extraction_result(result):
                return result
            else:
                logger.warning("Ollama result validation failed, trying fallback")
        except Exception as e:
            logger.error(f"Ollama extraction failed: {e}")
        
        # Fallback to rule-based extraction
        logger.info("Falling back to rule-based extraction")
        return self._extract_with_rules(text)
    
    def _validate_extraction_result(self, result: Dict) -> bool:
        """
        Validate extraction result structure and content
        
        Args:
            result: The extraction result to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(result, dict):
            logger.warning("Extraction result is not a dictionary")
            return False
        
        if 'nodes' not in result or 'edges' not in result:
            logger.warning("Extraction result missing required keys")
            return False
        
        nodes = result.get('nodes', [])
        edges = result.get('edges', [])
        
        if not isinstance(nodes, list) or not isinstance(edges, list):
            logger.warning("Nodes or edges are not lists")
            return False
        
        # Check for reasonable number of entities
        if len(nodes) > 1000:
            logger.warning(f"Too many nodes: {len(nodes)}")
            return False
        
        if len(edges) > 2000:
            logger.warning(f"Too many edges: {len(edges)}")
            return False
        
        # Validate node structure
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                logger.warning(f"Node {i} is not a dictionary")
                return False
            
            required_fields = ['id', 'label', 'type']
            for field in required_fields:
                if field not in node or not node[field]:
                    logger.warning(f"Node {i} missing or empty field: {field}")
                    return False
        
        # Validate edge structure
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                logger.warning(f"Edge {i} is not a dictionary")
                return False
            
            required_fields = ['source', 'target', 'relationship']
            for field in required_fields:
                if field not in edge or not edge[field]:
                    logger.warning(f"Edge {i} missing or empty field: {field}")
                    return False
        
        logger.info(f"Extraction result validated: {len(nodes)} nodes, {len(edges)} edges")
        return True
    
    def _extract_with_ollama(self, text: str) -> Dict:
        """
        Use Ollama LLM for extraction with improved error handling
        """
        prompt = self._create_extraction_prompt(text)
        
        try:
            # Check if Ollama is available
            health_response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if health_response.status_code != 200:
                raise Exception("Ollama service not available")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,  # Increased for better results
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=settings.OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                graph_text = result.get('response', '{}')
                
                if not graph_text or graph_text.strip() == '{}':
                    raise Exception("Empty response from Ollama")
                
                # Parse the JSON response with multiple fallback strategies
                graph_data = self._parse_llm_response(graph_text)
                return self._validate_and_format_graph(graph_data)
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timeout")
            raise Exception("Ollama timeout")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama")
            raise Exception("Ollama connection error")
        except Exception as e:
            logger.error(f"Ollama extraction error: {e}")
            raise
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response with multiple fallback strategies
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed graph data
            
        Raises:
            Exception: If parsing fails
        """
        if not response_text or not response_text.strip():
            raise Exception("Empty response from LLM")
        
        # Strategy 1: Try to parse as JSON directly
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*(\{[\s\S]*?\})\s*```',  # JSON in code block
            r'```\s*(\{[\s\S]*?\})\s*```',  # Generic code block
            r'`(\{[\s\S]*?\})`',  # Inline code
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Find JSON object boundaries
        json_patterns = [
            r'\{[\s\S]*\}',  # Simple object
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Strategy 4: Try to fix common JSON issues
        fixed_text = self._fix_common_json_issues(response_text)
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        # If all strategies fail, raise an exception
        raise Exception("Could not parse JSON from LLM response")
    
    def _fix_common_json_issues(self, text: str) -> str:
        """
        Fix common JSON formatting issues in LLM responses
        
        Args:
            text: Raw text that might contain JSON
            
        Returns:
            Potentially fixed JSON text
        """
        # Remove any text before the first {
        start_idx = text.find('{')
        if start_idx > 0:
            text = text[start_idx:]
        
        # Remove any text after the last }
        end_idx = text.rfind('}')
        if end_idx > 0:
            text = text[:end_idx + 1]
        
        # Fix common issues
        text = re.sub(r',\s*}', '}', text)  # Remove trailing commas
        text = re.sub(r',\s*]', ']', text)  # Remove trailing commas in arrays
        text = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', text)  # Quote unquoted keys
        text = re.sub(r':\s*([^",{\[\s][^,}]*?)(\s*[,}])', r': "\1"\2', text)  # Quote unquoted string values
        
        return text.strip()
    
    def _extract_with_openai(self, text: str) -> Dict:
        """
        Use OpenAI for extraction with improved error handling
        """
        from openai import OpenAI
        
        client = OpenAI(api_key=self.openai_key)
        prompt = self._create_extraction_prompt(text)
        
        try:
            response = client.chat.completions.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are an expert at extracting entities and relationships from text. Always return valid JSON in the exact format specified."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            graph_text = response.choices[0].message.content
            if not graph_text:
                raise Exception("Empty response from OpenAI")
            
            # Use the robust parsing method
            graph_data = self._parse_llm_response(graph_text)
            return self._validate_and_format_graph(graph_data)
            
        except Exception as e:
            logger.error(f"OpenAI extraction error: {e}")
            raise
    
    def _create_extraction_prompt(self, text: str) -> str:
        """
        Create prompt for LLM
        """
        return f"""Extract entities and relationships from the following text and return ONLY a valid JSON object with this exact structure:

{{
  "nodes": [
    {{"id": "n1", "label": "Entity Name", "type": "Person"}},
    {{"id": "n2", "label": "Another Entity", "type": "Organization"}}
  ],
  "edges": [
    {{"source": "n1", "target": "n2", "relationship": "works_at"}}
  ]
}}

Entity types can be: Person, Organization, Location, Concept, Event, Product, Technology, etc.
Relationships should be concise verbs or phrases like: works_at, located_in, founded_by, created, manages, etc.

Text to analyze:
{text[:2000]}

Return ONLY the JSON object, no other text."""
    
    def _extract_with_rules(self, text: str) -> Dict:
        """
        Fallback rule-based extraction using simple NLP patterns
        """
        nodes = []
        edges = []
        node_counter = 1
        
        # Preprocess text to handle multi-sentence relationships better
        # Split into sentences for better matching
        sentences = re.split(r'[.!?]+', text)
        
        # Improved patterns for entities - multi-word proper nouns
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        capitalized_words = re.findall(capitalized_pattern, text)
        
        # Filter out common words that aren't entities
        stop_words = {'In', 'The', 'A', 'An', 'This', 'That', 'These', 'Those', 'It', 'Is', 'Was', 'Are', 'Were', 'Be', 'Been'}
        capitalized_words = [word for word in capitalized_words if word not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in capitalized_words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        capitalized_words = unique_words[:15]  # Limit to 15 unique entities
        
        node_map = {}
        for word in capitalized_words:
            node_id = f"n{node_counter}"
            node_type = self._guess_entity_type(word, text)
            nodes.append({
                "id": node_id,
                "label": word,
                "type": node_type
            })
            node_map[word] = node_id
            node_counter += 1
        
        # Improved relationship patterns - process each sentence
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Extract relationships from this sentence
            self._extract_relationships_from_sentence(sentence, node_map, edges)
        
        return {"nodes": nodes, "edges": edges}
    
    def _extract_relationships_from_sentence(self, sentence: str, node_map: dict, edges: list):
        """Extract relationships from a single sentence"""
        
        print(f"Processing sentence for relationships: {sentence}")
        relationship_patterns = [
            # CEO/Leadership patterns
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+the\s+CEO\s+of\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'ceo_of'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+the\s+CTO\s+of\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'cto_of'),
            
            # Work relationships
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:works?|worked|working)\s+(?:as\s+a?\s+)?(?:\w+\s+)?(?:at|for|in|with)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'works_at'),
            
            # Founding/Creation with location
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+founded\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+in\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'founded'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:founded|established|created|started)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'founded'),
            
            # Location - with "in" pattern
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+in\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+in\s+\d{4}', 'located_in'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:headquartered|located|based)\s+in\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'located_in'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+located\s+in\s+(?:the\s+)?(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'located_in'),
            
            # Acquisition with details
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+acquired\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:for|in)', 'acquired'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:acquired|bought|purchased)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'acquired'),
            
            # Management
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:manages|managed|leads|led|oversees)\s+(?:the\s+)?(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'manages'),
            
            # Role/Position
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+serves\s+as\s+(?:\w+\s+)?of\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'member_of'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+now\s+serves\s+as\s+\w+\s+of\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'member_of'),
            
            # Development
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+developed\s+(?:an?\s+)?(?:\w+\s+)?(?:platform\s+)?called\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'developed'),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:developed|built|designed|created)\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'developed'),
            
            # Usage
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+used\s+by\s+(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'used_by'),
        ]
        
        for pattern, rel_type in relationship_patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle patterns with 2 or 3 groups
                    if len(match) == 3:
                        # Pattern like "X founded Y in Z" - create two relationships
                        source, target, location = match
                        self._add_edge_if_valid(source, target, rel_type, node_map, edges)
                        self._add_edge_if_valid(target, location, 'located_in', node_map, edges)
                    else:
                        source, target = match
                        self._add_edge_if_valid(source, target, rel_type, node_map, edges)
    
    def _add_edge_if_valid(self, source: str, target: str, rel_type: str, node_map: dict, edges: list):
        """Add an edge if both nodes exist and edge doesn't already exist"""
        # Find the exact case version from node_map
        source_key = next((k for k in node_map.keys() if k.lower() == source.lower()), None)
        target_key = next((k for k in node_map.keys() if k.lower() == target.lower()), None)
        
        if source_key and target_key and source_key != target_key:
            # Avoid duplicate edges
            edge_exists = any(
                e['source'] == node_map[source_key] and 
                e['target'] == node_map[target_key] and 
                e['relationship'] == rel_type 
                for e in edges
            )
            if not edge_exists:
                edges.append({
                    "source": node_map[source_key],
                    "target": node_map[target_key],
                    "relationship": rel_type
                })
    
    def _guess_entity_type(self, entity: str, context: str) -> str:
        """
        Guess entity type based on context and entity characteristics
        """
        entity_lower = entity.lower()
        
        # Check for organization indicators
        org_keywords = ['corporation', 'corp', 'company', 'inc', 'ltd', 'llc', 'university', 'institute', 'department', 'division']
        if any(keyword in entity_lower for keyword in org_keywords):
            return "Organization"
        
        # Check for location indicators
        location_keywords = ['city', 'country', 'state', 'street', 'avenue', 'road', 'york', 'francisco', 'london', 'paris', 'tokyo']
        if any(keyword in entity_lower for keyword in location_keywords):
            return "Location"
        
        # Check for technology/product indicators
        tech_keywords = ['bot', 'app', 'system', 'platform', 'software', 'tool', 'ai', 'tech']
        if any(keyword in entity_lower for keyword in tech_keywords):
            return "Technology"
        
        # Check for job titles (likely part of person's description)
        title_keywords = ['engineer', 'manager', 'director', 'ceo', 'cto', 'cfo', 'president', 'vice president']
        if any(keyword in entity_lower for keyword in title_keywords):
            return "JobTitle"
        
        # Check context for person indicators
        person_context_patterns = [
            rf'{re.escape(entity)}\s+(?:is|was|works|worked|manages|founded)',
            rf'(?:Mr\.|Mrs\.|Dr\.|Ms\.)\s+{re.escape(entity)}',
            rf'{re.escape(entity)}\s+(?:serves as|joined|left)'
        ]
        if any(re.search(pattern, context, re.IGNORECASE) for pattern in person_context_patterns):
            return "Person"
        
        # Check if it looks like a person name (two capitalized words)
        if len(entity.split()) == 2 and all(word[0].isupper() for word in entity.split()):
            return "Person"
        
        # Default to Entity for ambiguous cases
        return "Entity"
    
    def _validate_and_format_graph(self, graph_data: Dict) -> Dict:
        """
        Validate and format graph data
        """
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        # Ensure all nodes have required fields
        formatted_nodes = []
        for node in nodes:
            if 'id' in node and 'label' in node:
                formatted_nodes.append({
                    'id': node['id'],
                    'label': node['label'],
                    'type': node.get('type', 'Entity')
                })
        
        # Ensure all edges have required fields
        formatted_edges = []
        node_ids = {node['id'] for node in formatted_nodes}
        for edge in edges:
            if 'source' in edge and 'target' in edge and edge['source'] in node_ids and edge['target'] in node_ids:
                formatted_edges.append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relationship': edge.get('relationship', 'related_to')
                })
        
        return {
            'nodes': formatted_nodes,
            'edges': formatted_edges
        }
    
    def _extract_json_from_text(self, text: str) -> Dict:
        """
        Try to extract JSON from text response
        """
        # Look for JSON object in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                graph_data = json.loads(json_match.group())
                return self._validate_and_format_graph(graph_data)
            except json.JSONDecodeError:
                pass
        
        # If all else fails, return empty graph
        return {'nodes': [], 'edges': []}