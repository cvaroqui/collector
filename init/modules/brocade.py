import os

class Brocade(object):
    def __init__(self, dir=None):
        if dir is None:
            return
        self.dir = dir
        self.name = os.path.basename(dir)
        self.load_switchshow()
        self.load_nsshow()

    def readfile(self, fname):
        fpath = os.path.join(self.dir, fname)
        with open(fpath, 'r') as f:
            buff = f.read()
        return buff

    def load_nsshow(self):
        """
 Type Pid    COS     PortName                NodeName                 TTL(sec)
 N    020f01;      3;50:01:43:80:07:2d:f5:e6;50:01:43:80:07:2d:f5:e7; na
    FC4s: FCP 
    NodeSymb: [33] "QMH2462 FW:v5.04.04 DVR:v9.1.9.26"
    Fabric Port Name: 20:20:00:05:33:40:1e:53 
    Permanent Port Name: 20:11:00:05:33:a0:e6:42
    Port Index: 32
    Share Area: No
    Device Shared in Other AD: No
    Redirect: No 
    Partial: No
        """
        lines = self.readfile("brocadensshow").split('\n')
        for i, line in enumerate(lines):
            if len(line) <= 2:
                continue
            if line[1] != ' ':
                # new entry
                l = line.split(';')
                if len(l) != 5:
                    continue
                portname = l[2].replace(':','')
                continue
            elif line.strip().startswith('Port Index:'):
                index = line.split(':')[-1].strip()
                self.ports[index]['nse'].append(portname)

    def load_switchshow(self):
        lines = self.readfile("brocadeswitchshow").split('\n')
        self.ports = {}
        self.rindex = {}
        for i, line in enumerate(lines):
            if line.startswith("switchName:"):
                self.name = line.split(':')[1].strip().lower()
            elif line.startswith("switchType"):
                self.model = line.split(':')[1].strip()
            elif line.startswith("switchWwn"):
                self.wwn = ''.join(line.split(':')[1:]).strip()
            elif line.startswith("===="):
                start = i + 1
                comment_idx = len(line)
                cols = lines[i-1].split()
                n_cols = len(cols)
                break
        for line in lines[start:]:
            if len(line) < comment_idx:
                continue
            a = line[:comment_idx]
            comment = line[comment_idx:]
            l = a.split()
            port = {
              "Index": "",
              "Slot": "0",
              "Port": "",
              "Type": "",
              "RemotePortName": "",
              "Nego": "",
              "Speed": 0,
              "nse": [],
            }
            for i, col in enumerate(cols):
                if len(l)-1 < i:
                    break
                port[col] = l[i]
            if 'Area' in port:
                port['Index'] = port['Area']
            if len(comment) > 0:
                if 'E-Port' in comment:
                    port['Type'] = 'E-Port'
                elif 'F-Port' in comment:
                    port['Type'] = 'F-Port'
                l = comment.split()
                if len(l) >= 2 and ':' in l[1]:
                    port['RemotePortName'] = l[1].replace(':','').lower()
                if "master is Port" in comment:
                    master = comment.split('Port')[-1].strip(')').strip()
                    port['TrunkMaster'] = port['Slot'], master
            if port['Speed'] == "AN":
                port['Speed'] = 0
                port['Nego'] = False
            elif port['Speed'].startswith('N'):
                port['Speed'] = int(port['Speed'].replace('N',''))
                port['Nego'] = True
            elif port['Speed'].endswith('G'):
                port['Speed'] = int(port['Speed'].replace('G',''))
                port['Nego'] = False
            self.rindex[port['Slot'], port['Port']] = port['Index']
            self.ports[port['Index']] = port

        # assign slave trunk port remote port name
        # E-Port  (Trunk port, master is Port  3 )
        for port in self.ports.values():
            if "TrunkMaster" not in port:
                continue
            i = port['Index']
            ri = self.rindex[port['TrunkMaster']]
            self.ports[i]['RemotePortName'] = self.ports[ri]['RemotePortName']

    def __str__(self):
        s = "name: %s\n" % self.name
        s += "model: %s\n" % self.model
        s += "wwn: %s\n" % self.wwn
        for d in self.ports.values():
            s += "index %s slot %s port %s: type %s, remote %s, speed %d, nego %s\n"%(str(d['Index']), str(d['Slot']), str(d['Port']), str(d['Type']), str(d['RemotePortName']), d['Speed'], str(d['Nego']))
            for nse in d['nse']:
                s += "  ns entry: %s\n" % nse
        return s


def get_brocade(dir=None):
    try:
        return Brocade(dir)
    except:
        return None

import sys
def main():
    s = Brocade(sys.argv[1])
    print s

if __name__ == "__main__":
    main()

