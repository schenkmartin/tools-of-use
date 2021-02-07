## google-drive-api-upload.py
##
## author: m.a.schenk@zoho.com
## version: 0.01.1
## 
## Upload files to your Google Drive account using Googles Drive API tools. It allows uploading of files
## larger than 5MB, too.
## 
##
## The file client_secret.json must exist at the specified location. It can be created in the Google developers console.
## Create or use an existing project. Then create OAuth2 credentials and configure the consent screen. 
## Export the OAuth2 credentials, they will be stored as client_secret.json.
## 
## By default authentication files placed in the same directory as the script. The script must be executed in this
## directory. This may change in future versions.
##
## The second authentication file credentials.json will be created upon first start of this script. The API tool
## will check for existence and guide you to the Google authentication page, were you can allow the script access
## to Google Drive. On the authentication page, use the Google account to whoms drive you want to upload. The API
## requests full access to Google Drive, this is not my fault. It would be nice if it could only access the files
## that are uploaded by itself. Google would provide such credentials as "drive.file". 
## 
## The API tool will also provide the correct MIME type for your upload file, so you cannot specify it.
##
## Usage: google-drive-api-upload.py <file> [<target folder>]
##        <file> The file you want to upload
##        <target folder> The target folder on Google Drive. By default the script will upload to your home directory
##

version="0.01.1"

import sys
import os
import datetime
from os import path
from googleapiclient.http import MediaFileUpload
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

# define path variables for authentication files here
credentials_file_path = 'credentials.json'
clientsecret_file_path = 'client_secret.json'

# A litte help
def usage():
    print("Usage: google-drive-api-upload.py <file> [<target folder>]")
    print("v" + version)


# Check arguments
## catch the help
if ( len(sys.argv)>1 and sys.argv[1]=="-h"):
    usage()
    exit(0)

## at least a filename must be provided
if ( len(sys.argv)<2 ):
    print("ERROR: no filename provided")
    usage()
    exit (1)

## more than 3 arguments don't make sense
if ( len(sys.argv)>3):
    print("ERROR: too many arguments")
    usage()
    exit(1)

## if there are 3 arguments, the 3rd is the Google Drive target folder
if ( len(sys.argv)==3):
    my_location=sys.argv[2]
else:
    my_location=""

## check if the specified file exists
if not ( path.exists(sys.argv[1]) ):
    print("ERROR: file", sys.argv[1], "does not exist")
    exit(1)

# Split the file provided into its path and name of the file 
my_file=sys.argv[1]
my_filepath, my_filename = os.path.split(my_file)

print(datetime.datetime.now(),"Starting upload of",my_file)


# Authentication 
## define API scope
SCOPE = 'https://www.googleapis.com/auth/drive'

print(datetime.datetime.now(),"Authentication started");

## define store
sys.argv = [sys.argv[0]]  # If the file credentials.json does not exist, the arguments passed to this script must be removed or it will lead to a syntax error of the google apis external authentication
store = file.Storage(credentials_file_path)
credentials = store.get()
if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(clientsecret_file_path, SCOPE)
    credentials = tools.run_flow(flow, store)

print(datetime.datetime.now(),"Authentication finished");

## define API service
http = credentials.authorize(Http())
http.redirect_codes = http.redirect_codes - {308}
service = discovery.build('drive', 'v3', http=http)


# check if location provided exists and get the folder id
folderID = None
folder = None

if ( my_location != ""):
    response = service.files().list(q="name='" + my_location + "' and mimeType='application/vnd.google-apps.folder' and trashed=false",spaces='drive').execute()
    for folder in response.get('files', []):
        #print (folder['name'])
        if ( my_location == folder['name']):  # The specified location was found
            folderID=folder['id']  # We need the id of the folder for the upload

## A folder name was provided but not found
if ( my_location != "" and folderID == None ):
    print(datetime.datetime.now(), "ERROR the folder provided does not exist")
    exit(1)

# Construct the metadata - basically file name, and path if specified       
file_metadata = None
if folderID is None:
    print(datetime.datetime.now(), "Uploading "+my_filename +" to home folder")
    file_metadata = {
        'name' : my_filename
    }
else:
    print(datetime.datetime.now(), "Uploading "+my_filename +" to folder " + my_location+ " [" +folderID+"]")
    file_metadata = {
        'name' : my_filename,
        'parents': [ folderID ]
    }

# Upload as resumable upload, allowing files larger than 5MB
media = MediaFileUpload(my_file, resumable=True)
file = service.files().create(body=file_metadata, media_body=media, fields='name,id').execute()
print(datetime.datetime.now(),"Upload finished")

# Receive file information from Google
fileID = file.get('id')
print('File ID: %s ' % fileID)
print('File Name: %s \n' % file.get('name'))


exit(0)

