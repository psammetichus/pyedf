import io
import datetime as dt
import numpy as np

class EDFEEG:
  header = None
  siginfo = None
  signals = None
  def samp_rate(self, chan_N):
    return self.siginfo[chan_N].nsamp / self.header.dur
  def labels(self):
    return [i.label for i in self.siginfo]


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


class Demographics:

  def __init__(self):
    self.name = None
    self.sex = None
    self.dob = None
    self.mrn = None


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


def edfparse(filename, edftype="default"):
  eegrawf = io.open(filename, 'rb')
  beeg = io.BufferedReader(eegrawf)

  eegstuff = EDFEEG()
  eegstuff.header = parseHdr(beeg.read(256), edftype)
  eegstuff.siginfo = parsesighdrs(
                beeg.read(eegstuff.header.hdrbytes-256),
                eegstuff.header.ns)

  beeg.seek(eegstuff.header.hdrbytes)
  eegstuff.data = parsesignals(beeg.read(-1), eegstuff)

  beeg.close()
  return eegstuff


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
  k = 0
  for fld in offsets:
    for j in range(i):
      a = getit(bb, k+j*fld.length + fld.off, fld.length)
      setattr(jj[j], fld.lbl, fld.postprocess(a))
    k += (i-1)*fld.length
  return jj


def storeit(sig, off, i, k, n):
    sig[i,off[i]:off[i]+n] = k


def transform(qty, dmin, dmax, phmin, phmax):
    qq = (qty-dmin)/float(dmax-dmin)
    return qq*(phmax-phmin)+phmin


def tx_by_sig(qty, siginfo, i):
    return transform(qty, siginfo[i].dig_min, siginfo[i].dig_max,
                            siginfo[i].ph_min, siginfo[i].ph_max)


def parsesignals(bb, ss):
  ns = ss.header.ns
  nsamps = [ss.siginfo[k].nsamp for k in range(ns)]
  sigs = np.zeros( (ns, max(nsamps)*ss.header.ndr), dtype='<f8')
  drecsize = sum(nsamps)
  offsets = [0 for i in range(ns)]
  buffers = [np.zeros( nsamps[i], dtype='<i2') for i in range(ns)]

  #loop over drecs
  for i in range(ss.header.ndr):
    k = i*drecsize
    #loop over sig chunks in a drec
    for j in range(ns):
      m = k + nsamps[j]*2
      buffers[j] = np.frombuffer(bb[k:m], dtype='<i2')
      #storeit(sigs, offsets, j, buffers[j], nsamps[j])
      storeit(sigs, offsets, j, tx_by_sig(buffers[j], ss.siginfo, j), nsamps[j])
      offsets[j] += nsamps[j]
      k = m
  return sigs


