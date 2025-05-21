import os
import re
import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import concurrent.futures
from diskcache import Cache
import markdown2
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize disk cache
cache = Cache("./cache")

# Constants
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
SEARCH_API_URL = os.getenv("SEARCH_API_URL", "https://serpapi.com/search")
MAX_SOURCES = 3
SCRAPE_TIMEOUT = 10
MAX_CONTENT_LENGTH = 4000

# Subject categories and their keywords
SUBJECT_CATEGORIES = {
    "Mathematics": ["math", "algebra", "geometry", "calculus", "equation", "number", "arithmetic", "statistics"],
    "Science": ["physics", "chemistry", "biology", "science", "scientific", "experiment", "molecule", "atom"],
    "History": ["history", "historical", "ancient", "civilization", "war", "empire", "century", "era"],
    "Literature": ["literature", "book", "author", "novel", "poetry", "writing", "story", "literary"],
    "Programming": ["programming", "code", "algorithm", "software", "developer", "python", "javascript", "computer"],
    "General": []  # Default category
}

# Predefined responses for common questions
PREDEFINED_RESPONSES = {
    "Mathematics": {
        "algebra": "Algebra is a branch of mathematics that deals with symbols and the rules for manipulating these symbols. It's used to solve equations and understand relationships between variables.",
        "geometry": "Geometry is the study of shapes, sizes, positions, and dimensions of things. It includes concepts like points, lines, angles, and surfaces.",
        "calculus": "Calculus is a branch of mathematics that studies continuous change. It has two main branches: differential calculus and integral calculus.",
        "statistics": "Statistics is the science of collecting, analyzing, and interpreting data. It helps us understand patterns and make predictions based on data."
    },
    "Science": {
        "physics": "Physics is the study of matter, energy, and their interactions. It explains how the universe works at its most fundamental level.",
        "chemistry": "Chemistry is the study of substances, their properties, and how they interact with each other. It's often called the central science.",
        "biology": "Biology is the study of living organisms and their interactions with each other and their environment. It covers everything from cells to ecosystems."
    },
    "History": {
        "ancient": "Ancient history covers the period from the beginning of recorded history to the fall of the Western Roman Empire in 476 CE.",
        "modern": "Modern history typically begins around 1500 CE and continues to the present day. It includes major events like the Renaissance, Industrial Revolution, and World Wars."
    },
    "Programming": {
        "python": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in data science, web development, and automation.",
        "javascript": "JavaScript is a programming language primarily used for web development. It allows you to create interactive elements on websites.",
        "algorithm": "An algorithm is a step-by-step procedure for solving a problem or accomplishing a task. It's like a recipe for a computer to follow."
    }
}

