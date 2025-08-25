#!/usr/bin/env python3
"""
Configuración centralizada para DataPM Processor
"""

import os
from typing import Dict, List

# Configuración de LLMs
LLM_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 100000,
        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
    },
    "ollama": {
        "model": "llama3.2:3b",  # Modelo por defecto
        "url": "http://localhost:11434",
        "timeout": 30,
    }
}

# Schema de normalización expandido para mayor cobertura
NORMALIZATION_SCHEMA = {
    "job_title_short": [
        # Product Management
        "Product Manager", "Product Owner", "Product Marketing Manager", "Product Operations", "Product Analyst",
        
        # Datos & AI
        "Data Analyst", "BI Analyst", "Data Engineer", "Data Scientist", "ML Engineer", "Analytics Engineer", "Data Product Manager",
        
        # Design Roles
        "UX/UI Designer", "UX Designer", "UI Designer", "Product Designer",  "Graphic Designer", "Web Designer", "Visual Designer",
        
        # Engineering Roles
        "Software Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "DevOps / SRE", "QA / Test Engineer", "Test Engineer", "Mobile Developer",
        
        # Marketing Roles
        "Growth / Performance Analyst", "Growth Marketer", "Digital Marketing Specialist", "Product Marketing Manager",
        
        # Project & Business Roles
        "Business Analyst", "Project Manager", "Implementation / Onboarding Manager", "Operations Manager", "Process Analyst",
        
        # IT & Technical Roles
        "System Administrator", "Network Engineer", "Security Engineer", "IT Specialist", "Technical Support Engineer",
        
        # Compliance & Quality
        "Quality Assurance Specialist", "Compliance / Regulatory Specialist","Quality Analyst","Auditor", "Risk Analyst",
        
        # Sales & Customer Success
        "Sales Manager", "Sales Representative", "Account Manager", "Customer Success", 
        
        # Research & Analytics
        "Research Analyst", "User Researcher",
        
        # Other Common Roles
        "Consultant", "Advisor", "Assistant",
    ],
    "experience_years": ["0-3", "3-5", "5+"],
    "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
    "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
    "degrees": [
        "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
        "Higher Education", "Engineering", "Automotive Engineering", 
        "Vocational Training", "Other"
    ],
    "skills": [
         # -------------------------
        # Project Management & Methodology
        # -------------------------
        "Project Management",
        "Agile",
        "Scrum",
        "Kanban",
        "Lean",
        "Six Sigma",
        "Waterfall",
        "SAFe",
        "DevOps",
        "CI/CD",
        "SDLC",
        "Product Lifecycle Management",
        "Project Management (advanced)",
        "Release Management",
        "Change Management",
        "Technical debt management",
        "OkR facilitation",
        # -------------------------
        # Data & Analytics (quantitative)
        # -------------------------
        "Data Analysis",
        "Data Visualization",
        "Statistical Analysis",
        "Predictive Analytics",
        "Machine Learning",
        "Deep Learning",
        "AI",
        "Natural Language Processing",
        "NLP",
        "Business Intelligence",
        "Data Mining",
        "Data Modeling",
        "Data Governance",
        "A/B Testing",
        "Hypothesis Testing",
        "Quantitative Research",
        "Qualitative Research",
        "Experimentation",
        "Experiment Design",
        "Experiment Analysis",
        "Causal Inference",
        "Cohort Analysis",
        "Funnel Analysis",
        "Retention Analysis",
        "Attribution Modeling",
        "Cohort Retention Curve Analysis",
        "Survival Analysis (basic intuition)",
        "Power analysis (sample size calculation)",
        "Bayesian A/B testing",
        # -------------------------
        # Design & UX (product-facing)
        # -------------------------
        "UI/UX Design",
        "User Research",
        "User-Centered Design",
        "Design Thinking",
        "Wireframing",
        "Prototyping",
        "Visual Design",
        "Interaction Design",
        "Information Architecture",
        "Usability Testing",
        "Accessibility Design",
        "Design Systems",
        "Brand Design",
        "Graphic Design",
        "Digital Design",
        "Prototype Testing",
        "User Interviews",
        "Persona Development",
        "Journey Mapping",
        "User Journey Mapping",
        "Onboarding Optimization",
        "UX metrics (task success, time on task)",
        "A11y testing basics",
        # -------------------------
        # Product Management core
        # -------------------------
        "Product Management",
        "Product Strategy",
        "Product Development",
        "Product Launch",
        "Product Roadmapping",
        "Feature Prioritization",
        "User Stories",
        "Requirements Gathering",
        "Market Research",
        "Competitive Analysis",
        "Product Analytics",
        "Growth Hacking",
        "Tracking Plan",
        "Event Taxonomy",
        "Event Tracking",
        "Instrumentation",
        "Feature Flagging",
        "Product Ops support tasks",
        "Product portfolio management (basic)",
        "Opportunity Sizing",
        "Requirement Gathering (detailed)",
        "Acceptance Criteria",
        "Go-to-Market (GTM)",
        "Launch Planning",
        "Pricing Strategy",
        "Business Model Design",
        "Subscription Models",
        "Churn Reduction",
        "Customer Segmentation",
        "Jobs To Be Done (JTBD)",
        "Roadmap Prioritization",
        "Stakeholder Management",
        "Cross-functional Collaboration",
        "Executive Communication",
        "OKRs",
        "KPI Definition",
        "Metrics Design",
        "Performance Measurement",
        "Roadmap Communication",
        "Roadmap tradeoff communication",
        "Launch post-mortems and learnings",
        # -------------------------
        # Growth, Acquisition & Monetization
        # -------------------------
        "Growth Strategy",
        "Product-led Growth (PLG)",
        "PLG",
        "Growth Hacking",
        "User Acquisition",
        "Acquisition Channels (Paid / Organic)",
        "Paid Acquisition",
        "Landing Page Conversion Optimization",
        "Subscription Models",
        "Monetization",
        "Monetization Strategy",
        "Average Order Value (AOV)",
        "AOV",
        "Lifetime Value (LTV / CLTV)",
        "LTV",
        "Customer Acquisition Cost (CAC)",
        "ARPU / ARPA",
        "MRR / ARR / Churn Metrics",
        "Unit Economics",
        "Attribution Modeling",
        "Campaign Measurement",
        "Channel Partnerships basics",
        "Revenue operations basics (RevOps)",
        "Funnel optimization methodology",
        "E-commerce product considerations (checkout optimization)",
        # -------------------------
        # Experimentation, CRO & Funnels
        # -------------------------
        "Experimentation Culture",
        "Hypothesis Driven Development",
        "A/B Testing",
        "A/B Test Execution",
        "Multivariate Testing",
        "Experiment Design",
        "Experiment Analysis",
        "Feature Flagging",
        "Experimentation Platform",
        "Experimentation Platform (e.g. Optimizely/VWO)",
        "Conversion Rate Optimization (CRO)",
        "Conversion Funnels",
        "Funnel Analysis",
        "Funnel Performance",
        "Conversion Rate (CVR) Analysis",
        "Funnel Optimization",
        "AB Testing (statistical foundations)",
        # -------------------------
        # BI / Measurement / Reporting
        # -------------------------
        "Reporting & Dashboards",
        "KPI Dashboards",
        "Data-driven decision making",
        "Business Intelligence",
        "Data Warehousing concepts",
        "Funnel & Retention Dashboards",
        "Self-serve analytics literacy",
        # -------------------------
        # Technical literacy for PMs (engineering adjacent)
        # -------------------------
        "API",
        "REST APIs",
        "GraphQL",
        "API awareness (REST/GraphQL)",
        "API Design Awareness",
        "Microservices",
        "Microservices awareness",
        "Cloud Computing",
        "Cloud Computing awareness",
        "AWS",
        "Azure",
        "GCP",
        "Infrastructure as Code",
        "Infrastructure as Code (awareness)",
        "Terraform",
        "Pulumi",
        "DevOps literacy",
        "CI/CD awareness",
        "System Design",
        "System Design awareness",
        "Technical Specification",
        "Instrumentation & Telemetry basics",
        "Security & Privacy awareness (GDPR)",
        "Performance optimization awareness",
        "Mobile product considerations (iOS/Android differences)",
        "App performance monitoring basics",
        "MLOps awareness",
        # -------------------------
        # ML / AI basics (for PMs)
        # -------------------------
        "Machine Learning literacy for PMs",
        "Model evaluation basics (precision/recall/AUC)",
        "NLP awareness",
        "Ethical AI awareness",
        "Generative AI awareness",
        "Prompt engineering basics (for GenAI products)",
        # -------------------------
        # Programming & Development (PM awareness & basic)
        # -------------------------
        "Programming",
        "Software Development",
        "Web Development",
        "Mobile Development",
        "Frontend Development",
        "Backend Development",
        "Full Stack Development",
        "Object-Oriented Programming",
        "Functional Programming",
        "Test-Driven Development",
        "Code Review",
        "Version Control",
        "Git",
        "Debugging",
        "Performance Optimization",
        "Database Design",
        "SQL",
        "NoSQL",
        "Data Warehousing",
        "ETL",
        "Data Pipeline",
        "Data Pipeline awareness",
        # -------------------------
        # BI / Data tooling & pipelines
        # -------------------------
        "BigQuery",
        "Snowflake",
        "Amazon Redshift",
        "ClickHouse",
        "Presto",
        "Trino",
        "Druid",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "Cassandra",
        "DynamoDB",
        "Elasticsearch",
        "SQLite",
        "Fivetran",
        "Stitch",
        "Airbyte",
        "Talend",
        "Informatica",
        "Matillion",
        "dbt",
        "Airflow",
        "Prefect",
        "Dagster",
        "Apache Kafka",
        "Confluent",
        "Kafka Streams",
        "Apache Flink",
        "Spark",
        "Hadoop",
        "Kinesis",
        # -------------------------
        # Data Science / ML tooling (PM-relevant)
        # -------------------------
        "Python",
        "R",
        "Jupyter",
        "Colab",
        "Databricks",
        "Hugging Face",
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "XGBoost",
        "LightGBM",
        "MLflow",
        "SageMaker",
        "Kubeflow",
        "Weights & Biases",
        "OpenAI API",
        "Anthropic API",
        "Cohere",
        "LangChain",
        "LlamaIndex",
        "H2O.ai",
        # -------------------------
        # Design & Prototyping tools
        # -------------------------
        "Figma",
        "Sketch",
        "Adobe XD",
        "InVision",
        "Marvel",
        "Axure RP",
        "Framer",
        "Principle",
        "Zeplin",
        "Abstract",
        "Balsamiq",
        "Proto.io",
        "Origami Studio",
        # -------------------------
        # User Research & Testing tools
        # -------------------------
        "UserTesting",
        "UserZoom",
        "Lookback",
        "Hotjar",
        "FullStory",
        "PlaybookUX",
        "Maze",
        "Optimal Workshop",
        "UsabilityHub",
        "Typeform",
        "SurveyMonkey",
        "Qualtrics",
        # -------------------------
        # Experimentation & Feature Flags / A/B testing platforms
        # -------------------------
        "Optimizely",
        "VWO",
        "Google Optimize",
        "LaunchDarkly",
        "Split.io",
        "Flagsmith",
        "GrowthBook",
        "Unleash",
        "Adobe Target",
        # -------------------------
        # Analytics & BI platforms
        # -------------------------
        "Google Analytics (UA)",
        "GA4",
        "Mixpanel",
        "Amplitude",
        "Heap",
        "PostHog",
        "Tableau",
        "Power BI",
        "Looker",
        "Looker Studio",
        "Mode Analytics",
        "Metabase",
        "Redash",
        "Apache Superset",
        "Qlik Sense",
        "QlikView",
        "MicroStrategy",
        "Domo",
        # -------------------------
        # Mobile analytics / attribution
        # -------------------------
        "Firebase Analytics",
        "Appsflyer",
        "Adjust",
        "Branch",
        # -------------------------
        # Backend / Cloud / Infra / DevOps tools
        # -------------------------
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Pulumi",
        "Ansible",
        "Chef",
        "Puppet",
        "Jenkins",
        "GitHub Actions",
        "GitLab CI",
        "CircleCI",
        "Travis CI",
        "Argo CD",
        "Prometheus",
        "Grafana",
        "Datadog",
        "New Relic",
        "Sentry",
        "ELK Stack (Elasticsearch, Logstash, Kibana)",
        # -------------------------
        # Version control & code hosting
        # -------------------------
        "GitHub",
        "GitLab",
        "Bitbucket",
        "Azure DevOps",
        # -------------------------
        # Feature management & rollout
        # -------------------------
        "LaunchDarkly",
        "Split",
        "Flagsmith",
        "GrowthBook",
        # (kept duplicates purposeful: platforms appear in multiple contexts)
        # -------------------------
        # Collaboration & Whiteboarding
        # -------------------------
        "Slack",
        "Microsoft Teams",
        "Zoom",
        "Google Meet",
        "Miro",
        "Mural",
        "Whimsical",
        "Lucidchart",
        "Jamboard",
        "FigJam",
        "MS Whiteboard",
        # -------------------------
        # Office & File storage
        # -------------------------
        "Dropbox",
        "Google Drive",
        "OneDrive",
        "Box",
        "Microsoft Office",
        "Excel",
        "PowerPoint",
        "Word",
        "Outlook",
        "Google Workspace",
        "Notion",
        "Confluence",
        # -------------------------
        # CRM & Customer Support / Engagement
        # -------------------------
        "Salesforce",
        "HubSpot",
        "Zendesk",
        "Intercom",
        "Freshdesk",
        "Front",
        "Help Scout",
        "Gorgias",
        "Pipedrive",
        "Zoho CRM",
        "Microsoft Dynamics 365",
        # -------------------------
        # Marketing & Acquisition tools
        # -------------------------
        "Google Ads",
        "Google Marketing Platform",
        "Google Tag Manager",
        "Facebook Ads / Meta Ads",
        "TikTok Ads",
        "LinkedIn Ads",
        "Twitter Ads",
        "Bing Ads",
        "Adobe Advertising Cloud",
        "Mailchimp",
        "Klaviyo",
        "Braze",
        "Iterable",
        "SendGrid",
        "Postmark",
        "ActiveCampaign",
        "HubSpot Marketing Hub",
        "Marketo",
        "Eloqua",
        "PPC",
        "SEO",
        "SEM",
        "Content Marketing",
        "Social Media Marketing",
        "Email Marketing",
        "Marketing Analytics",
        # -------------------------
        # E-commerce & Payments
        # -------------------------
        "Shopify",
        "Magento",
        "WooCommerce",
        "BigCommerce",
        "Stripe",
        "Adyen",
        "Braintree",
        "PayPal",
        "Chargebee",
        "Recurly",
        "Zuora",
        # -------------------------
        # CDP / Integration / No-code
        # -------------------------
        "Segment",
        "RudderStack",
        "mParticle",
        "Tealium",
        "BlueConic",
        "Zapier",
        "Make (Integromat)",
        "Workato",
        "Tray.io",
        "Airtable",
        "Bubble",
        "Webflow",
        # -------------------------
        # Monitoring / APM / Security / Compliance
        # -------------------------
        "New Relic",
        "Datadog",
        "Sentry",
        "AppDynamics",
        "Raygun",
        "OneTrust",
        "Snyk",
        "SonarQube",
        "Qualys",
        "CrowdStrike",
        "Splunk",
        "Security",
        "Cybersecurity",
        "Information Security",
        "SLA awareness",
        "OneTrust",
        # -------------------------
        # Experimentation & Analytic add-ons
        # -------------------------
        "Snowplow",
        "Segment",
        "Amplitude",
        "Mixpanel",
        # -------------------------
        # Additional analytics/ML platforms
        # -------------------------
        "Alteryx",
        "RapidMiner",
        "SAS",
        "DataRobot",
        # -------------------------
        # Data stores & orchestration advanced
        # -------------------------
        "ClickHouse",
        "Presto",
        "Trino",
        "Druid",
        # -------------------------
        # API / dev tools & misc
        # -------------------------
        "Postman",
        "Insomnia",
        "Swagger / OpenAPI",
        "GraphQL",
        "Apollo",
        "Vercel",
        "Netlify",
        "Heroku",
        "Firebase",
        # -------------------------
        # Mobile / App stores / ASO
        # -------------------------
        "App Store Connect",
        "Google Play Console",
        "App Store Optimization (ASO) tools",
        "ASO",
        # -------------------------
        # Customer Feedback & Community
        # -------------------------
        "Typeform",
        "SurveyMonkey",
        "Canny",
        "Productboard (insights)",
        "UserVoice",
        "Discourse",
        "Zendesk Talk",
        # -------------------------
        # Reporting & Visualization (repeated for emphasis)
        # -------------------------
        "Tableau",
        "Power BI",
        "Looker",
        "Looker Studio",
        "Mode",
        "Metabase",
        "Redash",
        "Superset",
        # -------------------------
        # Automation & No-code / Low-code
        # -------------------------
        "Zapier",
        "Make.com",
        "Airtable",
        "Bubble",
        "Webflow",
        "OutSystems",
        # -------------------------
        # Security & Compliance tools (again)
        # -------------------------
        "OneTrust",
        "Snyk",
        "SonarQube",
        "Qualys",
        "CrowdStrike",
        "Splunk",
        # -------------------------
        # Misc / Developer tools
        # -------------------------
        "Postman",
        "Insomnia",
        "Swagger / OpenAPI",
        "GraphQL",
        "Apollo",
        # -------------------------
        # Additional / domain-specific and soft skills
        # -------------------------
        "Communication",
        "Problem Solving",
        "Critical Thinking",
        "Analytical Thinking",
        "Business Acumen",
        "Strategic Thinking",
        "Leadership",
        "Team Management",
        "Cross-functional Collaboration",
        "Stakeholder Management",
        "Presentation Skills",
        "Negotiation",
        "Conflict Resolution",
        "Time Management",
        "Organization",
        "Regulatory Compliance",
        "Quality Assurance",
        "Quality Control",
        "Process Optimization",
        "Supply Chain Management",
        "Logistics",
        "Healthcare Knowledge",
        "Financial Analysis",
        "Risk Management",
        "Auditing",
        "Document Management",
        "Technical Writing",
        "Training",
        "Mentoring",
        "Coaching",
        "Customer Success alignment",
        "Sales enablement understanding",
        "Account Management basics",
        "Support escalation processes",
        "Localization / Internationalization basics",
        "Ethical product considerations",
        "Data Privacy Impact Assessment (basic)",
        "Developer experience awareness (DX)",
        "Internal tools product awareness",
        "Mobile-first mindset",
        "Progressive Web App awareness",
        "Offline-first design awareness",
        "App store and store policy awareness (iOS/Android)",
        "Regulatory compliance for health/med apps (HIPAA/GDPR basics)",
        "B2B vs B2C product differences awareness",
        "Feature adoption analysis",
        "Cohort retention monitoring",
        "Churn root cause analysis",
        "AARRR framework fluency",
        "Growth loops design",
        "Optimization backlog management",
        "Cost-benefit analysis",
        "P&L awareness (basic)",
        "Investment case building",
        "Stakeholder ROI communication",
        "Supplier / Vendor Management",
        "Contract Basics (SOW awareness)",
        "Audit & Traceability basics",
        "SLA awareness",
        "Hiring & Interviewing (for PMs)",
        "Mentoring & Coaching",
        "Influence without authority",
        "Empathy & user-centric mindset",
        "Storytelling with data",
        "Facilitation",
        # -------------------------
        # Legacy / niche (kept as keywords)
        # -------------------------
        "Google Optimize (legacy)",
        "Chartio",
        "Periscope",
        "Keen.io"
    ],
    "software": [
        # -------------------------
        # Programming Languages & Environments
        # -------------------------
        "Python",
        "R",
        "SQL",
        "JavaScript",
        "TypeScript",
        "Java",
        "C#",
        "C++",
        "C",
        "Go",
        "Rust",
        "Scala",
        "PHP",
        "Ruby",
        "Swift",
        "Kotlin",
        "Dart",
        "Perl",
        "MATLAB",
        "Julia",
        "VBA",
        "PowerShell",
        "Bash",
        "Jupyter",
        "Google Colab",

        # -------------------------
        # Frontend / Web Frameworks & Platforms (base names)
        # -------------------------
        "HTML",
        "CSS",
        "React",
        "Angular",
        "Vue.js",
        "Svelte",
        "Node.js",
        "Express",
        "Next.js",
        "Nuxt.js",
        "Gatsby",
        "Vercel",
        "Netlify",
        "WordPress",
        "Django",
        "Flask",
        "FastAPI",
        "Spring Boot",
        "Laravel",
        "Ruby on Rails",

        # -------------------------
        # Databases & Data Stores (base names)
        # -------------------------
        "PostgreSQL",
        "MySQL",
        "SQL Server",
        "Oracle",
        "SQLite",
        "MongoDB",
        "Redis",
        "Cassandra",
        "DynamoDB",
        "Firebase",
        "Supabase",
        "PlanetScale",
        "Elasticsearch",
        "InfluxDB",
        "Neo4j",
        "ClickHouse",

        # -------------------------
        # Cloud Platforms & Hosting (base names)
        # -------------------------
        "AWS",
        "Azure",
        "GCP",
        "DigitalOcean",
        "Heroku",
        "Vercel",
        "Netlify",
        "Cloudflare",
        "Linode",
        "Vultr",
        "IBM Cloud",
        "Oracle Cloud",

        # -------------------------
        # Data Warehouses & OLAP
        # -------------------------
        "BigQuery",
        "Snowflake",
        "Redshift",
        "Databricks",

        # -------------------------
        # Analytics, Measurement & Session Replay (base names)
        # -------------------------
        "Google Analytics",
        "GA4",
        "Mixpanel",
        "Amplitude",
        "Heap",
        "PostHog",
        "FullStory",
        "Hotjar",
        "Pendo",
        "Microsoft Clarity",
        "Crazy Egg",
        "LogRocket",
        "Mouseflow",
        "Woopra",
        "Kissmetrics",
        "Snowplow",
        "Segment",
        "RudderStack",
        "mParticle",
        "Tealium",
        "BlueConic",
        "Tableau",
        "Power BI",
        "Looker",
        "Mode",
        "Metabase",
        "Superset",
        "Redash",
        "Qlik Sense",
        "MicroStrategy",
        "Domo",

        # -------------------------
        # Experimentation / A/B Testing / Feature Flags (base names)
        # -------------------------
        "Optimizely",
        "VWO",
        "Convert",
        "Kameleoon",
        "LaunchDarkly",
        "Split",
        "Flagsmith",
        "GrowthBook",
        "Unleash",
        "AB Tasty",
        "Adobe Target",

        # -------------------------
        # Attribution / Mobile Analytics
        # -------------------------
        "Firebase Analytics",
        "Appsflyer",
        "Adjust",
        "Branch",
        "Singular",

        # -------------------------
        # ETL / Data Integration / Pipelines (base names)
        # -------------------------
        "Fivetran",
        "Stitch",
        "Airbyte",
        "Talend",
        "Informatica",
        "Matillion",
        "dbt",
        "Airflow",
        "Prefect",
        "Dagster",
        "Apache Kafka",
        "Confluent",
        "Apache Flink",
        "Spark",
        "Hadoop",
        "Kinesis",

        # -------------------------
        # Data Science / ML / MLOps (base names)
        # -------------------------
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "Keras",
        "XGBoost",
        "LightGBM",
        "Pandas",
        "NumPy",
        "Matplotlib",
        "Seaborn",
        "Plotly",
        "Bokeh",
        "MLflow",
        "SageMaker",
        "Kubeflow",
        "Weights & Biases",
        "Hugging Face",
        "OpenAI API",
        "Anthropic API",
        "Cohere",
        "LangChain",
        "LlamaIndex",
        "H2O.ai",
        "DataRobot",

        # -------------------------
        # Design & Prototyping (base names)
        # -------------------------
        "Figma",
        "Sketch",
        "Adobe XD",
        "Photoshop",
        "Illustrator",
        "InDesign",
        "Premiere Pro",
        "After Effects",
        "Framer",
        "InVision",
        "Marvel",
        "Principle",
        "Lottie",
        "Canva",
        "Zeplin",
        "Abstract",
        "Balsamiq",
        "Proto.io",
        "Origami Studio",

        # -------------------------
        # User Research / Feedback / Satisfaction / VOC (base names)
        # -------------------------
        "UserTesting",
        "UserZoom",
        "Lookback",
        "Hotjar",
        "FullStory",
        "PlaybookUX",
        "Maze",
        "Optimal Workshop",
        "UsabilityHub",
        "Typeform",
        "SurveyMonkey",
        "Qualtrics",
        "Delighted",
        "Wootric",
        "AskNicely",
        "Usabilla",
        "Userback",
        "Canny",
        "UserVoice",
        "Intercom",
        "Zendesk",
        "Freshdesk",
        "Front",
        "Help Scout",
        "Gorgias",
        "Medallia",
        "Clarabridge",
        "Satismeter",
        "CustomerSure",
        "Alchemer",

        # -------------------------
        # Product Management / Roadmap / Prioritization / Feedback (base names)
        # -------------------------
        "Productboard",
        "Aha!",
        "ProdPad",
        "Roadmunk",
        "airfocus",
        "Jira",
        "Confluence",
        "Notion",
        "Trello",
        "Asana",
        "ClickUp",
        "Monday.com",
        "Wrike",
        "Pendo",
        "ProductPlan",
        "Canny",
        "UserReport",

        # -------------------------
        # Marketing Automation / Email / CRM / CDP (base names)
        # -------------------------
        "Mailchimp",
        "Constant Contact",
        "SendGrid",
        "Klaviyo",
        "ConvertKit",
        "Campaign Monitor",
        "Iterable",
        "Braze",
        "Customer.io",
        "CleverTap",
        "ActiveCampaign",
        "HubSpot",
        "Marketo",
        "Eloqua",
        "Salesforce",
        "Pipedrive",
        "Zoho CRM",
        "Microsoft Dynamics",
        "Amazon SES",
        "Mailgun",
        "Sendinblue",

        # -------------------------
        # Advertising / DSP / Tag Management (base names)
        # -------------------------
        "Google Ads",
        "Google Marketing Platform",
        "Google Tag Manager",
        "Facebook Ads",
        "TikTok Ads",
        "LinkedIn Ads",
        "Twitter Ads",
        "Bing Ads",
        "Adobe Advertising Cloud",
        "The Trade Desk",
        "DV360",

        # -------------------------
        # E-commerce / Payments / Billing (base names)
        # -------------------------
        "Shopify",
        "Magento",
        "WooCommerce",
        "BigCommerce",
        "Stripe",
        "Adyen",
        "Braintree",
        "PayPal",
        "Chargebee",
        "Recurly",
        "Zuora",

        # -------------------------
        # Integrations / No-code / Automation (base names)
        # -------------------------
        "Zapier",
        "Make.com",
        "IFTTT",
        "Workato",
        "Tray.io",
        "Airtable",
        "Bubble",
        "Webflow",
        "OutSystems",
        "Parabola",

        # -------------------------
        # Dev / CI / CD / Infra Monitoring / SRE (base names)
        # -------------------------
        "Docker",
        "Kubernetes",
        "Jenkins",
        "GitHub Actions",
        "GitLab CI",
        "CircleCI",
        "Travis CI",
        "Argo CD",
        "Prometheus",
        "Grafana",
        "Datadog",
        "New Relic",
        "Sentry",
        "ELK Stack",

        # -------------------------
        # Version Control / IDEs (base names)
        # -------------------------
        "Git",
        "GitHub",
        "GitLab",
        "Bitbucket",
        "VS Code",
        "PyCharm",
        "IntelliJ IDEA",
        "WebStorm",
        "Sublime Text",
        "Vim",
        "Emacs",
        "Xcode",
        "Android Studio",

        # -------------------------
        # API / Dev Tools & GraphQL (base names)
        # -------------------------
        "Postman",
        "Insomnia",
        "Swagger",
        "OpenAPI",
        "GraphQL",
        "Apollo",
        "gRPC",

        # -------------------------
        # Monitoring & APM (base names)
        # -------------------------
        "AppDynamics",
        "Raygun",
        "Datadog APM",
        "New Relic APM",
        "Sentry",

        # -------------------------
        # Collaboration / Whiteboards / Communication (base names)
        # -------------------------
        "Slack",
        "Microsoft Teams",
        "Zoom",
        "Google Meet",
        "Miro",
        "Mural",
        "Whimsical",
        "Lucidchart",
        "Jamboard",
        "FigJam",
        "MS Whiteboard",
        "Loom",

        # -------------------------
        # Reporting / Visualization (base names)
        # -------------------------
        "Tableau",
        "Power BI",
        "Looker",
        "Mode",
        "Metabase",
        "Redash",
        "Apache Superset",
        "Chartio",
        "Periscope",

        # -------------------------
        # Security / Compliance / Governance (base names)
        # -------------------------
        "OneTrust",
        "Snyk",
        "SonarQube",
        "Qualys",
        "CrowdStrike",
        "Splunk",
        "Veracode",
        "Tenable",

        # -------------------------
        # CDP / Customer Data Platforms (base names)
        # -------------------------
        "Segment",
        "RudderStack",
        "mParticle",
        "Tealium",
        "BlueConic",
        "Treasure Data",

        # -------------------------
        # Legacy / Niche / Historical (kept for matching)
        # -------------------------
        "Google Optimize",
        "Chartio",
        "Periscope",
        "Keen.io",
        "Adobe Target",
        "Chartbeat",

        # -------------------------
        # Misc / Office / File Storage / Productivity (base names)
        # -------------------------
        "Dropbox",
        "Google Drive",
        "OneDrive",
        "Box",
        "Microsoft Office",
        "Excel",
        "PowerPoint",
        "Word",
        "Outlook",
        "Google Workspace",
        "Notion",
        "Confluence"
    ]
}

