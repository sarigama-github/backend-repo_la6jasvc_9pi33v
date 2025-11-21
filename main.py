import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Project as ProjectSchema, TeamMember as TeamMemberSchema

app = FastAPI(title="Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectOut(BaseModel):
    title: str
    slug: str
    description: str
    technologies: List[str] = []
    images: List[str] = []
    demo_url: Optional[str] = None
    repo_url: Optional[str] = None
    team_members: List[str] = []
    timeline: Optional[str] = None
    category: Optional[str] = None


class TeamMemberOut(BaseModel):
    name: str
    slug: str
    role: str
    bio: str
    skills: List[str] = []
    projects: List[str] = []
    socials: dict = {}
    email: Optional[str] = None
    photo: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Portfolio API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ---------- Helper functions ----------

def _collection(name: str):
    return db[name] if db is not None else None


def _ensure_indexes():
    if db is None:
        return
    _collection("project").create_index("slug", unique=True)
    _collection("teammember").create_index("slug", unique=True)


# ---------- Seed Data ----------

@app.post("/api/seed")
def seed_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    _ensure_indexes()

    # Only seed if empty
    project_count = _collection("project").count_documents({})
    member_count = _collection("teammember").count_documents({})

    if project_count > 0 or member_count > 0:
        return {"status": "ok", "message": "Data already present"}

    team = [
        TeamMemberSchema(
            name="Alex Johnson",
            slug="alex-johnson",
            role="Full-Stack Developer",
            bio="Engineer focused on building delightful, scalable web apps.",
            skills=["React", "FastAPI", "MongoDB", "Tailwind"],
            socials={
                "linkedin": "https://www.linkedin.com/in/example",
                "github": "https://github.com/example",
                "website": "https://example.com"
            },
            email="alex@example.com",
            photo="https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=400&q=80"
        ),
        TeamMemberSchema(
            name="Jamie Lee",
            slug="jamie-lee",
            role="UI/UX Designer",
            bio="Designer blending aesthetics with usability for meaningful products.",
            skills=["Figma", "Design Systems", "Prototyping"],
            socials={
                "linkedin": "https://www.linkedin.com/in/example2",
                "github": "https://github.com/example2"
            },
            email="jamie@example.com",
            photo="https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=400&q=80"
        ),
        TeamMemberSchema(
            name="Sam Patel",
            slug="sam-patel",
            role="Backend Engineer",
            bio="API-first developer who loves clean architecture and performance.",
            skills=["Python", "FastAPI", "Databases"],
            socials={"github": "https://github.com/example3"},
            email="sam@example.com",
            photo="https://images.unsplash.com/photo-1541534401786-2077eed87a56?w=400&q=80"
        )
    ]

    for m in team:
        create_document("teammember", m)

    projects = [
        ProjectSchema(
            title="Nova Portfolio",
            slug="nova-portfolio",
            description="A modern, animated portfolio template with 3D hero and dynamic content.",
            technologies=["React", "Tailwind", "Framer Motion"],
            images=[
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&q=80"
            ],
            demo_url="https://example.com/demo",
            repo_url="https://github.com/example/nova",
            team_members=["alex-johnson", "jamie-lee"],
            timeline="2024",
            category="Web"
        ),
        ProjectSchema(
            title="API Atlas",
            slug="api-atlas",
            description="A developer dashboard for exploring public APIs with analytics.",
            technologies=["FastAPI", "MongoDB", "Vite"],
            images=[
                "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&q=80"
            ],
            demo_url="https://example.com/atlas",
            repo_url="https://github.com/example/atlas",
            team_members=["alex-johnson", "sam-patel"],
            timeline="2023",
            category="Tool"
        )
    ]

    for p in projects:
        create_document("project", p)

    # Backfill reverse references (member.projects)
    for m in team:
        slugs = []
        for p in projects:
            if m.slug in p.team_members:
                slugs.append(p.slug)
        _collection("teammember").update_one({"slug": m.slug}, {"$set": {"projects": slugs}})

    return {"status": "ok", "message": "Seeded sample data"}


# ---------- API: Projects ----------

@app.get("/api/projects", response_model=List[ProjectOut])
def list_projects(q: Optional[str] = Query(None), tech: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    filter_dict = {}
    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]
    if tech:
        filter_dict["technologies"] = {"$in": [tech]}
    if category:
        filter_dict["category"] = category

    docs = get_documents("project", filter_dict)
    return [
        ProjectOut(
            title=d.get("title"),
            slug=d.get("slug"),
            description=d.get("description"),
            technologies=d.get("technologies", []),
            images=[str(x) for x in d.get("images", [])],
            demo_url=d.get("demo_url"),
            repo_url=d.get("repo_url"),
            team_members=d.get("team_members", []),
            timeline=d.get("timeline"),
            category=d.get("category"),
        ) for d in docs
    ]


@app.get("/api/projects/{slug}", response_model=ProjectOut)
def get_project(slug: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = _collection("project").find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(
        title=doc.get("title"),
        slug=doc.get("slug"),
        description=doc.get("description"),
        technologies=doc.get("technologies", []),
        images=[str(x) for x in doc.get("images", [])],
        demo_url=doc.get("demo_url"),
        repo_url=doc.get("repo_url"),
        team_members=doc.get("team_members", []),
        timeline=doc.get("timeline"),
        category=doc.get("category"),
    )


# ---------- API: Team ----------

@app.get("/api/team", response_model=List[TeamMemberOut])
def list_team(q: Optional[str] = Query(None), skill: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    filter_dict = {}
    if q:
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"bio": {"$regex": q, "$options": "i"}},
            {"role": {"$regex": q, "$options": "i"}},
        ]
    if skill:
        filter_dict["skills"] = {"$in": [skill]}

    docs = get_documents("teammember", filter_dict)
    return [
        TeamMemberOut(
            name=d.get("name"),
            slug=d.get("slug"),
            role=d.get("role"),
            bio=d.get("bio"),
            skills=d.get("skills", []),
            projects=d.get("projects", []),
            socials=d.get("socials", {}),
            email=d.get("email"),
            photo=d.get("photo"),
        ) for d in docs
    ]


@app.get("/api/team/{slug}", response_model=TeamMemberOut)
def get_team_member(slug: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = _collection("teammember").find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Team member not found")
    return TeamMemberOut(
        name=doc.get("name"),
        slug=doc.get("slug"),
        role=doc.get("role"),
        bio=doc.get("bio"),
        skills=doc.get("skills", []),
        projects=doc.get("projects", []),
        socials=doc.get("socials", {}),
        email=doc.get("email"),
        photo=doc.get("photo"),
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
