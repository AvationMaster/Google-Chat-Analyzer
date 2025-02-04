import os
import json
import re
from collections import defaultdict, Counter
import emoji

#You must do a google takeout of your Google Chat to run this script.
def get_takeout_path():
    user_input = input("Enter the path to your Google Takeout directory: ").strip()
    if not user_input.endswith("Groups"):
        if not user_input.endswith("Google Chat"):
            if not user_input.endswith("Takeout"):
                user_input = os.path.join(user_input, "Takeout")
            user_input = os.path.join(user_input, "Google Chat")
        user_input = os.path.join(user_input, "Groups")
    if not os.path.exists(user_input):
        raise FileNotFoundError(f"Path '{user_input}' does not exist.")
    return user_input

TAKEOUT_PATH = get_takeout_path()

def extract_emojis(text):
    """Extracts all emojis from a given text."""
    return [char for char in text if char in emoji.EMOJI_DATA]

def get_all_chats():
    """Scans all DM and Group Chat/Space folders and categorizes them."""
    dms = {}  
    group_chats = {}  

    for folder in os.listdir(TAKEOUT_PATH):
        folder_path = os.path.join(TAKEOUT_PATH, folder)
        if not os.path.isdir(folder_path):
            continue

        group_info_path = os.path.join(folder_path, "group_info.json")
        messages_path = os.path.join(folder_path, "messages.json")

        if not os.path.exists(group_info_path) or not os.path.exists(messages_path):
            continue

        with open(group_info_path, "r", encoding="utf-8") as f:
            group_info = json.load(f)

        participants = [f"{member['name']} - {member.get('email', 'Unknown Email')}" for member in group_info["members"]]
        chat_name = group_info.get("name", None)
        if not chat_name or chat_name == "Group Chat":
            chat_name = ", ".join(participants)

        if len(participants) == 2:
            dms[folder] = participants
        else:
            group_chats[folder] = chat_name

    return dms, group_chats