class RuleBasedModel:
    def __init__(self):
        self.logger = logger
        
    def detect_subject_category(self, query):
        """Detect the subject category of the query based on keywords."""
        query_lower = query.lower()
        scores = defaultdict(int)
        
        for category, keywords in SUBJECT_CATEGORIES.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[category] += 1
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "General"
    
    def get_category_specific_sources(self, category):
        """Get category-specific educational sources."""
        category_sources = {
            "Mathematics": ["khanacademy.org", "mathway.com", "wolframalpha.com"],
            "Science": ["sciencedaily.com", "nature.com", "scientificamerican.com"],
            "History": ["history.com", "britannica.com", "worldhistory.org"],
            "Literature": ["gutenberg.org", "poetryfoundation.org", "literarydevices.net"],
            "Programming": ["stackoverflow.com", "github.com", "dev.to"]
        }
        return category_sources.get(category, [])
    
    def _is_educational_site(self, url):
        """Check if the URL is from an educational website."""
        educational_domains = [
            'wikipedia.org', 'khanacademy.org', 'britannica.com', 
            'edu', 'coursera.org', 'edx.org', 'mit.edu', 
            'stanford.edu', 'harvard.edu', 'scholarpedia.org'
        ]
        
        # Add category-specific sources
        category = getattr(self, 'current_category', 'General')
        educational_domains.extend(self.get_category_specific_sources(category))
        
        try:
            domain = urlparse(url).netloc
            return any(edu_domain in domain for edu_domain in educational_domains)
        except:
            return False
    
    def search_web(self, query):
        """Search the web for educational content related to the query."""
        if not SEARCH_API_KEY:
            self.logger.warning("Search API key not available, using direct scraping")
            return self._get_default_educational_urls(query)
            
        try:
            params = {
                "q": query + " educational content",
                "api_key": SEARCH_API_KEY,
                "engine": "google",
                "num": 5
            }
            response = requests.get(SEARCH_API_URL, params=params)
            data = response.json()
            
            urls = []
            if "organic_results" in data:
                for result in data["organic_results"]:
                    url = result.get("link")
                    if url and self._is_educational_site(url):
                        urls.append(url)
                        if len(urls) >= MAX_SOURCES:
                            break
            
            return urls
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}")
            return self._get_default_educational_urls(query)
    
    def _get_default_educational_urls(self, query):
        """Get default educational URLs when search API is not available."""
        query_formatted = query.replace(" ", "_")
        urls = [
            f"https://en.wikipedia.org/wiki/{query_formatted}",
            f"https://simple.wikipedia.org/wiki/{query_formatted}"
        ]
        return urls
    
    def scrape_content(self, url):
        """Scrape educational content from a URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            title = soup.title.string if soup.title else ""
            
            domain = urlparse(url).netloc
            content = ""
            
            if 'wikipedia.org' in domain:
                main_content = soup.find('div', {'id': 'mw-content-text'})
                if main_content:
                    paragraphs = main_content.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs])
            else:
                main_elements = soup.find_all(['article', 'main', 'div'], class_=re.compile(r'content|article|main|body'))
                
                if main_elements:
                    main_element = max(main_elements, key=lambda x: len(x.get_text()))
                    paragraphs = main_element.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs])
                else:
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs])
            
            content = re.sub(r'\s+', ' ', content).strip()
            content = re.sub(r'\[\d+\]', '', content)
            
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "..."
                
            return {
                "title": title,
                "content": content,
                "url": url
            }
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_multiple_sources(self, urls):
        """Scrape content from multiple URLs in parallel."""
        sources = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SOURCES) as executor:
            future_to_url = {executor.submit(self.scrape_content, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result and result["content"]:
                    sources.append(result)
        
        return sources
    
    def generate_response(self, query, context=None):
        """Generate a response using the rule-based model."""
        try:
            # First, try to find a predefined response
            category = self.current_category
            query_lower = query.lower()
            
            # Check for exact matches in predefined responses
            for topic, response in PREDEFINED_RESPONSES.get(category, {}).items():
                if topic in query_lower:
                    return response
            
            # If no exact match, use context if available
            if context:
                # Extract key information from context
                key_points = []
                for source in context.split('\n\n'):
                    if 'Source:' in source:
                        content = source.split('\n', 1)[1]
                        # Extract first few sentences as key points
                        sentences = re.split(r'[.!?]+', content)
                        key_points.extend([s.strip() for s in sentences if s.strip()][:2])
                
                if key_points:
                    response = "Based on the available information:\n\n"
                    response += "\n".join(f"- {point}" for point in key_points)
                    response += "\n\nFor more detailed information, please check the sources provided."
                    return response
            
            # If no context or predefined response, provide a generic response
            return f"I understand you're asking about {query}. While I don't have a specific answer prepared, I recommend checking the provided sources for more information."
        
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm having trouble generating a response right now. Please try again later."
    
    def answer_query(self, query):
        """Main method to answer educational queries."""
        # Detect subject category
        self.current_category = self.detect_subject_category(query)
        self.logger.info(f"Detected category: {self.current_category}")
        
        # Check disk cache
        cache_key = f"{self.current_category}:{query.lower().strip()}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            self.logger.info(f"Returning cached response for: {query}")
            return cached_response
        
        try:
            # Log the query
            self.logger.info(f"Received query: {query}")
            
            # Try to get web content first
            urls = self.search_web(query)
            
            if urls:
                sources = self.scrape_multiple_sources(urls)
                
                if sources:
                    context = "\n\n".join([
                        f"Source: {source['title']} ({source['url']})\n{source['content']}"
                        for source in sources
                    ])
                    
                    response = self.generate_response(query, context)
                    
                    # Format source links in Markdown
                    source_urls = [f"- [{source['title']}]({source['url']})" for source in sources]
                    response += "\n\n**Sources:**\n" + "\n".join(source_urls)
                else:
                    response = self.generate_response(query)
            else:
                response = self.generate_response(query)
            
            # Convert response to Markdown HTML
            formatted_response = markdown2.markdown(response)
            
            # Cache the response
            cache.set(cache_key, formatted_response, expire=3600)  # Cache for 1 hour
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error answering query: {str(e)}")
            return markdown2.markdown("I apologize, but I'm experiencing technical difficulties right now. Please try again later.")

# Initialize the chatbot
chatbot = RuleBasedModel()

@app.route('/query', methods=['POST'])
def query():
    """API endpoint to handle queries."""
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data['question']
    response = chatbot.answer_query(question)
    category = chatbot.current_category
    
    return jsonify({
        "question": question,
        "answer": response,
        "category": category
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

# Simple web interface for testing
@app.route('/', methods=['GET'])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Teacher Chatbot</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .chat-container { 
                border: 1px solid #ddd; 
                border-radius: 10px; 
                padding: 20px; 
                height: 500px; 
                overflow-y: auto; 
                margin-bottom: 20px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .input-container { 
                display: flex; 
                gap: 10px;
                position: relative;
            }
            input { 
                flex: 1; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 25px; 
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #4CAF50;
            }
            button { 
                padding: 12px 25px; 
                background-color: #4CAF50; 
                color: white; 
                border: none; 
                border-radius: 25px; 
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
            .message { 
                margin-bottom: 15px; 
                padding: 12px 15px; 
                border-radius: 10px; 
                max-width: 80%;
                line-height: 1.4;
            }
            .user-message { 
                background-color: #e3f2fd; 
                margin-left: auto;
                color: #1565c0;
            }
            .bot-message { 
                background-color: #f5f5f5;
                color: #333;
            }
            .typing-indicator {
                display: none;
                padding: 12px 15px;
                background-color: #f1f1f1;
                border-radius: 10px;
                margin-bottom: 15px;
                width: fit-content;
            }
            .typing-indicator span {
                display: inline-block;
                width: 8px;
                height: 8px;
                background-color: #90a4ae;
                border-radius: 50%;
                margin-right: 5px;
                animation: typing 1s infinite;
            }
            .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
            .category-tag {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin-bottom: 5px;
                color: white;
            }
            .category-Mathematics { background-color: #2196F3; }
            .category-Science { background-color: #4CAF50; }
            .category-History { background-color: #FFC107; }
            .category-Literature { background-color: #9C27B0; }
            .category-Programming { background-color: #F44336; }
            .category-General { background-color: #607D8B; }
            pre code {
                display: block;
                padding: 10px;
                border-radius: 5px;
                background-color: #f8f8f8;
                overflow-x: auto;
            }
            @keyframes typing {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-5px); }
            }
        </style>
    </head>
    <body>
        <h1>AI Teacher Chatbot</h1>
        <div class="chat-container" id="chat-container">
            <div class="typing-indicator" id="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        <div class="input-container">
            <input type="text" id="question-input" placeholder="Ask your educational question...">
            <button onclick="askQuestion()">Send</button>
        </div>
        
        <script>
            // Initialize syntax highlighting
            hljs.highlightAll();

            function showTypingIndicator() {
                const indicator = document.getElementById('typing-indicator');
                indicator.style.display = 'block';
                scrollToBottom();
            }

            function hideTypingIndicator() {
                const indicator = document.getElementById('typing-indicator');
                indicator.style.display = 'none';
            }

            function scrollToBottom() {
                const chatContainer = document.getElementById('chat-container');
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function getCategoryColor(category) {
                return `category-${category}`;
            }

            async function askQuestion() {
                const questionInput = document.getElementById('question-input');
                const chatContainer = document.getElementById('chat-container');
                
                const question = questionInput.value.trim();
                if (!question) return;
                
                // Add user message
                const userDiv = document.createElement('div');
                userDiv.className = 'message user-message';
                userDiv.textContent = question;
                chatContainer.appendChild(userDiv);
                
                // Clear input and show typing indicator
                questionInput.value = '';
                showTypingIndicator();
                
                try {
                    // Send question to API
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ question: question }),
                    });
                    
                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTypingIndicator();
                    
                    // Create bot response container
                    const botDiv = document.createElement('div');
                    botDiv.className = 'message bot-message';
                    
                    // Add category tag
                    const categoryTag = document.createElement('div');
                    categoryTag.className = `category-tag ${getCategoryColor(data.category)}`;
                    categoryTag.textContent = data.category;
                    botDiv.appendChild(categoryTag);
                    
                    // Add response content
                    const contentDiv = document.createElement('div');
                    contentDiv.innerHTML = data.answer;
                    botDiv.appendChild(contentDiv);
                    
                    chatContainer.appendChild(botDiv);
                    
                    // Initialize syntax highlighting for new code blocks
                    botDiv.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightBlock(block);
                    });
                    
                    scrollToBottom();
                    
                } catch (error) {
                    hideTypingIndicator();
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message bot-message';
                    errorDiv.textContent = 'Sorry, there was an error processing your question.';
                    chatContainer.appendChild(errorDiv);
                    console.error('Error:', error);
                }
            }
            
            // Allow Enter key to send
            document.getElementById('question-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    askQuestion();
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 