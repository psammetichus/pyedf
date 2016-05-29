import io
import datetime as dt
import numpy as np

class EDFEEG:
  header = None
  sigdata = None
  signals = None
  def samp_rate(self, chan_N):
    return self.sig[chan_N].nsamp / self.header.dur

def edfparse(filename, edfsubtype="default"):
  eegrawf = io.open(filename, 'rb')
  beeg = io.BufferedReader(eegrawf)

  eegstuff = EDFEEG()
  eegstuff.header = parseHdr(beeg.read(256), edfsubtype)
  eegstuff.sigdata = parsesighdrs(
                beeg.read(eegstuff.header.hdrbytes-256),
                eegstuff.header.ns)

  beeg.seek(eegstuff.header.hdrbytes)
  eegstuff.data = parsesignals(beeg.read(-1), eegstuff)

  beeg.close()

class Header:
  def __init__(self):
    self.version = None 
    self.demo=None
    self.recinfo=None
    self.epoch = None
    self.hdrbytes=None
    self.ndr = None
    self.dur = None
    self.ns = None
    self.other = None



def parseHdr(bb, parsestyle):
  h = Header()
  h.version = int(bb[0:8].rstrip())
  if parsestyle == 'default':
      h.demo = parseptinfo(bb[8:88])
      h.recinfo = parserecinfo(bb[88:168])
  else:
      h.demo = ""
      h.recinfo = ""
      h.other = bb[8:168].decode()
  h.epoch = dt.datetime.strptime(bb[168:184].decode(),
        "%d.%m.%y%H.%M.%S")
  h.hdrbytes = int(bb[184:192])
  h.ndr = int(bb[236:244])
  h.dur = int(bb[244:252])
  h.ns = int(bb[252:256])
  return h

class Demographics:
  def __init__(self):
    self.name = None
    self.sex = None
    self.dob = None
    self.mrn = None


def parseptinfo(bb):
  [mrn, sex, bday, name, *rest] = bb.split(b" ")
  dob = dt.datetime.strptime(bday.decode(), "%d-%b-%Y").date()
  lname, gname = name.split(b"_")
  d = Demographics()
  d.name = (lname.decode(), gname.decode())
  d.sex = sex.decode()
  d.dob = dob.decode()
  d.mrn = mrn.decode()
  return d

def parserecinfo(bb):
  [stmark, stdate, eegnum, techcode, equipcode, *rest] = bb.split(b" ")
  recdate = dt.datetime.strptime(stdate.decode(), "%d-%b-%Y").date()
  return {  "recdate" : recdate.decode(),
            "eegnum"  : eegnum.decode(),
            "techcode"  : techcode.decode(),
            "equip" : equipcode.decode() }


def getit(x, a, b):
  return x[a:a+b]

class ChannelInfo:
  label = ""
  trans_type = ""
  ph_dim = ""
  ph_min = None
  ph_max = None
  dig_min = None
  dig_max = None
  prefilt = ""
  nsamp = -1 # per data record


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
  jj = [ChannelInfo() for i in range(i)]
  for j in range(i):
    jj[j].label = getit(bb, lbloff, 8).rstrip().decode()
    jj[j].trans_type = getit(bb, troff, 80).decode()
    jj[j].ph_dim = getit(bb, phdimoff, 8).rstrip().decode()
    jj[j].ph_min = float(getit(bb, phminoff, 8).rstrip())
    jj[j].ph_max = float(getit(bb, phmaxoff, 8).rstrip())
    jj[j].dig_min = int(getit(bb, digminoff, 8).rstrip())
    jj[j].dig_max = int(getit(bb, digmaxoff, 8).rstrip())
    jj[j].prefilt = getit(bb, prefoff, 80).decode()
    jj[j].nsamp = int(getit(bb, nsampoff, 8).rstrip())

  return jj
    

def storeit(sig, off, i, k):
  sig[i,off[i]] = k

def transform(qty, dmin, dmax, phmin, phmax):
    qq = (qty-dmin)/float(dmax-dmin)
    return qq*(phmax-phmin)+phmin

def tx_by_sig(qty, sigdata, i):
    return transform(qty, sigdata[i].dig_min, sigdata[i].dig_max,
                            sigdata[i].ph_min, sigdata[i].ph_max)

def parsesignals(bb, ss):
  ns = ss.header.ns
  nsamps = [ss.sigdata[k].nsamp for k in range(ns)]
  sigs = np.zeros( (ns, max(nsamps)*ss.header.ndr), dtype=np.float)
  drecsize = sum(nsamps)
  offsets = [0 for i in range(ns)]
  buffers = [np.zeros( nsamps[i], dtype=np.int16) for i in range(ns)]

  #loop over drecs
  for i in range(ss.header.ndr):
    k = i*drecsize
    #loop over sig chunks in a drec
    for j in range(ns):
      m = i*drecsize + nsamps[j]*2
      buffers[j] = np.frombuffer(bb[k:m+1], dtype=np.int16)
      storeit(sigs, offsets, j, tx_by_sig(buffers[j], ss.sigdata, j))
      offsets[j] = nsamps[j]
      k = m
  return sigs


