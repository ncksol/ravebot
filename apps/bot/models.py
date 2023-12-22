import datetime

class Event:
    def __init__(self, title: str, start_time: str, end_time: str, location: str, url: str, description: str, event_id: str = None):
        self.event_id = event_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.url = url
        self.description = description

    def __str__(self):
        return f'<b>{datetime.datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%d.%m")}</b> - {self.title} @ {self.location} - <a href="{self.url}">{self.url}</a>'        

class Cache:
    def __init__(self, last_update: datetime, events: list[Event]):
        self.last_update = last_update
        self.events = events

    def update(self, events: list[Event]):
        self.last_update = datetime.datetime.now()
        self.events = events