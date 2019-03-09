# -*- coding: utf-8 -*-

import telnetlib

i = 1
with open("https_ip.txt", "r") as f:
    with open("httpsFreeProxy.txt", "a") as f2:
        for line in f.readlines():
            res = line.replace("\n", "").split("\t")
            https_ip = res[0]
            port = res[1]
            print("第", i, "个")
            f2.write(https_ip + ":" + port + "\n")
            """
            try:
                telnetlib.Telnet(https_ip, port, timeout=1)
                print(https_ip)
                
            except:
                pass
            i += 1
            if i > 200:
                break
            """

