import json
import os.path
import subprocess

"""
This file has language specific execution code.
For each language, there is a class which has two function - 'compile' and 'run'
    => compile function : this function will compile the code and return True if compilation
                       is successful.
    => run function: this function will execute the code in isolate sandbox
"""
# import language settings
# with open('langs_config.json') as f:
#     langs_config = json.load(f)

# find input files
import os, fnmatch
def find(pattern, box):
    result = []
    path = "/var/local/lib/isolate/"+str(box)+"/box/"
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(name)
    return result


# Python3
class py3ml:
    def compile(box_id):
        return True
 
    def run(box_id):
        print("in run py3")
        try:
            no_of_input_files = find('input_*.txt', box_id)
            for input in range(len(no_of_input_files)):
                subprocess.call("isolate --run -p --cg -s"+
                                " --mem=256000"+
                                " -t 2 "+
                                " -w 3 "+
                                " -b " + str(box_id) +
                                " --share-net --full-env  --env=HOME=/home/user" +
                                " -o output_{}.txt".format(input)+
                                " -i input_{}.txt".format(input)+
                                " -M /var/local/lib/isolate/" + str(box_id) + "/box/meta_{}.txt".format(input)+
                                " -r error_{}.txt".format(input) +
                                " /usr/local/bin/python3 main.py " , shell=True)
        except Exception as e:
            print(e)




# R
class R:
    def compile(box_id):
        return True

    def run(box_id):
        no_of_input_files = find('input_*.txt', box_id)
        for input in range(len(no_of_input_files)):
            subprocess.call("prlimit --nofile=1048576:1048576 isolate --run "
                            +" -p --cg -s "
                            +" --cg-mem=26500000 "
                            +" --time=2 "
                            +" --wall-time=3 "
                            +" --open-files=512"
                            +" -b " + str(box_id) 
                            +" --dir=/etc/=/etc/ --dir=/lib/=/lib/ --dir=/lib64/=/lib64/ "
                            +" -o output_{}.txt -i input_{}.txt -M /var/local/lib/isolate/".format(input, input)+ str(box_id)
                            +"/box/meta_{}.txt -r error_{}.txt ".format(input,input) 
                            +" /bin/Rscript main.rs",
                        shell=True)


class java19:
    def compile(box_id):
        subprocess.call("cd /var/local/lib/isolate/" 
                        + str(box_id) 
                        + '/box;' 
                        + "javac --release 19 ./Main.java 2> error.txt",shell=True)
        if not (
        os.path.exists('/var/local/lib/isolate/' + str(box_id) + '/box/Main.java')):
            # If error file is empty but Main.class does not exist, main class name is not "Main"
            err_file = open('/var/local/lib/isolate/' + str(box_id) + '/box/error.txt', 'r+')

            if err_file.read() == "":
                err_file.write(
                    'Please use the main class name as "Main" only.')

            err_file.close()
            return False
        return True

    def run(box_id):
        print("java19")
        no_of_input_files = find('input_*.txt', box_id)
        for input in range(len(no_of_input_files)):
            subprocess.call("isolate --run "
                            +" -p --cg --cg "
                            +" --mem=26500000 "
                            +" --time=2 "
                            +" --wall-time=3 "
                            +" -b " + str(box_id) 
                            +" --share-net --full-env   --env=HOME=/home/mocha "
                            +" -o output_{}.txt -i input_{}.txt -M /var/local/lib/isolate/".format(input, input) 
                            + str(box_id) 
                            +"/box/meta_{}.txt -r error_{}.txt".format(input, input) 
                            +" /usr/lib/jvm/jdk-19/bin/java Main",
                            shell=True)

class cpp20:
    def compile(box_id):
        try:
            print("Compile Code")
            subprocess.call("cd /var/local/lib/isolate/" 
                            + str(box_id) 
                            + '/box;' 
                            + "/usr/bin/g++ -std=c++20  -Wall -Wextra -pedantic ./main.cpp -O2  -o output.out  2> error.txt",shell=True)
            if not (os.path.exists('/var/local/lib/isolate/' + str(box_id) + '/box/output.out')):
                return False
            return True
        except Exception as e:
            print(e)

    def run(box_id):
        print("Run code")
        no_of_input_files = find('input_*.txt', box_id)
        for input in range(len(no_of_input_files)):
            subprocess.call("isolate --run "
                            +" -p --cg -s "
                            +" --mem=265000 "
                            +" --time=2 "
                            +" --wall-time=3 "
                            +" -b " + str(box_id) 
                            +" -o output_{}.txt -i input_{}.txt -M /var/local/lib/isolate/".format(input, input) 
                            + str(box_id) 
                            + "/box/meta_{}.txt -r error_{}.txt ./output.out".format(input, input) ,shell=True)