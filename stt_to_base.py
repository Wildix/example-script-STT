#!/usr/bin/python3
# Example script for wildix stt dialplan application
# Set(SttRes=${SHELL(/usr/local/sbin/stt_to_base.py ${CALLERID(num)} ${BASE64_ENCODE(${RECOGNITION_RESULTS})})})

import base64
import json
import os
import subprocess
import sys
import uuid


# The first argument of the script is caller number from dialplan custom application
# Please see README file and dialplan example
CALLER_ID_NUMBER = sys.argv[1]

# The second argument of the script is JSON data from dialplan tts application
# Example for used dialpaln:
#{
#   "questions":[
#      {
#         "question":"Hello, what is your name?",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105711-500-wildixbox-1665133023.5-1.wav",
#         "result":"victor",
#         "label":""
#      },
#      {
#         "question":"Where are you live?",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105720-500-wildixbox-1665133023.5-2.wav",
#         "result":"new york",
#         "label":""
#      },
#      {
#         "question":"Do you have a best friend?",
#         "status":"SUCCESS",
#         "audio_file":"",
#         "result":"yes",
#         "label":""
#      },
#      {
#         "question":"What is your friend name?",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105736-500-wildixbox-1665133023.5-4-friend_name.wav",
#         "result":"peter",
#         "label":"friend_name"
#      },
#      {
#         "question":"Where are your friend live?",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105744-500-wildixbox-1665133023.5-5-friend_live.wav",
#         "result":"miami",
#         "label":"friend_live"
#      }
#   ],
#   "timestamp":"2022-10-07 10:57:11",
#   "linkedid":"wildixbox-1665133023.5"
#}
STT_DATA = json.loads(base64.b64decode(sys.argv[2]))

# Example uses sqlite. Can be changed to any with python DB-API 2.0 (PEP 249)
# Redefine for used db backend (additional Python libraries installed on the pbx required)
def get_db_connection():
    import sqlite3
    return sqlite3.connect("/var/opt/sttdb")

# Name of the db table
TABLE_NAME = "stt_data"
# Example table create sql command
# CREATE TABLE stt_data (
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    caller_id TEXT,
#    user_name TEXT,
#    user_place TEXT,
#    have_friend INTEGER,
#    friend_name TEXT,
#    friend_place TEXT,
#    audio_file TEXT,
#    error INTEGER
#);

# tts application creates sound files, there are parameters related to sound files
# Use sounds
PROCESS_SOUNDS = True
# Remove sources audio
REMOVE_AUDIO_SOURCES = True
# Output directory
SOUND_OUTPUT_DIR = "/tmp"

# Recognition columns mapping related to json data. Labels and questions accepted
# Recognision results from the tts application will be written to values columns names
# Please see example of the dialplan
STT_COLUMNS = {
    "Hello, what is your name?": "user_name",
    "Where are you live?": "user_place",
    "friend_name": "friend_name",
    "friend_live": "friend_place"
}

# Additional columns which is not directly related to stt results
ADD_COLUMN = {}

ADD_COLUMN["caller_id"] = CALLER_ID_NUMBER

# Create one audio file from all dialplan recognition results with save audio enabled
# and write it to the destination directory with random name (added to separate db column)
def concatenate_audio_files():
    sound_files = [item["audio_file"] for item in STT_DATA["questions"] if item["audio_file"]]
    if sound_files:
        file_ext = sound_files[0].split(".")[-1]
        out_file = "%s/%s.%s" % (SOUND_OUTPUT_DIR, str(uuid.uuid4()), file_ext)
        subprocess.run(["/usr/bin/sox"] + sound_files + [out_file], check=True)
        if REMOVE_AUDIO_SOURCES:
            for file in sound_files:
                os.remove(file)
        return out_file

if PROCESS_SOUNDS:
    out_file = concatenate_audio_files()
    if out_file:
        ADD_COLUMN["audio_file"] = out_file

def get_result(ident):
    for item in STT_DATA["questions"]:
        if ident in (item["label"], item["question"]):
            return item["result"]
    return ""

def get_error():
    for item in STT_DATA["questions"]:
        if item["status"] != "SUCCESS":
            return 1
    return 0

# Calculate error column
ADD_COLUMN["error"] = get_error()

# Process result of dialplan choice, please see example dialplan
ADD_COLUMN["have_friend"] = 1 if "yes" in get_result("Do you have a best friend?") else 0

def create_query():
    columns = []
    values = []

    for item in STT_DATA["questions"]:
        if item["label"] and item["label"] in STT_COLUMNS:
            columns.append(STT_COLUMNS[item["label"]])
            values.append(item["result"])
        elif item["question"] in STT_COLUMNS:
            columns.append(STT_COLUMNS[item["question"]])
            values.append(item["result"])

    columns.extend(list(ADD_COLUMN.keys()))
    values.extend(list(ADD_COLUMN.values()))

    columns_list = ",".join(columns)
    values_template = ",".join(["?"] * len(values))

    query = "INSERT INTO %s (%s) VALUES (%s)" % (TABLE_NAME, columns_list, values_template)
    return (query, values)

con = get_db_connection()
cur = con.cursor()
query, values = create_query()
cur.execute(query, values)
con.commit()
con.close()
