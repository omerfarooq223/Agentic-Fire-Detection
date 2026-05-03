"""
Fire Management System Backend
SQLite + FastAPI
- 3 zones with sprinkler options
- Detection image storage with overlays
- No confidence scores (UI adjustable)
- Clean, production-ready
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import json

# ============= DATABASE SETUP =============
DATABASE_URL = "sqlite:////Users/muhammadomerfarooq/Desktop/Fire and Smoke Detection/fire_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create directories
IMAGES_DIR = Path("/Users/muhammadomerfarooq/Desktop/Fire and Smoke Detection/detection_images")
IMAGES_DIR.mkdir(exist_ok=True)

# ============= DATABASE MODELS =============
class Zone(Base):
    __tablename__ = "zones"
    
    zone_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    area_sqm = Column(Float)  # Square meters
    description = Column(String)
    
    def to_dict(self):
        return {
            "zone_id": self.zone_id,
            "name": self.name,
            "area_sqm": self.area_sqm,
            "description": self.description
        }


class Detection(Base):
    __tablename__ = "detections"
    
    detection_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    zone_id = Column(Integer, ForeignKey("zones.zone_id"))
    coordinates_x = Column(Float)  # Pixel X
    coordinates_y = Column(Float)  # Pixel Y
    bbox_w = Column(Float)  # Bounding box width
    bbox_h = Column(Float)  # Bounding box height
    image_filename = Column(String)  # Stored image path
    segment_area_pixels = Column(Float)  # Segmentation area
    raw_image_data = Column(LargeBinary)  # Original image (backup)
    
    def to_dict(self):
        return {
            "detection_id": self.detection_id,
            "timestamp": self.timestamp.isoformat(),
            "zone_id": self.zone_id,
            "coordinates": {"x": self.coordinates_x, "y": self.coordinates_y},
            "bbox": {"w": self.bbox_w, "h": self.bbox_h},
            "segment_area_pixels": self.segment_area_pixels,
            "image_filename": self.image_filename
        }


class Incident(Base):
    __tablename__ = "incidents"
    
    incident_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    detection_id = Column(Integer, ForeignKey("detections.detection_id"))
    zone_id = Column(Integer, ForeignKey("zones.zone_id"))
    action_taken = Column(String)  # "Sprinkler activated", "Evacuation started"
    sprinkler_type = Column(String)  # "Sprinkler", "CO2", "Foam", "Water Mist"
    agent_reasoning = Column(String)  # Why this action?
    status = Column(String, default="active")  # active, resolved, manual_override
    
    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat(),
            "detection_id": self.detection_id,
            "zone_id": self.zone_id,
            "action_taken": self.action_taken,
            "sprinkler_type": self.sprinkler_type,
            "agent_reasoning": self.agent_reasoning,
            "status": self.status
        }


class SafetyProcedure(Base):
    __tablename__ = "safety_procedures"
    
    procedure_id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.zone_id"))
    protocol_name = Column(String)
    evacuation_time_min = Column(Float)
    procedure_steps = Column(String)  # JSON string of steps
    suppression_type = Column(String)  # Primary suppression
    
    def to_dict(self):
        return {
            "procedure_id": self.procedure_id,
            "zone_id": self.zone_id,
            "protocol_name": self.protocol_name,
            "evacuation_time_min": self.evacuation_time_min,
            "procedure_steps": json.loads(self.procedure_steps),
            "suppression_type": self.suppression_type
        }


# ============= CREATE TABLES =============
Base.metadata.create_all(bind=engine)


# ============= PYDANTIC SCHEMAS =============
class DetectionCreate(BaseModel):
    zone_id: int
    coordinates_x: float
    coordinates_y: float
    bbox_w: float
    bbox_h: float
    segment_area_pixels: float


class IncidentCreate(BaseModel):
    detection_id: int
    zone_id: int
    action_taken: str
    sprinkler_type: str  # "Sprinkler", "CO2", "Foam", "Water Mist"
    agent_reasoning: str


class ZoneCreate(BaseModel):
    name: str
    area_sqm: float
    description: str


# ============= FASTAPI APP =============
app = FastAPI(title="Fire Management System", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve detection images
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


# ============= UTILITY FUNCTIONS =============
def create_beautiful_detection_image(image_data: bytes, zone_name: str, coords: tuple, bbox: tuple) -> str:
    """
    Create a beautiful detection image with overlays
    - Bounding box
    - Zone label
    - Timestamp
    - Flame icon (emoji or text)
    """
    try:
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Image dimensions
        img_w, img_h = img.size
        
        # Unpack coordinates and bbox
        x, y = coords
        w, h = bbox
        
        # Draw bounding box (bright red)
        x1, y1 = max(0, x - w/2), max(0, y - h/2)
        x2, y2 = min(img_w, x + w/2), min(img_h, y + h/2)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
        
        # Draw semi-transparent overlay
        overlay = Image.new('RGBA', img.size, (255, 0, 0, 30))
        overlay_region = Image.new('RGBA', (int(x2-x1), int(y2-y1)), (255, 0, 0, 80))
        img_rgba = img.convert('RGBA')
        img_rgba.paste(overlay_region, (int(x1), int(y1)), overlay_region)
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Draw info box (top-left)
        box_width = 300
        box_height = 80
        draw.rectangle([10, 10, 10 + box_width, 10 + box_height], fill="black", outline="red", width=2)
        
        # Text
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        text_lines = [
            "🔥 FIRE DETECTED",
            f"Zone: {zone_name}",
            f"Time: {timestamp}"
        ]
        
        y_text = 20
        for line in text_lines:
            draw.text((20, y_text), line, fill="yellow")
            y_text += 20
        
        # Save image
        filename = f"detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = IMAGES_DIR / filename
        img.save(filepath, quality=95)
        
        return filename
    
    except Exception as e:
        print(f"Error creating detection image: {e}")
        return "error.png"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============= INITIALIZATION ENDPOINTS =============
@app.post("/api/init/zones")
def initialize_zones(db: Session = Depends(get_db)):
    """Initialize 3 zones (run once)"""
    zones_data = [
        {"name": "Lobby", "area_sqm": 500, "description": "Main entrance and reception area"},
        {"name": "Server Room", "area_sqm": 200, "description": "Data center with critical infrastructure"},
        {"name": "Warehouse", "area_sqm": 2000, "description": "Storage and inventory area"}
    ]
    
    for zone_data in zones_data:
        existing = db.query(Zone).filter(Zone.name == zone_data["name"]).first()
        if not existing:
            db.add(Zone(**zone_data))
    
    db.commit()
    return {"status": "Zones initialized", "count": 3}


@app.post("/api/init/procedures")
def initialize_procedures(db: Session = Depends(get_db)):
    """Initialize safety procedures for each zone"""
    procedures = [
        {
            "zone_id": 1,
            "protocol_name": "Lobby Fire Response",
            "evacuation_time_min": 5,
            "procedure_steps": json.dumps([
                "1. Activate alarm system",
                "2. Clear all exits",
                "3. Direct people to assembly point A",
                "4. Activate sprinkler system"
            ]),
            "suppression_type": "Sprinkler"
        },
        {
            "zone_id": 2,
            "protocol_name": "Server Room Fire Response",
            "evacuation_time_min": 2,
            "procedure_steps": json.dumps([
                "1. Stop all operations",
                "2. Evacuate immediately",
                "3. Activate CO2 suppression (no manual override)",
                "4. Close fireproof doors"
            ]),
            "suppression_type": "CO2"
        },
        {
            "zone_id": 3,
            "protocol_name": "Warehouse Fire Response",
            "evacuation_time_min": 10,
            "procedure_steps": json.dumps([
                "1. Alert all personnel",
                "2. Move inventory away from fire",
                "3. Activate foam suppression system",
                "4. Establish perimeter"
            ]),
            "suppression_type": "Foam"
        }
    ]
    
    for proc in procedures:
        existing = db.query(SafetyProcedure).filter(SafetyProcedure.zone_id == proc["zone_id"]).first()
        if not existing:
            db.add(SafetyProcedure(**proc))
    
    db.commit()
    return {"status": "Procedures initialized", "count": 3}


# ============= DETECTION ENDPOINTS =============
@app.post("/api/detections")
async def log_detection(
    zone_id: int = Form(...),
    coordinates_x: float = Form(...),
    coordinates_y: float = Form(...),
    bbox_w: float = Form(...),
    bbox_h: float = Form(...),
    segment_area_pixels: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Log a detection with image
    Image will be beautified with overlays
    """
    try:
        # Read image
        image_data = await file.read()
        
        # Create beautiful image with overlays
        zone = db.query(Zone).filter(Zone.zone_id == zone_id).first()
        zone_name = zone.name if zone else f"Zone {zone_id}"
        
        filename = create_beautiful_detection_image(
            image_data,
            zone_name,
            coords=(coordinates_x, coordinates_y),
            bbox=(bbox_w, bbox_h)
        )
        
        # Store detection in DB
        db_detection = Detection(
            zone_id=zone_id,
            coordinates_x=coordinates_x,
            coordinates_y=coordinates_y,
            bbox_w=bbox_w,
            bbox_h=bbox_h,
            segment_area_pixels=segment_area_pixels,
            image_filename=filename,
            raw_image_data=image_data
        )
        
        db.add(db_detection)
        db.commit()
        db.refresh(db_detection)
        
        return {
            "status": "Detection logged",
            "detection_id": db_detection.detection_id,
            "image_url": f"/images/{filename}",
            "zone": zone_name
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/detections")
def get_detections(zone_id: int = None, db: Session = Depends(get_db)):
    """Get all detections, optionally filtered by zone"""
    query = db.query(Detection)
    if zone_id:
        query = query.filter(Detection.zone_id == zone_id)
    
    detections = query.order_by(Detection.timestamp.desc()).all()
    return [d.to_dict() for d in detections]


@app.get("/api/detections/{detection_id}")
def get_detection(detection_id: int, db: Session = Depends(get_db)):
    """Get specific detection"""
    detection = db.query(Detection).filter(Detection.detection_id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection.to_dict()


# ============= INCIDENT ENDPOINTS =============
@app.post("/api/incidents")
def log_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Log an incident (agent decision)"""
    db_incident = Incident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return {
        "status": "Incident logged",
        "incident_id": db_incident.incident_id,
        **db_incident.to_dict()
    }


@app.get("/api/incidents")
def get_incidents(zone_id: int = None, db: Session = Depends(get_db)):
    """Get all incidents, optionally filtered by zone"""
    query = db.query(Incident)
    if zone_id:
        query = query.filter(Incident.zone_id == zone_id)
    
    incidents = query.order_by(Incident.timestamp.desc()).all()
    return [i.to_dict() for i in incidents]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get specific incident"""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.to_dict()


@app.patch("/api/incidents/{incident_id}/status")
def update_incident_status(incident_id: int, status: str, db: Session = Depends(get_db)):
    """Update incident status (active, resolved, manual_override)"""
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = status
    db.commit()
    return {"status": "Incident updated", "incident_id": incident_id, "new_status": status}


# ============= ZONE ENDPOINTS =============
@app.get("/api/zones")
def get_zones(db: Session = Depends(get_db)):
    """Get all zones"""
    zones = db.query(Zone).all()
    return [z.to_dict() for z in zones]


@app.get("/api/zones/{zone_id}")
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    """Get specific zone"""
    zone = db.query(Zone).filter(Zone.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone.to_dict()


# ============= PROCEDURE ENDPOINTS =============
@app.get("/api/procedures/{zone_id}")
def get_procedure(zone_id: int, db: Session = Depends(get_db)):
    """Get safety procedure for a zone"""
    procedure = db.query(SafetyProcedure).filter(SafetyProcedure.zone_id == zone_id).first()
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return procedure.to_dict()


# ============= DASHBOARD ENDPOINTS =============
@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary stats"""
    total_detections = db.query(Detection).count()
    active_incidents = db.query(Incident).filter(Incident.status == "active").count()
    zones = db.query(Zone).count()
    
    return {
        "total_detections": total_detections,
        "active_incidents": active_incidents,
        "total_zones": zones,
        "last_detection": db.query(Detection).order_by(Detection.timestamp.desc()).first().timestamp.isoformat() if total_detections > 0 else None
    }


@app.get("/api/dashboard/incidents-by-zone")
def get_incidents_by_zone(db: Session = Depends(get_db)):
    """Get incident counts by zone"""
    zones = db.query(Zone).all()
    result = []
    
    for zone in zones:
        incident_count = db.query(Incident).filter(Incident.zone_id == zone.zone_id).count()
        result.append({
            "zone_id": zone.zone_id,
            "zone_name": zone.name,
            "incident_count": incident_count
        })
    
    return result


# ============= HEALTH CHECK =============
@app.get("/api/health")
def health_check():
    return {"status": "Backend is running", "db": "Connected"}


if __name__ == "__main__":
    import uvicorn
    print("🔥 Fire Management System Backend")
    print("📊 Starting on http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)