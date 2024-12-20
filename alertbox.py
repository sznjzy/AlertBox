import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext
import pandas as pd
from datetime import datetime
import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from fuzzywuzzy import process

# Function to generate spam and ham data
def generate_spam_ham_data(num_samples):
    spam_templates = [
        "Congratulations! You've won a ${amount} gift card. Click {link} to claim your prize.",
        "Earn ${amount} per month from home! No experience required. Visit {link} now.",
        "You've been selected for a free {item}. Claim it fast at {link}.",
        "Limited time offer: Buy one {item}, get one free! Check it out at {link}.",
        "You're a lucky winner of our {type} lottery! Claim your prize today.",
        "Don't miss out on exclusive deals! Visit {link} for more details.",
        "Your account shows suspicious activity. Verify now at {link}.",
        "Please provide your OTP for the following",
        "New message from {sender}. Open it immediately at {link}.",
        "Act quickly! Your chance to win {item} ends soon.",
        "Work from home and earn ${amount} quickly! Details at {link}."
    ]

    ham_templates = [
        "Hi {name}, I hope this email finds you well. Let's catch up soon.",
        "Dear {name}, can we schedule a call to discuss the {topic} project?",
        "Hi {name}, just wanted to confirm our meeting on {date}. Let me know if the time still works.",
        "Come home by 9 pm",
        "New comment on your photo! Check it out now.",
        "You have a new message from Bob. Check it out now!",
        "Your account has been credited with $500.",
        "Please come to class on time from now on",
        "You have a new friend request from Alice.",
        "Your order has shipped! Track it here.",
        "New episode of your favorite show is now available.",
        "Your ride is on the way! Estimated arrival: 5 minutes.",
        "Please find the attached document related to our {topic} discussion.",
        "Thank you for your response, {name}. I appreciate your support.",
        "Hi {name}, looking forward to discussing project updates during our next meeting.",
        "Good morning {name}, hope you are having a productive day.",
        "Hello {name}, can you let me know your availability for a quick chat?",
        "Dear {name}, please share your thoughts on the attached proposal.",
        "Hi {name}, here's the update regarding the {topic} you requested."
    ]

    spam_messages = [
        template.format(
            amount=random.randint(100, 1000),
            item=random.choice(["iPhone", "TV", "Laptop", "Headphones"]),
            type=random.choice(["mega", "monthly", "holiday"]),
            sender=random.choice(["unknown sender", "support team"]),
            link="www.example.com"
        ) for template in spam_templates for _ in range(10)
    ]

    ham_messages = [
        template.format(
            name=random.choice(["Alice", "Bob", "Charlie", "David"]),
            topic=random.choice(["budget", "marketing", "sales"]),
            date=random.choice(["Monday", "Wednesday", "Friday"])
        ) for template in ham_templates for _ in range(10)
    ]

    data = {
        'message': [],
        'label': []
    }

    all_messages = [(msg, 'spam') for msg in spam_messages] + [(msg, 'ham') for msg in ham_messages]
    random.shuffle(all_messages)

    for message, label in all_messages[:num_samples]:
        data['message'].append(message)
        data['label'].append(label)

    return pd.DataFrame(data)

# Generate dataset with 1000 samples
df = generate_spam_ham_data(1000)
df = df.sample(frac=1).reset_index(drop=True)

# Initialize TF-IDF Vectorizer and Naive Bayes model
vectorizer = TfidfVectorizer()
X_tfidf = vectorizer.fit_transform(df['message'])
model = MultinomialNB()
model.fit(X_tfidf, df['label'])

# Global list to store notifications
notifications = []

def classify_notification(notification_text):
    """
    Classifies a notification as 'spam' or 'ham'.
    """
    notification_tfidf = vectorizer.transform([notification_text])
    prediction = model.predict(notification_tfidf)
    return prediction[0]

