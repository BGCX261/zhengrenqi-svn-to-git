# -*- coding: utf-8 -*-
'''
Created on 2010-5-5

@author: Administrator
'''
import aes
import unittest
import hashlib

modes = 'OFB CFB CBC'.split()

class Test(unittest.TestCase):


  def setUp(self):
    pass


  def tearDown(self):
    pass


  def test01(self):
    print '-------------------------'
    plaintext = 'This is just an example'
    moo = aes.AESModeOfOperation()
    for smode in modes:
      pymode = moo.modeOfOperation[smode]
      print 'mode %r (%s)' % (smode, pymode)
      skey = 'Call me Ishmael.'[:16]
      #print 'skey is %s' % skey
      nkey = str2nums(skey)
      print 'nkey:', nkey
      #[67, 97, 108, 108, 32, 109, 101, 32, 73, 115, 104, 109, 97, 101, 108, 46]
      iv = [12, 34, 96, 15] * 4
      pymo, pyos, pyen = moo.encrypt(plaintext, pymode, nkey, len(nkey), iv)
      print '  PY enc (mode=%s, orgsize=%s):' % (pymo, pyos)
      print ' ', pyen

      pydec = moo.decrypt(pyen, pyos, pymo, nkey, len(nkey), iv)
      print '  PY dec (mode=%s, orgsize=%s):' % (pymo, pyos)
      print pydec
    pass

  def test02(self):
    print '-------------------------'
    plaintext = 'This is not a block length.'
    #54686973206973206a75737420616e206578616d706c65
    #54686973206973206a75737420616e206578616d706c65
    textnum = str2nums(plaintext);
    print textnum
    print str2hex(plaintext)
    moo = aes.AESModeOfOperation()
    smode = 'CBC'
    pymode = moo.modeOfOperation[smode]
    print 'mode %r (%s)' % (smode, pymode)
    skey = 'Call me Ishmael.'[:16]
    #print 'skey is %s' % skey
    nkey = str2nums(skey)
    print 'nkey:', nkey
    #[67, 97, 108, 108, 32, 109, 101, 32, 73, 115, 104, 109, 97, 101, 108, 46]
    #iv = [12, 34, 96, 15] * 4
    iv = [12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15]
    pymo, pyos, pyen = moo.encrypt(plaintext, pymode, nkey, len(nkey), iv)
    print '  PY enc (mode=%s, orgsize=%s):' % (pymo, pyos)
    print type(bytes(pyen[1])), bytes(pyen[1])

    print ' pyen:' , type(pyen), pyen
    print ashex(pyen)
    pyos = 32
    pydec = moo.decrypt(pyen, pyos, pymo, nkey, len(nkey), iv)
    print '  PY dec (mode=%s, orgsize=%s):' % (pymo, pyos)

    print pydec

    pass

  def test03(self):
    print '-------------------------'
    skey = 'Call me Ishmael.'[:16]
    nkey = str2nums(skey)
    plaintext = 'This is not a block length.'
    iv = [12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15]
    pyen = aes.encryptDataIv(nkey, plaintext, iv)
    print pyen
    print ashex(pyen)


  def testAesSha256en(self):
    print 'testAesSha256-------------------------'
    password = 'zhengrenqi'
    sha = hashlib.sha256()
    sha.update(password)
    key = str2nums(sha.digest())

    md5 = hashlib.md5()
    md5.update(password)
    iv = str2nums(md5.digest())

    plaintext = "This is zhengrenqi's text."

    pyen = aes.encryptDataIv(key, plaintext, iv)
    print 'pyen:' , type(pyen), pyen
    print ashex(pyen)

  def testAesSha256de(self):
    password = 'zhengrenqi'
    sha = hashlib.sha256()
    sha.update(password)
    dm = sha.digest()
    key = str2nums(dm)

    md5 = hashlib.md5()
    md5.update(password)
    iv = str2nums(md5.digest())
    enhex = 'bda7fe34586e7297a661ba30b2df27d05e54fb579224ab5d1f6bbc11ec330d01'
    endata = hex2ls(enhex)

    plaintext = aes.decryptDataIv(key, endata, iv)
    print plaintext
    pass
  def test08(self):
    print 'test08-------------------------'
    # en--
    key = 'Call me Ishmael.'[:16]
    key = map(ord, key)
    data = 'This is not a block length.'
    mode = aes.AESModeOfOperation.modeOfOperation["CBC"]


    if mode == aes.AESModeOfOperation.modeOfOperation["CBC"]:
        data = aes.append_PKCS7_padding(data)
    keysize = len(key)
    assert keysize in aes.AES.keySize.values(), 'invalid key size: %s' % keysize
    # create a new iv using random data
    iv = [12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15, 12, 34, 96, 15]
    moo = aes.AESModeOfOperation()
    (mode, length, ciph) = moo.encrypt(data, mode, key, keysize, iv)
    # With padding, the original length does not need to be known. It's a bad
    # idea to store the original message length.
    # prepend the iv.
    encrypt_data = ciph
    print aes.decryptDataIv(key, ciph, iv)


    keysize = len(key)
    assert keysize in aes.AES.keySize.values(), 'invalid key size: %s' % keysize
    # iv is first 16 bytes
    #iv = map(ord, encrypt_data[:16])

    moo = aes.AESModeOfOperation()
    decr = moo.decrypt(encrypt_data, None, mode, key, keysize, iv)
    if mode == aes.AESModeOfOperation.modeOfOperation["CBC"]:
        decr = aes.strip_PKCS7_padding(decr)
    print decr
  #[37, -54, -113, -33, -35, -30, 30, 31, 102, -14, -49, 121, 44, 56, 23, 53, 32, 58, -23, 36, 5, -119, -78, -9, 95, -21, 125, -59, 119, 35, 16, 31]
  #[37, 202, 143, 223, 221, 226, 30, 31, 102, 242, 207, 121, 44, 56, 23, 53, 32, 58, 233, 36, 5, 137, 178, 247, 95, 235, 125, 197, 119, 35, 16, 31]

    #25ca8fdfdde21e1f66f2cf792c381735203ae924589b2f75feb7dc57723101f
    #25ca8fdfdde21e1f66f2cf792c381735203ae9240589b2f75feb7dc57723101f

  def testhex(self):
    s = 'T'
    print ord(s)
    print eval('0x0a')
    hexstr = 'e35601000001000000000000037777770475313438036e65740000010001'
    print [hexstr[i * 2:i * 2 + 2] for i in range(len(hexstr) / 2)]
    print hex2ls(hexstr)
    print lambda hexstr:chr(int(hexstr, 16))
    print map(str.__add__, hexstr[::2], hexstr[1::2])
    print [hexstr[i * 2:i * 2 + 2] for i in range(len(hexstr) / 2)]
    s = ''.join(map(lambda hexstr:chr(int(hexstr, 16)), map(str.__add__, hexstr[::2], hexstr[1::2])))
    print repr(s)
    print '1'.zfill(2)
    pass

  def testSHA256(self):
    print 'testSHA256-------------------------'
    sha = hashlib.sha256()
    sha.update('zhengrenqi')
    dm = sha.digest()
    print str2nums(dm)
    print str2hex(dm)
    pass

  def testUnsignedInt(self):
    a = -86
    print 0x000000ff & a
    pass

  def testAesSha256EnCrypt(self):
    password = raw_input('password:')
    repass = raw_input('re input password:')
    if repass != password :
      raise Exception()
    data = """renqizheng恢复
2010-1-8
cal 2010-2-23
pic 2010-2-23
"""
    print len(data)
    en = aes.encryptDataPassword(password, data)
    print '------'
    print len(en), en

    pass
def str2nums(s):
    return map(ord, s)

def str2hex(s):
  return ashex(str2nums(s))

def nums2str(ns):
    return ''.join(map(chr, ns))

def ashex(ls):
  return ''.join([hex(a)[2:].zfill(2)for a in ls])
def toUnsignedInt(bytes):
  return [0x000000ff & a for a in bytes]

def hex2ls(hexstr):
  return [eval('0x' + hexstr[i * 2:i * 2 + 2]) for i in range(len(hexstr) / 2)]

if __name__ == "__main__":
  import sys;sys.argv = ['', 'Test.testAesSha256EnCrypt' ]
  unittest.main()
