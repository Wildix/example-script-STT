## Example of using Wildix STT application script
1. Copy the script named `stt_to_base.py` to the PBX
2. Provide executable permissions to the script
3. Install the library mysql.connector
```
# apt-get update
# apt-get install python3-pip
# pip3 install mysql.connector
```
4. Prepare database (see an example of db connection and structure in stt_to_base.py script)
5. Configure Dialplan with Speech to Text application. See examples on the screenshots below.<br>
For detailed instructions, check out the document: [Speech to Text](https://wildix.atlassian.net/wiki/spaces/DOC/pages/30281834/Dialplan+applications+-+Admin+Guide#Dialplanapplications-AdminGuide-SpeechtoText).
   ![extension +393123456789](stt_context_a.png)
   ![extension ask_other](stt_context_b.png)
   ![extension end_poll](stt_context_c.png)


### Description of custom application string example:
- `/usr/local/sbin/stt_to_base.py` - path to the script file
- `${CALLERID(num)}` - first argument, caller number
- `${RECOGNITION_RESULTS}` - second argument, results of STT application recognition in JSON

### Dump of the Dialplan example in the developer mode:
```
[
  {
    "number": "+393123456789",
    "apps": [
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "caller_name"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "What is your name?",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "caller_surname"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "What is your surname?",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "caller_number"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "What is your contact number?",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "looking_for_other"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Do you need help for yourself, or for another person?",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "GotoIf",
        "params": {
          "condition": "\"${RECOGNITION_RESULT}\"=\"yes\" | \"${RECOGNITION_RESULT}\"=\"si\"",
          "number": "ask_other",
          "dialplan": "main"
        }
      },
      {
        "name": "Goto",
        "params": {
          "number": "end_poll",
          "dialplan": "main"
        }
      }
    ]
  },
  {
    "number": "ask_other",
    "apps": [
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "other_name"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Please, give the name of the person",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "other_surname"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Please, give the surname of the person",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "other_number"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Please, give the phone number of the person",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "RECOGNITION_LABEL",
          "value": "other_country"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Please, name the country of origin of the person",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Stt",
        "params": {
          "question": "Please, name the city of origin of the person",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Goto",
        "params": {
          "number": "end_poll",
          "dialplan": "main"
        }
      }
    ]
  },
  {
    "number": "end_poll",
    "apps": [
      {
        "name": "Stt",
        "params": {
          "question": "If you wish, you can leave an additional message",
          "errorMessage": "",
          "retries": "1",
          "repeatQuestion": "",
          "maxLength": "10",
          "maxSilence": "3",
          "saveAudio": "1"
        }
      },
      {
        "name": "Set",
        "params": {
          "key": "SttRes",
          "value": "${SHELL(/usr/local/sbin/stt_to_base.py ${CALLERID(num)} ${BASE64_ENCODE(${RECOGNITION_RESULTS})})})"
        }
      }
    ]
  }
]
```