# Configuración de archivos
FILE_CONFIG = {
    "input_dir": "csv",
    "output_dir": "csv/archive",
    "default_input": "linkedin_jobs_make.csv",
    "output_prefix": "DataPM_result",
    "encoding": "utf-8",
    "delimiter": ",",
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "batch_size": 1,  # Procesar uno por uno para evitar rate limiting
    "delay_between_requests": 1,  # Segundos entre requests
    "max_retries": 3,  # Máximo de reintentos por request
    "timeout": 30,  # Timeout por request
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "datapm.log",
}

# Configuración de países y estados
LOCATION_CONFIG = {
    "countries": [
        "United States", "Spain", "Mexico", "United Kingdom", "Germany", 
        "France", "Panamá", "Venezuela", "European Union", "Unknown"
    ],
    "us_states": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    },
    "ca_provinces": {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
        "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
        "SK": "Saskatchewan", "YT": "Yukon"
    }
}

def get_api_key(llm_type: str) -> str:
    """Obtiene la API key desde variables de entorno"""
    if llm_type == "gemini":
        return os.getenv('GEMINI_API_KEY', '')
    return ''

def get_ollama_url() -> str:
    """Obtiene la URL de Ollama desde variables de entorno"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')

def get_output_filename(prefix: str = None) -> str:
    """Genera un nombre de archivo de salida con timestamp"""
    from datetime import datetime
    
    if not prefix:
        prefix = FILE_CONFIG["output_prefix"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{prefix}.csv"

def get_full_output_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de salida"""
    if not filename:
        filename = get_output_filename()
    
    output_dir = FILE_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    return os.path.join(output_dir, filename)

