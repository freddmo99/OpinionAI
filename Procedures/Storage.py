from flask import send_file
from google.cloud import storage
from google.cloud import datastore
import traceback
import os
import sys
from PIL import Image, ExifTags

# Storage configuration
bucketname = 'cloudnativebucket'
storage_client = storage.Client()
datastore_client = datastore.Client()  # Assuming you're using Datastore


# Function to get a list of image files and their associated text files from the bucket
def get_image_list(bucket_name):
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    image_files = {}
    for blob in blobs:
        if blob.name.endswith((".jpeg", ".png", ".jpg")):
            # Check if a corresponding text file exists for the image
            base_name = blob.name.rsplit('.', 1)[0]  # Strip the image extension
            text_file_name = base_name + '.txt'
            
            # Check if the text file exists
            text_blob = bucket.blob(text_file_name)
            if text_blob.exists():
                text_content = text_blob.download_as_text()
                
                # Step 1: Extract the title from the description (assuming it's the first part or in quotes)
                if '"' in text_content:
                    title = text_content.split('"')[1]  # Extract title between quotes
                else:
                    title = text_content.splitlines()[0]  # Otherwise, use the first line as the title
            else:
                text_content = "No description available."
                title = "Untitled"

            # Store the image and its associated text (description and title)
            image_files[blob.name] = {'description': text_content, 'title': title}

    print(f"Files in bucket: {list(image_files.keys())}")  # Debug print to check fetched image files
    return image_files  # Return a dictionary of image files and their associated text descriptions

def upload_text_file(bucket_name, file_name, text_content):
    """Upload a text file to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    # Upload the string content as the file content
    blob.upload_from_string(text_content)
    
    print(f"Uploaded text file {file_name} to bucket {bucket_name}.")
    return

def get_file_metadata(filename):
    """Fetch the metadata for the file from the datastore."""
    obj = {"Filename": filename}
    metadata = fetch_db_entry(obj)
    return metadata

def fetch_db_entry(object):
    """Fetch a database entry based on the object attributes."""
    query = datastore_client.query(kind='photos')

    for attr in object.keys():
        query.add_filter(attr, "=", object[attr])
    
    obj = list(query.fetch())
    return obj[0] if len(obj) else {}

def add_db_entry(object):
    """Add a new entry to the datastore."""
    entity = datastore.Entity(key=datastore_client.key('photos'))
    entity.update(object)
    print("add_db_entry: " + str(object))
    datastore_client.put(entity)

def upload_file(bucket_name, file_name, file):
    """Upload a file to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_file(file)
    print(f"Uploaded file {file_name} to bucket {bucket_name}.")
    return

def get_image_metadata(filename):
    """Extract metadata from the image file."""
    download_file(bucketname, filename)
    
    # Load image to extract EXIF metadata
    image = Image.open(filename)
    exif_data = image._getexif()

    metadata = {'Filename': filename}

    if exif_data:
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            metadata[tag_name] = str(value)

    return metadata

def get_list_of_files(bucket_name):
    """Get a list of image files from the bucket."""
    blobs = storage_client.list_blobs(bucket_name)
    files = [blob.name for blob in blobs if blob.name.endswith((".jpeg", ".png", ".jpg"))]
    return files

def download_file(bucket_name, file_name):
    """Download a file from Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    blob.download_to_filename(file_name)
    blob.reload()

    print(f"Blob: {blob.name}, Bucket: {blob.bucket.name}, Size: {blob.size} bytes, Content-type: {blob.content_type}")
    return

def serve_image(bucket_name, filename):
    """Serve an image file."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    
    # Download the image to a temporary location and serve it
    temp_file = f"/tmp/{filename}"
    blob.download_to_filename(temp_file)
    
    print(f"Serving file {filename} from bucket {bucket_name}.")
    return send_file(temp_file)

def get_image_list_with_metadata(bucketname):
    # This function retrieves the list of images and their descriptions from Datastore
    query = datastore_client.query(kind='ImageMetadata')
    results = query.fetch()

    image_list_with_metadata = []
    for entity in results:
        image_data = {
            'filename': entity['filename'],
            'description': entity.get('description', 'No description available')  # Default if no description
        }
        image_list_with_metadata.append(image_data)

    return image_list_with_metadata
