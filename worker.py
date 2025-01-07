import base64
import json
import time
import os, fnmatch

# 3rd party imports 
import subprocess
from azure.servicebus import ServiceBusClient

from language_handler import *
from redis_engine import RedisClient
from dotenv import load_dotenv

load_dotenv()

client_redis=RedisClient()

def find_worker(pattern, box):
    result = []
    # print(path)
    path = "/var/local/lib/isolate/" + str(box) + "/box/"
    for root, dirs, files in os.walk(path):
        for name in files:
            # print(name)
            if fnmatch.fnmatch(name, pattern):
                result.append(name)
    return result

def read_meta(file_name):
    """
    Function to read meta data of the program such as execution time, memory, etc

    Parameters:
        fileName(str): Name of file which contains meta data of program

    Returns:
        dict: Dictionary which contains all metadata
    """
    meta = {}
    with open(file_name) as myfile:
        for line in myfile:
            name, var = line.partition(":")[::2]
            meta[name.strip()] = str(var).rstrip()

    return meta


# read the compilation error in sandbox
def read_compilation_error(box_id, list_of_testcase_input):
    print(list_of_testcase_input)
    error_info = ''
    with open("/var/local/lib/isolate/" + str(box_id) + "/box/error.txt", "r") as fs:
        error_info = fs.read()
        if len(error_info) >= 1000:
            # if output is too long it is truncated
            error_info = error_info[:1000]
            error_info = error_info + '...(output truncated)'
        print(error_info)
        return error_info


# formatted data for successful compilation
def formatted_output(box_id, list_of_testcase_input):
    print("In formatted output")
    list_of_input_files = find_worker('input_*.txt', box_id)
    output_dict = {'input': '', 'output': ''}
    output = []
    try:
        for i in range(len(list_of_input_files)):
            with open("/var/local/lib/isolate/" + str(box_id) + "/box/input_{}.txt".format(i), "r") as fs:
                with open("/var/local/lib/isolate/" + str(box_id) + "/box/output_{}.txt".format(i), "r") as f:
                    meta = read_meta("/var/local/lib/isolate/" + str(box_id) + "/box/meta_{}.txt".format(i))
                    with open("/var/local/lib/isolate/" + str(box_id) + "/box/error_{}.txt".format(i), "r") as fd:
                        input_data = fs.read()
                        output_data = f.read().replace("\x00", "")    # NULL value replace with ""
                        error_data = fd.read().replace("\x00", "")   # NULL value replace with ""
                        print("meta", meta)
                        if len(output_data) >= 1000:
                            # if output is too long it is truncated
                            output_data = output_data[:1000]
                            output_data = output_data + '...(output truncated)'
                        output_dict['input'] = input_data  
                        output_dict['output'] = output_data 
                        output_dict['memory'] = meta['cg-mem']
                        output_dict['exctime'] = meta['time']
                        output_dict['error'] = error_data

                        exitcode = meta.get('exitcode', None)
                        if exitcode == '0':
                            meta['status'] = 'OK'
                            meta['message'] = 'compilation successful'
                        elif meta['status'] == 'TLE' or meta['status'] == 'RE' or meta['status'] == 'SG' or meta[
                            'status'] == 'XX':
                            meta["cg-mem"] = "--"

                        output_dict['status'] = meta['status']
                        output_dict['message'] = meta['message']
                        output.append(output_dict.copy())

        print(output)
    except Exception as e:
        print("getting error  while generating output {}".format(e))

    for i in range(len(list_of_testcase_input)):
        for j in range(len(output)):
            if i == j:
                output[j]['tc_id'] = list_of_testcase_input[i]['tc_id']

    return output


# update the database

def isolate_initiate(box_id, input_data, code, language_file):

    """
    initialize the isolate sandbox

    Parameters:
        box_id(int): isolate box ID for the submission
        input_data(list): input Data for the submission and testcase id
        code(str): Main file for the submission
        lang(str): language for the submission
    """

    print('Call isolate_initiate')
    print(input_data)
    # initialize box for isolate module
    subprocess.call("isolate --cleanup -b " + str(box_id), shell=True)
    subprocess.call("isolate --cg --init -d rw -b " + str(box_id), shell=True)

    # Write input file (input to the code)
    count = 0
    for item in input_data:
        if count<(len(input_data)):
            with open("/var/local/lib/isolate/" + str(box_id) + "/box/input_{}.txt".format(count), "w+") as f_input:
                f_input.write(item['input']+'\n')
                count +=1

    # Write output file( write the code in associated file)
    f_code = open("/var/local/lib/isolate/" + str(box_id) + "/box/" +language_file, "w+")
    f_code.write(code)

    f_code.close()
    print("isolate executed")