def add_notification():
    """
    Adds a new notification with time and optional media attachment.
    """
    content = input_box.get("1.0", END).strip()
    app_name = app_name_entry.get().strip()
    media_attached = media_var.get()

    if not content or not app_name:
        ttk.Messagebox.show_error("Please enter app name and notification content.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    classification = classify_notification(content)

    notification = {
        "app_name": app_name,
        "content": content,
        "time": timestamp,
        "media": "Media Attached" if media_attached else "No Media",
        "classification": classification
    }
    notifications.append(notification)

    refresh_notifications()
    input_box.delete("1.0", END)
    app_name_entry.delete(0, END)
    media_var.set(False)

def refresh_notifications():
    """
    Refreshes the notifications displayed in the app.
    """
    spam_box.delete("1.0", END)
    ham_box.delete("1.0", END)

    for notification in notifications:
        text = f"[{notification['time']}] {notification['app_name']}: {notification['content']} ({notification['media']})\n"
        if notification["classification"] == "spam":
            spam_box.insert(END, text)
        else:
            ham_box.insert(END, text)

def search_notifications():
    """
    Searches notifications by app name, content, or filters.
    """
    query = search_entry.get().strip()
    filter_app = app_filter_entry.get().strip()
    from_date = from_date_entry.get().strip()
    to_date = to_date_entry.get().strip()
    media_only = media_filter_var.get()

    search_box.delete("1.0", END)

    for notification in notifications:
        match_query = (
            query.lower() in notification["app_name"].lower()
            or query.lower() in notification["content"].lower()
            or process.extractOne(query, [notification["content"]])[1] > 70  # Fuzzy matching
        )
        match_app = filter_app.lower() in notification["app_name"].lower() if filter_app else True
        match_date = True
        if from_date or to_date:
            try:
                notification_time = datetime.strptime(notification["time"], "%Y-%m-%d %H:%M:%S")
                if from_date:
                    match_date &= notification_time >= datetime.strptime(from_date, "%Y-%m-%d")
                if to_date:
                    match_date &= notification_time <= datetime.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                ttk.Messagebox.show_error("Invalid date format. Use YYYY-MM-DD.")
                return
        match_media = notification["media"] == "Media Attached" if media_only else True

        if match_query and match_app and match_date and match_media:
            text = f"[{notification['time']}] {notification['app_name']}: {notification['content']} ({notification['media']})\n"
            search_box.insert(END, text)

def export_notifications():
    """
    Exports notifications to a JSON file.
    """
    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if filepath:
        with open(filepath, "w") as file:
            json.dump(notifications, file)
        ttk.Messagebox.show_info("Notifications exported successfully.")

def import_notifications():
    """
    Imports notifications from a JSON file.
    """
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filepath:
        with open(filepath, "r") as file:
            imported_data = json.load(file)
        notifications.extend(imported_data)
        refresh_notifications()
        ttk.Messagebox.show_info("Notifications imported successfully.")

# Main Tkinter window with ttkbootstrap theme
app = ttk.Window(themename="morph")
app.title("Material You - Notification Manager")
app.geometry("1200x800")

# Input Frame
input_frame = ttk.Frame(app, padding=10)
input_frame.pack(fill=X, pady=10)

ttk.Label(input_frame, text="App Name:", font=("Roboto", 12)).pack(side=LEFT, padx=10)
app_name_entry = ttk.Entry(input_frame, width=20)
app_name_entry.pack(side=LEFT, padx=10)

ttk.Label(input_frame, text="Notification Content:", font=("Roboto", 12)).pack(side=LEFT, padx=10)
input_box = scrolledtext.ScrolledText(input_frame, width=50, height=5)
input_box.pack(side=LEFT, padx=10)

media_var = ttk.BooleanVar()
media_checkbox = ttk.Checkbutton(input_frame, text="Attach Media", variable=media_var, bootstyle="secondary")
media_checkbox.pack(side=LEFT, padx=10)

add_button = ttk.Button(input_frame, text="Add Notification", command=add_notification, bootstyle="success")
add_button.pack(side=LEFT, padx=10)

# Search Frame
search_frame = ttk.Frame(app, padding=10)
search_frame.pack(fill=X, pady=10)

ttk.Label(search_frame, text="Search:", font=("Roboto", 12)).pack(side=LEFT, padx=10)
search_entry = ttk.Entry(search_frame, width=20)
search_entry.pack(side=LEFT, padx=10)

ttk.Label(search_frame, text="Filter App Name:", font=("Roboto", 12)).pack(side=LEFT, padx=10)
app_filter_entry = ttk.Entry(search_frame, width=20)
app_filter_entry.pack(side=LEFT, padx=10)

ttk.Label(search_frame, text="From Date (YYYY-MM-DD):", font=("Roboto", 12)).pack(side=LEFT, padx=10)
from_date_entry = ttk.Entry(search_frame, width=15)
from_date_entry.pack(side=LEFT, padx=10)

ttk.Label(search_frame, text="To Date (YYYY-MM-DD):", font=("Roboto", 12)).pack(side=LEFT, padx=10)
to_date_entry = ttk.Entry(search_frame, width=15)
to_date_entry.pack(side=LEFT, padx=10)

media_filter_var = ttk.BooleanVar()
media_filter_checkbox = ttk.Checkbutton(search_frame, text="Media Only", variable=media_filter_var, bootstyle="info")
media_filter_checkbox.pack(side=LEFT, padx=10)

search_button = ttk.Button(search_frame, text="Search", command=search_notifications, bootstyle="primary")
search_button.pack(side=LEFT, padx=10)

# Export/Import Frame
export_import_frame = ttk.Frame(app, padding=10)
export_import_frame.pack(fill=X, pady=10)

export_button = ttk.Button(export_import_frame, text="Export Notifications", command=export_notifications, bootstyle="warning")
export_button.pack(side=LEFT, padx=20)

import_button = ttk.Button(export_import_frame, text="Import Notifications", command=import_notifications, bootstyle="warning")
import_button.pack(side=LEFT, padx=20)

# Output Frames
output_frame = ttk.Frame(app, padding=10)
output_frame.pack(fill=BOTH, expand=True)

ham_frame = ttk.LabelFrame(output_frame, text="Ham Notifications", padding=10, bootstyle="info")
ham_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

ham_box = scrolledtext.ScrolledText(ham_frame, width=50, height=20)
ham_box.pack(pady=5)

spam_frame = ttk.LabelFrame(output_frame, text="Spam Notifications", padding=10, bootstyle="danger")
spam_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

spam_box = scrolledtext.ScrolledText(spam_frame, width=50, height=20)
spam_box.pack(pady=5)

search_results_frame = ttk.LabelFrame(output_frame, text="Search Results", padding=10, bootstyle="secondary")
search_results_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

search_box = scrolledtext.ScrolledText(search_results_frame, width=50, height=20)
search_box.pack(pady=5)

# Run the application
app.mainloop()
