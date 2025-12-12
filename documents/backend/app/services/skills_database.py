"""
Pre-populated skills database for autocomplete
Organized by category with popularity scores
"""

SKILLS_DATABASE = {
    # Programming Languages
    "Python": {"category": "Programming Languages", "popularity": 95, "related": ["Django", "Flask", "FastAPI", "Pandas"]},
    "JavaScript": {"category": "Programming Languages", "popularity": 98, "related": ["React", "Node.js", "TypeScript", "Vue.js"]},
    "TypeScript": {"category": "Programming Languages", "popularity": 90, "related": ["JavaScript", "React", "Angular", "Node.js"]},
    "Java": {"category": "Programming Languages", "popularity": 92, "related": ["Spring Boot", "Maven", "Hibernate", "JUnit"]},
    "C#": {"category": "Programming Languages", "popularity": 85, "related": [".NET", "ASP.NET", "Azure", "Entity Framework"]},
    "Go": {"category": "Programming Languages", "popularity": 78, "related": ["Docker", "Kubernetes", "Microservices", "gRPC"]},
    "Rust": {"category": "Programming Languages", "popularity": 65, "related": ["Systems Programming", "WebAssembly", "Performance"]},
    "PHP": {"category": "Programming Languages", "popularity": 75, "related": ["Laravel", "WordPress", "Symfony", "MySQL"]},
    "Ruby": {"category": "Programming Languages", "popularity": 70, "related": ["Ruby on Rails", "RSpec", "PostgreSQL"]},
    "Swift": {"category": "Programming Languages", "popularity": 80, "related": ["iOS", "Xcode", "SwiftUI", "UIKit"]},
    "Kotlin": {"category": "Programming Languages", "popularity": 82, "related": ["Android", "Spring", "Ktor"]},
    
    # Frontend
    "React": {"category": "Frontend", "popularity": 96, "related": ["JavaScript", "Redux", "Next.js", "TypeScript"]},
    "Angular": {"category": "Frontend", "popularity": 85, "related": ["TypeScript", "RxJS", "NgRx"]},
    "Vue.js": {"category": "Frontend", "popularity": 88, "related": ["JavaScript", "Vuex", "Nuxt.js"]},
    "Next.js": {"category": "Frontend", "popularity": 90, "related": ["React", "TypeScript", "SSR", "Vercel"]},
    "HTML5": {"category": "Frontend", "popularity": 95, "related": ["CSS3", "JavaScript", "Accessibility"]},
    "CSS3": {"category": "Frontend", "popularity": 95, "related": ["Sass", "Tailwind", "Responsive Design"]},
    "Sass": {"category": "Frontend", "popularity": 85, "related": ["CSS3", "SCSS", "Preprocessors"]},
    "Tailwind CSS": {"category": "Frontend", "popularity": 92, "related": ["CSS3", "Utility-First", "Responsive"]},
    "Redux": {"category": "Frontend", "popularity": 87, "related": ["React", "State Management", "Redux Toolkit"]},
    "Webpack": {"category": "Frontend", "popularity": 83, "related": ["Module Bundler", "JavaScript", "Build Tools"]},
    
    # Backend
    "Node.js": {"category": "Backend", "popularity": 94, "related": ["JavaScript", "Express", "NestJS", "MongoDB"]},
    "Express.js": {"category": "Backend", "popularity": 90, "related": ["Node.js", "REST API", "Middleware"]},
    "Django": {"category": "Backend", "popularity": 88, "related": ["Python", "PostgreSQL", "REST Framework"]},
    "Flask": {"category": "Backend", "popularity": 82, "related": ["Python", "Microservices", "REST API"]},
    "FastAPI": {"category": "Backend", "popularity": 86, "related": ["Python", "Async", "Pydantic", "OpenAPI"]},
    "Spring Boot": {"category": "Backend", "popularity": 89, "related": ["Java", "Microservices", "JPA"]},
    "Ruby on Rails": {"category": "Backend", "popularity": 78, "related": ["Ruby", "MVC", "ActiveRecord"]},
    ".NET Core": {"category": "Backend", "popularity": 87, "related": ["C#", "ASP.NET", "Entity Framework"]},
    "GraphQL": {"category": "Backend", "popularity": 85, "related": ["API", "Apollo", "REST"]},
    "REST API": {"category": "Backend", "popularity": 96, "related": ["HTTP", "JSON", "API Design"]},
    
    # Databases
    "PostgreSQL": {"category": "Databases", "popularity": 93, "related": ["SQL", "ACID", "Relational"]},
    "MySQL": {"category": "Databases", "popularity": 91, "related": ["SQL", "Relational", "MariaDB"]},
    "MongoDB": {"category": "Databases", "popularity": 89, "related": ["NoSQL", "Document DB", "Mongoose"]},
    "Redis": {"category": "Databases", "popularity": 87, "related": ["Caching", "In-Memory", "Key-Value"]},
    "Elasticsearch": {"category": "Databases", "popularity": 80, "related": ["Search", "Analytics", "Logging"]},
    "DynamoDB": {"category": "Databases", "popularity": 75, "related": ["AWS", "NoSQL", "Serverless"]},
    "Cassandra": {"category": "Databases", "popularity": 70, "related": ["NoSQL", "Distributed", "Big Data"]},
    "SQLite": {"category": "Databases", "popularity": 78, "related": ["SQL", "Embedded", "Mobile"]},
    
    # Cloud & DevOps
    "AWS": {"category": "Cloud & DevOps", "popularity": 95, "related": ["EC2", "S3", "Lambda", "CloudFormation"]},
    "Azure": {"category": "Cloud & DevOps", "popularity": 88, "related": ["Cloud Computing", "DevOps", "Microsoft"]},
    "Google Cloud": {"category": "Cloud & DevOps", "popularity": 85, "related": ["GCP", "BigQuery", "Kubernetes"]},
    "Docker": {"category": "Cloud & DevOps", "popularity": 94, "related": ["Containers", "Kubernetes", "DevOps"]},
    "Kubernetes": {"category": "Cloud & DevOps", "popularity": 91, "related": ["Docker", "Orchestration", "Microservices"]},
    "CI/CD": {"category": "Cloud & DevOps", "popularity": 93, "related": ["Jenkins", "GitLab", "GitHub Actions"]},
    "Terraform": {"category": "Cloud & DevOps", "popularity": 88, "related": ["IaC", "AWS", "DevOps"]},
    "Jenkins": {"category": "Cloud & DevOps", "popularity": 82, "related": ["CI/CD", "Automation", "Pipeline"]},
    "GitHub Actions": {"category": "Cloud & DevOps", "popularity": 89, "related": ["CI/CD", "Git", "Automation"]},
    "Ansible": {"category": "Cloud & DevOps", "popularity": 80, "related": ["Configuration Management", "DevOps"]},
    
    # Data & AI
    "Machine Learning": {"category": "Data & AI", "popularity": 92, "related": ["Python", "TensorFlow", "PyTorch"]},
    "TensorFlow": {"category": "Data & AI", "popularity": 87, "related": ["Machine Learning", "Deep Learning", "Python"]},
    "PyTorch": {"category": "Data & AI", "popularity": 86, "related": ["Machine Learning", "Deep Learning", "Python"]},
    "Pandas": {"category": "Data & AI", "popularity": 90, "related": ["Python", "Data Analysis", "NumPy"]},
    "NumPy": {"category": "Data & AI", "popularity": 88, "related": ["Python", "Scientific Computing", "Pandas"]},
    "Scikit-learn": {"category": "Data & AI", "popularity": 85, "related": ["Machine Learning", "Python", "Data Science"]},
    "Data Analysis": {"category": "Data & AI", "popularity": 91, "related": ["Python", "SQL", "Statistics"]},
    "NLP": {"category": "Data & AI", "popularity": 82, "related": ["Machine Learning", "Transformers", "LLMs"]},
    "LLMs": {"category": "Data & AI", "popularity": 88, "related": ["AI", "GPT", "Transformers"]},
    
    # Testing
    "Jest": {"category": "Testing", "popularity": 90, "related": ["JavaScript", "Unit Testing", "React"]},
    "Pytest": {"category": "Testing", "popularity": 87, "related": ["Python", "Unit Testing", "TDD"]},
    "JUnit": {"category": "Testing", "popularity": 85, "related": ["Java", "Unit Testing", "TDD"]},
    "Selenium": {"category": "Testing", "popularity": 82, "related": ["Test Automation", "Web Testing"]},
    "Cypress": {"category": "Testing", "popularity": 88, "related": ["E2E Testing", "JavaScript", "React"]},
    "Test-Driven Development": {"category": "Testing", "popularity": 84, "related": ["TDD", "Unit Testing", "Agile"]},
    
    # Soft Skills
    "Leadership": {"category": "Soft Skills", "popularity": 95, "related": ["Team Management", "Communication", "Mentoring"]},
    "Communication": {"category": "Soft Skills", "popularity": 98, "related": ["Collaboration", "Presentation", "Writing"]},
    "Problem Solving": {"category": "Soft Skills", "popularity": 97, "related": ["Critical Thinking", "Analysis", "Creativity"]},
    "Team Collaboration": {"category": "Soft Skills", "popularity": 96, "related": ["Communication", "Agile", "Teamwork"]},
    "Mentoring": {"category": "Soft Skills", "popularity": 85, "related": ["Leadership", "Teaching", "Coaching"]},
    "Project Management": {"category": "Soft Skills", "popularity": 90, "related": ["Planning", "Organization", "Agile"]},
    "Agile Methodologies": {"category": "Soft Skills", "popularity": 93, "related": ["Scrum", "Kanban", "Sprint Planning"]},
    "Critical Thinking": {"category": "Soft Skills", "popularity": 94, "related": ["Problem Solving", "Analysis"]},
    "Time Management": {"category": "Soft Skills", "popularity": 88, "related": ["Organization", "Prioritization"]},
    "Adaptability": {"category": "Soft Skills", "popularity": 91, "related": ["Flexibility", "Learning", "Change Management"]},
}


def search_skills(query: str, category: str = None, limit: int = 10):
    """Search skills by partial match"""
    query_lower = query.lower()
    results = []
    
    for skill_name, skill_data in SKILLS_DATABASE.items():
        if category and skill_data["category"] != category:
            continue
        
        if query_lower in skill_name.lower():
            results.append({
                "skill": skill_name,
                "category": skill_data["category"],
                "popularity": skill_data["popularity"],
                "related_skills": skill_data["related"]
            })
    
    # Sort by popularity (descending) and then alphabetically
    results.sort(key=lambda x: (-x["popularity"], x["skill"]))
    
    return results[:limit]


def get_skill_categories():
    """Get list of all skill categories"""
    categories = set()
    for skill_data in SKILLS_DATABASE.values():
        categories.add(skill_data["category"])
    return sorted(list(categories))
