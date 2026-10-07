"""Knowledge base for the AI Career Analysis module (Person 1).

Central place for:
  * SKILL_CATEGORIES            – skill taxonomy used in the skill profile
  * SKILLS                      – canonical skills with aliases + category
  * COURSE_TO_SKILLS            – coursework -> skills mapping
  * ROLES                       – job role -> required skills (for recommendations)
  * Resume / job-description heuristics (sections, degrees, certifications)

Pure data + tiny matching helpers. No external dependencies.
Real AI can be wired in `ai.py`; this keeps the deterministic fallback stable.
"""

import re

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[^a-z0-9+#]+")


def normalize(text: str) -> str:
    """Lowercase and normalize a string for matching.

    Keeps letters, digits, `+` and `#` so "C++" / "C#" survive; everything
    else (dots, slashes, dashes, parens...) becomes a single space.
    """
    return _TOKEN_RE.sub(" ", (text or "").lower()).strip()


# ---------------------------------------------------------------------------
# Skill taxonomy
# ---------------------------------------------------------------------------

SKILL_CATEGORIES = [
    "Programming",
    "Web Development",
    "Databases",
    "Cloud & DevOps",
    "Data & AI",
    "Tools & Platforms",
    "Networking & Security",
    "Testing & QA",
    "Mobile & UI/UX",
    "Soft Skills",
]

# canonical skill -> {category, aliases}
# aliases are normalized lowercase strings (dots removed, so "node.js" -> "node js").
SKILLS: dict[str, dict] = {
    # --- Programming ---
    "Python": {"category": "Programming", "aliases": ["python", "py"]},
    "Java": {"category": "Programming", "aliases": ["java", "core java"]},
    "C": {"category": "Programming", "aliases": [" c ", "c programming"]},
    "C++": {"category": "Programming", "aliases": ["c++", "cpp", "c plus plus"]},
    "C#": {"category": "Programming", "aliases": ["c#", "c sharp"]},
    "JavaScript": {"category": "Programming", "aliases": ["javascript", "js", "es6"]},
    "TypeScript": {"category": "Programming", "aliases": ["typescript", "ts"]},
    "Go": {"category": "Programming", "aliases": ["golang", "go lang"]},
    "Rust": {"category": "Programming", "aliases": ["rust"]},
    "Swift": {"category": "Programming", "aliases": ["swift"]},
    "Kotlin": {"category": "Programming", "aliases": ["kotlin"]},
    "R": {"category": "Programming", "aliases": ["r programming", "r language"]},
    "PHP": {"category": "Programming", "aliases": ["php"]},
    "Ruby": {"category": "Programming", "aliases": ["ruby"]},
    "Dart": {"category": "Programming", "aliases": ["dart"]},
    "MATLAB": {"category": "Programming", "aliases": ["matlab"]},
    "OOPS": {"category": "Programming", "aliases": ["oops", "object oriented", "oop"]},
    "Data Structures": {
        "category": "Programming",
        "aliases": ["data structures", "dsa", "ds"],
    },
    "Algorithms": {"category": "Programming", "aliases": ["algorithms", "algo"]},
    "Problem Solving": {
        "category": "Programming",
        "aliases": ["problem solving", "problem-solving", "logical thinking"],
    },
    "Operating Systems": {
        "category": "Programming",
        "aliases": ["operating systems", "operating system", "os concepts"],
    },
    "IoT": {"category": "Programming", "aliases": ["iot", "internet of things"]},
    "Shell Scripting": {"category": "Programming", "aliases": ["shell scripting", "bash scripting"]},
    # --- Web Development ---
    "HTML": {"category": "Web Development", "aliases": ["html", "html5"]},
    "CSS": {"category": "Web Development", "aliases": ["css", "css3"]},
    "React": {"category": "Web Development", "aliases": ["react", "reactjs", "react js"]},
    "Angular": {"category": "Web Development", "aliases": ["angular", "angularjs", "angular js"]},
    "Vue.js": {"category": "Web Development", "aliases": ["vue js", "vue", "vuejs"]},
    "Node.js": {"category": "Web Development", "aliases": ["node js", "nodejs", "node"]},
    "Express.js": {"category": "Web Development", "aliases": ["express js", "express", "expressjs"]},
    "Django": {"category": "Web Development", "aliases": ["django"]},
    "Flask": {"category": "Web Development", "aliases": ["flask"]},
    "Spring Boot": {"category": "Web Development", "aliases": ["spring boot", "springboot", "spring"]},
    "REST APIs": {"category": "Web Development", "aliases": ["rest api", "rest apis", "restful", "restful api", "restful apis"]},
    "GraphQL": {"category": "Web Development", "aliases": ["graphql"]},
    "Web Development": {"category": "Web Development", "aliases": ["web development", "web dev", "fullstack", "full stack"]},
    "Bootstrap": {"category": "Web Development", "aliases": ["bootstrap"]},
    "Tailwind CSS": {"category": "Web Development", "aliases": ["tailwind", "tailwind css"]},
    # --- Databases ---
    "SQL": {"category": "Databases", "aliases": ["sql"]},
    "MySQL": {"category": "Databases", "aliases": ["mysql"]},
    "PostgreSQL": {"category": "Databases", "aliases": ["postgresql", "postgres"]},
    "MongoDB": {"category": "Databases", "aliases": ["mongodb", "mongo"]},
    "Oracle": {"category": "Databases", "aliases": ["oracle"]},
    "SQLite": {"category": "Databases", "aliases": ["sqlite"]},
    "NoSQL": {"category": "Databases", "aliases": ["nosql"]},
    "Redis": {"category": "Databases", "aliases": ["redis"]},
    "Database Design": {"category": "Databases", "aliases": ["database design", "schema design", "er diagram"]},
    "DBMS": {"category": "Databases", "aliases": ["dbms", "database management"]},
    # --- Cloud & DevOps ---
    "AWS": {"category": "Cloud & DevOps", "aliases": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudfront"]},
    "Azure": {"category": "Cloud & DevOps", "aliases": ["azure", "microsoft azure"]},
    "Google Cloud": {"category": "Cloud & DevOps", "aliases": ["google cloud", "gcp", "google cloud platform"]},
    "Docker": {"category": "Cloud & DevOps", "aliases": ["docker"]},
    "Kubernetes": {"category": "Cloud & DevOps", "aliases": ["kubernetes", "k8s"]},
    "CI/CD": {"category": "Cloud & DevOps", "aliases": ["ci cd", "cicd", "continuous integration", "continuous delivery"]},
    "Jenkins": {"category": "Cloud & DevOps", "aliases": ["jenkins"]},
    "Linux": {"category": "Cloud & DevOps", "aliases": ["linux", "ubuntu", "unix"]},
    "DevOps": {"category": "Cloud & DevOps", "aliases": ["devops"]},
    "Terraform": {"category": "Cloud & DevOps", "aliases": ["terraform"]},
    "Cloud Computing": {"category": "Cloud & DevOps", "aliases": ["cloud computing", "cloud"]},
    # --- Data & AI ---
    "Machine Learning": {"category": "Data & AI", "aliases": ["machine learning", "ml"]},
    "Deep Learning": {"category": "Data & AI", "aliases": ["deep learning", "dl", "neural network", "cnn", "rnn"]},
    "Artificial Intelligence": {"category": "Data & AI", "aliases": ["artificial intelligence", "ai", "genai", "generative ai"]},
    "NLP": {"category": "Data & AI", "aliases": ["nlp", "natural language processing"]},
    "Computer Vision": {"category": "Data & AI", "aliases": ["computer vision", "opencv"]},
    "Data Analysis": {"category": "Data & AI", "aliases": ["data analysis", "data analytics"]},
    "Data Visualization": {"category": "Data & AI", "aliases": ["data visualization", "visualization"]},
    "Statistics": {"category": "Data & AI", "aliases": ["statistics", "statistical"]},
    "Mathematics": {"category": "Data & AI", "aliases": ["mathematics", "math", "maths", "linear algebra", "calculus", "discrete mathematics", "probability"]},
    "Pandas": {"category": "Data & AI", "aliases": ["pandas"]},
    "NumPy": {"category": "Data & AI", "aliases": ["numpy"]},
    "TensorFlow": {"category": "Data & AI", "aliases": ["tensorflow", "tf"]},
    "PyTorch": {"category": "Data & AI", "aliases": ["pytorch", "torch"]},
    "Power BI": {"category": "Data & AI", "aliases": ["power bi", "powerbi"]},
    "Tableau": {"category": "Data & AI", "aliases": ["tableau"]},
    "Excel": {"category": "Data & AI", "aliases": ["excel", "spreadsheet"]},
    "Big Data": {"category": "Data & AI", "aliases": ["big data"]},
    "Hadoop": {"category": "Data & AI", "aliases": ["hadoop"]},
    "Spark": {"category": "Data & AI", "aliases": ["spark", "pyspark"]},
    # --- Tools & Platforms ---
    "Git": {"category": "Tools & Platforms", "aliases": ["git"]},
    "GitHub": {"category": "Tools & Platforms", "aliases": ["github", "gitlab"]},
    "Jupyter": {"category": "Tools & Platforms", "aliases": ["jupyter", "jupyter notebook"]},
    "VS Code": {"category": "Tools & Platforms", "aliases": ["vs code", "vscode", "visual studio code"]},
    "Postman": {"category": "Tools & Platforms", "aliases": ["postman"]},
    "Agile": {"category": "Tools & Platforms", "aliases": ["agile"]},
    "Scrum": {"category": "Tools & Platforms", "aliases": ["scrum"]},
    "Project Management": {"category": "Tools & Platforms", "aliases": ["project management"]},
    "SDLC": {"category": "Tools & Platforms", "aliases": ["sdlc", "software development life cycle"]},
    # --- Networking & Security ---
    "Networking": {"category": "Networking & Security", "aliases": ["networking", "computer networks", "computer network"]},
    "TCP/IP": {"category": "Networking & Security", "aliases": ["tcp ip", "tcp/ip", "tcpip", "ip addressing"]},
    "Cybersecurity": {"category": "Networking & Security", "aliases": ["cybersecurity", "cyber security", "information security"]},
    "Ethical Hacking": {"category": "Networking & Security", "aliases": ["ethical hacking", "penetration testing", "pentesting"]},
    "Network Security": {"category": "Networking & Security", "aliases": ["network security"]},
    "Cryptography": {"category": "Networking & Security", "aliases": ["cryptography", "crypto"]},
    # --- Testing & QA ---
    "Software Testing": {"category": "Testing & QA", "aliases": ["software testing", "testing"]},
    "Manual Testing": {"category": "Testing & QA", "aliases": ["manual testing"]},
    "Automation Testing": {"category": "Testing & QA", "aliases": ["automation testing", "test automation"]},
    "Selenium": {"category": "Testing & QA", "aliases": ["selenium"]},
    "JUnit": {"category": "Testing & QA", "aliases": ["junit", "unit testing"]},
    # --- Mobile & UI/UX ---
    "Android": {"category": "Mobile & UI/UX", "aliases": ["android"]},
    "iOS": {"category": "Mobile & UI/UX", "aliases": ["ios"]},
    "React Native": {"category": "Mobile & UI/UX", "aliases": ["react native"]},
    "Flutter": {"category": "Mobile & UI/UX", "aliases": ["flutter"]},
    "Mobile Development": {"category": "Mobile & UI/UX", "aliases": ["mobile development", "mobile app", "app development"]},
    "UI/UX Design": {"category": "Mobile & UI/UX", "aliases": ["ui ux", "ui/ux", "ui design", "ux design", "design thinking"]},
    "Figma": {"category": "Mobile & UI/UX", "aliases": ["figma"]},
    "User Research": {"category": "Mobile & UI/UX", "aliases": ["user research", "user testing"]},
    "Wireframing": {"category": "Mobile & UI/UX", "aliases": ["wireframing", "wireframe", "prototyping"]},
    # --- Soft Skills ---
    "Communication": {"category": "Soft Skills", "aliases": ["communication", "verbal communication", "written communication"]},
    "Teamwork": {"category": "Soft Skills", "aliases": ["teamwork", "team player", "collaborative"]},
    "Leadership": {"category": "Soft Skills", "aliases": ["leadership", "leading"]},
    "Time Management": {"category": "Soft Skills", "aliases": ["time management"]},
    "Critical Thinking": {"category": "Soft Skills", "aliases": ["critical thinking"]},
    "Adaptability": {"category": "Soft Skills", "aliases": ["adaptability", "flexible"]},
    "Presentation Skills": {"category": "Soft Skills", "aliases": ["presentation", "presentations"]},
    "Collaboration": {"category": "Soft Skills", "aliases": ["collaboration", "collaborate"]},
    "Public Speaking": {"category": "Soft Skills", "aliases": ["public speaking"]},
    "Analytical Thinking": {"category": "Soft Skills", "aliases": ["analytical thinking", "analytical skills", "analytics skills"]},
}

# Name (lowercased) -> canonical skill, for fast direct lookups
_SKILL_BY_NAME = {k.lower(): k for k in SKILLS}

TECH_CATEGORIES = {c for c in SKILL_CATEGORIES if c != "Soft Skills"}

# ---------------------------------------------------------------------------
# Skill matching
# ---------------------------------------------------------------------------


def canonicalize(name: str) -> str | None:
    """Best-effort map of a raw skill string to a canonical KB skill."""
    key = _SKILL_BY_NAME.get(name.strip().lower())
    if key:
        return key
    norm = normalize(name)
    if norm in _SKILL_BY_NAME:
        return _SKILL_BY_NAME[norm]
    for canonical, meta in SKILLS.items():
        for alias in meta["aliases"]:
            if alias == norm:
                return canonical
    return None


def match_skills(text: str) -> dict[str, dict]:
    """Return {canonical: {count, category, alias}} for every skill found.

    * aliases of 3 chars or fewer are matched as whole tokens (avoids "go"
      matching "goal", "c" matching every word with a c);
    * longer aliases are substring matches on the normalized text.
    """
    norm = normalize(text)
    if not norm:
        return {}
    tokens = set(norm.split(" "))
    hits: dict[str, dict] = {}
    for canonical, meta in SKILLS.items():
        count = 0
        matched_alias = None
        for alias in meta["aliases"]:
            alias_norm = alias.strip().lower()
            if not alias_norm:
                continue
            if len(alias_norm) <= 3:
                if alias_norm in tokens:
                    count += 1
                    matched_alias = matched_alias or alias_norm
            elif alias_norm in norm:
                count += 1
                matched_alias = matched_alias or alias_norm
        if count:
            hits[canonical] = {
                "count": count,
                "category": meta["category"],
                "alias": matched_alias,
            }
    return hits


# ---------------------------------------------------------------------------
# Coursework -> skills
# ---------------------------------------------------------------------------

# (normalized name substring, [canonical skill names])
COURSE_TO_SKILLS: list[tuple[str, list[str]]] = [
    ("data structures", ["Data Structures", "Algorithms", "Problem Solving"]),
    ("algorithms", ["Algorithms", "Problem Solving"]),
    ("dbms", ["DBMS", "SQL", "Database Design"]),
    ("database management", ["DBMS", "SQL", "Database Design"]),
    ("database", ["SQL", "Database Design"]),
    ("sql", ["SQL"]),
    ("mongodb", ["MongoDB", "NoSQL"]),
    ("python", ["Python"]),
    ("java", ["Java", "OOPS"]),
    ("c programming", ["C"]),
    ("c++", ["C++"]),
    ("cpp", ["C++"]),
    ("javascript", ["JavaScript"]),
    ("html", ["HTML"]),
    ("css", ["CSS"]),
    ("web technology", ["HTML", "CSS", "JavaScript", "Web Development"]),
    ("web development", ["HTML", "CSS", "JavaScript", "Web Development"]),
    ("react", ["React"]),
    ("node", ["Node.js"]),
    ("express", ["Express.js"]),
    ("django", ["Django"]),
    ("flask", ["Flask"]),
    ("operating system", ["Operating Systems", "Linux"]),
    ("computer network", ["Networking", "Network Security"]),
    ("machine learning", ["Machine Learning", "Python"]),
    ("deep learning", ["Deep Learning"]),
    ("artificial intelligence", ["Artificial Intelligence"]),
    ("intelligence", ["Artificial Intelligence"]),
    ("data mining", ["Data Analysis", "Data Visualization"]),
    ("data analytics", ["Data Analysis", "Data Visualization", "Excel"]),
    ("cloud", ["Cloud Computing"]),
    ("aws", ["AWS"]),
    ("azure", ["Azure"]),
    ("docker", ["Docker"]),
    ("git", ["Git", "GitHub"]),
    ("github", ["Git", "GitHub"]),
    ("linux", ["Linux"]),
    ("software engineering", ["SDLC", "Agile", "Git"]),
    ("software testing", ["Software Testing", "Manual Testing", "Automation Testing"]),
    ("automation", ["Automation Testing", "Selenium"]),
    ("android", ["Android", "Kotlin"]),
    ("ios", ["iOS", "Swift"]),
    ("mobile", ["Mobile Development"]),
    ("security", ["Cybersecurity"]),
    ("cyber", ["Cybersecurity"]),
    ("iot", ["IoT"]),
    ("big data", ["Big Data", "Hadoop", "Spark"]),
    ("probability", ["Statistics", "Mathematics"]),
    ("statistics", ["Statistics", "Mathematics"]),
    ("linear algebra", ["Mathematics"]),
    ("calculus", ["Mathematics"]),
    ("mathematics", ["Mathematics"]),
    ("maths", ["Mathematics"]),
    ("excel", ["Excel"]),
    ("power bi", ["Power BI", "Data Visualization"]),
    ("tableau", ["Tableau", "Data Visualization"]),
    ("communication", ["Communication"]),
    ("english", ["Communication"]),
    ("aptitude", ["Problem Solving"]),
    ("reasoning", ["Problem Solving"]),
    ("interview", ["Communication", "Presentation Skills"]),
    ("ui ux", ["UI/UX Design", "Figma", "User Research"]),
    ("design thinking", ["UI/UX Design", "Wireframing"]),
    ("project management", ["Project Management", "Agile"]),
    ("r programming", ["R"]),
    ("data structures and algorithms", ["Data Structures", "Algorithms", "Problem Solving"]),
    ("oop", ["OOPS", "Java"]),
    ("object oriented", ["OOPS", "Java"]),
]


def match_course(name: str) -> list[str]:
    """Canonical skills implied by a course name (pattern map + direct lookup)."""
    norm = normalize(name)
    skills: list[str] = []
    seen: set[str] = set()
    for pattern, mapped in COURSE_TO_SKILLS:
        if pattern in norm:
            for s in mapped:
                if s not in seen and s in SKILLS:
                    seen.add(s)
                    skills.append(s)
    # direct KB match (e.g. a course literally named "Deep Learning")
    for canonical in match_skills(name):
        if canonical not in seen:
            seen.add(canonical)
            skills.append(canonical)
    return skills


# ---------------------------------------------------------------------------
# Job role -> required skills (career recommendations)
# ---------------------------------------------------------------------------

ROLES: list[dict] = [
    {
        "role": "Frontend Developer",
        "summary": "Builds the user-facing side of web products with HTML, CSS and JS frameworks.",
        "required": ["HTML", "CSS", "JavaScript", "React", "REST APIs", "Git", "Bootstrap", "Problem Solving", "Communication"],
    },
    {
        "role": "Backend Developer",
        "summary": "Designs servers, APIs and databases that power applications.",
        "required": ["Python", "Java", "Node.js", "SQL", "MySQL", "REST APIs", "Database Design", "Git", "Docker"],
    },
    {
        "role": "Full-Stack Developer",
        "summary": "Owns features end-to-end across frontend, backend and databases.",
        "required": ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "MongoDB", "REST APIs", "Git"],
    },
    {
        "role": "Data Analyst",
        "summary": "Turns raw data into reports and dashboards that drive decisions.",
        "required": ["SQL", "Excel", "Power BI", "Data Analysis", "Data Visualization", "Statistics", "Python", "Pandas"],
    },
    {
        "role": "Data Scientist",
        "summary": "Builds models that explain data and predict outcomes.",
        "required": ["Python", "Machine Learning", "Statistics", "SQL", "Pandas", "NumPy", "Data Visualization", "Mathematics", "Deep Learning"],
    },
    {
        "role": "Machine Learning Engineer",
        "summary": "Ship ML models to production: pipelines, serving and monitoring.",
        "required": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Data Structures", "Algorithms", "SQL", "Docker"],
    },
    {
        "role": "DevOps Engineer",
        "summary": "Automates building, testing and deploying software at scale.",
        "required": ["Linux", "Docker", "Kubernetes", "CI/CD", "Jenkins", "AWS", "Terraform", "Git", "Shell Scripting", "Azure"],
    },
    {
        "role": "Cloud Engineer",
        "summary": "Designs and runs reliable infrastructure on public clouds.",
        "required": ["AWS", "Azure", "Google Cloud", "Linux", "Docker", "Networking", "Cloud Computing", "Git", "Terraform"],
    },
    {
        "role": "Software Engineer",
        "summary": "Designs, builds and ships reliable software in a team.",
        "required": ["Python", "Java", "C++", "Data Structures", "Algorithms", "SQL", "OOPS", "Git", "Problem Solving"],
    },
    {
        "role": "Android Developer",
        "summary": "Builds native Android apps with Kotlin/Java.",
        "required": ["Kotlin", "Java", "Android", "REST APIs", "Git", "SQLite", "Mobile Development"],
    },
    {
        "role": "Cybersecurity Analyst",
        "summary": "Protects systems and data from threats; monitors and responds to incidents.",
        "required": ["Networking", "Cybersecurity", "Linux", "Ethical Hacking", "Network Security", "Operating Systems", "TCP/IP"],
    },
    {
        "role": "UI/UX Designer",
        "summary": "Designs intuitive, usable interfaces grounded in user research.",
        "required": ["UI/UX Design", "Figma", "HTML", "CSS", "User Research", "Wireframing", "Communication"],
    },
    {
        "role": "QA / Test Engineer",
        "summary": "Ensures software quality through manual and automated testing.",
        "required": ["Software Testing", "Manual Testing", "Automation Testing", "Selenium", "Python", "JUnit", "SQL"],
    },
    {
        "role": "AI Engineer",
        "summary": "Turns foundation models and ML into products at scale.",
        "required": ["Python", "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch", "Data Structures", "Algorithms", "Docker"],
    },
    {
        "role": "Database Administrator",
        "summary": "Installs, tunes, secures and backs up database systems.",
        "required": ["SQL", "MySQL", "Oracle", "Database Design", "DBMS", "PostgreSQL", "MongoDB", "Linux"],
    },
]


# ---------------------------------------------------------------------------
# Resume heuristics
# ---------------------------------------------------------------------------

SECTION_HEADERS = {
    "education": [r"education", r"academic", r"qualification", r"academics"],
    "projects": [r"projects?", r"academic projects?", r"personal projects?", r"mini projects?"],
    "experience": [r"experience", r"work experience", r"internship", r"internships", r"professional experience"],
    "certifications": [r"certification", r"certifications", r"courses", r"achievements", r"accomplishments"],
    "skills": [r"technical skills", r"skills", r"skill set", r"core competencies"],
    "summary": [r"summary", r"objective", r"profile", r"about"],
}

DEGREE_KEYWORDS = [
    "btech", "bsc", "mtech", "msc", "bca", "mca", "bcom", "mcom", "bba", "mba",
    "bachelor", "master", "diploma", "phd", "be",
]

CERT_KEYWORDS = [
    "certificate", "certification", "certified", "coursera", "udemy", "nptel",
    "nasscom", "hackerrank", "great learning", "infosys springboard",
]

EXPERIENCE_KEYWORDS = ["intern", "worked at", "work at", "job", "role", "team lead"]

PROJECT_KEYWORDS = ["project", "built", "developed", "implemented", "created", "application", "app "]


def is_section_header(line: str) -> str:
    """Return the section name if `line` looks like a resume section header."""
    nl = normalize(line).strip(" :")
    if not nl or len(line) > 60:
        return ""
    for section, patterns in SECTION_HEADERS.items():
        for pat in patterns:
            if re.fullmatch(pat + r"[\s:]?", nl) or re.fullmatch(pat, nl):
                return section
    return ""