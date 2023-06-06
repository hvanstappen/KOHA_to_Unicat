import xml.etree.ElementTree as ET
import sys
import requests
from ftplib import FTP
from datetime import datetime, timedelta
import signal
import config

# Custom exception to handle timeout
class TimeoutException(Exception):
    pass

# Function to raise TimeoutException after a specified time limit
def timeout_handler(signum, frame):
    raise TimeoutException("Geen datum ingevoerd. Records die in de laatste 7 dagen werden aangepast, zullen worden verwerkt.\n")

# Read the timeout duration in seconds from config
timeout_duration = config.timeout_duration
current_date = datetime.now().strftime("%Y%m%d")

# Set the default frequency
frequency = config.frequency

try:
    # Set the signal handler for the timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_duration)

    # Prompt user for the start date and validate the format of the date
    while True:
        start_date = input("Geef de startdatum (formaat YYYYMMDD) en druk op Enter (Type '0' om alle records te verwerken):\n")
        if start_date == '0':
            start_date = '00010101'
        
        # check if date is 8 digits
        if len(start_date) != 8 or not start_date.isdigit():
            print("Ongeldige datum! Voer de datum in het juiste formaat (YYYYMMDD) in.")
            continue

        # check if date is valid
        year = int(start_date[:4])
        month = int(start_date[4:6])
        day = int(start_date[6:8])

        try:
            datetime(year, month, day)
            # date is valid, break out of the while-loop
            break
        except ValueError:
            print("Ongeldige datum! Voer een bestaande datum in.")

    # Clear the alarm after receiving input
    signal.alarm(0)

    # Check if the user provided input
    if start_date == "":
        start_date = (datetime.now() - timedelta(days=frequency)).strftime("%Y%m%d")

    # Process the value of 'start_date'
    print("Startdatum: ", start_date)

except TimeoutException as e:
    print(str(e))
    # Set 'start_date' to 7 days before the 'current_date'
    start_date = (datetime.now() - timedelta(days=frequency)).strftime("%Y%m%d")
    print("Startdatum: ", start_date)

# Get XML from KOHA
url = config.url
username = config.username
password = config.password

print("Data worden opgehaald van de server. Dit kan even duren...")

# Sending a GET request with authentication
response = requests.get(url, auth=(username, password))

# Checking the response status code
if response.status_code == 200:
    # Successful request
    xml_data = response.content.decode('UTF-8')
    # Process the XML data as needed
    root = ET.fromstring(xml_data)  # Parse the XML data
    # Access XML elements, attributes, etc.

else:
    # Request was not successful
    print("Error:", response.status_code)


print("Data worden gefilterd...")

# Parsing the XML file
#tree = ET.ElementTree(root)

# Namespace mapping
namespace = {'marc': 'http://www.loc.gov/MARC21/slim'}
ET.register_namespace("", namespace["marc"])

print("Selectie wordt gemaakt van alle records gewijzigd sinds ",start_date,"\n")

# Select records updated since input date
selected_records = []
total_record_count = 0
for record in root.findall('marc:record', namespace):
    total_record_count = total_record_count + 1
    controlfield_005 = record.find("marc:controlfield[@tag='005']", namespace)
    if controlfield_005 is not None:
        changedate = controlfield_005.text[:8]
        if changedate > start_date:
            selected_records.append(record)
#            print("Record gewijzigd op ", changedate, " wordt verwerkt.")

