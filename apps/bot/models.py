import datetime

class Event:
    def __init__(self, title: str, start_time: str, end_time: str, location: str, url: str):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.url = url

    def __str__(self):
        return f'<b>{datetime.datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d.%m")}</b> - {self.location} @ {self.title} - <a href="{self.url}">{self.url}</a>'        

class Cache:
    def __init__(self, last_update: datetime, events: list[Event]):
        self.last_update = last_update
        self.events = events

    def update(self, events: list[Event]):
        self.last_update = datetime.datetime.now()
        self.events = events