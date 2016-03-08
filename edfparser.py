import module io
import datetime as dt

def edfparse(filename):
  eegrawf = io.open(filename, 'rb')
  beeg = io.BufferedReader(eegrawf)

  eegstuff = parseHdr(str(beeg.read(256)))

  ns = eegstuff["ns"]
  
  labels = 

  beeg.close()


def parseHdr(bb):
  version = int(bb[0:8].rstrip())
  ptinfo = parseptinfo(bb[8:88])
  recinfo = parserecinfo(bb[88:168])
  epoch = dt.datetime.strptime(bb[168:184],
        "%d.%m.%y%h.%M.%S")
  hdrbytes = int(bb[184:192])
  ndr = int(bb[236:244])
  dur_dr = int(bb[244:252])
  ns = int(bb[252:256])
  return {  "demo":ptinfo,
            "recinfo":recinfo,
            "epoch":epoch,
            "ndr":ndr,
            "dur":dur_dr,
            "ns":ns}



def parseptinfo(bb):
  [mrn, sex, bday, name] = bb.split(" ")
  dob = dt.datetime.strptime(bday, "%d-%b-%Y").date()
  lname, gname = name.split("_")
  return {"name":(lname,gname),
          "sex":sex,
          "dob":dob,
          "mrn":mrn}


def parserecinfo(bb):
  [stmark, stdate, eegnum, techcode, equipcode] = bb.split(" ")
  recdate = dt.datetime.strptime(stdate, "%d-%b-%Y").date()
  return {  "recdate" : recdate,
            "eegnum"  : eegnum,
            "techcode"  : techcode,
            "equip" : equipcode }


