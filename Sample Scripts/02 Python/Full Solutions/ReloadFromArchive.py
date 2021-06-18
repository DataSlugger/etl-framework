import os
import sys
import glob
import pyodbc as db
import zipfile as zf

#The following three varaibles should be
#populated by configuration
WarehouseProcessingRootDirectory = ''
BusinessDirectory = ''
ProcessDirectory = ''

DataDirectory = 'In\\'
ArchiveDirectory = 'Archive\\'
FileName = ''
fileTimeStampedTXT = ''

DestinationDirectory = os.path.join(WarehouseProcessingRootDirectory, BusinessDirectory, ProcessDirectory, DataDirectory)
ArchiveDestinationDirectory = os.path.join(WarehouseProcessingRootDirectory, BusinessDirectory, ProcessDirectory, ArchiveDirectory)

print("Starting: Processing ReloadAchive")

# get list of zip file
try:
    print("Getting zip files from archive directory {}".format(ArchiveDestinationDirectory))
    zipFiles = glob.glob(ArchiveDestinationDirectory + "*.zip", recursive=False)
except Exception as e:
    print(e)


# Report number of zip files found
print("{} zip files found".format(len(zipFiles)))

# unzip each file in zipFiles
for zFile in zipFiles:
    try:
        print("Unzipping file {}".format(zFile))
        zip_ref = zf.ZipFile(zFile, 'r')
        zip_ref.extractall(DestinationDirectory)
        zip_ref.close()
    except Exception as e:
        print(e)

# get list of txt files in C:/InterfaceAndExtractFiles/../In/
try:
    print("Getting txt files from directory {}".format(DestinationDirectory))
    txtFiles = glob.glob(DestinationDirectory + "*.txt", recursive=False)
except Exception as e:
    print(e)

# Report number of zip files found
print("{} txt files found".format(len(txtFiles)))

# Create database connection
try:
    print("Connecting to SQL Server database")
    connection_string = 'DSN=ETL;'
    conn = db.connect(connection_string)
except Exception as e:
    print(e)

# preparing SQL Server
try:
    print("Preparing database for update")
    csr = conn.cursor()
    csr.execute("DELETE FROM [stage table] WHERE Processed = 1")
    csr.execute("DROP INDEX IF EXISTS [index name] ON [stage table]")
    conn.commit()
    csr.close()
except Exception as e:
    print(e)

# creating counters
txtFileCount = len(txtFiles)
n = 1

# process each txt file
for tFile in txtFiles:
    try:
        print("Processng file {} of {}: Update database with {} file data.".format(n, txtFileCount, tFile))
        n += 1
        csr = conn.cursor()
        sql = "BULK INSERT [stage table view] FROM '" + tFile + "' WITH (FIELDTERMINATOR = '|', ROWTERMINATOR = '0x0a', FIRSTROW = 2)"
        csr.execute(sql)
        conn.commit()
        csr.close()
    except Exception as e:
        print(e)

    try:
        print("Deleting {} file".format(tFile))
        if os.path.isfile(tFile):
            os.remove(tFile)
    except Exception as e:
        print(e)

# Complete SQL Server processing
try:
    print("Completing SQL Server update")
    print("Creating index on SQL table")
    csr = conn.cursor()
    csr.execute("CREATE NONCLUSTERED INDEX [index name] ON [stage table]([column name])")
    print("Completing SQL Server update")
    conn.commit()
    csr.close()
    conn.close()
except Exception as e:
    print(e)

# Complete
print("COMPLETE: Process Reload from Archive")