def update_submission(submission_id:int, submission_data:dict, status:str, output_data:list):
 
    # print("update submissioin output: ", output_data)
    # print("update submission data: ", submission_data['input'])
    submission_data['status'] = status
    if status == 'OK' or status == 'TLE' or status== 'RE' or status == 'SG' or status == 'XX':
        try:
            for i in output_data:
                if "\x00" in i["output"]:
                    i["output"] = "NULL"
                   
                i["output"].replace("\x00", "\uFFFD")

            for testcase in submission_data['output']:
                for updated_testcase in output_data:
                    # print("output_dic: ", output_dic)
                    if testcase['tc_id'] == updated_testcase['tc_id']:
                        # print("update submission_id: ", submission_id)
                        testcase['output'] = updated_testcase['output']
                        testcase['memory'] = updated_testcase['memory']
                        testcase['exctime'] = updated_testcase['exctime']
                        testcase['status'] = updated_testcase['status']
                        testcase['error'] = updated_testcase['error']
           
        except Exception as e:
            print(" Error {} while storing output for submission {}".format(e, submission_id))
            # logger.error(" Error {} while storing output for submission {}".format(e, submission))
       
    elif status == 'CTE' or status  == "TO":
            submission_data['error_message'] = output_data[0]['error_message']
 
            for testcase in submission_data['output']:
                testcase['status'] = status
                testcase['error'] = output_data[0]['error_message']
 
    elif status == 'DOJ':
        submission_data['error_message'] = "Denial Of Judgement"
    # submission_data['output'] = submission_data['input']
    # submission_data.pop('input')
    ser_submission_data = json.dumps(submission_data)
   
    client_redis.upsert_value(str(submission_id), ser_submission_data)
 
    return True



def callback(body):
    """Main function which is called back by RabbitMQ"""
    print('The message body is ', body)
    try:
        submissionid = int(body)
        submission_data_str=client_redis.get_value(submissionid)
        submission_data=json.loads(submission_data_str)
        print(submission_data)
        status= 'queue'
        output_data = []
        try:
            
            list_of_testcases_inputs = []
            
            box_id = submissionid % 1000

            language_map={
                'py3ml': {'compile': getattr(py3ml, 'compile'), 'run': getattr(py3ml, 'run'), 'mainfile':'main.py'},
                'cpp20': {'compile': getattr(cpp20, 'compile'), 'run': getattr(cpp20, 'run'), 'mainfile':'main.cpp'},
                'r': {'compile': getattr(R, 'compile'), 'run': getattr(R, 'run'), 'mainfile':'main.rs'},
                'java19': {'compile': getattr(java19, 'compile'), 'run': getattr(java19, 'run'), 'mainfile':'Main.java'}
                }
            
            if submission_data['language'] in list(language_map.keys()):
    
                isolate_initiate(box_id, submission_data['output'], submission_data['code'],language_map[submission_data['language']]['mainfile'])
    
                compile_code = language_map[submission_data['language']]['compile']
    
                run_code = language_map[submission_data['language']]['run']
    
            else:
                print("language not supported")
    
            is_compile = compile_code(box_id)
            print("iscompile" , is_compile)
            if not is_compile:
                try:
                    status = 'CTE'
    
                    error = read_compilation_error(box_id, submission_data['output'])
                    
                    # submission_data['status'] = status
                    # submission_data['error_message'] = error
                    output_data = [
                        {
                            'error_message': error
                        }
                    ]
                    # client_redis.upsert_value(submissionid,new_value=json.dumps(submission_data))
                except Exception as e:
                    
                    print("Exception CTE ", e)
            else:
                run_code(box_id)
                # os.system("cd /var/local/lib/isolate/" + str(box_id) + "/box/  && ls -a  ")
                status ='OK'
                output_data = formatted_output(box_id, submission_data['output'])
                print(output_data)
                # submission_data['output'] = output_data
                # submission_data['status'] = output_data[0]['status']
                # client_redis.upsert_value(submissionid,new_value=json.dumps(submission_data))
    
    
        except Exception as e:
            submissionid = int(body) 
            status = 'DOJ'
            output_data = list([dict({})])
            print("DOJ")
            print("getting error {} and doj message for {}".format(e, submissionid))
            # update_database(submission, 'DOJ', {})
        finally:
            update_submission(submissionid,submission_data, status, output_data )

    except Exception as e:
        print("Error {} in submission {} ".format(e, submissionid))
        return None
    
# connstr = "Endpoint=sb://mocservicebus-qa.servicebus.windows.net/;SharedAccessKeyName=worker-1;SharedAccessKey=bdGP7fe/4FD1J/K18UYAPwmCmgwYpggRvIhXwsS8ySo="
# queue_name = "moc_queue_6"
# print(os.environ.get("CONNECTION_STR"))
with ServiceBusClient.from_connection_string(os.getenv("CONNECTION_STR")) as client:   
    with client.get_queue_receiver(queue_name=os.getenv("QUEUE_1_NAME")) as receiver:
        for msg in receiver:
            print(str(msg))
            callback(str(msg))
            receiver.complete_message(msg)
