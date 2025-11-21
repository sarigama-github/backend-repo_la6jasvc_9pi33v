"""
Database Schemas for Portfolio

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase of the class name.
- Project -> "project"
- TeamMember -> "teammember"
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl

class Project(BaseModel):
    title: str = Field(..., description="Project title")
    slug: str = Field(..., description="URL-friendly identifier")
    description: str = Field(..., description="Detailed description")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    images: List[HttpUrl] = Field(default_factory=list, description="Image URLs or screenshots")
    demo_url: Optional[HttpUrl] = Field(None, description="Live demo link")
    repo_url: Optional[HttpUrl] = Field(None, description="GitHub repository link")
    team_members: List[str] = Field(default_factory=list, description="Slugs of team members who worked on it")
    timeline: Optional[str] = Field(None, description="Timeline or date range")
    category: Optional[str] = Field(None, description="Category or type of project")

class TeamMember(BaseModel):
    name: str = Field(..., description="Full name")
    slug: str = Field(..., description="URL-friendly identifier")
    role: str = Field(..., description="Role or position")
    bio: str = Field(..., description="Short biography")
    skills: List[str] = Field(default_factory=list, description="Skills list")
    projects: List[str] = Field(default_factory=list, description="Slugs of projects worked on")
    socials: Dict[str, Optional[HttpUrl]] = Field(default_factory=dict, description="Social links: linkedin, github, twitter, website")
    email: Optional[str] = Field(None, description="Contact email")
    photo: Optional[HttpUrl] = Field(None, description="Photo URL")