def analyze_individual_dm(folder, contact_name):
    """Analyzes a specific DM for message count, common words, and emojis."""
    messages_path = os.path.join(TAKEOUT_PATH, folder, "messages.json")

    with open(messages_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    message_count = len(messages.get("messages", []))
    word_counts = Counter()
    emoji_counts = Counter()

    for message in messages.get("messages", []):
        text = message.get("text", "").lower()

        # Extract words (alphanumeric only, ignores punctuation)
        words = re.findall(r"\b[a-zA-Z0-9']+\b", text)
        word_counts.update(words)

        # Extract emojis
        emojis = extract_emojis(text)
        emoji_counts.update(emojis)

    # Get the most used word
    most_common_word = word_counts.most_common(1)
    most_common_word = most_common_word[0] if most_common_word else ("N/A", 0)

    # Get the top 3 emojis
    top_emojis = emoji_counts.most_common(3)
    emoji_display = [f"{e} ({c} times)" for e, c in top_emojis] + [""] * (3 - len(top_emojis))

    print(f"\n📊 DM Recap with {contact_name} 📊\n")
    print(f"Total Messages Exchanged: {message_count}")
    print(f"Most Common Word: {most_common_word[0]} ({most_common_word[1]} times)")
    print("Top 3 Emojis Used:", ", ".join(emoji_display))

def analyze_dms(dms, user_name, user_email):
    """Counts total messages in all DMs and allows detailed analysis of a selected contact."""
    message_counts = defaultdict(int)
    user_identifier = f"{user_name} - {user_email}"

    dm_folders = {}

    for folder, participants in dms.items():
        messages_path = os.path.join(TAKEOUT_PATH, folder, "messages.json")

        with open(messages_path, "r", encoding="utf-8") as f:
            messages = json.load(f)

        other_person = next(participant for participant in participants if participant != user_identifier)
        message_counts[other_person] += len(messages.get("messages", []))
        dm_folders[other_person] = folder

    sorted_counts = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
    print("\nGoogle Chat Recap - Most Messaged Contacts\n")

    for rank, (identifier, count) in enumerate(sorted_counts, 1):
        name, email = identifier.split(" - ")
        print(f"{rank}. {name} ({email}): {count} messages")

    # Allow user to select a specific DM for deeper analysis
    choice = input("\nEnter a number to view detailed stats or press Enter to exit: ").strip()

    if choice.isdigit():
        choice = int(choice) - 1
        if 0 <= choice < len(sorted_counts):
            selected_contact, _ = sorted_counts[choice]
            analyze_individual_dm(dm_folders[selected_contact], selected_contact)
        else:
            print("Invalid selection. Exiting.")

def analyze_group_chat(group_chats):
    """Lets user pick a group chat and finds the most active members, common words, and emojis."""
    print("\nAvailable Group Chats & Spaces:\n")
    chat_list = list(group_chats.items())

    for i, (folder, chat_name) in enumerate(chat_list, 1):
        print(f"{i}. {chat_name}")

    try:
        choice = int(input("\nEnter the number of the group chat to analyze: ")) - 1
        if choice < 0 or choice >= len(chat_list):
            print("Invalid selection. Exiting.")
            return
    except ValueError:
        print("Invalid input. Exiting.")
        return

    selected_folder, chat_name = chat_list[choice]
    messages_path = os.path.join(TAKEOUT_PATH, selected_folder, "messages.json")

    message_counts = defaultdict(int)
    word_counts = Counter()
    emoji_counts = Counter()

    with open(messages_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    for message in messages.get("messages", []):
        sender_name = message["creator"]["name"]
        sender_email = message["creator"].get("email", "Unknown Email")
        sender_identifier = f"{sender_name} - {sender_email}"
        message_counts[sender_identifier] += 1

        text = message.get("text", "").lower()

        # Extract words (alphanumeric only, ignores punctuation)
        words = re.findall(r"\b[a-zA-Z0-9']+\b", text)
        word_counts.update(words)

        # Extract emojis
        emojis = extract_emojis(text)
        emoji_counts.update(emojis)

    most_common_word = word_counts.most_common(1)
    most_common_word = most_common_word[0] if most_common_word else ("N/A", 0)

    top_emojis = emoji_counts.most_common(3)
    emoji_display = [f"{e} ({c} times)" for e, c in top_emojis] + [""] * (3 - len(top_emojis))

    sorted_counts = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\n📊 Activity Recap for {chat_name} 📊\n")
    for rank, (identifier, count) in enumerate(sorted_counts, 1):
        name, email = identifier.split(" - ")
        print(f"{rank}. {name} ({email}): {count} messages")

    print(f"\nMost Common Word: {most_common_word[0]} ({most_common_word[1]} times)")
    print("Top 3 Emojis Used:", ", ".join(emoji_display))

def main():
    """Main function with input selection."""
    dms, group_chats = get_all_chats()

    print("Welcome to Google Chat Recap!\n")
    print("1. See most messaged people (DMs only)")
    print("2. See activity in a specific group chat/space")

    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        try:
            user_info_path = os.path.join(os.path.dirname(TAKEOUT_PATH), "Users")
            if len(os.listdir(user_info_path)) != 1:
                raise FileNotFoundError
            user_info_path = os.path.join(user_info_path, os.listdir(user_info_path)[0], "user_info.json")

            with open(user_info_path, "r", encoding="utf-8") as f:
                user_info = json.load(f)
                user_name = user_info["user"]["name"]
                user_email = user_info["user"]["email"]
        except FileNotFoundError:
            print("User info not found. Please enter your name and email manually.")
            user_name = input("\nWhat is your name in Google Chat? (Case sensitive) ").strip()
            user_email = input("What is your email in Google Chat? (Case sensitive) ").strip()
        analyze_dms(dms, user_name, user_email)
    elif choice == "2":
        analyze_group_chat(group_chats)
    else:
        print("Invalid selection. Exiting.")

if __name__ == "__main__":
    main()
