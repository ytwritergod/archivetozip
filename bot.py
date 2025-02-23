import os
import zipfile
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import InputMediaUploadedDocument

# MTProto credentials (Render ke environment variables se)
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")

# Initialize Telegram client
client = TelegramClient('session_name', api_id, api_hash)

# Global variables to store user data
user_data = {}

# Function to create a password-protected ZIP file
def create_zip_with_password(file_paths, zip_path, password):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))
        if password:
            zipf.setpassword(password.encode())  # Set password for the ZIP file

# Function to split large files (>2GB) into smaller parts
def split_file(file_path, max_size):
    split_files = []
    part_num = 1
    with open(file_path, 'rb') as f:
        while chunk := f.read(max_size):
            part_path = f"{file_path}.part{part_num}"
            with open(part_path, 'wb') as part:
                part.write(chunk)
            split_files.append(part_path)
            part_num += 1
    return split_files

# Function to upload files using MTProto
async def upload_file(file_path, chat_id):
    try:
        if os.path.getsize(file_path) > 2 * 1024 * 1024 * 1024:  # Check if file >2GB
            print("File size exceeds 2 GB. Splitting into parts...")
            split_files = split_file(file_path, 2 * 1024 * 1024 * 1024)  # Split into 2GB parts
            for part in split_files:
                print(f"Uploading {part}...")
                file = await client.upload_file(part)
                await client.send_file(chat_id, file)
                os.remove(part)  # Cleanup after upload
                print(f"{part} uploaded and deleted.")
        else:
            print(f"Uploading {file_path}...")
            file = await client.upload_file(file_path)
            await client.send_file(chat_id, file)
            print(f"{file_path} uploaded successfully!")
    except Exception as e:
        print(f"Error uploading file: {e}")

# Event handler for private messages
@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_private_message(event):
    user_id = event.sender_id
    chat_id = event.chat_id

    if user_id not in user_data:
        user_data[user_id] = {"files": [], "step": "receiving_files"}

    # Step 1: Receive files
    if user_data[user_id]["step"] == "receiving_files":
        if event.file:
            file_path = await event.download_media(file=f"temp_files/{event.file.name}")
            user_data[user_id]["files"].append(file_path)
            await event.reply(f"File saved! Send more files or type /done to finish.")
        elif event.text == "/done":
            if not user_data[user_id]["files"]:
                await event.reply("No files received. Please send files first.")
            else:
                await event.reply("Please enter a password for the ZIP file:")
                user_data[user_id]["step"] = "asking_password"
        else:
            await event.reply("Please send files or type /done to finish.")

    # Step 2: Ask for password
    elif user_data[user_id]["step"] == "asking_password":
        user_data[user_id]["password"] = event.text
        await event.reply("Please enter a custom name for the ZIP file:")
        user_data[user_id]["step"] = "asking_zip_name"

    # Step 3: Ask for custom ZIP name
    elif user_data[user_id]["step"] == "asking_zip_name":
        zip_name = event.text
        if not zip_name.endswith(".zip"):
            zip_name += ".zip"
        zip_path = f"temp_files/{zip_name}"

        # Create password-protected ZIP
        create_zip_with_password(user_data[user_id]["files"], zip_path, user_data[user_id]["password"])

        # Upload the ZIP file
        await upload_file(zip_path, chat_id)

        # Cleanup
        for file_path in user_data[user_id]["files"]:
            os.remove(file_path)
        os.remove(zip_path)

        # Reset user data
        user_data[user_id] = {"files": [], "step": "receiving_files"}
        await event.reply("ZIP file uploaded successfully! You can send more files.")

# Main function
async def main():
    await client.start(phone_number)
    print("Client created. Listening for private messages...")

    # Keep the client running
    await client.run_until_disconnected()

# Run the script
if __name__ == "__main__":
    # Create temp_files directory if it doesn't exist
    os.makedirs("temp_files", exist_ok=True)

    with client:
        client.loop.run_until_complete(main())
