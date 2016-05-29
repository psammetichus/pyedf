import io
import datetime as dt
import numpy as np

class EDFEEG:
  header = None
  sigdata = None
  signals = None
  def samp_rate(self, chan_N):
    return self.sig[chan_N].nsamp / self.header.dur
  def labels(self):
    return [i.label for i in self.sigdata]



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
  return eegstuff

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
  h.dur = float(bb[244:252])
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

class field:
  def __init__(self, fieldlabel, offset, length, post):
    self.lbl = fieldlabel
    self.off = offset
    self.length = length
    self.post = post
  
  def postprocess(self, bytesvalue):
    if self.post == 'float':
      return float(bytesvalue.rstrip())
    elif self.post == 'int':
      return int(bytesvalue.rstrip())
    elif self.post == "str":
      return bytesvalue.rstrip().decode()
    elif self.post == 'lstr':
      return bytesvalue.decode()


def parsesighdrs(bb, i):
  jj = [ChannelInfo() for i in range(i)]

  offsets = [ 
    field('label', 0, 16, 'str'),
    field('trans_type', 16, 80, 'lstr'),
    field('ph_dim', (16+80), 8, 'str'),
    field('ph_min', (16+80+8), 8, 'float'),
    field('ph_max', (16+80+8+8), 8, 'float'),
    field('dig_min', (16+80+8+8+8), 8, 'int'),
    field('dig_max', (16+80+8+8+8+8), 8, 'int'),
    field('prefilt',  (16+80+8+8+8+8+8), 80, 'lstr'),
    field('nsamp',  (16+80+8+8+8+8+8+80), 8, 'int') ]

  for fld in offsets:
    for j in range(i):
      setattr(jj[j], fld.fieldlabel, 
            fld.postprocess(
              getit(bb, fld.offset, fld.length)))

  return jj



def storeit(sig, off, i, k, n):
    sig[i,off[i]:off[i]+n] = k

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
    print("k is : {}".format(k))#printdebug
    print("drec number is : {0} out of {1}".format(i, ss.header.ndr))#printdebug
    #loop over sig chunks in a drec
    for j in range(ns):
      print("j is : {}".format(j))#printdebug
      m = k + nsamps[j]*2
      print("buffer size is : {}".format(buffers[j].size))#printdebug
      print ("index difference is : {}".format(m-k))#printdebug
      aa = np.frombuffer(bb[k:m], dtype=np.int16)
      print("Actual retrieved buf size : {}".format(aa.size))#printdebug
      buffers[j] = aa
      storeit(sigs, offsets, j, tx_by_sig(buffers[j], ss.sigdata, j), nsamps[j])
      offsets[j] = nsamps[j]
      k = m
  return sigs