# update XML
update_record_count = 0
for record in selected_records:
    update_record_count = update_record_count + 1
    
    # find values from KOHA element 001, create one if empty
    controlfield_001 = record.find("marc:controlfield[@tag='001']", namespace)
    if controlfield_001 is not None and controlfield_001.text is not None:
        controlfield_001_text = controlfield_001.text
    else:
        controlfield_001_text = ""

    # replace values for KOHA element 001 with value datafield 999 subfield c
    controlfield_001 = record.find("marc:controlfield[@tag='001']", namespace)
    datafield_999c = record.find("marc:datafield[@tag='999']/marc:subfield[@code='c']", namespace)
    if controlfield_001 is not None and datafield_999c is not None:
        controlfield_001.text = datafield_999c.text


    # create element 852 [(repeatable) is to be supplied using the Antilope model]
    datafield_852 = ET.Element('datafield')
    datafield_852.set('tag', '852')

    subfield_a = ET.SubElement(datafield_852, 'subfield', {'code': 'a'})
    subfield_a.text = 'BE-BxLRC'

    subfield_c = ET.SubElement(datafield_852, 'subfield', {'code': 'c'})
    subfield_c.text = controlfield_001

    record.append(datafield_852)

    # create element 919 [identifier of the institution]
    datafield_919 = ET.Element('datafield')
    datafield_919.set('tag', '919')
    subfield_a = ET.SubElement(datafield_919, 'subfield', {'code': 'a'})
    subfield_a.text = 'B-Bc'

    record.append(datafield_919)

    # create element 920 [resource type]
    # find values for KOHA datafield 942
    # datafield_942 = record.find("marc:datafield[@tag='942']/marc:subfield[@code='c']", namespace).text
    datafield_942_element = record.find("marc:datafield[@tag='942']/marc:subfield[@code='c']", namespace)
    datafield_942 = datafield_942_element.text if datafield_942_element is not None else ""

    # mapping of values for datafield_919
    mapping = {
        'AR': 'book',
        'CD': 'audio',
        'CF': 'digital',
        'FI': 'film',
        'IM': 'image',
        'LP': 'audio',
        'MM': 'book',
        'MP': 'book',
        'SM': 'book',
        'TP': 'book',
        'PE': 'periodical',
        'RE': 'object',
        'TA': 'audio',
        'TM': 'book',
        'VI': 'film'
    }           
    datafield_942 = mapping.get(datafield_942, 'book')
    # create element 920
    datafield_920 = ET.Element('datafield')
    datafield_920.set('tag', '920')

    subfield_a = ET.SubElement(datafield_920, 'subfield', {'code': 'a'})
    subfield_a.text = datafield_942
    
    record.append(datafield_920)


# Save the modified XML
if selected_records:
    if start_date > "00010101":
        dump_name = "KCBunicat." + current_date + ".xml"
    else:
        dump_name = "KCBunicat" + ".completedump.xml"

    # create a new root element to hold the selected records
    new_root = ET.Element(root.tag, attrib=root.attrib)
    new_root.extend(selected_records)

    # create an ElementTree object with the new root element
    tree = ET.ElementTree(new_root)

    # write the ElementTree to the file
    tree.write(dump_name, xml_declaration=True, encoding='UTF-8')

    print("\nSuccess :-)")
    print("Records worden bewaard als ", dump_name)

# Upload the XML file to the FTP server
    ftp_host = config.ftp_host
    ftp_username = config.ftp_username
    ftp_password = config.ftp_password

    ftp = FTP(ftp_host)
    ftp.login(user=ftp_username, passwd=ftp_password)

    print("Records worden gekopieerd naar FTP server...")

    # upload the file to the FTP server
    with open(dump_name, 'rb') as file:
        ftp.storbinary(f'STOR {dump_name}', file)

    ftp.quit()

else:
    print("\nGeen gewijzigde records gevonden.")

print("aantal gewijzigde records: ", update_record_count)
print("totaal aantal records: ", total_record_count)
print("resultaat wordt weggeschreven naar log.txt...")

# Open the log file in append mode
with open("log.txt", "a") as file:
    # write the current date to the log file
    file.write("datum: " + current_date + "\n")
    file.write("updated records sinds: " + start_date + "\n")
    file.write("aantal gewijzigde records: "+ str(update_record_count) + "\n")
    file.write("==============\n")
    
print("Klaar!")
