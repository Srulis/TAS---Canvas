#required libraries
import requests, datetime, os, csv, json, zipfile, io, sys
from shutil import copyfile

# TAS Variables
tas_URL = "http://api.tasscloud.com.au/tassweb/api/"
tas_APIToken = ""
tas_appCope = ""
tas_company = "10"

# Canvas Variables
authentication_provider_id = ""

# debug
debug = False

#======================== Start functions ========================

#create zip from folder
def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=True,zipTimeStamp = None):
    if not zipFilePath:
        zipFilePath = dirPath + ".zip"
    if not os.path.isdir(dirPath):
        raise OSError("dirPath argument must point to a directory. "
            "'%s' does not." % dirPath)
    parentDir, dirToZip = os.path.split(dirPath)
    #Little nested function to prepare the proper archive path
    def trimPath(path):
        archivePath = path.replace(parentDir, "", 1)
        if parentDir:
            archivePath = archivePath.replace(os.path.sep, "", 1)
        if not includeDirInZip:
            archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
        return os.path.normcase(archivePath)

    outFile = zipfile.ZipFile(zipFilePath, "w",
        compression=zipfile.ZIP_DEFLATED)
    for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
        for fileName in fileNames:
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))
        #Make sure we get empty directories as well
        if not fileNames and not dirNames:
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
            outFile.writestr(zipInfo, "")
    outFile.close()
    outputMessage("Created .zip file from folder: " + dirPath)
    outputMessage("Zip file location: " + zipFilePath)

    #Copy the "Canvas.zip" to the source location
    copyPath = dirPath + "/" + zipTimeStamp + "_canvas_sis_import.zip"
    copyfile(zipFilePath, copyPath)
    outputMessage("Copy of zip location: " + copyPath)
#end Zip Folder

#start output message
def outputMessage(message=None):
	print(datetime.datetime.now().isoformat() + "# " + message)
#end output message

#start TAS GET Student Details function
def tasGET_GetStudentsDetails():
	url = tas_URL

	querystring = {
		"method":"getStudents",
		"currentstatus": "current",
		"appcode":tas_appCope,
		"company":tas_company,
		"v":"2",
		"token":tas_APIToken,
		"includephoto": "false", #does not appear to be working on the server end
		"thumbnail": "false" #does not appear to be working on the server end
	}
	#Ensure that the request IS NOT encoded as it may contain '%' which should not be translated
	payload_str = "&".join("%s=%s" % (k,v) for k,v in querystring.items())

	headers = {
    	'Cache-Control': "no-cache"
    }

	response = requests.get(url, params=payload_str, headers=headers)
	
	if debug:
		print("Current return string: "+response.text)

	response = response.json()
	return response
# end TAS Get Student Details

# Start create student array
def createStudentList(studentArray = []):
	returnStudentList=[]
	
	for student in studentArray:
		currentStudent = {}
		currentStudent['user_id'] = str(student['general_details']['student_code'])
		currentStudent['email'] = student['school_details']['email_address']
		currentStudent['login_id'] = student['school_details']['email_address']
		currentStudent['last_name'] = student['general_details']['surname']
		currentStudent['first_name'] = student['general_details']['given_names']
		currentStudent['short_name'] = student['general_details']['preferred_name'] + ' ' + student['general_details']['surname']
		currentStudent['integration_id'] = str(student["general_details"]["alternate_id"])
		
		#Static info from the global variables
		currentStudent['authentication_provider_id'] = authentication_provider_id
		
		# Students are always 'Active' - Their enrolments in courses will determine their true status
		currentStudent['status'] = 'active'
		
		currentStudent = json.dumps(currentStudent)
		returnStudentList.append(currentStudent)
		if debug:
			print("Current student: "+currentStudent)
	
	return returnStudentList
# End student array

# Start convert CSV to JSON
def createCSV(csv_fileType,csv_thisImportFolder,timeStamp, csv_outputData = []):
	csv_file = csv_thisImportFolder + "/" + timeStamp + '_' + csv_fileType + '.csv'
	
	#open the file
	csv_open_file = open(csv_file, "wb+")

	#output the JSON to the file
	output = csv.writer(csv_open_file) #create a csv.write
	
	#get and write the CSV keys
	csv_keys = json.loads(csv_outputData[0])
	output.writerow(csv_keys.keys()) #Header row
	
	for row in csv_outputData[0:]:
		phasedRow = json.loads(row)
		output.writerow(phasedRow.values()) #values row
    
	csv_open_file.close()
	outputMessage("Completed creating file (" + csv_fileType + "): " + csv_file)
# End convert CSV to JSON

#======================== End functions ========================

#======================== Start Main ========================

#1 - get current date/time for filenames and folders
timeStamp = datetime.datetime.now().isoformat()
timeStamp = timeStamp.replace(":", ".")
outputMessage("Current time stamp: " + timeStamp)
timeStamp = "Export_" + timeStamp


#2 - create the foler for this import
currentDirectory = os.path.dirname(os.path.abspath(__file__))
outputMessage("Current DIR: "+ currentDirectory)
thisImportFolder = currentDirectory + "/" + timeStamp
os.makedirs(thisImportFolder)
outputMessage("Export DIR: " + thisImportFolder)

#3 - Get the student details from the TAS API then create JSON object in Canvas form
currentStudents = tasGET_GetStudentsDetails()
studentList = createStudentList(currentStudents['students'])


#4 - Output the JSON arrays to CSVs
createCSV('students',thisImportFolder,timeStamp,studentList)

#5 - zip the CSVs
#create the master .zip in the current DIR
zipdir(thisImportFolder, currentDirectory + "/canvas.zip",False, timeStamp)

outputMessage("\n")

#======================== End Main ========================
