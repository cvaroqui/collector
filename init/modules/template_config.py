#!/usr/bin/env python 
# coding: utf8 
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
# request, response, session, cache, T, db(s) 
# must be passed and cannot be imported!
http_host = "opensvc.mydomain.com"

token_quota = 150000
billing_method = "agents"

sansymphony_v_pool = {
  'local': {
    'sds1_pool1': 'sds1:sds1_pool1',
    'sds2_pool2': 'sds2:sds2_pool2',
  },
  'dcspra2': {
  },
  'dcslmw1': {
  },
}
sansymphony_v_mirrored_pool = {
  'local': {
    'sds1_pool1': 'sds1:sds1_pool1,sds2:sds2_pool2',
    'sds2_pool2': 'sds1:sds1_pool1,sds2:sds2_pool2',
  },
  'dcspra2': {
    'sdsert01_sas_optima3': 'sdsert01:sdsert01_sas_optima3,sdsert02:sdsert02_sas_optima3',
    'sdsert02_sas_optima3': 'sdsert01:sdsert01_sas_optima3,sdsert02:sdsert02_sas_optima3',
  },
  'dcslmw1': {
    'sdslmw01_miroir_n2_argent': 'sdslmw01:sdslmw01_miroir_n2_argent,sdslmw03:sdslmw03_miroir_n3_argent',
    'sdslmw03_miroir_n3_argent': 'sdslmw01:sdslmw01_miroir_n2_argent,sdslmw03:sdslmw03_miroir_n3_argent',
    'sdslmw01_miroir_n2_or': 'sdslmw01:sdslmw01_miroir_n2_or,sdslmw03:sdslmw03_miroir_n3_or',
    'sdslmw03_miroir_n3_or': 'sdslmw01:sdslmw01_miroir_n2_or,sdslmw03:sdslmw03_miroir_n3_or',
    'sdslmw01_miroir_n2_platine': 'sdslmw01:sdslmw01_miroir_n2_platine,sdslmw03:sdslmw03_miroir_n3_platine',
    'sdslmw03_miroir_n3_platine': 'sdslmw01:sdslmw01_miroir_n2_platine,sdslmw03:sdslmw03_miroir_n3_platine',
  },
}

stats_retention_days = 367
