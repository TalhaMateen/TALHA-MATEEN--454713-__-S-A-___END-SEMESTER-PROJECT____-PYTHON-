import string
import time
import feedparser
from tkinter import *  # Use lowercase 't' for tkinter
from datetime import datetime
import pytz
import collections
import threading  # Import threading for multi-threading

collections.Callable = collections.abc.Callable
USE_TZ = True

global stories


# Data structure design
# Problem 1


class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        self.pubdate = pubdate

    def get_guid(self):
        return self.guid

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_link(self):
        return self.link

    def get_pubdate(self):
        return self.pubdate


# Triggers


class Trigger(object):
    def evaluate(self, story):
        raise NotImplementedError


# PHRASE TRIGGERS
# Problem 2


class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for p in string.punctuation:
            text = text.replace(p, ' ')
        words = text.split()
        phrase_words = self.phrase.split()
        for i in range(len(words) - len(phrase_words) + 1):
            if words[i:i + len(phrase_words)] == phrase_words:
                return True
        return False


# Problem 3


class TitleTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_title())


# Problem 4


class DescriptionTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_description())


# TIME TRIGGERS
# Problem 5


class TimeTrigger(Trigger):
    def __init__(self, time):
        self.time = datetime.strptime(time, "%d %b %Y %H:%M:%S")
        self.time = self.time.replace(tzinfo=pytz.timezone("EST"))


# Problem 6


class BeforeTrigger(TimeTrigger):
    def evaluate(self, story):
        pub_date = (story.get_pubdate()).replace(
            tzinfo=pytz.timezone("EST"))
        return pub_date < self.time


class AfterTrigger(TimeTrigger):
    def evaluate(self, story):
        pub_date = (story.get_pubdate()).replace(
            tzinfo=pytz.timezone("EST"))
        return pub_date > self.time


# COMPOSITE TRIGGERS
# Problem 7


class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)


# Problem 8


class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)


# Problem 9


class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)


# Filtering
# Problem 10


def filter_stories(stories, triggerlist):
    filtered_stories = []

    for story in stories:
            if isinstance(story, NewsStory):  # Check if story is a NewsStory object
                for trigger in triggerlist:
                    if trigger.evaluate(story):
                        filtered_stories.append(story)
                        break
            else:
                print("No Description")


# User-Specified Triggers
# Problem 11


def read_trigger_config(filename):
    trigger_file = open(filename, 'r')
    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//')):
            lines.append(line)

    triggers = {}
    trigger_list = []

    for line in lines:
        parts = line.split(',')
        if parts[0] == 'ADD':
            for name in parts[1:]:
                trigger_list.append(triggers[name])
        else:
            trigger_name, trigger_type = parts[0], parts[1]
            if trigger_type == 'TITLE':
                triggers[trigger_name] = TitleTrigger(parts[2])
            elif trigger_type == 'DESCRIPTION':
                triggers[trigger_name] = DescriptionTrigger(parts[2])
            elif trigger_type == 'AFTER':
                triggers[trigger_name] = AfterTrigger(parts[2])
            elif trigger_type == 'BEFORE':
                triggers[trigger_name] = BeforeTrigger(parts[2])
            elif trigger_type == 'NOT':
                triggers[trigger_name] = NotTrigger(triggers[parts[2]])
            elif trigger_type == 'AND':
                triggers[trigger_name] = AndTrigger(
                    triggers[parts[2]], triggers[parts[3]])
                trigger_list.append(triggers[trigger_name])
            elif trigger_type == 'OR':
                triggers[trigger_name] = OrTrigger(
                    triggers[parts[2]], triggers[parts[3]])
                trigger_list.append(triggers[trigger_name])

    return trigger_list  # Return the trigger list, not print


SLEEPTIME = 120  # seconds -- how often we poll


def main_thread(master):
    try:
        # Uncomment the line below after implementing read_trigger_config
        triggerlist = read_trigger_config('triggers.txt')

        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica", 14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)

        button.pack(side=BOTTOM)
        guidShown = []

        def get_cont(newstory):
            if newstory.get_guid() not in guidShown:
                cont.insert(END, newstory.get_title() + "\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.get_description())
                cont.insert(END, "\n*********************************************************************\n", "title")
                guidShown.append(newstory.get_guid())

        while True:
            print("Polling . . .", end=' ')
            google_stories = feedparser.parse("http://news.google.com/news?output=rss")
            yahoo_stories = feedparser.parse("http://news.yahoo.com/rss/topstories")

            all_entries = google_stories.copy()
            all_entries.update(yahoo_stories)

            filtered_stories = filter_stories(all_entries, triggerlist)

            list(map(get_cont, filtered_stories))
            scrollbar.config(command=cont.yview)

            print("Sleeping...")
            time.sleep(SLEEPTIME)

    except Exception as e:
        print(e)

if __name__ == '__main__':
    root = Tk()
    root.title("News Letter A*")
    t = threading.Thread(target=main_thread, args=(root,))
    t.start()
    root.mainloop()
