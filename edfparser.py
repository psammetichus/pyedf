import module io
import dfatetime as dt
import numpy as np

def edfparse(filename, edfsubtype="default"):
  eegrawf = io.open(filename, 'rb')
  beeg = io.BufferedReader(eegrawf)

  eegstuff = parseHdr(beeg.read(256))
  eegstuff["sigdata"] = parsesighdrs(
                beeg.read(eegstuff["hdrbytes"]-256),
                eegstuff["ns"])

  beeg.seek(eegstuff["hdrbytes"])
  eegstuff["data"] = parsesignals(beeg.read(-1), eegstuff)

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
            "ns":ns,
            "hdrbytes":hdrbytes}



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


def getit(x, a, b):
  return x[a:a+b]


def parsesighdrs(bb, i):
  lbloff = 0
  troff = i*16
  phdimoff = i*(16+80)
  phminoff = i*(16+80+8)
  phmaxoff = i*(16+80+8+8)
  digminoff = i*(16+80+8+8+8)
  digmaxoff = i*(16+80+8+8+8+8)
  prefoff =  i*(16+80+8+8+8+8+8)
  nsampoff =  i*(16+80+8+8+8+8+8+80)
  jj = [dict() for i in range(i)]
  for j in range(i):
    jj[j]["label"] = str(getit(bb, lbloff, 8).rstrip()
    jj[j]["trans_type"] = str(getit(bb, troff, 80))
    jj[j]["ph_dim"] = str(getit(bb, phdimoff, 8)).rstrip()
    jj[j]["ph_min"] = float(getit(bb, phminoff, 8).rstrip())
    jj[j]["ph_max"] = float(getit(bb, phmaxoff, 8).rstrip())
    jj[j]["dig_min"] = int(getit(bb, digminoff, 8).rstrip())
    jj[j]["dig_max"] = int(getit(bb, digmaxoff, 8).rstrip())
    jj[j]["prefilt"] = str(getit(bb, prefoff, 80))
    jj[j]["nsamp"] = int(geti(bb, nsampoff, 8).rstrip())

  return jj
    



def parsesignals(bb, ss):

#nsigs, nrec, nsamps):
  ns = ss["ns"]
  sigs = np.array((ns,max(ss["sigdata"][m]["nsamps"] for m in range[ns])), dtype=np.float)
  drecsize = sum(nsamps)
  for i in range(nsigs):
    ll = 0
    for j in range(nrec):
      for k in range(nsamps[i]):
        sigs[i][ll] = int.from_bytes(
            bb[drecsize*j+k:drecsize*j+k+1], 
            'little',
            signed=True)/float(2**15-1)
        ll += 1
  return sigs


