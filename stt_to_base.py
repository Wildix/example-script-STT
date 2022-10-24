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
# Example of results after stt dialplan's application
#{
#   "questions":[
#      {
#         "question":"Prego, dica il suo nome",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105711-500-wildixbox-1665133023.5-1.wav",
#         "result":"victor",
#         "label":"caller_name"
#      },
#      {
#         "question":"Prego, dica il suo cognome",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105720-500-wildixbox-1665133023.5-2.wav",
#         "result":"сonte",
#         "label":"caller_surname"
#      },
#      {
#         "question":"Prego, dica il numero di telefono a cui possiamo ricontattarla",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105723-500-wildixbox-1665133023.5-3.wav",
#         "result":"393123456789",
#         "label":"caller_number"
#      },
#      {
#         "question":"Ha bisogno di aiuto per sé o per un’altra persona?",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105736-500-wildixbox-1665133023.5-4.wav",
#         "result":"yes",
#         "label":"looking_for_other"
#      },
#      {
#         "question":"Prego, dica il nome della persona cercata",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105744-500-wildixbox-1665133023.5-5.wav",
#         "result":"mike",
#         "label":"other_name"
#      },
#      {
#         "question":"Prego, dica il cognome della persona cercata",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105757-500-wildixbox-1665133023.5-6.wav",
#         "result":"neri",
#         "label":"other_surname"
#      },
#      {
#         "question":"Prego, dica il numero di telefono della persona cercata",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105778-500-wildixbox-1665133023.5-7.wav",
#         "result":"380671234567",
#         "label":"other_number"
#      },
#      {
#         "question":"Prego, dica la nazione di provenienza della persona cercata",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105781-500-wildixbox-1665133023.5-8.wav",
#         "result":"ucraina",
#         "label":"other_country"
#      },
#      {
#         "question":"Prego, dica la città di provenienza della persona cercata",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105793-500-wildixbox-1665133023.5-9.wav",
#         "result":"odesa",
#         "label":""
#      },
#      {
#         "question":"Se lo desidera, può lasciare un messaggio aggiuntivo",
#         "status":"SUCCESS",
#         "audio_file":"/dev/shm/var/spool/callweaver/monitor/stt/20221007-105793-500-wildixbox-1665133023.5-10.wav",
#         "result":"bisogno di consigli per ottenere un permesso di soggiorno",
#         "label":""
#      }
#   ],
#   "timestamp":"2022-10-07 10:57:11",
#   "linkedid":"wildixbox-1665133023.5"
#}
STT_DATA = json.loads(base64.b64decode(sys.argv[2]))

# Example uses mysql. Can be changed to any with python DB-API 2.0 (PEP 249)
# Redefine for used db backend (additional Python libraries installed on the pbx required)
def get_db_connection():
    import mysql.connector
    return mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword",
        database="dbname"
    )

# Name of the db table
TABLE_NAME = "stt_data"
# Example table create sql command
# CREATE TABLE stt_data (
#    id INT AUTO_INCREMENT,
#    unique_id TEXT NOT NULL,
#    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#    error INT,
#    audio_file TEXT,
#    caller_name TEXT,
#    caller_surname TEXT,
#    caller_number TEXT,
#    real_caller_number TEXT,
#    looking_for_other BOOLEAN NOT NULL DEFAULT FALSE,
#    other_name TEXT,
#    other_surname TEXT,
#    other_number TEXT,
#    other_country TEXT,
#    other_city TEXT,
#    notes TEXT,
#    handled BOOLEAN NOT NULL DEFAULT FALSE,
#    PRIMARY KEY (id)
#);

# tts application creates sound files, there are parameters related to sound files
# Use sounds
PROCESS_SOUNDS = True
# Remove sources audio
REMOVE_AUDIO_SOURCES = True
# Output directory. Setup path to your mounted storage
SOUND_OUTPUT_DIR = "/tmp"

# Recognition columns mapping related to json data. Labels and questions accepted
# Recognision results from the tts application will be written to values columns names
# The format: "lable name or question": "column name".
# Need to exclude columns (labels/questsions) which additionally processed
# like `ADD_COLUMN["looking_for_other"]` in this example below.
# Please see example of the dialplan
STT_COLUMNS = {
    "caller_name": "caller_name",
    "caller_surname": "caller_surname",
    "caller_number": "caller_number",
    "other_name": "other_name",
    "other_surname":"other_surname",
    "other_number": "other_number",
    "other_country": "other_country",
    "Prego, dica la città di provenienza della persona cercata": "other_city",
    "Se lo desidera, può lasciare un messaggio aggiuntivo": "notes"
}

# Additional columns which is not directly related to stt results
ADD_COLUMN = {}

ADD_COLUMN["real_caller_number"] = CALLER_ID_NUMBER
ADD_COLUMN["unique_id"] = STT_DATA["linkedid"]

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
    counter = 0
    for item in STT_DATA["questions"]:
        if item["status"] != "SUCCESS":
            counter += 1
    return counter

# Calculate error column(s)
ADD_COLUMN["error"] = get_error()

# Process result of dialplan choice, please see example dialplan
ADD_COLUMN["looking_for_other"] = True if "yes" in get_result("looking_for_other") else False

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
    values_template = ",".join(["%s"] * len(values))

    query = "INSERT INTO %s (%s) VALUES (%s)" % (TABLE_NAME, columns_list, values_template)
    return (query, values)

con = get_db_connection()
cur = con.cursor()
query, values = create_query()
cur.execute(query, values)
con.commit()
con.close()
