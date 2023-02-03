from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from models import Event
from db_engine import engine

def cleanup_events():
    with Session(engine) as db:
        db.execute(delete(Event))
        db.commit()

def insert_event(event: Event) -> Event:
    with Session(engine) as db:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

def upsert_event(new_event: Event) -> Event:
    with Session(engine) as db:
        query = select(Event).filter_by(event_id=new_event.event_id)
        result = db.execute(query).first()
        if result != None:
            event = result.Event
            update_cmd = update(Event).where(Event.event_id == event.event_id).values(title=new_event.title, start_time=new_event.start_time, end_time=new_event.end_time, location=new_event.location, url=new_event.url)
            db.execute(update_cmd)
            db.commit()
            db.refresh(event)
            return event
        else:        
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event