def get_full_input_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de entrada"""
    if not filename:
        filename = FILE_CONFIG["default_input"]
    
    input_dir = FILE_CONFIG["input_dir"]
    return os.path.join(input_dir, filename)

# Configuración de prompts
PROMPT_TEMPLATES = {
    "system": """You are a strict information extraction and normalization engine. Return ONLY one single-line valid JSON object (compact, no spaces beyond necessary), with NO markdown and NO extra text.
Schema: include ALL keys below, always.
- job_title_original (string)
- job_title_raw (string)
- job_title_candidates (array of objects: {candidate:string, score:float})
- job_title_normalized (string; MUST be one of {job_titles} or "UNMAPPED")
- skills_detected (array of objects: {text:string, span:[start,end]})
- skills_normalized (array of objects: {canonical:string (from {skills} or "UNMAPPED"), suggestions:[{value,score}]})
- software_detected (array of objects: {text:string, span:[start,end]})
- software_normalized (array of objects: {canonical:string (from {software} or "UNMAPPED"), suggestions:[{value,score}]})
- experience_years (string; one of {experience_years})
- experience_years_hint (string or null)
- job_schedule_type (string; one of {schedule_types})
- seniority (string; one of {seniority_levels})
- seniority_hint (string or null)
- city (string)
- state (string)
- country (string)
- degrees (array of strings; each from {degrees})
- company_name (string)
- confidence_scores ({title:float, skills:float, software:float})
- provenance (object): for each detected item (title, each skill/software), include text_span and a short rationale (<=30 words). Rationale MUST NOT contain PII (emails/phones).
Rules:
1) Canonical lists are provided by config at runtime; do NOT invent new canonical values. If a value does not exactly match a canonical in the provided lists, set the canonical to "UNMAPPED" and include up to top 3 fuzzy suggestions from the SAME canonical list with scores in [0,1].
2) All spans are [start,end] indices over the input text in UTF-8 codepoints.
3) Output MUST be a single-line JSON object, no pretty printing, no code fences, no commentary.
4) If you cannot determine a value, use "Unknown" for strings and [] for arrays.
""",
    "user": """INPUT: {\"text\":\"{description}\"}\nTASK: Analyze INPUT.text and output ONLY a single-line JSON strictly matching the schema in the system instructions."""
}

def get_system_prompt() -> str:
    """Obtiene el prompt del sistema con valores normalizados"""
    return PROMPT_TEMPLATES["system"].format(
        job_titles=NORMALIZATION_SCHEMA["job_title_short"],
        schedule_types=NORMALIZATION_SCHEMA["job_schedule_type"],
        seniority_levels=NORMALIZATION_SCHEMA["seniority"],
        degrees=NORMALIZATION_SCHEMA["degrees"],
        skills=NORMALIZATION_SCHEMA["skills"],
        software=NORMALIZATION_SCHEMA["software"],
        experience_years=NORMALIZATION_SCHEMA["experience_years"],
    )

def get_user_prompt(description: str) -> str:
    """Obtiene el prompt del usuario"""
    return PROMPT_TEMPLATES["user"].format(description=description)
