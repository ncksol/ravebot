import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = 'event'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String)
    title = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String)
    url = Column(String)

    def __str__(self):
        return f'<b>{datetime.datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d.%m")}</b> - {self.location} @ {self.title} - <a href="{self.url}">{self.url}</a>'        